"""
features/fare.py
================
Fare utilities for ordinary, Vajra/AC, and toll-inclusive BMTC pricing.
"""

from core.config import (
    ORDINARY_FARE_SLABS,
    ORDINARY_FARE_DEFAULT,
    VAJRA_FARE_SLABS,
    VAJRA_FARE_DEFAULT,
    TOLL_STOP_SURCHARGES,
    VAJRA_ROUTE_PATTERNS,
)


def _fare_from_slab(distance_km: float, slabs: list[tuple[int, int]], default_fare: int) -> int:
    """Return the fare (Rs) from a slab table for a given distance."""
    for d, f in slabs:
        if distance_km <= d:
            return f
    return default_fare


def is_vajra_route(route_no: str) -> bool:
    """Return True when a route should use Vajra / AC fare slabs."""
    route = route_no.replace("_REV", "").upper()
    return any(token in route for token in VAJRA_ROUTE_PATTERNS)


def fare_category_for_route(route_no: str) -> str:
    """Return the pricing bucket for a route."""
    return "vajra" if is_vajra_route(route_no) else "ordinary"


def bmtc_fare(distance_km: float, route_no: str | None = None) -> int:
    """Return the base BMTC fare (Rs) for a given distance and route type."""
    if route_no and is_vajra_route(route_no):
        return _fare_from_slab(distance_km, VAJRA_FARE_SLABS, VAJRA_FARE_DEFAULT)
    return _fare_from_slab(distance_km, ORDINARY_FARE_SLABS, ORDINARY_FARE_DEFAULT)


def segment_toll(seg_stops: list[str]) -> int:
    """
    Return toll surcharge for a segment.
    ELC Flyover = Rs.7, NICE Road = Rs.5 (each charged at most once per segment).
    """
    elc  = any(TOLL_STOP_SURCHARGES.get(s, 0) == 7 for s in seg_stops)
    nice = any(TOLL_STOP_SURCHARGES.get(s, 0) == 5 for s in seg_stops)
    return (7 if elc else 0) + (5 if nice else 0)


def segment_fare_breakdown(route_no: str, distance_km: float, seg_stops: list[str]) -> dict:
    """Return base fare, toll add-on, total fare, and pricing category."""
    base_fare = bmtc_fare(distance_km, route_no)
    toll = segment_toll(seg_stops)
    fare_category = fare_category_for_route(route_no)
    return {
        "fare_category": fare_category,
        "base_fare": base_fare,
        "toll": toll,
        "total_fare": base_fare + toll,
        "has_toll": bool(toll),
    }
