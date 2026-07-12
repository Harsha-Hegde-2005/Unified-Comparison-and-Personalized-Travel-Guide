"""
core/graph.py
=============
Builds the frequency-weighted, route-aware graph and exposes
two Dijkstra variants:
  - dijkstra()             → single best path
  - dijkstra_all_options() → up to N paths sorted by transfer count

Graph nodes are (stop_norm, route_no) pairs.
Transfer edges are generated lazily — not pre-built at startup.
Edge weight = haversine_km / log(1 + trips_per_day).

The graph is built inside @st.cache_resource so it is constructed
ONCE per server session. Button clicks never rebuild it.
"""

from __future__ import annotations

import heapq
import math
from math import radians, sin, cos, sqrt, atan2
from functools import lru_cache

import pandas as pd
import streamlit as st

from core.config import MAX_TRANSFERS, GTFS_TRIPS, GTFS_ROUTES, STOP_CLUSTERS, FAST_QUERY_MODE


# ── Haversine ─────────────────────────────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km."""
    R    = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a    = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


# ── Cached graph builder — runs exactly once per server session ───────────────

@st.cache_resource(show_spinner="Building route graph…")
def _build_everything() -> tuple[dict, dict, dict, dict]:
    """
    Returns (graph, _stop_routes, _raw_km, _route_trips).
    Cached by Streamlit — never re-runs on button clicks or reruns.
    """
    from core.loader import stops_df, _rev_df

    # 1. Route frequency
    route_trips: dict[str, int] = {}
    try:
        trips_df  = pd.read_csv(GTFS_TRIPS,  dtype={"route_id": str, "trip_id": str})
        routes_df = pd.read_csv(GTFS_ROUTES, dtype={"route_id": str, "route_short_name": str})
        merged    = trips_df.merge(routes_df[["route_id", "route_short_name"]], on="route_id", how="left")
        route_trips = merged.groupby("route_short_name").size().to_dict()
        print(f"Route frequency loaded: {len(route_trips)} routes")
    except FileNotFoundError:
        print("trips.txt / routes.txt not found — frequency weighting disabled")
    except Exception as e:
        print(f"Frequency load error: {e}")

    def freq_weight(distance_km: float, route_no: str) -> float:
        base  = route_no.replace("_REV", "")
        trips = route_trips.get(base, 1)
        return distance_km / math.log1p(trips)

    # 2. Load precomputed stop-location clusters.
    # Each (route_no, stop_sequence) → a cluster_key that is unique per
    # physical stop location. This eliminates the "same name, different place"
    # transfer bug where two "Hunasemara" stops 6km apart were treated as one.
    cluster_lookup: dict[tuple, str] = {}
    try:
        cl_df = pd.read_csv(STOP_CLUSTERS, dtype={"route_no": str, "stop_sequence": int,
                                                    "stop_norm": str, "final_cluster": str})
        for _, row in cl_df.iterrows():
            cluster_lookup[(row["route_no"], int(row["stop_sequence"]))] = row["final_cluster"]
        print(f"Stop clusters loaded: {cl_df['final_cluster'].nunique()} unique stop-location keys")
    except FileNotFoundError:
        print("stop_clusters.csv not found — falling back to stop_norm (name collisions possible)")

    def _cluster_key(route_no: str, stop_seq: int, stop_norm: str) -> str:
        """Return the location-aware cluster key for this stop, falling back to stop_norm."""
        return cluster_lookup.get((route_no, stop_seq), stop_norm)

    # 3. Build graph — nodes are (cluster_key, route_no) pairs.
    # cluster_key replaces bare stop_norm, so same-named stops in different
    # locations get different graph nodes and cannot be used as false transfers.
    stop_routes: dict[str, set]           = {}   # cluster_key → set of route_no
    graph_:      dict[tuple, list[tuple]] = {}
    raw_km_:     dict[tuple, float]       = {}
    # Reverse map: cluster_key → stop_norm (for display / segment extraction)
    cluster_to_norm: dict[str, str]       = {}
    norm_to_cluster_keys: dict[str, list[str]] = {}

    def _add_df(df_src: pd.DataFrame) -> None:
        for route_no, group in df_src.groupby("route_no"):
            group = group.sort_values("stop_sequence")
            rows  = list(group.itertuples(index=False))
            for i in range(len(rows) - 1):
                a, b   = rows[i], rows[i + 1]
                ck_a   = _cluster_key(route_no, int(a.stop_sequence), a.stop_norm)
                ck_b   = _cluster_key(route_no, int(b.stop_sequence), b.stop_norm)
                u      = (ck_a, route_no)
                v      = (ck_b, route_no)
                raw_d  = haversine(a.latitude, a.longitude, b.latitude, b.longitude)
                weight = freq_weight(raw_d, route_no)
                graph_.setdefault(u, []).append((v, weight))
                raw_km_[(u, v)] = raw_d
                stop_routes.setdefault(ck_a, set()).add(route_no)
                cluster_to_norm[ck_a] = a.stop_norm
                norm_to_cluster_keys.setdefault(a.stop_norm, []).append(ck_a)
            last = rows[-1]
            ck_last = _cluster_key(route_no, int(last.stop_sequence), last.stop_norm)
            stop_routes.setdefault(ck_last, set()).add(route_no)
            cluster_to_norm[ck_last] = last.stop_norm
            norm_to_cluster_keys.setdefault(last.stop_norm, []).append(ck_last)

    _add_df(stops_df)
    if not _rev_df.empty:
        _add_df(_rev_df)

    n_edges = sum(len(v) for v in graph_.values())
    rev_ct  = _rev_df["route_no"].nunique() if not _rev_df.empty else 0
    print(f"Graph built: {len(graph_):,} nodes, {n_edges:,} edges "
          f"(freq-weighted + {rev_ct} reverse routes)")

    # 4. Build proximity-based stop cluster map using a grid-bucket spatial index on cluster_keys.
    # Naive O(n²) over 5,700+ unique cluster_keys is too slow.
    # Grid buckets reduce this to O(n) average.
    WALK_TRANSFER_KM = 1.0   # 1.0 km walking tolerance (to integrate up to 1km walking shortcut)

    # Degree-to-km conversion at Bengaluru latitude (~13°N)
    KM_PER_DEG_LAT = 111.0
    KM_PER_DEG_LNG = 111.0 * math.cos(math.radians(13.0))  # ≈ 108.1

    # Grid cell size: slightly larger than threshold so a single cell lookup suffices
    CELL_DEG_LAT = WALK_TRANSFER_KM / KM_PER_DEG_LAT * 1.05
    CELL_DEG_LNG = WALK_TRANSFER_KM / KM_PER_DEG_LNG * 1.05

    # Compute coordinate per cluster_key
    all_combined = pd.concat([stops_df, _rev_df], ignore_index=True) if not _rev_df.empty else stops_df
    all_combined["cluster_key"] = [
        _cluster_key(r.route_no, int(r.stop_sequence), r.stop_norm)
        for r in all_combined.itertuples(index=False)
    ]
    cluster_coords = all_combined.groupby("cluster_key")[["latitude", "longitude"]].mean()
    cluster_keys   = list(cluster_coords.index)
    lats           = cluster_coords["latitude"].values
    lngs           = cluster_coords["longitude"].values

    # Build grid: cell → list of (cluster_key, lat, lng)
    grid: dict[tuple[int, int], list] = {}
    for i, ck in enumerate(cluster_keys):
        cell = (int(lats[i] / CELL_DEG_LAT), int(lngs[i] / CELL_DEG_LNG))
        grid.setdefault(cell, []).append((ck, lats[i], lngs[i]))

    # For each cluster_key, check only the 9 surrounding cells
    nearby_cluster_keys: dict[str, list[str]] = {}
    for i, ck in enumerate(cluster_keys):
        cx = int(lats[i] / CELL_DEG_LAT)
        cy = int(lngs[i] / CELL_DEG_LNG)
        neighbours = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for m_ck, mlat, mlng in grid.get((cx + dx, cy + dy), []):
                    if m_ck == ck:
                        continue
                    d = haversine(lats[i], lngs[i], mlat, mlng)
                    if d <= WALK_TRANSFER_KM:
                        neighbours.append(m_ck)
        if neighbours:
            nearby_cluster_keys[ck] = neighbours

    # Keep nearby_stops and nearby_ct for logs & compatibility
    nearby_stops: dict[str, list[str]] = {}
    for ck, neighbours in nearby_cluster_keys.items():
        norm = cluster_to_norm[ck]
        for n_ck in neighbours:
            n_norm = cluster_to_norm[n_ck]
            if n_norm != norm:
                nearby_stops.setdefault(norm, set()).add(n_norm)
    nearby_stops = {k: list(v) for k, v in nearby_stops.items()}

    nearby_ct = sum(len(v) for v in nearby_cluster_keys.values())
    print(f"Proximity clusters: {len(nearby_cluster_keys)} cluster_keys have <={int(WALK_TRANSFER_KM*1000)}m neighbours "
          f"({nearby_ct} proximity pairs)")
    return (
        graph_,
        stop_routes,
        raw_km_,
        route_trips,
        nearby_stops,
        cluster_to_norm,
        norm_to_cluster_keys,
        nearby_cluster_keys,
    )


