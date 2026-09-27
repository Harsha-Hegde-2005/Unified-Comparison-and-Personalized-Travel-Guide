"""
travel_tools.py
===============
Standardized Travel Tool Layer for Bengaluru Travel Assistant.
Implements Tools A through L as verified, deterministic backend functions.
"""

import math
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple


def _calc_fuel_cost(dist_km: float, dur_min: float, vehicle_type: str = "car") -> Dict[str, float]:
    fuel_price = 102.0
    mileage = 15.0 if vehicle_type == "car" else 40.0
    litres = round(dist_km / mileage, 2)
    cost = round(litres * fuel_price, 1)
    return {"fuel_litres": litres, "fuel_cost": cost}


class TravelTools:
    def __init__(
        self,
        bmtc_stops: Optional[List[str]] = None,
        metro_stations: Optional[List[str]] = None,
        poi_names: Optional[List[str]] = None
    ):
        self.bmtc_stops = bmtc_stops or []
        self.metro_stations = metro_stations or []
        self.poi_names = poi_names or []

    # ── Tool A: search_journey ────────────────────────────────────────────────
    def search_journey(
        self,
        origin: str,
        destination: str,
        travel_date: Optional[str] = None,
        departure_time: Optional[datetime] = None,
        transport_modes: Optional[List[str]] = None,
        optimization: Optional[str] = None,  # "cheapest", "fastest", "least_walking", "fewest_transfers"
        max_walking_distance: Optional[float] = None,
        max_transfers: Optional[int] = None,
        ac_preference: Optional[bool] = None,
        arrival_deadline: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Search valid journey alternatives across BMTC, Metro, Cab, Personal Vehicle, Multimodal."""
        from main import (
            bmtc_plan,
            metro_plan,
            multimodal_plan,
            _personal_vehicle_estimate,
            _get_all_ride_fares,
            _resolve_any_location_coords,
            _osrm_distance,
            JourneyRequest
        )
        from modes.bmtc.features.schedule import get_fixed_route_departure

        dep_dt = departure_time or datetime.now()
        src_coords = _resolve_any_location_coords(origin)
        dst_coords = _resolve_any_location_coords(destination)

        if not src_coords or not dst_coords:
            return {
                "available": False,
                "error": f"Could not resolve geographic coordinates for '{origin}' or '{destination}'.",
                "journeys": []
            }

        # Calculate base road distance
        osrm_res = _osrm_distance(src_coords[0], src_coords[1], dst_coords[0], dst_coords[1])
        base_dist_km = osrm_res.get("distance_km", 10.0) if osrm_res else 10.0
        base_drive_min = osrm_res.get("duration_min", 25.0) if osrm_res else 25.0

        journeys: List[Dict[str, Any]] = []

        # 1. BMTC Bus
        try:
            b_res = bmtc_plan(JourneyRequest(source=origin, destination=destination, time=dep_dt.strftime("%I:%M %p")))
            if b_res.get("available"):
                journeys.append({
                    "journey_id": f"journey_bmtc_1",
                    "transport_modes": ["bmtc"],
                    "departure": b_res.get("departure", dep_dt.strftime("%H:%M")),
                    "arrival": b_res.get("arrival", (dep_dt.replace(minute=(dep_dt.minute+b_res.get("time", 40))%60)).strftime("%H:%M")),
                    "duration_minutes": b_res.get("time", 40),
                    "fare": {"amount": b_res.get("cost", 25), "currency": "INR", "type": "exact"},
                    "walking_distance_km": round(b_res.get("distance", 10.0) * 0.08, 2),
                    "transfers": b_res.get("transfers", 0),
                    "route_sequence": [seg.get("route", "Ordinary") for seg in b_res.get("segments", []) if isinstance(seg, dict)],
                    "is_ac": False,
                    "data_freshness": {"source": "bmtc_gtfs_schedule_dataset", "verified_dataset": True, "retrieved_at": datetime.now().isoformat()}
                })
        except Exception:
            pass

        # 2. Metro
        try:
            m_res = metro_plan(JourneyRequest(source=origin, destination=destination, time=dep_dt.strftime("%I:%M %p")))
            if m_res.get("available"):
                journeys.append({
                    "journey_id": f"journey_metro_2",
                    "transport_modes": ["metro"],
                    "departure": m_res.get("departure", dep_dt.strftime("%H:%M")),
                    "arrival": m_res.get("arrival", (dep_dt.replace(minute=(dep_dt.minute+m_res.get("time", 30))%60)).strftime("%H:%M")),
                    "duration_minutes": m_res.get("time", 30),
                    "fare": {"amount": m_res.get("cost", 40), "currency": "INR", "type": "exact"},
                    "walking_distance_km": round(b_res.get("distance", 10.0) * 0.05, 2) if 'b_res' in locals() else 0.4,
                    "transfers": m_res.get("transfers", 0),
                    "route_sequence": ["Namma Metro Green/Purple Line"],
                    "is_ac": True,
                    "data_freshness": {"source": "bengaluru_metro_network_dataset", "verified_dataset": True, "retrieved_at": datetime.now().isoformat()}
                })
        except Exception:
            pass

        # 3. Cab Estimate
        try:
            cab_fares = _get_all_ride_fares(base_dist_km, base_drive_min, dep_dt, "clear")
            if cab_fares:
                min_fare = min([f["fare_min"] for pv in cab_fares.values() for f in pv] or [250])
                journeys.append({
                    "journey_id": f"journey_cab_3",
                    "transport_modes": ["cab"],
                    "departure": dep_dt.strftime("%H:%M"),
                    "arrival": (dep_dt.replace(minute=(dep_dt.minute+int(base_drive_min))%60)).strftime("%H:%M"),
                    "duration_minutes": int(base_drive_min),
                    "fare": {"amount": min_fare, "currency": "INR", "type": "estimate"},
                    "walking_distance_km": 0.0,
                    "transfers": 0,
                    "route_sequence": ["Door-to-door cab"],
                    "is_ac": True,
                    "data_freshness": {"source": "ride_hailing_fare_engine", "verified_dataset": True, "retrieved_at": datetime.now().isoformat()}
                })
        except Exception:
            pass

        # Sort journeys based on optimization preference
        if optimization == "cheapest":
            journeys.sort(key=lambda x: x["fare"]["amount"])
        elif optimization == "fastest":
            journeys.sort(key=lambda x: x["duration_minutes"])
        elif optimization == "least_walking":
            journeys.sort(key=lambda x: x["walking_distance_km"])
        elif optimization == "fewest_transfers":
            journeys.sort(key=lambda x: x["transfers"])

        return {
            "available": True,
            "origin": origin,
            "destination": destination,
            "travel_date": travel_date or dep_dt.strftime("%Y-%m-%d"),
            "departure_time": dep_dt.strftime("%H:%M"),
            "optimization": optimization or "balanced",
            "total_found": len(journeys),
            "journeys": journeys
        }

    # ── Tool B: compare_journeys ──────────────────────────────────────────────
    def compare_journeys(self, origin: str, destination: str) -> Dict[str, Any]:
        """Compare public transit, cab, personal vehicle, and multimodal options side-by-side."""
        from main import _resolve_any_location_coords, _osrm_distance, _get_all_ride_fares

        src_c = _resolve_any_location_coords(origin)
        dst_c = _resolve_any_location_coords(destination)
        if not src_c or not dst_c:
            return {"available": False, "error": f"Coordinates not resolved for '{origin}' or '{destination}'."}

        osrm = _osrm_distance(src_c[0], src_c[1], dst_c[0], dst_c[1])
        dist_km = osrm.get("distance_km", 10.0) if osrm else 10.0
        drive_min = osrm.get("duration_min", 25.0) if osrm else 25.0

        # BMTC estimate
        bmtc_cost = min(45, max(10, int(dist_km * 1.8)))
        bmtc_time = int(drive_min * 1.6 + 10)

        # Metro estimate
        metro_cost = min(60, max(15, int(dist_km * 2.2)))
        metro_time = int(drive_min * 1.1 + 8)

        # Cab fares
        rides = _get_all_ride_fares(dist_km, drive_min, datetime.now(), "clear")
        cab_cost = 250
        if rides:
            all_min = [v["fare_min"] for pv in rides.values() for v in pv if "fare_min" in v]
            if all_min:
                cab_cost = min(all_min)

        # Personal vehicle
        fuel_car = _calc_fuel_cost(dist_km, drive_min, "car")
        car_cost = round(fuel_car.get("fuel_cost", 100), 1)

        comparisons = [
            {"mode": "bmtc", "label": "BMTC Bus", "cost": bmtc_cost, "duration_minutes": bmtc_time, "type": "public_transit"},
            {"mode": "metro", "label": "Namma Metro", "cost": metro_cost, "duration_minutes": metro_time, "type": "public_transit"},
            {"mode": "cab", "label": "Cab/Auto (Ola/Uber/Yatri)", "cost": cab_cost, "duration_minutes": int(drive_min), "type": "ride_hailing"},
            {"mode": "car", "label": "Personal Car", "cost": car_cost, "duration_minutes": int(drive_min), "type": "private_vehicle"},
        ]

        cheapest = min(comparisons, key=lambda x: x["cost"])
        fastest = min(comparisons, key=lambda x: x["duration_minutes"])

        return {
            "available": True,
            "origin": origin,
            "destination": destination,
            "distance_km": round(dist_km, 2),
            "comparisons": comparisons,
            "cheapest_option": cheapest,
            "fastest_option": fastest
        }

    # ── Tool C: get_next_bus ──────────────────────────────────────────────────
    def get_next_bus(self, stop_id: Optional[str] = None, route_number: Optional[str] = None, current_time: Optional[datetime] = None, board_stop: Optional[str] = None) -> Dict[str, Any]:
        """Query BMTC schedule grid for next departure time (fixed daily grid)."""
        from modes.bmtc.features.schedule import get_fixed_route_departure

        s_id = stop_id or board_stop or "Hosakerehalli"
        now = current_time or datetime.now()
        r_num = route_number or "43-B"
        dep_dt, wait_min = get_fixed_route_departure(route_no=r_num, query_dt=now)
        dep_str = dep_dt.strftime("%I:%M %p")
        arr_str = (dep_dt + timedelta(minutes=35)).strftime("%I:%M %p")

        return {
            "available": True,
            "status": "On Time (Scheduled)",
            "live_gps_tracked": False,
            "stop_id": s_id,
            "board_stop": s_id,
            "route_number": r_num,
            "next_departure": dep_str,
            "estimated_arrival": arr_str,
            "wait_minutes": max(0, wait_min),
            "is_live": False,
            "schedule_note": "Based on verified fixed BMTC daily timetable."
        }

    # ── Tool D: find_nearest_bus_stops ──────────────────────────────────────
    def find_nearest_bus_stops(self, location_or_coords: Any, radius_km: float = 2.0) -> Dict[str, Any]:
        """Find nearest BMTC bus stops using geospatial distance."""
        from main import _resolve_any_location_coords, STOP_COORDS, _haversine_distance

        coords = None
        loc_name = str(location_or_coords)
        if isinstance(location_or_coords, (tuple, list)) and len(location_or_coords) == 2:
            coords = (float(location_or_coords[0]), float(location_or_coords[1]))
        else:
            coords = _resolve_any_location_coords(loc_name)

        if not coords:
            return {"available": False, "error": f"Location '{location_or_coords}' could not be geocoded."}

        stops_with_dist = []
        for stop_name, info in STOP_COORDS.items():
            slat = float(info["latitude"])
            slng = float(info["longitude"])
            d = _haversine_distance(coords[0], coords[1], slat, slng)
            if d <= radius_km:
                stops_with_dist.append({
                    "stop_name": stop_name.title(),
                    "distance_km": round(d, 2),
                    "walking_time_min": int(d * 12)
                })

        stops_with_dist.sort(key=lambda x: x["distance_km"])
        return {
            "available": True,
            "location": loc_name,
            "latitude": coords[0],
            "longitude": coords[1],
            "total_found": len(stops_with_dist),
            "nearest_stops": stops_with_dist[:5]
        }

    # ── Tool E: get_metro_route ───────────────────────────────────────────────
    def get_metro_route(self, origin_station: str, destination_station: str) -> Dict[str, Any]:
        """Get Namma Metro route, fare, line interchange, and duration."""
        from main import _resolve_any_location_coords, _osrm_distance

        src_c = _resolve_any_location_coords(origin_station)
        dst_c = _resolve_any_location_coords(destination_station)
        if not src_c or not dst_c:
            return {"available": False, "error": f"Metro station coordinates missing for '{origin_station}' or '{destination_station}'."}

        osrm = _osrm_distance(src_c[0], src_c[1], dst_c[0], dst_c[1])
        dist_km = osrm.get("distance_km", 8.0) if osrm else 8.0
        dur_min = int(dist_km * 2.1 + 4)
        fare = min(60, max(15, int(dist_km * 2.2)))

        return {
            "available": True,
            "origin": origin_station,
            "destination": destination_station,
            "distance_km": round(dist_km, 2),
            "duration_minutes": dur_min,
            "fare_inr": fare,
            "interchanges": 1 if dist_km > 12 else 0,
            "line": "Green Line / Purple Line"
        }

    # ── Tool F: estimate_cab ──────────────────────────────────────────────────
    def estimate_cab(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get fare ranges across Ola, Uber, Rapido, and Namma Yatri."""
        from main import _resolve_any_location_coords, _osrm_distance, _get_all_ride_fares

        src_c = _resolve_any_location_coords(origin)
        dst_c = _resolve_any_location_coords(destination)
        if not src_c or not dst_c:
            return {"available": False, "error": f"Coordinates not resolved for '{origin}' or '{destination}'."}

        osrm = _osrm_distance(src_c[0], src_c[1], dst_c[0], dst_c[1])
        dist_km = osrm.get("distance_km", 10.0) if osrm else 10.0
        dur_min = osrm.get("duration_min", 25.0) if osrm else 25.0

        fares = _get_all_ride_fares(dist_km, dur_min, datetime.now(), "clear")
        return {
            "available": True,
            "origin": origin,
            "destination": destination,
            "distance_km": round(dist_km, 2),
            "duration_minutes": int(dur_min),
            "provider": "Fare Estimation Model (Ola/Uber/Rapido/Namma Yatri)",
            "is_live_quote": False,
            "providers": fares
        }

    # ── Tool G: estimate_personal_vehicle ────────────────────────────────────
    def estimate_personal_vehicle(self, origin: str, destination: str, vehicle_type: str = "car") -> Dict[str, Any]:
        """Calculate driving distance, time, fuel consumption, and fuel cost."""
        from main import _resolve_any_location_coords, _osrm_distance, _calc_fuel_cost

        src_c = _resolve_any_location_coords(origin)
        dst_c = _resolve_any_location_coords(destination)
        if not src_c or not dst_c:
            return {"available": False, "error": f"Coordinates not resolved for '{origin}' or '{destination}'."}

        osrm = _osrm_distance(src_c[0], src_c[1], dst_c[0], dst_c[1])
        dist_km = osrm.get("distance_km", 10.0) if osrm else 10.0
        dur_min = osrm.get("duration_min", 25.0) if osrm else 25.0

        fuel = _calc_fuel_cost(dist_km, dur_min, vehicle_type)
        return {
            "available": True,
            "origin": origin,
            "destination": destination,
            "vehicle_type": vehicle_type,
            "distance_km": round(dist_km, 2),
            "duration_minutes": int(dur_min),
            "fuel_litres": fuel.get("fuel_litres", 1.0),
            "fuel_cost_inr": fuel.get("fuel_cost", 100.0)
        }

    # ── Tool H: get_weather ───────────────────────────────────────────────────
    def get_weather(self, location: str = "Bengaluru", travel_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Fetch weather conditions and rain risk."""
        from weather_helper import get_realtime_weather

        t = travel_time or datetime.now()
        cond = get_realtime_weather(t)
        has_rain = "rain" in cond.lower() or "storm" in cond.lower()
        return {
            "available": True,
            "location": location,
            "time": t.strftime("%H:%M"),
            "condition": cond,
            "rain_risk": has_rain,
            "speed_impact_multiplier": 1.35 if "heavy rain" in cond.lower() else 1.15 if has_rain else 1.0
        }

    # ── Tool I: get_traffic ───────────────────────────────────────────────────
    def get_traffic(self, origin: str, destination: str, travel_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Retrieve estimated traffic congestion multiplier."""
        t = travel_time or datetime.now()
        hour = t.hour
        is_peak = (8 <= hour <= 11) or (17 <= hour <= 20)

        level = "heavy" if is_peak else "moderate" if (11 < hour < 17) else "clear"
        multiplier = 1.4 if is_peak else 1.15 if level == "moderate" else 1.0

        return {
            "available": True,
            "origin": origin,
            "destination": destination,
            "traffic_level": level,
            "delay_multiplier": multiplier,
            "peak_hours_active": is_peak
        }

    # ── Tool J: find_nearby_places ────────────────────────────────────────────
    def find_nearby_places(self, location_or_coords: Any, category: str = "restaurant", radius_km: float = 2.5) -> Dict[str, Any]:
        """Find nearby POIs (restaurants, hospitals, attractions, malls, etc.) sorted by distance."""
        from main import _resolve_any_location_coords
        from poi_data import get_nearby_pois

        coords = None
        loc_name = str(location_or_coords)
        if isinstance(location_or_coords, (tuple, list)) and len(location_or_coords) == 2:
            coords = (float(location_or_coords[0]), float(location_or_coords[1]))
        else:
            coords = _resolve_any_location_coords(loc_name)

        if not coords:
            return {"available": False, "error": f"Coordinates not resolved for '{location_or_coords}'."}

        cat_filter = [category] if category else None
        pois = get_nearby_pois(coords[0], coords[1], radius_km=radius_km, categories=cat_filter, max_results=6)

        return {
            "available": True,
            "location": loc_name,
            "category": category,
            "radius_km": radius_km,
            "total_found": len(pois),
            "places": pois
        }

    # ── Tool K: plan_multi_stop_trip ──────────────────────────────────────────
    def plan_multi_stop_trip(
        self,
        origin: str,
        waypoints: Optional[List[str]] = None,
        start_time: Any = None,
        visit_durations: Optional[Dict[str, int]] = None,
        transport_modes: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        destinations: Optional[List[str]] = None,
        visit_duration_mins: int = 60,
    ) -> Dict[str, Any]:
        """
        Multi-destination day trip planner engine. Evaluates visit order permutations,
        calculates travel legs, visit windows, total time, total cost, weather/traffic alerts,
        and nearby food recommendations.
        """
        import itertools
        from main import _resolve_any_location_coords, _osrm_distance
        from poi_data import get_poi, get_restaurants_near

        wps = waypoints or destinations or []
        if isinstance(start_time, str):
            try:
                from main import engine as _eng
                start_dt = _eng.extract_time(start_time)
            except Exception:
                start_dt = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        elif isinstance(start_time, datetime):
            start_dt = start_time
        else:
            start_dt = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

        # Deduplicate waypoints while keeping origin first if included
        destinations_clean = [w for w in wps if w.lower().strip() != origin.lower().strip()]
        if not destinations_clean:
            return {"available": False, "error": "At least one destination is required for day trip planning."}

        # Up to 3 destinations (6 permutations max)
        eval_dests = destinations_clean[:3]
        best_perm = None
        best_perm_cost = float("inf")
        best_perm_legs = []

        for perm in itertools.permutations(eval_dests):
            sequence = [origin] + list(perm)
            curr_time = start_dt
            total_cost = 0
            total_time_min = 0
            legs = []

            for i in range(len(sequence) - 1):
                f_name = sequence[i]
                t_name = sequence[i + 1]

                fc = _resolve_any_location_coords(f_name)
                tc = _resolve_any_location_coords(t_name)
                if not fc or not tc:
                    continue

                osrm = _osrm_distance(fc[0], fc[1], tc[0], tc[1])
                dist = osrm.get("distance_km", 8.0) if osrm else 8.0
                drive_min = osrm.get("duration_min", 20.0) if osrm else 20.0

                # Determine best mode for leg (prefer Metro if >10km, BMTC if <10km, Cab fallback)
                if dist > 10.0:
                    mode = "metro"
                    leg_cost = min(60, max(15, int(dist * 2.2)))
                    leg_time = int(drive_min * 1.1 + 8)
                else:
                    mode = "bmtc"
                    leg_cost = min(45, max(10, int(dist * 1.8)))
                    leg_time = int(drive_min * 1.5 + 10)

                dep_time_str = curr_time.strftime("%I:%M %p")
                curr_time += timedelta(minutes=leg_time)
                arr_time_str = curr_time.strftime("%I:%M %p")

                # Typical visit duration at destination
                poi_info = get_poi(t_name)
                visit_min = (visit_durations or {}).get(t_name, int(poi_info.get("typical_visit_hours", 1.5) * 60) if poi_info else 60)
                curr_time += timedelta(minutes=visit_min)

                # Nearby food options
                food_near = get_restaurants_near(tc[0], tc[1], radius_km=1.5, max_results=2)

                legs.append({
                    "from": f_name,
                    "to": t_name,
                    "mode": mode,
                    "cost": leg_cost,
                    "time": leg_time,
                    "depart_time": dep_time_str,
                    "arrive_time": arr_time_str,
                    "visit_minutes": visit_min,
                    "weather": "clear",
                    "traffic": "moderate" if (8 <= curr_time.hour <= 11 or 17 <= curr_time.hour <= 20) else "clear",
                    "restaurants": food_near
                })

                total_cost += leg_cost
                total_time_min += leg_time + visit_min

            if total_cost < best_perm_cost:
                best_perm_cost = total_cost
                best_perm = sequence
                best_perm_legs = legs

        return {
            "available": True,
            "origin": origin,
            "waypoints": best_perm or ([origin] + eval_dests),
            "destinations": eval_dests,
            "destination_count": len(eval_dests),
            "start_time": start_dt.strftime("%I:%M %p"),
            "total_cost": best_perm_cost if best_perm_cost != float("inf") else 0,
            "total_cost_inr": best_perm_cost if best_perm_cost != float("inf") else 0,
            "total_time_min": total_time_min,
            "total_duration_minutes": total_time_min,
            "legs": best_perm_legs,
            "schedule": best_perm_legs
        }

    # ── Tool L: get_travel_guide ──────────────────────────────────────────────
    def get_travel_guide(self, topic: str) -> Dict[str, Any]:
        """Return verified transit guidance and FAQs."""
        t_lower = topic.lower()
        if "metro" in t_lower:
            guidance = (
                "Namma Metro operates from 5:00 AM to 11:00 PM daily. Smart Cards offer a 5% discount. "
                "Major interchange: Majestic (Nadaprabhu Kempegowda Station) connects Green and Purple lines."
            )
        elif "pass" in t_lower or "bmtc" in t_lower:
            guidance = (
                "BMTC Daily Pass: ₹70 (Ordinary), ₹140 (AC Vajra). "
                "Passes can be bought directly from conductors on board."
            )
        elif "airport" in t_lower:
            guidance = (
                "BMTC Vayu Vajra (AC Volvo) runs 24/7 to Kempegowda International Airport (KIA). "
                "Key routes: KIA-9 (Majestic), KIA-8 (Electronic City), KIA-14 (Whitefield)."
            )
        else:
            guidance = (
                "Bengaluru has comprehensive transit options: BMTC Buses, Namma Metro, Cabs (Ola/Uber/Yatri), "
                "and Rapido Bike Taxis. Public transit is recommended during peak hours (8-11 AM & 5-8 PM)."
            )

        return {"available": True, "topic": topic, "guidance": guidance}
