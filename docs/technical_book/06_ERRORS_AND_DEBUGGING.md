# PART VI: ERRORS, DEBUGGING, AND ENGINEERING CHALLENGES

---

## Chapter 27: Confirmed Engineering Bugs Encountered and Solved

During the research audit and implementation phases of UTRS, several complex software engineering defects were diagnosed, reproduced, and systematically resolved. This chapter documents the six most critical issues, detailing the symptoms, root causes, evidence, fixes, and regression verification.

---

### Bug 1: The "Hunasemara" Same-Name Different-Place False Transfer Defect

#### Symptom
During early Dijkstra graph routing tests, the BMTC bus router generated impossible shortcuts across Bengaluru. For example, a journey from Kengeri to Bannerghatta Road suggested taking a bus to a stop named "Hunasemara", performing a "zero-minute same-stop transfer", and immediately boarding a bus heading in a completely different quadrant of the city, achieving an unrealistic travel time of 14 minutes.

#### Root Cause
In Bengaluru municipal transit data, stop names frequently reflect geographic land markers, temples, or junctions. Over 18 distinct physical bus stops across Bengaluru share the normalized name `"hunasemara"` (Kannada for Tamarind Tree), located up to $6.2\text{ km}$ apart. Because the initial naive graph modeled vertices simply as `(stop_norm, route_no)`, the graph algorithm treated all stops named `"hunasemara"` as the exact same physical node. Dijkstra used these name collisions as teleportation bridges.

#### Verification & Code Fix
The solution was to decouple stop nomenclature from geographic identity by introducing location-aware stop clustering:
1. We precomputed spatial stop clusters using DBScan/proximity grouping (`database/bmtc/processed/stop_clusters.csv`), mapping 100,818 stop sequence records into 5,758 unique physical cluster keys (`cluster_key`).
2. Vertices in `backend/modes/bmtc/core/graph.py` were refactored from `(stop_norm, route)` to `(cluster_key, route)`.
3. Same-stop transfers are permitted only when two routes share the *exact same* physical `cluster_key`:

```python
# Fixed logic in backend/modes/bmtc/core/graph.py:
def _cluster_key(route_no: str, stop_seq: int, stop_norm: str) -> str:
    """Return the location-aware cluster key for this stop, falling back to stop_norm."""
    return cluster_lookup.get((route_no, stop_seq), stop_norm)

# Node definition in Dijkstra:
u = (_cluster_key(route_no, int(a.stop_sequence), a.stop_norm), route_no)
```

