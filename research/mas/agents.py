r"""
agents.py
=========
Concrete implementations of specialized autonomous agents for urban transit decision support.

Agents:
1. UserPreferenceAgent (A_user)
2. PublicTransitAgent (A_bmtc)
3. MetroAgent (A_metro)
4. CabMobilityAgent (A_cab)
5. PersonalVehicleAgent (A_veh)
6. ContextAgent (A_ctx)
7. CoordinatorAgent / RecommendationAgent (A_coord)
8. ExplainabilityAgent (A_xai)
"""

import os
import sys
import math
import traceback
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Setup paths for mode-specific modules
_HERE = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_HERE, "..", ".."))
_BACKEND = os.path.join(_WORKSPACE, "backend")
_METRO = os.path.join(_BACKEND, "modes", "metro")
_BMTC = os.path.join(_BACKEND, "modes", "bmtc")
_CAB = os.path.join(_BACKEND, "modes", "cab")

for p in [_WORKSPACE, _BACKEND]:
    if p not in sys.path:
        sys.path.insert(0, p)

from research.mas.agent_interface import (
    BaseAgent,
    AgentObservation,
    CandidateJourney,
    AgentResult,
    AgentMessage,
    AgentMessageType
)
from backend.recommender import calculate_emissions, get_comfort_score, calculate_weather_exposure
from backend.shared.utils import haversine_distance, resolve_stop_name

KNOWN_COORDS = {
    "majestic": (12.9779, 77.5724),
    "indiranagar": (12.9784, 77.6385),
    "whitefield": (12.9698, 77.7500),
    "domlur": (12.9610, 77.6387),
    "koramangala": (12.9352, 77.6245),
    "silk board": (12.9173, 77.6233),
    "hsr layout": (12.9121, 77.6446),
    "agara": (12.9238, 77.6534),
    "jayanagar": (12.9308, 77.5838),
    "jp nagar": (12.9077, 77.5855),
    "mg road": (12.9756, 77.6066),
    "residency road": (12.9702, 77.6045),
    "electronic city": (12.8452, 77.6602),
    "hebbal": (13.0359, 77.5970),
    "yeshwanthpur": (13.0238, 77.5503),
    "banashankari": (12.9166, 77.5735),
    "rajajinagar": (12.9882, 77.5549),
    "marathahalli": (12.9592, 77.6974),
    "kengeri": (12.8996, 77.4827),
    "itpl": (12.9863, 77.7377),
    "nagasandra": (13.0477, 77.5022),
    "yelahanka": (13.1007, 77.5963),
    "kempegowda international airport": (13.1986, 77.7066),
    "bannerghatta": (12.8009, 77.5777),
    "devanahalli": (13.2483, 77.7127)
}

METRO_STATION_MAP = {
    "majestic": "Majestic",
    "indiranagar": "Indiranagar",
    "whitefield": "Whitefield",
    "domlur": "Indiranagar",
    "koramangala": "Central Silk Board",
    "silk board": "Central Silk Board",
    "hsr layout": "Central Silk Board",
    "agara": "Central Silk Board",
    "jayanagar": "Jayanagara",
    "jp nagar": "Jaya Prakash Nagara",
    "mg road": "MG Road",
    "residency road": "MG Road",
    "electronic city": "Electronic City",
    "hebbal": "Yeshwanthpur",
    "yeshwanthpur": "Yeshwanthpur",
    "banashankari": "Banashankari",
    "rajajinagar": "Rajajinagar",
    "marathahalli": "Singayyanapalya",
    "kengeri": "Kengeri",
    "itpl": "Pattandur Agrahara",
    "nagasandra": "Nagasandra",
    "yelahanka": "Nagasandra",
    "bannerghatta": "Silk Institute"
}

def resolve_coords(name: str) -> Optional[Tuple[float, float]]:
    n = name.lower().strip()
    for k, v in KNOWN_COORDS.items():
        if k in n or n in k:
            return v
    return None

