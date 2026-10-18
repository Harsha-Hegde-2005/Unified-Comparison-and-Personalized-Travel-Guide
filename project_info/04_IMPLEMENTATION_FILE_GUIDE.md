# PART IV: REPOSITORY ARCHITECTURE AND SOURCE CODE WALKTHROUGH

---

## Chapter 8: Complete Repository and File-by-File Guide

### 8.1 Repository Directory Tree

```
c:\Users\Harsh\Downloads\BMTC_fixed\
├── backend/                               ── FastAPI backend services & computational engines
│   ├── adapters/                          ── Modality adapters for unified interfaces
│   │   ├── bmtc_adapter.py                ── Standardized wrapper around BMTC router
│   │   └── metro_adapter.py               ── Standardized wrapper around Metro journey planner
│   ├── benchmarks/                        ── GTFS reference evaluation & regression tester
│   │   ├── dataset.json                   ── Benchmark transit test cases
│   │   ├── evaluator.py                   ── Journey validation & ground-truth verification
│   │   ├── gtfs_reference_adapter.py      ── GTFS schedule ground truth reader
│   │   └── run_benchmark.py               ── Benchmark execution harness
│   ├── modes/                             ── Modal routing engines
│   │   ├── bmtc/                          ── Bus transit engine:
│   │   │   ├── core/
│   │   │   │   ├── config.py              ── Slabs, speeds, toll surcharges, constants
│   │   │   │   ├── graph.py               ── Frequency Dijkstra graph builder (193k nodes)
│   │   │   │   ├── gtfs.py                ── GTFS file parser & schedule unpacker
│   │   │   │   ├── loader.py              ── Cached stops dataset loader
│   │   │   │   └── stops.py               ── Fuzzy stop searches & canonical resolvers
│   │   │   └── features/
│   │   │       ├── fare.py                ── BMTC tariff slabs (Ordinary, Vajra, KIA)
│   │   │       ├── journey.py             ── Journey candidate formatter
│   │   │       ├── routing.py             ── Direct & transfer bus search coordinator
│   │   │       └── schedule.py            ── Speed profiles & segment time calculation
│   │   ├── metro/                         ── Rail transit engine:
│   │   │   ├── engines/
│   │   │   │   ├── distance_engine.py     ── Metro station coordinate distance calculator
│   │   │   │   ├── fare_engine.py         ── Stations-crossed tariff matrix & smart card discount
│   │   │   │   ├── graph_builder.py       ── Topological graph compiler from JSON master
│   │   │   │   ├── routing_engine.py      ── BFS shortest-hop station pathfinder
│   │   │   │   └── time_engine.py         ── Station dwell & inter-station run time model
│   │   │   └── planner/
│   │   │       └── journey_planner.py     ── Namma Metro multi-line journey coordinator
│   │   └── cab/                           ── Ride-hailing simulation engine:
│   │       ├── engines/
│   │       │   ├── distance_engine.py     ── OSRM road distance & duration wrapper
│   │       │   ├── fare_engine.py         ── Dynamic surge & multi-provider rate engine
│   │       │   ├── geocoding_engine.py    ── Coordinate lookups for colloquial locations
│   │       │   └── location_engine.py     ── Boundary validator for Bengaluru urban zone
│   │       └── planner/
│   │           └── ride_planner.py        ── Multi-tier cab candidate builder
│   ├── multimodal/                        ── Multimodal transit engine:
│   │   ├── config.py                      ── Metro stations with nearby BMTC stop mapping
│   │   ├── interchange_matcher.py         ── Spatial 500m proximity matcher
│   │   └── router.py                      ── BMTC + Metro + BMTC chain planner
│   ├── shared/                            ── Cross-cutting utilities & data interfaces
│   │   ├── interfaces/
│   │   │   ├── journey_plan.py            ── Standardized dataclasses for journey legs
│   │   │   └── stop_location.py           ── Coordinate schemas
│   │   └── utils/
│   │       ├── distance.py                ── Haversine and Euclidean helpers
│   │       ├── stop_resolver.py           ── Canonical synonym cleaner & alias resolver
│   │       └── time.py                    ── IST timestamp formatters
│   ├── auth.py                            ── Password hashing (bcrypt) & JWT token manager
│   ├── chatbot_engine.py                  ── Rule-based NLP intent parser & deterministic fallback
│   ├── db.py                              ── SQLAlchemy models (Users, Journeys, Vehicles, Docs)
│   ├── groq_chat.py                       ── Groq LLaMA-3.3-70B API integration with strict prompting
│   ├── location_aliases.py                ── Curated dictionary of 200+ Bengaluru local aliases
│   ├── main.py                            ── Primary FastAPI application (5,747 lines, 48 endpoints)
│   ├── poi_data.py                        ── 150+ Bengaluru tech parks, colleges, malls, hospitals
│   ├── recommender.py                     ── MCDM utility scorer & dynamic XAI justification builder
│   ├── travel_tools.py                    ── Standardized Travel Tool layer (Tools A to L)
│   └── weather_helper.py                  ── Open-Meteo live precipitation & temperature client
│
├── database/                              ── Raw, processed, and reference datasets
│   ├── bmtc/
│   │   ├── processed/
│   │   │   ├── bmtc_stop_level_cleaned.csv── 100,818 rows: route stops & sequences
│   │   │   ├── reverse_routes_supplement.csv ── 3,658 rows: reverse journey additions
│   │   │   ├── stop_canonical_names.csv   ── 5,758 rows: cluster_key to display name map
│   │   │   ├── stop_clusters.csv          ── 100,818 rows: stop_sequence to physical cluster key
│   │   │   └── stops_clean.csv            ── 14,137 rows: deduplicated stop coordinates
│   │   └── raw/
│   │       ├── routes.txt                 ── 3,959 GTFS bus routes
│   │       ├── stop_times.txt             ── 25 MB GTFS schedule stop arrival times
│   │       ├── stops.txt                  ── 8,303 GTFS raw bus stop records
│   │       └── trips.txt                  ── 34,336 GTFS trip definitions
│   ├── cab/
│   │   └── fare_config.json               ── Base fares, per-km, per-min, surge rules for 4 aggregators
│   ├── metro/
│   │   ├── fare_matrix.csv                ── 14 rows: stations crossed to rupee tariff mapping
│   │   ├── metro_coords.json              ── 83 metro stations mapped to exact latitude/longitude
│   │   └── station_master.json            ── Purple and Green line sequence definitions
│   ├── personal_vehicle/
│   │   ├── Car details v3.csv             ── 8,128 car models with mileage & fuel type
│   │   └── india_500_bike_models_master_dataset.csv ── 346 motorcycle models with ARAI mileage
│   └── poi/
│       └── pois.json                      ── Curated metadata for major Bengaluru destinations
│
├── frontend/                              ── React 18 + Vite client application
│   ├── src/
│   │   ├── assets/                        ── Static hero images and icons
│   │   ├── App.jsx                        ── Primary single-page app (Dashboard, Planner, Compare)
│   │   ├── BengaluruApp.jsx               ── Alternate mobile-responsive theme layout
│   │   ├── config.js                      ── API base URL configuration
│   │   ├── main.jsx                       ── React DOM entry point
│   │   ├── RapidoTester.jsx               ── Standalone developer testing tool for cab fares
│   │   └── RideModeModal.jsx              ── In-trip tracking with GPS stop-snapping & voice TTS
│   ├── package.json                       ── Frontend dependencies (React, Vite, ESLint)
│   └── vite.config.js                     ── Vite development server configuration
│
├── research/                              ── ADCOM 2027 Scientific Publication Package
│   ├── mas/                               ── Multi-Agent System architecture:
│   │   ├── agent_interface.py             ── Typed message dataclasses (`AgentMessage`, `AgentResult`)
│   │   ├── agents.py                      ── Specialized agents (User, Context, BMTC, Metro, Cab, Coord)
│   │   └── coordinator.py                 ── Parallel ThreadPoolExecutor MAS coordinator
│   ├── experiments/results/               ── Generated CSV artifacts for 20 benchmark corridors
│   ├── figures/                           ── Empirical plots (Figures 5 to 8)
│   ├── paper/main.tex                     ── Complete IEEE-format conference manuscript
│   └── scripts/
│       ├── run_experiments.py             ── Comprehensive empirical benchmark protocol ($N=10$)
│       ├── diagnose_agents.py             ── Candidate generation diagnostic tool
│       └── verify_paper_numbers.py        ── Automated assertion verifier (16/16 claims passed)
│
├── testing/                               ── Pytest verification suite (21 test files)
│   ├── conftest.py                        ── Mocked in-memory fixtures for rapid testing
│   ├── test_fare.py                       ── BMTC tariff slabs and toll surcharges (14 passed)
│   ├── test_gtfs.py                       ── GTFS schedule unpacking (13 passed)
│   ├── test_metro_coordinates.py          ── Coordinate bounds validation (1 passed)
│   ├── test_stops.py                      ── Fuzzy route search and canonical names (8 passed)
│   ├── test_weather.py                    ── Precipitation suitability penalties (3 passed)
│   ├── test_stop_resolver.py              ── Colloquial alias resolution (4 passed)
│   ├── test_short_distance_bmtc.py        ── Short-distance pedestrian walk trade-offs (6 passed)
│   ├── test_chatbot.py                    ── Intent parsing & API query validation
│   └── test_unified_modes.py              ── End-to-end integration across all modes
│
├── requirements.txt                       ── Backend Python dependencies
├── unified_transit.db                     ── Active SQLite database (users, bookmarks, documents)
└── README.md                              ── Project overview and setup instructions
```