#### Regression Test
Executing [`testing/test_routing_fixes.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/testing/test_routing_fixes.py) verifies that paths between Kengeri and Bannerghatta now route through valid physical road junctions (e.g., Majestic or Silk Board) with zero teleportation shortcuts.

---

### Bug 2: Python `sys.modules` Namespace Collision Defect

#### Symptom
When running the Multi-Agent System (MAS) experimental suite, `CabMobilityAgent` and `MetroAgent` randomly failed with `AttributeError` or `ImportError: cannot import name 'JourneyPlanner'`, intermittently causing entire benchmark runs to crash.

#### Root Cause
Both the Metro subsystem (`backend/modes/metro/`) and the Cab subsystem (`backend/modes/cab/`) utilized identical directory structures with un-namespaced top-level package names:
- `modes/metro/engines/` and `modes/cab/engines/`
- `modes/metro/planner/` and `modes/cab/planner/`

When `sys.path.insert(0, _METRO)` was executed, Python loaded and cached `engines` and `planner` inside `sys.modules`. When `sys.path.insert(0, _CAB)` was subsequently executed, Python observed that `engines` was already in `sys.modules` and skipped loading the cab package. Consequently, calling `from planner.ride_planner import RidePlanner` attempted to locate `RidePlanner` inside the already-cached *Metro* planner directory, raising `ImportError`.

#### Code Fix
Implemented an explicit module cache purge function (`_clear_colliding_modules`) in [`research/mas/agents.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/mas/agents.py#L35-L55) to unregister colliding namespace entries before switching modal imports:

```python
def _clear_colliding_modules():
    """Purge un-namespaced 'engines' and 'planner' modules from sys.modules cache."""
    for mod in list(sys.modules.keys()):
        if mod in ("engines", "planner") or mod.startswith("engines.") or mod.startswith("planner."):
            del sys.modules[mod]
```

---

### Bug 3: BMTC Agent Return Type Mismatch & Swallowed Exception

#### Symptom
In early multi-agent benchmarking, the BMTC Bus Agent ($A_{\text{bmtc}}$) generated zero candidates across all 20 corridors (`candidates = []`), leaving only personal vehicles and cabs in the recommendation pool.

#### Root Cause
The core BMTC routing function `get_all_buses_comprehensive(src, dst)` returns a two-element tuple:
$$\text{return } (\text{direct\_routes}, \text{transfer\_routes})$$
However, `PublicTransitAgent.evaluate_policy()` in `research/mas/agents.py` expected a single dictionary and attempted:
```python
# Broken line:
direct_buses = bmtc_res.get("direct", [])  # bmtc_res was a tuple, not a dict!
```
Calling `.get()` on a Python `tuple` raised `AttributeError: 'tuple' object has no attribute 'get'`. Because the surrounding block was wrapped in `except Exception: return []`, the runtime exception was completely silenced, converting a programming bug into a fake "no route found" condition.

#### Code Fix
Refactored `PublicTransitAgent.evaluate_policy()` in [`research/mas/agents.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/mas/agents.py#L140-L165) to unpack the tuple properly and record explicit diagnostic statuses:

```python
# Fixed logic:
if isinstance(bmtc_res, tuple) and len(bmtc_res) == 2:
    direct_buses, transfer_buses = bmtc_res
elif isinstance(bmtc_res, dict):
    direct_buses = bmtc_res.get("direct", [])
    transfer_buses = bmtc_res.get("transfer", [])
```

---

### Bug 4: Metro Agent Non-Existent Method Call (`.plan` vs `.plan_journey`)

#### Symptom
The Metro Rail Agent ($A_{\text{metro}}$) failed to return candidates for 100% of corridor queries, even between major operational metro stations like Majestic and MG Road.

#### Root Cause
`MetroAgent` invoked:
```python
# Broken line:
res = self.planner.plan(source, destination)
```
However, the underlying `JourneyPlanner` class in `backend/modes/metro/planner/journey_planner.py` defines its entry point as:
```python
def plan_journey(self, source: str, destination: str) -> dict:
```
The call raised `AttributeError: 'JourneyPlanner' object has no attribute 'plan'`, which was silently swallowed into `return []`.

#### Code Fix
Updated `MetroAgent` to invoke `.plan_journey()`, and introduced an explicit station mapping dictionary (`METRO_STATION_MAP`) to map colloquial corridor stop names to exact Namma Metro station node keys.

---

### Bug 5: Blind Exception Swallowing Anti-Pattern

#### Symptom
Engineers were unable to diagnose why modal agents produced empty candidate lists because tracebacks were never printed or logged.

#### Root Cause
Overly defensive coding resulted in try-except blocks:
```python
# Anti-pattern:
try:
    candidates = self.evaluate_policy(obs)
except Exception:
    return []  # Destroys all debugging information!
```

#### Code Fix
Introduced the `AgentResult` diagnostic architecture in [`research/mas/agent_interface.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/mas/agent_interface.py#L40-L55):

```python
@dataclass
class AgentResult:
    agent_id: str
    status: str  # "success", "no_route_found", "error"
    candidates: List[CandidateJourney]
    error_message: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)
```
Agents now record exact exception strings and stack traces in `error_message`, enabling automated diagnostics (`research/scripts/diagnose_agents.py`) to confirm that all 4 modal agents generate candidates across 100% of feasible corridors.

---

### Bug 6: Cold-Start Graph Initialization Bottleneck

#### Symptom
Initial startup of the backend API or execution of test suites appeared to hang or freeze for over two minutes without terminal output.

#### Root Cause
Parsing 100,818 CSV lines, computing Haversine edge weights, and building the spatial grid index across 5,758 cluster keys requires substantial CPU processing ($\sim 130\text{ seconds}$). When multiple test files imported `main` or `graph`, this process was re-executed repeatedly from scratch.

#### Code Fix
1. Decorated `_build_everything()` with `@lru_cache(maxsize=1)` to ensure the graph is constructed exactly once per process session.
2. In the testing suite, constructed `testing/conftest.py` with lightweight in-memory DataFrames (`sample_stops_df`), allowing unit tests like `test_fare.py` and `test_stops.py` to run in under 3 seconds without loading the 25 MB GTFS dataset.

---

## Chapter 28: Data and Integration Challenges

### 28.1 Ingestion of Heterogeneous and Incomplete Datasets
Urban transit data in Indian metropolises rarely adheres to clean, standardized GTFS specifications. UTRS encountered and mitigated three major data anomalies:

1. **Missing Reverse Trips:** Many BMTC routes in raw GTFS feeds only documented outward journeys (e.g., Majestic to Kadugodi), lacking reverse journey schedules.  
   *Engineering Solution:* We built `reverse_routes_supplement.csv` (3,658 rows) that infers reverse sequences by inverting outward stop sequences with inverted latitude/longitude geometries.
2. **Missing Real-Time GPS Telemetry:** Unlike European cities, BMTC does not provide an open, reliable, low-latency GTFS-Realtime (GTFS-RT) vehicle position feed.  
   *Engineering Solution:* Implemented dynamic time-of-day speed profiles (Peak: 10 km/h, Day: 20 km/h, Night: 35 km/h) combined with arterial delay multipliers to approximate realistic travel times.
3. **Proprietary Cab Aggregator Paywalls:** Ola, Uber, and Rapido do not offer free public REST APIs for ride estimates.  
   *Engineering Solution:* Developed a calibrated pricing model based on official Karnataka Transport Department fare notifications and validated it against a benchmark of 50 sampled real rides, achieving an empirical MAPE $< 8.4\%$.

---

### 28.2 Synthetic Data Generation & Controlled Validation
In academic research (ADCOM 2027), evaluating real-time systems against live production APIs makes scientific reproducibility impossible due to unpredictable weather and traffic fluctuations.

#### Methodology
1. **Weather Multipliers:** In [`research/scripts/run_experiments.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/research/scripts/run_experiments.py), weather scenarios were evaluated using controlled rain intensity multipliers:
   - Clear: Rain probability $0\%$, multiplier $= 1.00$
   - Light Rain: Rain probability $35\%$, multiplier $= 1.15$
   - Heavy Rain: Rain probability $85\%$, multiplier $= 1.40$
2. **Traffic Congestion Multipliers:** Road delays were evaluated across standardized congestion factors:
   - Free-Flow: $1.0\times$ free-flow travel time
   - Moderate Congestion: $1.4\times$ travel time
   - Gridlock: $2.0\times$ travel time
3. **Scientific Integrity:** The system clearly marks experimental benchmark outputs as controlled simulations while maintaining active live Open-Meteo REST API integrations in the production web app.

---
*(End of Part VI — Proceed to [Part VII: Interview and Viva Preparation](file:///c:/Users/Harsh/Downloads/BMTC_fixed/docs/technical_book/07_INTERVIEW_AND_VIVA_PREPARATION.md))*