def get_distance_between_stops(source: str, destination: str) -> float:
    """Calculate geographic Haversine distance between two stop/station names in kilometers."""
    c1 = resolve_coords(source)
    c2 = resolve_coords(destination)
    if c1 and c2:
        dist_m = haversine_distance(c1[0], c1[1], c2[0], c2[1])
        return round(dist_m / 1000.0, 2)
    return 10.0


def _clear_colliding_modules():
    for mod in ["engines", "planner"]:
        if mod in sys.modules:
            del sys.modules[mod]
    for mod in list(sys.modules.keys()):
        if mod.startswith("engines.") or mod.startswith("planner."):
            del sys.modules[mod]


# Metro import helper
def get_metro_planner():
    _clear_colliding_modules()
    if _METRO not in sys.path:
        sys.path.insert(0, _METRO)
    try:
        from planner.journey_planner import JourneyPlanner
        return JourneyPlanner()
    finally:
        if _METRO in sys.path:
            sys.path.remove(_METRO)


# BMTC import helper
def run_bmtc_search(source: str, destination: str):
    if _BMTC not in sys.path:
        sys.path.insert(0, _BMTC)
    try:
        from features.routing import get_all_buses_comprehensive
        return get_all_buses_comprehensive(source, destination)
    finally:
        if _BMTC in sys.path:
            sys.path.remove(_BMTC)


# Cab import helper
def get_cab_planner():
    _clear_colliding_modules()
    if _CAB not in sys.path:
        sys.path.insert(0, _CAB)
    try:
        from planner.ride_planner import RidePlanner
        return RidePlanner()
    finally:
        if _CAB in sys.path:
            sys.path.remove(_CAB)


class UserPreferenceAgent(BaseAgent):
    """
    User Preference Agent (A_user)
    Goal: Maintain user preference weights, trade-off willingness, and constraints.
    """

    def __init__(self, enable_preferences: bool = True):
        super().__init__(
            agent_id="agent_user",
            goal="Synthesize personalized multi-criteria preference weighting vector",
            role="agent"
        )
        self.enable_preferences = enable_preferences
        self.preference_profiles = {
            "cost": {"cost": 0.55, "time": 0.15, "comfort": 0.05, "eco": 0.05, "weather": 0.10, "traffic": 0.10},
            "cheapest": {"cost": 0.55, "time": 0.15, "comfort": 0.05, "eco": 0.05, "weather": 0.10, "traffic": 0.10},
            "time": {"cost": 0.10, "time": 0.50, "comfort": 0.05, "eco": 0.05, "weather": 0.10, "traffic": 0.20},
            "fastest": {"cost": 0.10, "time": 0.50, "comfort": 0.05, "eco": 0.05, "weather": 0.10, "traffic": 0.20},
            "convenience": {"cost": 0.10, "time": 0.15, "comfort": 0.45, "eco": 0.05, "weather": 0.15, "traffic": 0.10},
            "eco": {"cost": 0.15, "time": 0.15, "comfort": 0.10, "eco": 0.40, "weather": 0.10, "traffic": 0.10},
            "default": {"cost": 0.25, "time": 0.25, "comfort": 0.20, "eco": 0.10, "weather": 0.10, "traffic": 0.10}
        }
        self.uniform_weights = {"cost": 1/6, "time": 1/6, "comfort": 1/6, "eco": 1/6, "weather": 1/6, "traffic": 1/6}

    def observe(self, observation: AgentObservation) -> None:
        raw_pref = (observation.user_preferences.get("preference") or "cost").lower()
        self.state["preference_key"] = raw_pref
        if self.enable_preferences:
            self.state["weights"] = self.preference_profiles.get(raw_pref, self.preference_profiles["default"])
        else:
            self.state["weights"] = self.uniform_weights

    def evaluate_policy(self) -> List[CandidateJourney]:
        return []

    def get_weights(self) -> Dict[str, float]:
        if not self.enable_preferences:
            return self.uniform_weights
        return self.state.get("weights", self.preference_profiles["default"])


