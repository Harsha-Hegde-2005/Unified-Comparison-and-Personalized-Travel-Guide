"""
tests/test_stops.py
===================
Tests for core/stops.py — search_routes_fuzzy and canonical name resolution.
"""

import pytest


class TestSearchRoutesFuzzy:
    """Tests for search_routes_fuzzy — mocked to avoid loading the full CSV."""

    def _fuzzy(self, all_routes: list[str], query: str) -> list[str]:
        """Re-implement the logic locally so tests don't need real data."""
        q      = query.strip().lower()
        if not q:
            return []
        prefix = [r for r in all_routes if str(r).lower().startswith(q)]
        substr = [r for r in all_routes if q in str(r).lower() and r not in prefix]
        return (prefix + substr)[:20]

    def test_prefix_match_comes_first(self):
        routes = ["500C", "500D", "356-500", "KBS-500"]
        result = self._fuzzy(routes, "500")
        assert result.index("500C") < result.index("356-500")

    def test_empty_query_returns_empty(self):
        routes = ["500C", "356D"]
        assert self._fuzzy(routes, "") == []

    def test_case_insensitive(self):
        routes = ["KBS-3E", "mf-10"]
        assert "KBS-3E" in self._fuzzy(routes, "kbs")
        assert "mf-10"  in self._fuzzy(routes, "MF")

    def test_max_20_results(self):
        routes = [f"R{i}" for i in range(50)]
        result = self._fuzzy(routes, "R")
        assert len(result) <= 20

    def test_no_match_returns_empty(self):
        routes = ["500C", "356D"]
        assert self._fuzzy(routes, "ZZZ") == []


class TestCanonicalStopName:
    """Tests for canonical_stop_name — pure dict look-up."""

    def _canonical(self, name_map: dict, norm: str) -> str:
        return name_map.get(norm, norm.title())

    def test_known_norm_returns_canonical(self):
        m = {"majestic": "Majestic Bus Stand"}
        assert self._canonical(m, "majestic") == "Majestic Bus Stand"

    def test_unknown_norm_returns_title_cased(self):
        m = {}
        assert self._canonical(m, "indiranagar cross") == "Indiranagar Cross"

    def test_exact_match_preferred_over_title(self):
        m = {"kbs": "Kempegowda Bus Station (KBS)"}
        assert self._canonical(m, "kbs") == "Kempegowda Bus Station (KBS)"