# ── Module-level references — cheap after first load ─────────────────────────

graph, _stop_routes, _raw_km, _route_trips, _nearby_stops, _cluster_to_norm, _norm_to_cluster_keys, _nearby_cluster_keys = _build_everything()


# ── Transfer neighbours (lazy & cached) ────────────────────────────────────────

def _cluster_keys_for_norm(stop_norm: str) -> list[str]:
    """Return all cluster_keys that correspond to this stop_norm (handles name collisions)."""
    return _norm_to_cluster_keys.get(stop_norm, [])


_transfer_cache_dynamic: dict[tuple[str, str], list[tuple[tuple, float]]] = {}

def _transfer_neighbours(stop_norm: str, current_route: str) -> list[tuple[tuple, float]]:
    """
    Return all (node, weight) pairs reachable by transferring.
    stop_norm parameter is a cluster_key.
    Dynamically computes same-stop transfers and proximity transfers with caching.
    """
    key = (stop_norm, current_route)
    if key in _transfer_cache_dynamic:
        return _transfer_cache_dynamic[key]
    
    cluster_key = stop_norm
    results = []
    
    # Same-stop transfers (exact same physical location) - weight = 0.0
    for r in _stop_routes.get(cluster_key, set()):
        if r != current_route:
            results.append(((cluster_key, r), 0.0))
            
    # Proximity transfers (walking) - weight = 0.05
    for nearby_ck in _nearby_cluster_keys.get(cluster_key, []):
        for r in _stop_routes.get(nearby_ck, set()):
            results.append(((nearby_ck, r), 0.05))
            
    _transfer_cache_dynamic[key] = results
    return results