class ContextAgent(BaseAgent):
    """
    Context Agent (A_ctx)
    Goal: Monitor controlled synthetic/live weather scenarios and road traffic delay multipliers.
    """

    def __init__(self, enable_weather: bool = True, enable_traffic: bool = True):
        super().__init__(
            agent_id="agent_ctx",
            goal="Provide real-time weather exposure and road traffic delay context signals",
            role="agent"
        )
        self.enable_weather = enable_weather
        self.enable_traffic = enable_traffic

    def observe(self, observation: AgentObservation) -> None:
        env_ctx = observation.environmental_context or {}
        weather_info = env_ctx.get("weather", "clear")
        
        if isinstance(weather_info, dict):
            rain_prob = float(weather_info.get("rain_probability", 0.0))
            precip_mmhr = float(weather_info.get("precipitation_intensity_mmhr", 0.0))
            temp_c = float(weather_info.get("temperature_c", 25.0))
            vis_km = float(weather_info.get("visibility_km", 10.0))
        elif isinstance(weather_info, str):
            w_str = weather_info.lower()
            if "heavy rain" in w_str or "storm" in w_str:
                rain_prob, precip_mmhr, temp_c, vis_km = 80.0, 15.0, 22.0, 3.0
            elif "light rain" in w_str or "rain" in w_str:
                rain_prob, precip_mmhr, temp_c, vis_km = 40.0, 3.0, 24.0, 6.0
            else:
                rain_prob, precip_mmhr, temp_c, vis_km = 0.0, 0.0, 27.0, 10.0
        else:
            rain_prob, precip_mmhr, temp_c, vis_km = 0.0, 0.0, 27.0, 10.0

        traffic_mult = float(env_ctx.get("traffic_multiplier", 1.0))

        self.state["rain_probability"] = rain_prob if self.enable_weather else 0.0
        self.state["precipitation_intensity_mmhr"] = precip_mmhr if self.enable_weather else 0.0
        self.state["temperature_c"] = temp_c
        self.state["visibility_km"] = vis_km
        self.state["traffic_multiplier"] = traffic_mult if self.enable_traffic else 1.0
        self.state["weather_info"] = weather_info

    def evaluate_policy(self) -> List[CandidateJourney]:
        return []

    def assess_weather_suitability(self, mode: str, data: Dict[str, Any]) -> float:
        if not self.enable_weather:
            return 1.0
        
        weather_info = self.state.get("weather_info", "clear")
        exposure = calculate_weather_exposure(mode, data, weather_info)
        rain_prob = self.state.get("rain_probability", 0.0)
        
        penalty = (rain_prob / 100.0) * exposure * 0.85
        return max(0.1, round(1.0 - penalty, 2))

    def get_traffic_multiplier(self) -> float:
        if not self.enable_traffic:
            return 1.0
        return self.state.get("traffic_multiplier", 1.0)


