"""
tests/test_gtfs.py
==================
Tests for core/gtfs.py helpers — time parsing, formatting, and
route exclusion logic (no file I/O required).
"""

import pytest
from datetime import timedelta
from core.gtfs import _parse_gtfs_time, format_gtfs_time, _is_excluded_route


class TestParseGtfsTime:
    def test_normal_time(self):
        td = _parse_gtfs_time("08:30:00")
        assert td == timedelta(hours=8, minutes=30)

    def test_past_midnight_time(self):
        # GTFS allows >24h for trips continuing past midnight
        td = _parse_gtfs_time("25:10:00")
        assert td == timedelta(hours=25, minutes=10)

    def test_none_input_returns_none(self):
        import pandas as pd
        assert _parse_gtfs_time(pd.NA) is None

    def test_malformed_returns_none(self):
        assert _parse_gtfs_time("8:30") is None   # missing seconds field

    def test_midnight(self):
        assert _parse_gtfs_time("00:00:00") == timedelta(0)


class TestFormatGtfsTime:
    def test_normal_time(self):
        td = timedelta(hours=9, minutes=5, seconds=3)
        assert format_gtfs_time(td) == "09:05:03"

    def test_none_returns_placeholder(self):
        assert format_gtfs_time(None) == "(none)"

    def test_past_midnight_preserved(self):
        td = timedelta(hours=25, minutes=10)
        assert format_gtfs_time(td) == "25:10:00"


class TestIsExcludedRoute:
    def test_ac_route_not_excluded(self):
        assert _is_excluded_route("AC-1A") is False

    def test_airport_route_excluded(self):
        assert _is_excluded_route("KIAL-6") is True
        assert _is_excluded_route("AIRPORT SPECIAL") is True

    def test_ap_prefix_excluded(self):
        assert _is_excluded_route("AP-6") is True

    def test_regular_route_not_excluded(self):
        assert _is_excluded_route("500C")  is False
        assert _is_excluded_route("356-D") is False

    def test_empty_string_not_excluded(self):
        assert _is_excluded_route("") is False