# ── Dijkstra — single best path ───────────────────────────────────────────────

@lru_cache(maxsize=1024)
def dijkstra(
    src: str,
    dst: str,
    max_transfers: int = MAX_TRANSFERS,
) -> tuple[list, tuple] | None:
    pq:     list = []
    wscore: dict = {}
    raw_km: dict = {}
    parent: dict = {}

    # src/dst are stop_norms; expand to all matching cluster_keys
    src_keys = _cluster_keys_for_norm(src) or [src]
    dst_keys  = set(_cluster_keys_for_norm(dst)) or {dst}

    for src_ck in src_keys:
        for r in _stop_routes.get(src_ck, []):
            node = (src_ck, r)
            heapq.heappush(pq, (0.0, 0, node))
            wscore[node] = (0.0, 0)
            raw_km[node] = 0.0

    best_end = None

    while pq:
        w_dist, transfers, node = heapq.heappop(pq)
        if wscore.get(node, (999.0, 999)) < (w_dist, transfers):
            continue
        stop, route = node
        if stop in dst_keys:
            best_end = node
            break
        if transfers > max_transfers:
            continue

        for neighbour, weight in graph.get(node, []):
            raw_d   = _raw_km.get((node, neighbour), weight)
            new_t   = transfers
            new_w   = w_dist + weight
            new_raw = raw_km.get(node, 0.0) + raw_d
            if wscore.get(neighbour, (999.0, 999)) > (new_w, new_t):
                wscore[neighbour] = (new_w, new_t)
                raw_km[neighbour] = new_raw
                parent[neighbour] = node
                heapq.heappush(pq, (new_w, new_t, neighbour))

        for neighbour, _ in _transfer_neighbours(stop, route):
            new_t   = transfers + 1
            new_w   = w_dist + 2.0  # 2.0 km transfer penalty
            new_raw = raw_km.get(node, 0.0)
            if wscore.get(neighbour, (999.0, 999)) > (new_w, new_t):
                wscore[neighbour] = (new_w, new_t)
                raw_km[neighbour] = new_raw
                parent[neighbour] = node
                heapq.heappush(pq, (new_w, new_t, neighbour))

    if not best_end:
        return None

    path: list = []
    cur = best_end
    while cur:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()
    return path, (wscore[best_end][1], raw_km[best_end])


