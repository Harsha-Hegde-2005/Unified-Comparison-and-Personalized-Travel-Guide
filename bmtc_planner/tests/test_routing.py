"""
tests/test_routing.py
=====================
Tests for core/graph.py — haversine, extract_segments, and dijkstra
using the lightweight in-memory fixtures from conftest.py.
"""

import pytest
from core.graph import haversine, extract_segments


class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine(12.97, 77.59, 12.97, 77.59) == pytest.approx(0.0, abs=1e-9)

    def test_known_distance_bangalore(self):
        # Majestic ↔ MG Road — roughly 3.5 km
        d = haversine(12.977, 77.572, 12.975, 77.607)
        assert 2.5 < d < 5.0

    def test_symmetry(self):
        d1 = haversine(12.97, 77.59, 12.98, 77.60)
        d2 = haversine(12.98, 77.60, 12.97, 77.59)
        assert d1 == pytest.approx(d2, rel=1e-6)

    def test_returns_float(self):
        assert isinstance(haversine(12.97, 77.59, 12.98, 77.60), float)


class TestExtractSegments:
    def test_single_route_no_transfer(self):
        path = [("majestic", "500C"), ("shivajinagar", "500C"), ("indiranagar", "500C")]
        segs = extract_segments(path)
        assert len(segs) == 1
        route, start, end, stops = segs[0]
        assert route == "500C"
        assert start == "majestic"
        assert end   == "indiranagar"
        assert stops == ["majestic", "shivajinagar", "indiranagar"]

    def test_two_routes_one_transfer(self):
        path = [
            ("majestic",     "500C"),
            ("shivajinagar", "500C"),
            ("shivajinagar", "356D"),
            ("whitefield",   "356D"),
        ]
        segs = extract_segments(path)
        assert len(segs) == 2
        assert segs[0][0] == "500C"
        assert segs[1][0] == "356D"
        assert segs[0][2] == "shivajinagar"   # get-off stop for seg 1
        assert segs[1][1] == "shivajinagar"   # board stop for seg 2

    def test_rev_suffix_stripped(self):
        path = [("majestic", "500C_REV"), ("shivajinagar", "500C_REV")]
        segs = extract_segments(path)
        assert segs[0][0] == "500C"           # _REV stripped

    def test_empty_path_returns_empty(self):
        assert extract_segments([]) == []

    def test_single_node_path(self):
        path = [("majestic", "500C")]
        segs = extract_segments(path)
        assert len(segs) == 1
        assert segs[0][1] == segs[0][2] == "majestic"

