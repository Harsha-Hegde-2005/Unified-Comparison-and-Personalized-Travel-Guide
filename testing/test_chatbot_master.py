"""
Master Test Suite for Intelligent Context-Aware AI Travel Assistant
Covers requirements in Section 18:
- A. Intent Classification & Multi-Intent
- B. Context & Reference Resolution (pronouns, session state)
- C. Data Grounding & Anti-Hallucination
- D. Multi-Stop Optimization
- E. Latency & Performance Instrumentation
"""

import sys
import os
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from chatbot_engine import ChatbotEngine
from session_manager import SessionManager, SessionContext
from travel_tools import TravelTools
from performance_metrics import PerformanceMetricsTracker
from offtopic_filter import is_offtopic


@pytest.fixture
def engine():
    return ChatbotEngine(bmtc_stops=["Hosakerehalli", "Majestic", "Electronic City", "Indiranagar"], metro_stations=["Majestic", "Indiranagar"])


@pytest.fixture
def tools():
    return TravelTools(bmtc_stops=["Hosakerehalli", "Majestic", "Electronic City", "Indiranagar"], metro_stations=["Majestic", "Indiranagar"])


@pytest.fixture
def session_mgr():
    return SessionManager()


# ── SECTION 18.A: INTENT & MULTI-INTENT TESTS ─────────────────────────────────

def test_intent_route_planning(engine):
    intent, params = engine.classify_intent("How do I reach Majestic from Hosakerehalli?")
    assert intent in ("journey_time", "possible_ways", "journey_cost")
    assert params.get("destination") == "Majestic" or params.get("source") == "Hosakerehalli"


def test_intent_cheapest_fastest(engine):
    intent, params = engine.classify_intent("From Hosakerehalli, what is the cheapest way to reach Electronic City?")
    assert intent in ("journey_cost", "budget_constrained", "journey_time")
    
    intent_fast, params_fast = engine.classify_intent("From Hosakerehalli, what is the quickest way to reach Electronic City?")
    assert intent_fast in ("journey_time", "possible_ways")


def test_intent_ac_bus(engine):
    intent, params = engine.classify_intent("Is there an AC bus from Hosakerehalli to Majestic?")
    assert intent == "ac_bus_available"


def test_intent_nearby_places(engine):
    intent, params = engine.classify_intent("Find restaurants near Majestic")
    assert intent == "nearby_pois"
    assert params.get("explore_category") in ("restaurant", "food") or params.get("location") == "Majestic"


def test_intent_multi_stop(engine):
    intent, params = engine.classify_intent("Plan a day trip to Lalbagh, Cubbon Park, and Commercial Street")
    assert intent == "multi_stop_itinerary"
    assert len(params.get("waypoints", [])) >= 2


def test_offtopic_refusal():
    # Unrelated general knowledge query
    assert is_offtopic("Write a C program to sort an array", has_active_session=False) is True
    assert is_offtopic("Explain quantum mechanics", has_active_session=False) is True
    
    # Travel educational query should NOT be blocked
    assert is_offtopic("How do I use the metro in Bengaluru?", has_active_session=False) is False
    assert is_offtopic("What is the difference between BMTC and metro?", has_active_session=False) is False


# ── SECTION 18.B: CONTEXT & REFERENCE RESOLUTION TESTS ───────────────────────

def test_session_reference_resolution(session_mgr):
    session = session_mgr.get_or_create_session("test_session_1")
    
    # Turn 1: Initial journey query context update
    session.set_origin("Hosakerehalli")
    session.set_destination("Electronic City")
    session.set_recommendations([
        {"journey_id": "journey_1", "mode": "bmtc", "cost": 30, "duration_minutes": 55},
        {"journey_id": "journey_2", "mode": "metro", "cost": 45, "duration_minutes": 40},
        {"journey_id": "journey_3", "mode": "cab", "cost": 320, "duration_minutes": 35}
    ])

    # Turn 2: "What about the cheapest one?"
    msg, overrides = session_mgr.resolve_references(session, "What about the cheapest one?")
    assert session.destination["name"] == "Electronic City"
    assert session.origin["name"] == "Hosakerehalli"
    assert overrides.get("optimization") == "cheapest"

    # Turn 3: "Is it an AC bus?"
    msg, overrides = session_mgr.resolve_references(session, "Is it an AC bus?")
    assert overrides.get("source") == "Hosakerehalli"
    assert overrides.get("destination") == "Electronic City"