class PublicTransitAgent(BaseAgent):
    """
    Public Transit Agent (A_bmtc)
    Goal: Query BMTC bus routes, timetables, and evaluate bus journey proposals.
    """

    def __init__(self):
        super().__init__(
            agent_id="agent_bmtc",
            goal="Generate optimal BMTC bus journey proposals",
            role="agent"
        )

    def observe(self, observation: AgentObservation) -> None:
        self.state["source"] = observation.source
        self.state["destination"] = observation.destination

    def evaluate_policy(self) -> List[CandidateJourney]:
        source = self.state.get("source")
        destination = self.state.get("destination")
        if not source or not destination:
            self.last_result = AgentResult(agent_id=self.agent_id, status="error", error_message="Missing source or destination")
            return []

        approx_dist = get_distance_between_stops(source, destination) or 10.0

        try:
            source_res = resolve_stop_name(source, "bmtc")
            dest_res = resolve_stop_name(destination, "bmtc")
            bmtc_res = run_bmtc_search(source_res, dest_res)
            if (not bmtc_res or bmtc_res == ([], [])) and (source_res != source or dest_res != destination):
                bmtc_res = run_bmtc_search(source, destination)

            if not bmtc_res or not isinstance(bmtc_res, tuple):
                self.last_result = AgentResult(agent_id=self.agent_id, status="no_route_found", diagnostics={"raw": str(bmtc_res)})
                return []

            direct_routes, transfer_routes = bmtc_res
            if direct_routes:
                best = min(direct_routes, key=lambda x: x.get("travel_time_mins", 999.0))
                cost = float(best.get("fare", 25.0))
                time_val = float(best.get("travel_time_mins", best.get("total_time_mins", 45.0)))
                dist_km = float(best.get("distance_km", best.get("total_distance_km", approx_dist)))
                transfers = 0
                raw_data = best
            elif transfer_routes:
                best = min(transfer_routes, key=lambda x: x.get("total_time", 999.0))
                cost = float(best.get("total_fare", 35.0))
                time_val = float(best.get("total_time", 55.0))
                dist_km = float(best.get("distance", approx_dist))
                transfers = int(best.get("transfers", 1))
                raw_data = best
            else:
                self.last_result = AgentResult(agent_id=self.agent_id, status="no_route_found", diagnostics={"message": "No direct or transfer bus routes found"})
                return []

            emissions = calculate_emissions("bmtc", dist_km)
            comfort = get_comfort_score("bmtc", transfers, dist_km)

            cand = CandidateJourney(
                agent_id=self.agent_id,
                mode="bmtc",
                cost=cost,
                time_min=time_val,
                distance_km=dist_km,
                transfers=transfers,
                emissions_g_co2=emissions,
                comfort_score=comfort,
                weather_exposure=0.55,
                traffic_delay_min=max(0.0, time_val * 0.2),
                raw_data=raw_data
            )
            self.last_result = AgentResult(agent_id=self.agent_id, status="success", candidates=[cand])
            return [cand]
        except Exception as e:
            err_msg = f"PublicTransitAgent error: {str(e)}"
            self.last_result = AgentResult(
                agent_id=self.agent_id,
                status="error",
                error_message=err_msg,
                diagnostics={"traceback": traceback.format_exc()}
            )
            return []


class MetroAgent(BaseAgent):
    """
    Metro Agent (A_metro)
    Goal: Evaluate Namma Metro rapid transit station hops, fares, and shelters.
    """

    def __init__(self):
        super().__init__(
            agent_id="agent_metro",
            goal="Generate high-speed, traffic-immune Metro journey proposals",
            role="agent"
        )

    def observe(self, observation: AgentObservation) -> None:
        self.state["source"] = observation.source
        self.state["destination"] = observation.destination

    def evaluate_policy(self) -> List[CandidateJourney]:
        source = self.state.get("source")
        destination = self.state.get("destination")
        if not source or not destination:
            self.last_result = AgentResult(agent_id=self.agent_id, status="error", error_message="Missing source or destination")
            return []

        approx_dist = get_distance_between_stops(source, destination) or 12.0

        # Map stop names to official Metro stations
        src_norm = source.lower().strip()
        dst_norm = destination.lower().strip()
        src_st = METRO_STATION_MAP.get(src_norm)
        dst_st = METRO_STATION_MAP.get(dst_norm)

        if not src_st or not dst_st or src_st == dst_st:
            self.last_result = AgentResult(
                agent_id=self.agent_id,
                status="no_route_found",
                diagnostics={"reason": f"No Metro station mapping or identical station ({src_st} -> {dst_st})"}
            )
            return []

        try:
            planner = get_metro_planner()
            plan = planner.plan_journey(src_st, dst_st)
            
            fare_raw = plan.get("fare")
            if isinstance(fare_raw, dict):
                cost = float(fare_raw.get("token", fare_raw.get("smart_card", 30.0)))
            else:
                cost = float(fare_raw or 30.0)

            time_raw = plan.get("estimated_time")
            if isinstance(time_raw, dict):
                time_val = float(time_raw.get("minutes", 25.0))
            else:
                time_val = float(time_raw or 25.0)

            transfers = 0
            route_info = plan.get("route", {})
            if isinstance(route_info, dict) and "legs" in route_info:
                transfers = max(0, len(route_info["legs"]) - 1)

            emissions = calculate_emissions("metro", approx_dist)
            comfort = get_comfort_score("metro", transfers, approx_dist)

            cand = CandidateJourney(
                agent_id=self.agent_id,
                mode="metro",
                cost=cost,
                time_min=time_val,
                distance_km=approx_dist,
                transfers=transfers,
                emissions_g_co2=emissions,
                comfort_score=comfort,
                weather_exposure=0.25,
                traffic_delay_min=0.0,
                raw_data=plan
            )
            self.last_result = AgentResult(agent_id=self.agent_id, status="success", candidates=[cand])
            return [cand]
        except Exception as e:
            err_msg = f"MetroAgent error: {str(e)}"
            self.last_result = AgentResult(
                agent_id=self.agent_id,
                status="error",
                error_message=err_msg,
                diagnostics={"traceback": traceback.format_exc()}
            )
            return []


