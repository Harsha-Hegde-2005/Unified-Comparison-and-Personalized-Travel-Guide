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