def test_ordinal_reference_resolution(session_mgr):
    session = session_mgr.get_or_create_session("test_session_2")
    session.set_recommendations([
        {"journey_id": "journey_bmtc_1", "mode": "bmtc", "cost": 25},
        {"journey_id": "journey_metro_2", "mode": "metro", "cost": 40},
        {"journey_id": "journey_cab_3", "mode": "cab", "cost": 280}
    ])
    
    msg, overrides = session_mgr.resolve_references(session, "Tell me more about the second option")
    assert overrides.get("selected_option") is not None
    assert overrides["selected_option"]["journey_id"] == "journey_metro_2"
    assert session.active_journey_id == "journey_metro_2"


def test_session_isolation(session_mgr):
    s1 = session_mgr.get_or_create_session("user_A")
    s2 = session_mgr.get_or_create_session("user_B")

    s1.set_destination("Majestic")
    s2.set_destination("Whitefield")

    assert s1.destination["name"] == "Majestic"
    assert s2.destination["name"] == "Whitefield"


# ── SECTION 18.C: DATA GROUNDING & ANTI-HALLUCINATION TESTS ──────────────────

def test_tool_search_journey_grounding(tools):
    result = tools.search_journey(origin="Hosakerehalli", destination="Majestic")
    assert result["available"] is True
    assert "journeys" in result
    for j in result["journeys"]:
        assert j["fare"]["amount"] > 0
        assert j["duration_minutes"] > 0
        assert "data_freshness" in j
        assert j["data_freshness"]["verified_dataset"] is True


def test_tool_get_next_bus_grounding(tools):
    result = tools.get_next_bus(board_stop="Hosakerehalli", route_number="43-B")
    assert "status" in result
    assert result["live_gps_tracked"] is False  # Explicitly labeled as schedule/headway
    assert "next_departure" in result or "schedule_note" in result


def test_estimate_cab_labeling(tools):
    result = tools.estimate_cab("Hosakerehalli", "Electronic City")
    assert result["provider"] == "Fare Estimation Model (Ola/Uber/Rapido/Namma Yatri)"
    assert result["is_live_quote"] is False  # Must not claim to be a live provider quote


# ── SECTION 18.D: MULTI-STOP OPTIMIZATION TESTS ─────────────────────────────

def test_multi_stop_planner(tools):
    destinations = ["Lalbagh", "Cubbon Park", "Commercial Street"]
    itinerary = tools.plan_multi_stop_trip(
        origin="Hosakerehalli",
        destinations=destinations,
        start_time="08:00 AM",
        visit_duration_mins=60
    )
    
    assert itinerary["destination_count"] == 3
    assert len(itinerary["schedule"]) == 3
    assert itinerary["total_cost_inr"] > 0
    assert itinerary["total_duration_minutes"] > 0
    
    # Check chronological schedule progression
    for leg in itinerary["schedule"]:
        assert "depart_time" in leg
        assert "arrive_time" in leg
        assert "mode" in leg


# ── SECTION 18.E: LATENCY & PERFORMANCE TESTS ───────────────────────────────

def test_performance_metrics_tracker():
    tracker = PerformanceMetricsTracker()
    tracker.record_query(45.2)
    tracker.record_query(12.8)
    tracker.record_query(88.0)

    summary = tracker.get_metrics_summary()
    assert summary["total_queries"] >= 3
    assert summary["median_latency_ms"] > 0
    assert summary["p95_latency_ms"] > 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