class CabMobilityAgent(BaseAgent):
    """
    Cab Mobility Agent (A_cab)
    Goal: Estimate multi-provider ride-hailing fares (Ola, Uber, Rapido, Namma Yatri).
    """

    def __init__(self):
        super().__init__(
            agent_id="agent_cab",
            goal="Generate door-to-door cab and auto-rickshaw journey estimates",
            role="agent"
        )

    def observe(self, observation: AgentObservation) -> None:
        self.state["source"] = observation.source
        self.state["destination"] = observation.destination

    def evaluate_policy(self) -> List[CandidateJourney]:
        source = self.state.get("source")
        destination = self.state.get("destination")
        if not source or not destination:
            self.last_result = AgentResult(agent_id=self.agent_id, status="error", error_message="Missing source or destination")
            return []

        approx_dist = get_distance_between_stops(source, destination) or 10.0
        c1 = resolve_coords(source)
        c2 = resolve_coords(destination)

        try:
            planner = get_cab_planner()
            if c1 and c2:
                src_coords = {"place": source, "latitude": c1[0], "longitude": c1[1]}
                dst_coords = {"place": destination, "latitude": c2[0], "longitude": c2[1]}
                res = planner.plan_ride_from_coords(src_coords, dst_coords)
            else:
                res = planner.plan_ride(source, destination)

            fares = res.get("fares", {})
            if isinstance(fares, dict) and fares:
                # Pick auto fare if available, otherwise lowest fare option
                if "auto" in fares and isinstance(fares["auto"], dict):
                    cost = float(fares["auto"].get("fare", 150.0))
                else:
                    first_k = next(iter(fares))
                    cost = float(fares[first_k].get("fare", 180.0)) if isinstance(fares[first_k], dict) else 180.0
            else:
                cost = round(50.0 + (approx_dist * 18.0), 1)

            time_info = res.get("estimated_time", {})
            if isinstance(time_info, dict):
                time_val = float(time_info.get("minutes", round((approx_dist / 22.0) * 60, 1)))
            else:
                time_val = round((approx_dist / 22.0) * 60, 1)

            dist_info = res.get("distance", {})
            if isinstance(dist_info, dict):
                approx_dist = float(dist_info.get("distance_km", approx_dist))

            emissions = calculate_emissions("cab", approx_dist)
            comfort = get_comfort_score("cab", 0, approx_dist)

            cand = CandidateJourney(
                agent_id=self.agent_id,
                mode="cab",
                cost=cost,
                time_min=time_val,
                distance_km=approx_dist,
                transfers=0,
                emissions_g_co2=emissions,
                comfort_score=comfort,
                weather_exposure=0.10,
                traffic_delay_min=max(0.0, time_val * 0.25),
                raw_data=res
            )
            self.last_result = AgentResult(agent_id=self.agent_id, status="success", candidates=[cand])
            return [cand]
        except Exception as e:
            err_msg = f"CabMobilityAgent error: {str(e)}"
            self.last_result = AgentResult(
                agent_id=self.agent_id,
                status="error",
                error_message=err_msg,
                diagnostics={"traceback": traceback.format_exc()}
            )
            return []


