#!/usr/bin/env python3
"""
tools/build_stop_clusters.py
=============================
Precomputes stop_clusters.csv — run this whenever the main dataset changes.

Usage:
    cd bmtc_planner
    python tools/build_stop_clusters.py

WHAT'S NEW vs previous version:
  - Generates stop_canonical_names.csv alongside stop_clusters.csv
  - Ambiguous stops (same name, multiple locations) get area-aware display names:
      "Gollahalli (South Bengaluru)" vs "Gollahalli (North-East Bengaluru)"
  - Uses OSM Overpass to fetch Bangalore ward/suburb polygons (cached locally)
  - Falls back to a coarse grid if OSM is unavailable (no API key needed)
  - Everything else (clustering logic, union-find, grid buckets) unchanged
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, math, time, urllib.request, urllib.parse
import pandas as pd
from core.config import STOP_LEVEL_CLEANED, STOP_CLUSTERS, PROCESSED_DIR, RAW_DIR

CLUSTER_KM = 0.35
_GEOJSON_PATH   = os.path.join(RAW_DIR,      "bangalore_areas.geojson")
_CANONICAL_PATH = os.path.join(PROCESSED_DIR, "stop_canonical_names.csv")

# ── Haversine ─────────────────────────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2-lat1); dlon = math.radians(lon2-lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

KM_PER_DEG_LAT = 111.0
KM_PER_DEG_LNG = 108.1
CELL_LAT = CLUSTER_KM / KM_PER_DEG_LAT
CELL_LNG = CLUSTER_KM / KM_PER_DEG_LNG

# ── Union-Find (unchanged from original) ─────────────────────────────────────

def find(uf, x):
    while uf[x] != x:
        uf[x] = uf[uf[x]]
        x = uf[x]
    return x

def union(uf, x, y):
    uf[find(uf, x)] = find(uf, y)

# ── Cluster builder (unchanged from original) ─────────────────────────────────

def build_clusters(df: pd.DataFrame) -> pd.Series:
    final_cluster = [""] * len(df)
    for norm, grp in df.groupby("stop_norm"):
        idxs = list(grp.index)
        lats = grp["latitude"].values
        lngs = grp["longitude"].values
        n = len(idxs)
        uf = list(range(n))
        grid = {}
        for i in range(n):
            cx = int(lats[i] / CELL_LAT)
            cy = int(lngs[i] / CELL_LNG)
            grid.setdefault((cx, cy), []).append(i)
        for i in range(n):
            cx = int(lats[i] / CELL_LAT)
            cy = int(lngs[i] / CELL_LNG)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for j in grid.get((cx+dx, cy+dy), []):
                        if j <= i:
                            continue
                        if haversine(lats[i], lngs[i], lats[j], lngs[j]) <= CLUSTER_KM:
                            union(uf, i, j)
        roots = {find(uf, i) for i in range(n)}
        multi = len(roots) > 1
        for i, idx in enumerate(idxs):
            root = find(uf, i)
            final_cluster[idx] = f"{norm}###{root}" if multi else norm
    return pd.Series(final_cluster, index=df.index)

# ── OSM area download (one-time, cached) ──────────────────────────────────────

def _download_bangalore_areas() -> list:
    print("  Downloading Bangalore area boundaries from OpenStreetMap (one-time)…")
    query = """
