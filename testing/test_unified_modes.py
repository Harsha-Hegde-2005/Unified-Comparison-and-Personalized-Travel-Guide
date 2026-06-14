"""
tests/test_unified_modes.py
===========================
Verifies correctness of Metro planner, Cab estimate engine,
Personal vehicles cost, Multimodal router, and new BMTC endpoints.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestMetroPlannerIntegration:
    """Test Metro routing engine and fares."""

    def test_metro_plan_endpoint(self):
        # Majestic to Indiranagar
        resp = client.post("/api/metro/plan", json={
            "source": "Majestic",
            "destination": "Indiranagar"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert data["mode"] == "metro"
        assert data["cost"] > 0
        assert data["stations_crossed"] > 0
        assert len(data["segments"]) > 0


class TestCabEstimations:
    """Test cab provider listing and heuristic fare estimations."""

    def test_cab_providers(self):
        resp = client.get("/api/cab/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert len(data["providers"]) > 0

    def test_cab_estimate(self):
        resp = client.post("/api/cab/estimate", json={
            "src_lat": 12.9716,
            "src_lng": 77.5946,
            "dst_lat": 12.9279,
            "dst_lng": 77.6271
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert data["provider_count"] > 0
        for p in data["results"]:
            assert "provider" in data["results"][p]
            assert "estimates" in data["results"][p]


class TestPersonalVehicles:
    """Test Indian vehicle database lookup and trip cost calculations."""

    def test_vehicle_list(self):
        resp = client.get("/api/vehicle/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "vehicles" in data
        assert data["count"] > 0

    def test_vehicle_search(self):
        resp = client.post("/api/vehicle/search", json={"query": "Swift"})
        assert resp.status_code == 200
        data = resp.json()
        assert "matches" in data
        assert len(data["matches"]) > 0

    def test_vehicle_estimate(self):
        # Fetch the first vehicle from list to run a valid calculation
        v_resp = client.get("/api/vehicle/list")
        vehicles = v_resp.json()["vehicles"]
        assert len(vehicles) > 0
        sample_vehicle = vehicles[0]

        resp = client.post("/api/vehicle/estimate", json={
            "vehicle": sample_vehicle,
            "source_lat": 12.9716,
            "source_lng": 77.5946,
            "dest_lat": 12.9279,
            "dest_lng": 77.6271
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is True
        assert "cost" in data
        assert "mileage" in data
        assert data["distance"] > 0


class TestMultimodalRouter:
    """Test multimodal cross-connecting router (Metro + BMTC combos)."""

    def test_multimodal_plan_endpoint(self):
        # Test comparing all modes
        resp = client.post("/api/compare", json={
            "source": "hosa road",
            "destination": "silk board",
            "preference": "cost"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "bmtc" in data["results"]
        assert "metro" in data["results"]


class TestBmtcNewEndpoints:
    """Test new endpoints built to synchronize with the React UI."""

    def test_all_buses(self):
        resp = client.post("/api/bmtc/all-buses", json={
            "source": "hosa road",
            "destination": "silk board"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "direct" in data
        assert "transfer" in data

    def test_route_search(self):
        resp = client.get("/api/bmtc/route-search?route=356")
        assert resp.status_code == 200
        data = resp.json()
        assert data["route"] == "356"
        assert data["stop_count"] > 0
        assert len(data["stops"]) > 0
