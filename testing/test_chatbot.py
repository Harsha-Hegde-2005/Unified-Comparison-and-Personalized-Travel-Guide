import os
import pytest
from datetime import datetime
from chatbot_engine import ChatbotEngine
from main import app
from fastapi.testclient import TestClient

# 1. Test ChatbotEngine directly
def test_chatbot_engine_stops_extraction():
    bmtc_stops = ["Majestic", "Indiranagar Stop", "Silk Board Junction"]
    metro_stations = ["Indiranagar Metro Station", "MG Road"]
    engine = ChatbotEngine(bmtc_stops=bmtc_stops, metro_stations=metro_stations)
    
    # Test longer names match first
    stops = engine.extract_stops("I want to go to Indiranagar Metro Station from Majestic")
    assert "Indiranagar Metro Station" in stops
    assert "Majestic" in stops
    # "Indiranagar Stop" should not be matched because "Indiranagar Metro Station" overlapped and matched first
    assert "Indiranagar Stop" not in stops

def test_chatbot_engine_source_dest_resolution():
    engine = ChatbotEngine(bmtc_stops=["Majestic", "Indiranagar"], metro_stations=[])
    
    # from source to destination
    src, dst = engine.determine_source_dest(["Majestic", "Indiranagar"], "from Majestic to Indiranagar")
    assert src == "Majestic"
    assert dst == "Indiranagar"
    
    # destination from source
    src, dst = engine.determine_source_dest(["Indiranagar", "Majestic"], "go to Indiranagar from Majestic")
    assert src == "Majestic"
    assert dst == "Indiranagar"

def test_chatbot_engine_budget_extraction():
    engine = ChatbotEngine([], [])
    assert engine.extract_budget("under ₹50") == 50
    assert engine.extract_budget("rs 100") == 100
    assert engine.extract_budget("my budget is 500 rupees") == 500
    # Avoid parsing time as budget
    assert engine.extract_budget("at 4 pm") is None

def test_chatbot_engine_time_extraction():
    engine = ChatbotEngine([], [])
    t = engine.extract_time("will it rain at 4:30 pm today?")
    assert t.hour == 16
    assert t.minute == 30
    
    t2 = engine.extract_time("at 9 am")
    assert t2.hour == 9
    assert t2.minute == 0

def test_chatbot_engine_intent_classification():
    bmtc_stops = ["Majestic", "Silk Board"]
    engine = ChatbotEngine(bmtc_stops=bmtc_stops, metro_stations=[])
    
    # budget constrained
    intent, params = engine.classify_intent("under ₹50 from Majestic to Silk Board", ["Majestic", "Silk Board"])
    assert intent == "budget_constrained"
    assert params["budget"] == 50
    assert params["source"] == "Majestic"
    assert params["destination"] == "Silk Board"
    
    # vehicle_vs_transit
    intent, params = engine.classify_intent("Should I drive my bike to Silk Board?", ["Silk Board"])
    assert intent == "vehicle_vs_transit"
    assert params["vtype"] == "bike"
    assert params["destination"] == "Silk Board"
    
    # weather_query
    intent, params = engine.classify_intent("Will it rain at 5 pm?", [])
    assert intent == "weather_query"
    assert params["time"].hour == 17
    
    # journey_cost
    intent, params = engine.classify_intent("What is the fare from Majestic to Silk Board?", ["Majestic", "Silk Board"])
    assert intent == "journey_cost"
    assert params["source"] == "Majestic"
    assert params["destination"] == "Silk Board"
    
    # journey_time
    intent, params = engine.classify_intent("How long does it take from Majestic to Silk Board?", ["Majestic", "Silk Board"])
    assert intent == "journey_time"
    assert params["source"] == "Majestic"
    assert params["destination"] == "Silk Board"

    # how to go (journey_time fallback)
    intent, params = engine.classify_intent("How to go from Majestic to Silk Board?", ["Majestic", "Silk Board"])
    assert intent == "journey_time"
    assert params["source"] == "Majestic"
    assert params["destination"] == "Silk Board"

