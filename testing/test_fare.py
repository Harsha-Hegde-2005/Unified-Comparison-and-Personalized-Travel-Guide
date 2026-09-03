"""
tests/test_fare.py
==================
Unit tests for features/fare.py — fare slabs, route categories, and toll surcharges.
These are pure functions with no I/O: fast and deterministic.
"""

import pytest
from features.fare import (
    bmtc_fare,
    is_vajra_route,
    fare_category_for_route,
    segment_toll,
    segment_fare_breakdown,
)


class TestBmtcFare:
    def test_zero_distance_returns_first_slab(self):
        assert bmtc_fare(0.0) == 6

    def test_exact_slab_boundary(self):
        assert bmtc_fare(2.0)  == 6
        assert bmtc_fare(4.0)  == 12
        assert bmtc_fare(10.0) == 23
        assert bmtc_fare(30.0) == 30

    def test_between_slabs_uses_next_slab(self):
        assert bmtc_fare(3.0) == 12   # between 2 and 4 km → Rs.12

    def test_beyond_max_slab_returns_default(self):
        assert bmtc_fare(31.0) == 32
        assert bmtc_fare(100.0) == 32

    def test_fare_is_int(self):
        assert isinstance(bmtc_fare(5.5), int)

    def test_vajra_routes_use_premium_slab(self):
        assert bmtc_fare(2.0, "MF-211AC") == 12
        assert bmtc_fare(10.0, "V-500HK") == 30


class TestFareCategory:
    def test_detects_vajra_routes(self):
        assert is_vajra_route("MF-211AC") is True
        assert is_vajra_route("V-500HK") is True

    def test_detects_ordinary_routes(self):
        assert is_vajra_route("356-M") is False
        assert fare_category_for_route("356-M") == "ordinary"
        assert fare_category_for_route("MF-211AC") == "vajra"

    def test_segment_fare_breakdown_separates_base_and_toll(self):
        breakdown = segment_fare_breakdown(
            "MF-211AC", 10.0, ["electronic city flyover", "nice road 1st stone"]
        )
        assert breakdown["fare_category"] == "vajra"
        assert breakdown["base_fare"] == 30
        assert breakdown["toll"] == 12
        assert breakdown["total_fare"] == 42
        assert breakdown["has_toll"] is True


class TestSegmentToll:
    def test_no_toll_stops(self):
        assert segment_toll(["majestic", "shivajinagar", "indiranagar"]) == 0

    def test_elc_flyover_toll(self):
        stops = ["majestic", "electronic city flyover", "bommanahalli fly over"]
        # ELC is 7; only charged once even though two ELC stops appear
        assert segment_toll(stops) == 7

    def test_nice_road_toll(self):
        stops = ["nice road", "kanakapura road"]
        assert segment_toll(stops) == 5

    def test_combined_elc_and_nice(self):
        stops = ["electronic city flyover", "nice road 1st stone"]
        assert segment_toll(stops) == 12

    def test_empty_segment(self):
        assert segment_toll([]) == 0