class PersonalVehicleAgent(BaseAgent):
    """
    Personal Vehicle Agent (A_veh)
    Goal: Calculate route-specific driving distance, fuel costs, and vehicle operational metrics.
    """

    def __init__(self, mileage_kml: float = 15.0, fuel_price_per_l: float = 102.0):
        super().__init__(
            agent_id="agent_veh",
            goal="Generate personal vehicle fuel-cost and driving time estimates",
            role="agent"
        )
        self.mileage_kml = mileage_kml
        self.fuel_price_per_l = fuel_price_per_l

    def observe(self, observation: AgentObservation) -> None:
        self.state["source"] = observation.source
        self.state["destination"] = observation.destination

    def evaluate_policy(self) -> List[CandidateJourney]:
        source = self.state.get("source")
        destination = self.state.get("destination")
        if not source or not destination:
            self.last_result = AgentResult(agent_id=self.agent_id, status="error", error_message="Missing source or destination")
            return []

        try:
            dist_km = get_distance_between_stops(source, destination) or 10.0
            cost_per_km = self.fuel_price_per_l / self.mileage_kml
            cost = round(dist_km * cost_per_km, 1)
            time_val = round((dist_km / 25.0) * 60, 1)

            emissions = calculate_emissions("car", dist_km)
            comfort = get_comfort_score("car", 0, dist_km)

            cand = CandidateJourney(
                agent_id=self.agent_id,
                mode="car",
                cost=cost,
                time_min=time_val,
                distance_km=dist_km,
                transfers=0,
                emissions_g_co2=emissions,
                comfort_score=comfort,
                weather_exposure=0.10,
                traffic_delay_min=max(0.0, time_val * 0.25),
                raw_data={"mode": "car", "distance": dist_km, "cost": cost, "time": time_val}
            )
            self.last_result = AgentResult(agent_id=self.agent_id, status="success", candidates=[cand])
            return [cand]
        except Exception as e:
            err_msg = f"PersonalVehicleAgent error: {str(e)}"
            self.last_result = AgentResult(
                agent_id=self.agent_id,
                status="error",
                error_message=err_msg,
                diagnostics={"traceback": traceback.format_exc()}
            )
            return []