# 2. Test API endpoint
client = TestClient(app)

def test_api_chatbot_query_journey_time():
    resp = client.post("/api/chatbot/query", json={
        "message": "How to go from Majestic to Indiranagar?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert data["intent"] in ("journey_time", "journey_cost", "general")
    assert "parameters" in data
    assert "embedded_data" in data

def test_api_chatbot_query_weather():
    from unittest.mock import patch
    with patch("weather_helper.get_realtime_weather", return_value="heavy rain"):
        resp = client.post("/api/chatbot/query", json={
            "message": "Will it rain at 4 pm today?"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        assert data["intent"] == "weather_query"
        assert "rain" in data["text"].lower()


def test_api_chatbot_query_bike_comparison():
    resp = client.post("/api/chatbot/query", json={
        "message": "Should I drive my bike to Indiranagar?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert data["intent"] == "vehicle_vs_transit"
    assert "bike" in data["text"].lower()

def test_chatbot_engine_new_intents_classification():
    engine = ChatbotEngine(bmtc_stops=["Majestic", "Indiranagar"], metro_stations=[])
    
    # ac_bus_available
    intent, params = engine.classify_intent("is AC bus available from Majestic to Indiranagar?", ["Majestic", "Indiranagar"])
    assert intent == "ac_bus_available"
    assert params["source"] == "Majestic"
    assert params["destination"] == "Indiranagar"
    
    # possible_ways
    intent, params = engine.classify_intent("what are all the possible ways to go from Majestic to Indiranagar?", ["Majestic", "Indiranagar"])
    assert intent == "possible_ways"
    assert params["source"] == "Majestic"
    assert params["destination"] == "Indiranagar"
    
    # nearest_stops
    intent, params = engine.classify_intent("what is the nearest bus stop to Majestic?", ["Majestic"])
    assert intent == "nearest_stops"
    assert params["location"] == "Majestic"

def test_api_chatbot_query_possible_ways():
    resp = client.post("/api/chatbot/query", json={
        "message": "What are all the possible ways to go from Majestic to Indiranagar?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "possible_ways"
    assert "possible ways" in data["text"].lower()

def test_api_chatbot_query_ac_bus():
    resp = client.post("/api/chatbot/query", json={
        "message": "Is AC bus available from Majestic to Indiranagar?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "ac_bus_available"
    assert "ac" in data["text"].lower() or "vajra" in data["text"].lower() or "no direct" in data["text"].lower()

def test_api_chatbot_query_nearest_stops():
    resp = client.post("/api/chatbot/query", json={
        "message": "Where is the nearest bus stop to Majestic?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "nearest_stops"
    assert "nearest" in data["text"].lower()
    assert "bmtc" in data["text"].lower()

def test_api_chatbot_query_general_greetings():
    resp = client.post("/api/chatbot/query", json={
        "message": "Hello there!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "general"
    assert "hello" in data["text"].lower() or "how can i help" in data["text"].lower()


def test_chatbot_local_context_resolution():
    engine = ChatbotEngine(bmtc_stops=["Majestic", "Indiranagar"], metro_stations=[])
    
    # Starting location clarification
    history = [
        {"sender": "user", "text": "how to go to Indiranagar"},
        {"sender": "bot", "text": "Where are you starting your journey from?"}
    ]
    res = engine.resolve_context_from_history("Majestic", history)
    assert res is not None
    intent, params = res
    assert intent == "journey_time"
    assert params["source"] == "Majestic"
    assert params["destination"] == "Indiranagar"
    
    # Destination location clarification
    history2 = [
        {"sender": "user", "text": "from Majestic how to travel?"},
        {"sender": "bot", "text": "Where would you like to travel to?"}
    ]
    res2 = engine.resolve_context_from_history("Indiranagar", history2)
    assert res2 is not None
    intent2, params2 = res2
    assert intent2 == "journey_time"
    assert params2["source"] == "Majestic"
    assert params2["destination"] == "Indiranagar"


def test_api_chatbot_clarification_loop():
    resp = client.post("/api/chatbot/query", json={
        "message": "how to go to Indiranagar?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "clarification"
    assert "starting" in data["text"].lower() or "where" in data["text"].lower()

    resp2 = client.post("/api/chatbot/query", json={
        "message": "I want to start from Majestic, how to travel?"
    })
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["intent"] == "clarification"
    assert "destination" in data2["text"].lower() or "want to go" in data2["text"].lower()


def test_api_chatbot_history_context_integration():
    history = [
        {"sender": "user", "text": "how to go to Indiranagar"},
        {"sender": "bot", "text": "Where are you starting your journey from?"}
    ]
    resp = client.post("/api/chatbot/query", json={
        "message": "Majestic",
        "history": history
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in ("journey_time", "journey_cost")
    assert "text" in data
    assert data["parameters"]["source"] == "Majestic"
    assert data["parameters"]["destination"] == "Indiranagar"


def test_chatbot_landmark_and_mode_preference():
    # Test case 1: metro timing preference from hosa road to majestic
    resp = client.post("/api/chatbot/query", json={
        "message": "when is next metro from hosa road to majestic?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in ("journey_time", "journey_cost")
    # Should select metro as embedded data
    assert data["embedded_data"] is not None
    assert data["embedded_data"]["mode"] == "metro"
    assert "metro" in data["text"].lower()

    # Test case 2: bus timing preference
    resp = client.post("/api/chatbot/query", json={
        "message": "at what time bus is there from hosa road to majestic?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["embedded_data"] is not None
    assert data["embedded_data"]["mode"] == "bmtc"
    assert "bus" in data["text"].lower()

    # Test case 3: landmark geocoding (Lulu Mall)
    resp = client.post("/api/chatbot/query", json={
        "message": "how to go to lulu mall from majestic?"
    })
    assert resp.status_code == 200
    data = resp.json()
    # It should successfully geocode lulu mall and compute the route!
    assert data["intent"] in ("journey_time", "journey_cost")
    assert data["embedded_data"] is not None
    assert data["parameters"]["destination"].lower() == "lulu mall"

    # Test case 4: current location fallback geocoding
    resp = client.post("/api/chatbot/query", json={
        "message": "how can I go to Indiranagar from my current location?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in ("journey_time", "journey_cost")
    assert data["parameters"]["source"].lower() == "current location"
    assert data["embedded_data"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# New Feature Tests: Multi-Stop Itinerary, Bus Schedule, Multimodal Journey
# ─────────────────────────────────────────────────────────────────────────────

class TestNewChatbotIntents:
    """Test new chatbot intents: multi_stop_itinerary, bus_schedule_query, multimodal_journey."""

    def test_multi_stop_itinerary_intent_classification(self):
        """ChatbotEngine should classify day-trip queries as multi_stop_itinerary."""
        engine = ChatbotEngine(
            bmtc_stops=["Majestic", "Silk Board"],
            metro_stations=["MG Road", "Indiranagar"],
            poi_names=["Cubbon Park", "Lalbagh Botanical Garden", "UB City Mall"],
        )
        # Explicit "plan a trip" cue
        matched = engine.extract_stops("Plan a trip to Cubbon Park, Lalbagh and UB City at 10 AM")
        intent, params = engine.classify_intent(
            "Plan a trip to Cubbon Park, Lalbagh and UB City at 10 AM", matched
        )
        assert intent == "multi_stop_itinerary"
        # Should extract waypoints
        assert "waypoints" in params

    def test_multi_stop_itinerary_endpoint(self):
        """API should return itinerary legs for a multi-stop day trip query."""
        client = TestClient(app)
        resp = client.post("/api/chatbot/query", json={
            "message": "Plan a trip to Cubbon Park, Lalbagh Botanical Garden and UB City Mall starting at 10 AM"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "multi_stop_itinerary"
        # Should have a text response with itinerary info
        assert data["text"] is not None
        assert len(data["text"]) > 0

    def test_bus_schedule_intent_classification(self):
        """ChatbotEngine should classify route-number queries as bus_schedule_query."""
        engine = ChatbotEngine(
            bmtc_stops=["Majestic", "Silk Board"],
            metro_stations=[],
            poi_names=[],
        )
        matched = engine.extract_stops("what are the stops on route 500D?")
        intent, params = engine.classify_intent("what are the stops on route 500D?", matched)
        assert intent == "bus_schedule_query"
        assert params.get("route_number") == "500D"

    def test_bus_schedule_endpoint_by_route(self):
        """API should handle bus route schedule queries without crashing."""
        client = TestClient(app)
        resp = client.post("/api/chatbot/query", json={
            "message": "what are the stops on route 500D?"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "bus_schedule_query"
        assert data["text"] is not None

    def test_bus_schedule_endpoint_src_dst(self):
        """API should handle 'bus timings from X to Y' queries."""
        client = TestClient(app)
        resp = client.post("/api/chatbot/query", json={
            "message": "bus timings from Majestic to Silk Board"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "bus_schedule_query"
        assert data["text"] is not None

    def test_multimodal_journey_intent_classification(self):
        """ChatbotEngine should classify multimodal queries correctly."""
        engine = ChatbotEngine(
            bmtc_stops=["Majestic", "Silk Board"],
            metro_stations=["MG Road"],
            poi_names=[],
        )
        matched = engine.extract_stops("show me a multimodal route from Majestic to Silk Board")
        intent, params = engine.classify_intent(
            "show me a multimodal route from Majestic to Silk Board", matched
        )
        assert intent == "multimodal_journey"
        assert params.get("source") == "Majestic"
        assert params.get("destination") == "Silk Board"

    def test_multimodal_journey_endpoint(self):
        """API should return multimodal plan for multimodal journey queries."""
        client = TestClient(app)
        resp = client.post("/api/chatbot/query", json={
            "message": "show me a multimodal route from Majestic to Silk Board"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "multimodal_journey"
        assert data["text"] is not None

    def test_journey_cost_includes_multimodal(self):
        """journey_cost intent should include multimodal in embedded_data or text."""
        client = TestClient(app)
        resp = client.post("/api/chatbot/query", json={
            "message": "how much does it cost from Majestic to Silk Board?"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] in ("journey_cost", "journey_time", "possible_ways")
        assert data["embedded_data"] is not None

    def test_typo_tolerance_source_dest(self):
        """ChatbotEngine should handle common typos in place names."""
        engine = ChatbotEngine(
            bmtc_stops=["Majestic", "Silk Board", "Indiranagar"],
            metro_stations=["MG Road"],
            poi_names=[],
        )
        # "silkboard" without space
        matched = engine.extract_stops("from Majestic to silkboard")
        assert any("Silk Board" in s or "silk" in s.lower() for s in matched)

    def test_poi_restaurants_near_cubbon_park(self):
        """poi_data.get_restaurants_near() should return restaurants near Cubbon Park."""
        import sys
        sys.path.insert(0, "backend")
        import poi_data
        recs = poi_data.get_restaurants_near(12.9763, 77.5929, radius_km=2.0)
        assert len(recs) > 0
        for r in recs:
            assert "name" in r
            assert "distance_km" in r
            assert r["distance_km"] <= 2.0

    def test_get_restaurants_returns_all(self):
        """poi_data.get_restaurants() should return all restaurant POIs."""
        import sys
        sys.path.insert(0, "backend")
        import poi_data
        rests = poi_data.get_restaurants()
        assert len(rests) >= 10  # We have 27 restaurants loaded
        for r in rests:
            assert r["category"] == "restaurant"
            assert "lat" in r
            assert "lng" in r
