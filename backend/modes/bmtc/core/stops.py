"""
core/stops.py
=============
Stop-level utilities: look up stops on a route, fuzzy route search,
and everything that touches stops_df / _rev_df directly.
"""

from __future__ import annotations

from core.loader import stops_df, _rev_df, canonical_stop_name

_route_stop_map: dict[str, list[str]] = {}
for _route_no, _group in stops_df.groupby("route_no"):
    _route_stop_map[str(_route_no).lower()] = list(_group.sort_values("stop_sequence")["stop_norm"])

# Also include reverse routes if available
if not _rev_df.empty:
    for _route_no, _group in _rev_df.groupby("route_no"):
        _route_stop_map[str(_route_no).lower()] = list(_group.sort_values("stop_sequence")["stop_norm"])

_all_routes_sorted = sorted(stops_df["route_no"].unique().tolist())


def get_route_stop_list(route_no: str) -> list[str]:
    """Return ordered stop_norm list for a route number."""
    return _route_stop_map.get(str(route_no).lower(), [])


def get_route_stop_names(route_no: str) -> list[str]:
    """Return human-readable display names for every stop on a route."""
    return [canonical_stop_name(n) for n in get_route_stop_list(route_no)]


def search_routes_fuzzy(query: str) -> list[str]:
    """
    Case-insensitive route number search.
    Prefix matches come first, then substring matches.
    Returns at most 20 results.
    """
    q = query.strip().lower()
    if not q:
        return []
    prefix = [r for r in _all_routes_sorted if str(r).lower().startswith(q)]
    substr = [r for r in _all_routes_sorted if q in str(r).lower() and r not in prefix]
    return (prefix + substr)[:20]