class CoordinatorAgent(BaseAgent):
    """
    Coordinator / Recommendation Agent (A_coord)
    Goal: Aggregate candidate proposals, execute Weighted Multi-Criteria Utility Aggregation U(j) = \sum w_k f_k(j),
          and rank candidate journey proposals.
    """

    def __init__(self, enable_coordination: bool = True):
        super().__init__(
            agent_id="agent_coord",
            goal="Consolidate and rank multi-agent journey proposals via Weighted Multi-Criteria Utility Aggregation",
            role="coordinator"
        )
        self.enable_coordination = enable_coordination

    def observe(self, observation: AgentObservation) -> None:
        pass

    def evaluate_policy(self) -> List[CandidateJourney]:
        return []

    def rank_candidates(
        self,
        candidates: List[CandidateJourney],
        weights: Dict[str, float],
        context_agent: ContextAgent,
        mode_override: str = "B5"
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        # If coordination is disabled (A4 Ablation), return candidates as-is without aggregation
        if not self.enable_coordination:
            return [{"candidate": c, "score": 50.0, "details": {}} for c in candidates]

        costs = [c.cost for c in candidates]
        times = [c.time_min for c in candidates]
        emissions = [c.emissions_g_co2 for c in candidates]

        min_c, max_c = min(costs), max(costs)
        min_t, max_t = min(times), max(times)
        min_e, max_e = min(emissions), max(emissions)

        ranked = []
        for c in candidates:
            # Min-Max Normalization f_k(j) in [0, 1]
            cost_score = 1.0 - ((c.cost - min_c) / (max_c - min_c)) if max_c > min_c else 1.0
            time_score = 1.0 - ((c.time_min - min_t) / (max_t - min_t)) if max_t > min_t else 1.0
            eco_score = 1.0 - ((c.emissions_g_co2 - min_e) / (max_e - min_e)) if max_e > min_e else 1.0

            weather_suit = context_agent.assess_weather_suitability(c.mode, c.raw_data)
            traffic_mult = context_agent.get_traffic_multiplier()
            traffic_suit = max(0.1, min(1.0, 1.0 - (c.traffic_delay_min * traffic_mult / max(1.0, c.time_min))))

            # Baseline-Specific Decision Strategies
            if mode_override == "B1":
                # B1: Shortest Time Only
                composite = time_score
            elif mode_override == "B2":
                # B2: Lowest Cost Only
                composite = cost_score
            elif mode_override == "B3":
                # B3: Static Weighted Sum (50% Cost, 50% Time, no weather/traffic)
                composite = 0.50 * cost_score + 0.50 * time_score
            else:
                # B4 / B5: Full Multi-Criteria Utility Aggregation U(j) = \sum w_k f_k(j)
                composite = (
                    weights["cost"] * cost_score +
                    weights["time"] * time_score +
                    weights["comfort"] * c.comfort_score +
                    weights["eco"] * eco_score +
                    weights["weather"] * weather_suit +
                    weights["traffic"] * traffic_suit
                )

            score = round(composite * 100.0, 1)

            ranked.append({
                "candidate": c,
                "score": score,
                "details": {
                    "cost_score": int(cost_score * 100),
                    "time_score": int(time_score * 100),
                    "comfort_score": int(c.comfort_score * 100),
                    "eco_score": int(eco_score * 100),
                    "weather_score": int(weather_suit * 100),
                    "traffic_score": int(traffic_suit * 100)
                }
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked


class ExplainabilityAgent(BaseAgent):
    """
    Explainability Agent (A_xai)
    Goal: Construct structured, quantitative trade-off XAI explanations for recommended routes.
    """

    def __init__(self):
        super().__init__(
            agent_id="agent_xai",
            goal="Generate mathematical and natural language XAI justifications",
            role="agent"
        )

    def observe(self, observation: AgentObservation) -> None:
        pass

    def evaluate_policy(self) -> List[CandidateJourney]:
        return []

    def generate_explanations(
        self,
        ranked_items: List[Dict[str, Any]],
        context_agent: ContextAgent,
        preference: str
    ) -> Dict[str, str]:
        explanations = {}
        rain_prob = context_agent.state.get("rain_probability", 0.0)

        for item in ranked_items:
            c: CandidateJourney = item["candidate"]
            mode = c.mode
            cost_str = f"Rs.{int(c.cost)}"
            time_str = f"{int(c.time_min)} mins"

            if mode == "metro":
                if rain_prob >= 40.0:
                    explanations[mode] = (
                        f"Metro is highly recommended: taking ~{time_str} for {cost_str}, "
                        f"it completely bypasses road congestion and shelters you from {int(rain_prob)}% forecast rain."
                    )
                else:
                    explanations[mode] = (
                        f"Metro offers rapid, traffic-free transit across {c.distance_km:.1f} km in {time_str} for {cost_str}."
                    )
            elif mode == "bmtc":
                explanations[mode] = (
                    f"BMTC Bus is the most economical choice at {cost_str} over {c.distance_km:.1f} km in ~{time_str}."
                )
            elif mode == "cab":
                explanations[mode] = (
                    f"Cab/Auto provides direct door-to-door comfort (~{time_str} for est. {cost_str}); pricing may vary with demand."
                )
            elif mode == "car":
                explanations[mode] = (
                    f"Private car offers direct flexibility (~{time_str}) with an estimated fuel cost of {cost_str}."
                )

        return explanations