[out:json][timeout:60];
area["name"="Bengaluru Urban"]["admin_level"="6"]->.searchArea;
(
  relation["place"~"suburb|neighbourhood|quarter|village|town"](area.searchArea);
  relation["admin_level"~"9|10|11"](area.searchArea);
);
out geom;
"""
    try:
        data = ("data=" + urllib.parse.quote(query)).encode()
        req  = urllib.request.Request(
            "https://overpass-api.de/api/interpreter", data=data, method="POST"
        )
        req.add_header("User-Agent", "BMTC-Smart-Planner/1.0")
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  OSM download failed ({e}) — will use grid fallback")
        return []

    features = []
    for el in raw.get("elements", []):
        if el.get("type") != "relation":
            continue
        name = el.get("tags", {}).get("name:en") or el.get("tags", {}).get("name", "")
        if not name:
            continue
        coords = []
        for member in el.get("members", []):
            if member.get("role") == "outer" and "geometry" in member:
                coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
                break
        if len(coords) >= 3:
            features.append({"name": name, "ring": coords})

    os.makedirs(os.path.dirname(_GEOJSON_PATH), exist_ok=True)
    with open(_GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(features, f)
    print(f"  Saved {len(features)} area polygons → {_GEOJSON_PATH}")
    return features


def _load_areas() -> list:
    if os.path.exists(_GEOJSON_PATH):
        with open(_GEOJSON_PATH, encoding="utf-8") as f:
            features = json.load(f)
        print(f"  Loaded cached OSM areas: {len(features)} polygons")
        return features
    return _download_bangalore_areas()

# ── Point-in-polygon ──────────────────────────────────────────────────────────

def _pip(lat, lng, ring) -> bool:
    x, y, inside, j = lng, lat, False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (x < (xj-xi)*(y-yi)/(yj-yi+1e-12)+xi):
            inside = not inside
        j = i
    return inside

def _osm_area(lat, lng, features) -> str:
    for f in features:
        if _pip(lat, lng, f["ring"]):
            return f["name"]
    return ""

# ── Coarse grid fallback ──────────────────────────────────────────────────────

_GRID = [
    (13.10, 13.35, 77.45, 77.65, "North Bengaluru"),
    (13.10, 13.35, 77.65, 77.90, "North-East Bengaluru"),
    (12.90, 13.10, 77.45, 77.60, "West Bengaluru"),
    (12.90, 13.10, 77.60, 77.75, "Central Bengaluru"),
    (12.90, 13.10, 77.75, 77.90, "East Bengaluru"),
    (12.70, 12.90, 77.45, 77.60, "South-West Bengaluru"),
    (12.70, 12.90, 77.60, 77.75, "South Bengaluru"),
    (12.70, 12.90, 77.75, 77.90, "South-East Bengaluru"),
]

def _grid_area(lat, lng) -> str:
    for lat_min, lat_max, lng_min, lng_max, name in _GRID:
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            return name
    return "Bengaluru"

def _area_for(lat, lng, features) -> str:
    return _osm_area(lat, lng, features) or _grid_area(lat, lng)

# ── Canonical name builder ────────────────────────────────────────────────────

def build_canonical_names(df: pd.DataFrame, features: list) -> dict[str, str]:
    """
    For each cluster_key:
      - Single location → most frequent stop_name as-is
      - Multiple locations → "Most Frequent Name (Area)"
    """
    # Which stop_norms have multiple clusters?
    multi_norms = set(
        df.groupby("stop_norm")["final_cluster"]
        .nunique()
        .pipe(lambda s: s[s > 1].index)
    )

    # Most frequent stop_name per cluster_key
    best_name = (
        df.groupby("final_cluster")["stop_name"]
        .agg(lambda s: s.value_counts().index[0])
        .to_dict()
    )

    # Centroid per cluster_key
    centroid = (
        df.groupby("final_cluster")[["latitude", "longitude"]]
        .mean()
        .apply(lambda r: (r["latitude"], r["longitude"]), axis=1)
        .to_dict()
    )

    canonical: dict[str, str] = {}
    for ck, name in best_name.items():
        norm = ck.split("###")[0]
        if norm not in multi_norms:
            canonical[ck] = name
        else:
            lat, lng = centroid.get(ck, (12.97, 77.59))
            area = _area_for(lat, lng, features)
            canonical[ck] = f"{name} ({area})"

    return canonical

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Loading dataset…")
    df = pd.read_csv(STOP_LEVEL_CLEANED)
    df["stop_norm"] = df["stop_name"].str.strip().str.lower()

    print(f"Building clusters for {df['stop_norm'].nunique()} unique stop names…")
    t0 = time.time()
    df["final_cluster"] = build_clusters(df)
    print(f"  Clustered in {time.time()-t0:.1f}s")

    n_multi = (df.groupby("stop_norm")["final_cluster"].nunique() > 1).sum()
    print(f"  {df['final_cluster'].nunique()} unique clusters")
    print(f"  {n_multi} stop names split into multiple geographic clusters")

    # Save stop_clusters.csv (same format as before)
    out = df[["route_no", "stop_sequence", "stop_norm", "final_cluster"]]
    out.to_csv(STOP_CLUSTERS, index=False)
    print(f"  Saved → {STOP_CLUSTERS}")

    # Build area-aware canonical names
    print("\nBuilding area-aware display names…")
    features = _load_areas()
    canonical = build_canonical_names(df, features)

    # Show samples
    multi_norms = set(
        df.groupby("stop_norm")["final_cluster"]
        .nunique()
        .pipe(lambda s: s[s > 1].index)
    )
    print("\nSample disambiguated names:")
    shown = 0
    for norm in sorted(multi_norms):
        variants = {ck: canonical[ck] for ck in canonical if ck.startswith(f"{norm}###")}
        if variants:
            for ck, name in sorted(variants.items()):
                print(f"  {name}")
            shown += 1
        if shown >= 10:
            break

    # Save stop_canonical_names.csv
    cn_df = pd.DataFrame([
        {"cluster_key": k, "canonical_name": v}
        for k, v in canonical.items()
    ])
    cn_df.to_csv(_CANONICAL_PATH, index=False)
    print(f"\nSaved → {_CANONICAL_PATH} ({len(cn_df)} entries)")
    print("\nDone. Restart Streamlit to apply changes.")