---

## Chapter 23: Important Code Walkthroughs

### 23.1 Application Entry Point & Compare Orchestrator
**File:** [`backend/main.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/backend/main.py#L3291-L3470)  
**Function:** `@app.post("/api/compare") def compare(req: JourneyRequest)`

#### Rationale & Architecture
This endpoint is the central nerve center of the entire platform. When a user submits an origin and destination, `compare()` orchestrates canonical resolution, triggers parallel modal solvers, normalizes multi-objective utility metrics, and attaches dynamic natural language explanations.

#### Code Walkthrough
```python
@app.post("/api/compare")
def compare(req: JourneyRequest):
    # 1. Resolve stop aliases to canonical names
    src_norm = resolve_stop_name(req.source, "bmtc", bmtc_stops=ALL_STOPS)
    dst_norm = resolve_stop_name(req.destination, "bmtc", bmtc_stops=ALL_STOPS)
    
    # 2. Coordinate resolution
    src_coords = get_stop_coords(src_norm) or parse_coords(req.source)
    dst_coords = get_stop_coords(dst_norm) or parse_coords(req.destination)
    
    if not src_coords or not dst_coords:
        raise HTTPException(status_code=400, detail="Unable to resolve geographic coordinates.")

    results = {}

    # 3. Modal Solver: BMTC Bus
    try:
        results["bmtc"] = bmtc_plan(req)
    except Exception as e:
        results["bmtc"] = {"available": False, "error": str(e)}

    # 4. Modal Solver: Namma Metro
    try:
        results["metro"] = metro_plan(req)
    except Exception as e:
        results["metro"] = {"available": False, "error": str(e)}

    # 5. Modal Solver: Ride-Hailing (Cab/Auto)
    try:
        cab_req = CabEstimateRequest(
            src_lat=src_coords[0], src_lng=src_coords[1],
            dst_lat=dst_coords[0], dst_lng=dst_coords[1]
        )
        cab_data = _get_all_ride_fares(cab_req)
        results["cab"] = cab_data
    except Exception as e:
        results["cab"] = {"available": False, "error": str(e)}

    # 6. Modal Solver: Personal Vehicle (Car)
    try:
        results["car"] = _personal_vehicle_estimate(src_coords, dst_coords)
    except Exception as e:
        results["car"] = {"available": False, "error": str(e)}

    # 7. Modal Solver: Multimodal (Bus + Metro)
    try:
        results["multimodal"] = multimodal_plan(req)
    except Exception as e:
        results["multimodal"] = {"available": False, "error": str(e)}

    # 8. Environmental Context Ingestion
    weather_info = get_weather_at_eta(dst_coords[0], dst_coords[1], req.time)

    # 9. Recommendation Ranking & Explainable AI
    recommendations = get_recommendations(
        results=results,
        source=src_norm,
        destination=dst_norm,
        preference=req.preference or "cost",
        weather=weather_info
    )

    return {
        "status": "success",
        "source": src_norm,
        "destination": dst_norm,
        "results": results,
        "recommendations": recommendations,
        "weather": weather_info
    }
```

---

### 23.2 Frequency Dijkstra Graph Builder
**File:** [`backend/modes/bmtc/core/graph.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/backend/modes/bmtc/core/graph.py#L42-L198)  
**Function:** `@lru_cache(maxsize=1) def _build_everything()`

#### Rationale & Architecture
Raw GTFS graphs suffer from high memory consumption and poor path selection when unweighted. This function builds an optimized graph in RAM once per server lifecycle. It incorporates route frequency weighting to lower impedance on frequent routes and groups stops by location clusters to eliminate name collisions.

#### Code Walkthrough
```python
@lru_cache(maxsize=1)
def _build_everything():
    # 1. Load GTFS route frequency (trips per day)
    trips_df = pd.read_csv(GTFS_TRIPS, dtype={"route_id": str, "trip_id": str})
    routes_df = pd.read_csv(GTFS_ROUTES, dtype={"route_id": str, "route_short_name": str})
    merged = trips_df.merge(routes_df[["route_id", "route_short_name"]], on="route_id", how="left")
    route_trips = merged.groupby("route_short_name").size().to_dict()

    def freq_weight(distance_km: float, route_no: str) -> float:
        base = route_no.replace("_REV", "")
        trips = route_trips.get(base, 1)
        # Logarithmic impedance scaling
        return distance_km / math.log1p(trips)

    # 2. Load stop-location cluster mapping
    cl_df = pd.read_csv(STOP_CLUSTERS, dtype={"route_no": str, "stop_sequence": int, "final_cluster": str})
    cluster_lookup = {(r.route_no, int(r.stop_sequence)): r.final_cluster for r in cl_df.itertuples()}

    def _cluster_key(route_no: str, stop_seq: int, stop_norm: str) -> str:
        return cluster_lookup.get((route_no, stop_seq), stop_norm)

    # 3. Build directed edges between consecutive route stops
    graph_ = {}
    raw_km_ = {}
    stop_routes = {}

    for route_no, group in stops_df.groupby("route_no"):
        rows = list(group.sort_values("stop_sequence").itertuples())
        for i in range(len(rows) - 1):
            a, b = rows[i], rows[i + 1]
            ck_a = _cluster_key(route_no, int(a.stop_sequence), a.stop_norm)
            ck_b = _cluster_key(route_no, int(b.stop_sequence), b.stop_norm)
            
            u = (ck_a, route_no)
            v = (ck_b, route_no)
            
            raw_d = haversine(a.latitude, a.longitude, b.latitude, b.longitude)
            weight = freq_weight(raw_d, route_no)
            
            graph_.setdefault(u, []).append((v, weight))
            raw_km_[(u, v)] = raw_d
            stop_routes.setdefault(ck_a, set()).add(route_no)

    # 4. Build spatial grid bucket index for pedestrian walking transfers (<= 1.0 km)
    # Reduces proximity neighbor search from O(N^2) to O(N)
    nearby_cluster_keys = build_spatial_grid_index(stops_df, max_walk_km=1.0)

    return graph_, stop_routes, raw_km_, route_trips, nearby_cluster_keys
```

---

### 23.3 Dynamic Cab Surge & Tariff Engine
**File:** [`backend/modes/cab/engines/fare_engine.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/backend/modes/cab/engines/fare_engine.py#L45-L185)  
**Function:** `get_all_fares_for_provider(provider_key, distance_km, duration_min, current_time, weather)`

#### Rationale & Architecture
Simulates real-world dynamic pricing across GoRide, SwiftCab, ZipGo, and NammaMove. Rather than displaying a static number, it evaluates time-of-day traffic congestion, night-shift rates, and rain intensity to compute a realistic price range.

#### Code Walkthrough
```python
def get_all_fares_for_provider(self, provider_key, distance_km, duration_min, current_time=None, weather="clear"):
    provider_cfg = self.providers.get(provider_key, {})
    vehicles = provider_cfg.get("vehicles", {})
    results = []

    for vehicle_key, cfg in vehicles.items():
        base_fare = cfg.get("base_fare", 0.0)
        base_dist = cfg.get("base_dist", 0.0)
        per_km = cfg.get("per_km", 0.0)
        per_min = cfg.get("per_min", 0.0)

        # 1. Base distance and time charges
        billable_km = max(0.0, distance_km - base_dist)
        pre_surge = base_fare + (billable_km * per_km) + (duration_min * per_min)

        # 2. Time-of-day surge multiplier
        time_minutes = current_time.hour * 60 + current_time.minute
        delta_time = 0.0
        if (8 * 60 + 30) <= time_minutes <= (10 * 60 + 30):
            delta_time = 0.25  # Morning peak
        elif (17 * 60 + 30) <= time_minutes <= (20 * 60 + 30):
            delta_time = 0.30  # Evening peak
        elif time_minutes >= (22 * 60) or time_minutes < (5 * 60):
            delta_time = 0.50  # Late night

        # 3. Weather surge multiplier
        delta_weather = 0.0
        if "heavy rain" in weather.lower():
            delta_weather = 0.40
        elif "light rain" in weather.lower():
            delta_weather = 0.15

        surge_mult = 1.0 + delta_time + delta_weather
        surge_amount = pre_surge * (surge_mult - 1.0)

        # 4. Total and minimum fare threshold
        total = max(cfg.get("min_fare", 0.0), round(pre_surge + surge_amount + cfg.get("booking_fee", 0.0)))

        results.append({
            "vehicle": cfg.get("name", vehicle_key),
            "fare_estimate": total,
            "fare_min": int(total * 0.95),
            "fare_max": int(total * 1.05),
            "surge_active": surge_mult > 1.0
        })

    return results
```

---

### 23.4 Multi-Objective Utility Engine & Explainable AI
**File:** [`backend/recommender.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/backend/recommender.py#L320-L430)  
**Function:** `get_recommendations(results, source, destination, preference, weather)`

#### Rationale & Architecture
Translates multi-dimensional transit outputs (rupees, minutes, transfer counts, carbon grams, rain probabilities) into an ordered ranking accompanied by human-readable explanations.

#### Code Walkthrough
```python
def get_recommendations(results, source, destination, preference="cost", weather="clear"):
    available_options = [opt for opt in extract_options(results) if opt["available"]]
    if not available_options:
        return []

    # 1. Min-Max Scaling boundaries
    min_cost, max_cost = min(o["cost"] for o in available_options), max(o["cost"] for o in available_options)
    min_time, max_time = min(o["time"] for o in available_options), max(o["time"] for o in available_options)
    min_eco, max_eco = min(o["emissions"] for o in available_options), max(o["emissions"] for o in available_options)

    # 2. Select preference weights
    w = WEIGHT_SETS.get(preference.lower(), WEIGHT_SETS["default"])

    # 3. Compute normalized utility score
    for opt in available_options:
        f_cost = 1.0 - ((opt["cost"] - min_cost) / (max_cost - min_cost)) if max_cost > min_cost else 1.0
        f_time = 1.0 - ((opt["time"] - min_time) / (max_time - min_time)) if max_time > min_time else 1.0
        f_eco = 1.0 - ((opt["emissions"] - min_eco) / (max_eco - min_eco)) if max_eco > min_eco else 1.0
        
        composite = (
            w["cost"] * f_cost +
            w["time"] * f_time +
            w["comfort"] * opt["comfort"] +
            w["eco"] * f_eco +
            w["weather"] * opt["weather_suitability"] +
            w["traffic"] * opt["traffic_suitability"]
        )
        opt["score"] = round(composite * 100, 1)

    available_options.sort(key=lambda x: x["score"], reverse=True)

    # 4. Generate dynamic numerical explanations
    explanations = generate_fallback_explanations(available_options, weather, preference, source, destination)
    
    for idx, opt in enumerate(available_options):
        opt["rank"] = idx + 1
        opt["explanation"] = explanations.get(opt["mode"])

    return available_options
```

---

### 23.5 Grounded LLM Chatbot Integration
**File:** [`backend/groq_chat.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/backend/groq_chat.py#L84-L128)  
**Function:** `generate_groq_reply(message, history, context_data)`

#### Rationale & Architecture
Calls Groq’s high-throughput LLaMA-3.3-70B API. By inserting the output of verified travel tools into the prompt as `CONTEXT DATA (ground truth)`, the model is instructed never to hallucinate fares or bus routes.

#### Code Walkthrough
```python
def generate_groq_reply(message: str, history=None, context_data=None, timeout=8.0):
    client = _get_client()
    if client is None:
        return None  # Triggers graceful fallback to deterministic ChatbotEngine

    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Inject ground-truth routing/fare numbers
        if context_data:
            context_str = json.dumps(context_data, default=str)[:3000]
            messages.append({
                "role": "system",
                "content": f"CONTEXT DATA (ground truth for this question): {context_str}"
            })

        # Append conversation history
        for turn in (history or [])[-8:]:
            messages.append({"role": turn["role"], "content": str(turn["content"])[:1500]})

        messages.append({"role": "user", "content": message[:1500]})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4,
            max_tokens=350,
            timeout=timeout
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return None  # Silent fallback on timeout, quota, or network drop
```

---
*(End of Part IV — Proceed to [Part V: Testing, Results, and Limitations](file:///c:/Users/Harsh/Downloads/BMTC_fixed/project_info/05_TESTING_RESULTS_AND_LIMITATIONS.md))*