# ── Dijkstra — multiple options ───────────────────────────────────────────────

@lru_cache(maxsize=1024)
def dijkstra_all_options(
    src: str,
    dst: str,
    max_transfers: int = MAX_TRANSFERS,
    max_options: int   = 3,
) -> list[tuple]:
    pq:              list = []
    wscore:          dict = {}
    raw_km:          dict = {}
    parent:          dict = {}
    found_per_level: dict = {}

    # src/dst are stop_norms; expand to all matching cluster_keys so
    # "See All Buses" uses the same location-aware matching as dijkstra().
    src_keys = _cluster_keys_for_norm(src) or [src]
    dst_keys = set(_cluster_keys_for_norm(dst)) or {dst}

    for src_ck in src_keys:
        for r in _stop_routes.get(src_ck, []):
            node = (src_ck, r)
            heapq.heappush(pq, (0.0, 0, node))
            wscore[node] = (0.0, 0)
            raw_km[node] = 0.0

    while pq:
        w_dist, transfers, node = heapq.heappop(pq)
        if wscore.get(node, (999.0, 999)) < (w_dist, transfers):
            continue
        stop, route = node
        if stop in dst_keys:
            if transfers not in found_per_level:
                found_per_level[transfers] = (node, raw_km.get(node, 0.0))
            if len(found_per_level) >= max_options:
                break
            continue
        if transfers > max_transfers:
            continue

        for neighbour, weight in graph.get(node, []):
            raw_d   = _raw_km.get((node, neighbour), weight)
            new_t   = transfers
            new_w   = w_dist + weight
            new_raw = raw_km.get(node, 0.0) + raw_d
            if wscore.get(neighbour, (999.0, 999)) > (new_w, new_t):
                wscore[neighbour] = (new_w, new_t)
                raw_km[neighbour] = new_raw
                parent[neighbour] = node
                heapq.heappush(pq, (new_w, new_t, neighbour))

        for neighbour, _ in _transfer_neighbours(stop, route):
            new_t   = transfers + 1
            new_w   = w_dist + 2.0  # 2.0 km transfer penalty
            new_raw = raw_km.get(node, 0.0)
            if wscore.get(neighbour, (999.0, 999)) > (new_w, new_t):
                wscore[neighbour] = (new_w, new_t)
                raw_km[neighbour] = new_raw
                parent[neighbour] = node
                heapq.heappush(pq, (new_w, new_t, neighbour))

    if not found_per_level:
        return []

    options = []
    for t_count in sorted(found_per_level):
        end_node, end_real = found_per_level[t_count]
        path: list = []
        cur = end_node
        while cur:
            path.append(cur)
            cur = parent.get(cur)
        path.reverse()
        options.append((path, (t_count, end_real)))
    return options


# ── Segment extraction ────────────────────────────────────────────────────────

def extract_segments(path: list[tuple]) -> list[tuple]:
    if not path:
        return []
    segments      = []
    current_route = path[0][1]
    start_stop    = path[0][0]
    collected     = [start_stop]

    for i in range(1, len(path)):
        stop, route = path[i]
        if route == current_route:
            collected.append(stop)
        else:
            segments.append((current_route, start_stop, path[i - 1][0], collected.copy()))
            current_route = route
            start_stop    = stop
            collected     = [stop]

    segments.append((current_route, start_stop, path[-1][0], collected.copy()))
    # Strip cluster disambiguation suffix (###N) and CS- prefix to restore plain stop_norms for display
    def _to_norm(ck: str) -> str:
        s = ck.split("###")[0].strip().lower()
        for prefix in ["cs-", "cs "]:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
        return s
    return [
        (r.replace("_REV", ""), _to_norm(s), _to_norm(e),
         [_to_norm(x) for x in stops])
        for r, s, e, stops in segments
    ]
