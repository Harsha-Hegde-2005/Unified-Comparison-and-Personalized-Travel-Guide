# PART III: ALGORITHMS, MATHEMATICS, AND PSEUDOCODE

---

## Chapter 12: Geographic Distance and the Haversine Formula

### 12.1 Mathematical Derivation & Geographic Principles
To compute distances across the Earth's surface without expensive external API calls, UTRS implements the **Haversine Formula**. The Earth is modeled as an approximate sphere of mean volumetric radius:
$$R = 6371.0\text{ km}$$

#### The Geometry of Spherical Coordinates
A point on Earth is defined by latitude ($\phi$) and longitude ($\lambda$) in decimal degrees:
- Latitude $\phi \in [-90^\circ, +90^\circ]$: North-South position relative to the Equator.
- Longitude $\lambda \in [-180^\circ, +180^\circ]$: East-West position relative to the Prime Meridian.

Because trigonometric functions in programming standard libraries (`math.sin`, `math.cos`) require angles in radians, degrees must first be converted:
$$\text{radians} = \text{degrees} \times \frac{\pi}{180}$$

#### The Haversine Equations
Given two points $P_1(\phi_1, \lambda_1)$ and $P_2(\phi_2, \lambda_2)$, let:
$$\Delta \phi = \phi_2 - \phi_1 \quad (\text{difference in latitude in radians})$$
$$\Delta \lambda = \lambda_2 - \lambda_1 \quad (\text{difference in longitude in radians})$$

The square of half the chord length between the points, denoted as $a$, is:
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$

The angular distance in radians, denoted as $c$, is the central angle:
$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$

The resulting great-circle distance $d$ across the spherical surface is:
$$d = R \cdot c$$

---

### 12.2 Step-by-Step Worked Numerical Example
Let us trace the exact distance calculation between two key transit landmarks in Bengaluru:
- **Point 1: Kempegowda Bus Station (Majestic):** $\phi_1 = 12.9778^\circ\text{ N}, \lambda_1 = 77.5724^\circ\text{ E}$
- **Point 2: Indiranagar Metro Station:** $\phi_2 = 12.9784^\circ\text{ N}, \lambda_2 = 77.6408^\circ\text{ E}$

#### Step 1: Convert coordinates to radians
$$\phi_1 = 12.9778 \times \frac{\pi}{180} \approx 0.226505\text{ rad}$$
$$\phi_2 = 12.9784 \times \frac{\pi}{180} \approx 0.226515\text{ rad}$$
$$\Delta \phi = 0.226515 - 0.226505 = 0.000010\text{ rad}$$
$$\Delta \lambda = (77.6408 - 77.5724) \times \frac{\pi}{180} = 0.0684 \times \frac{\pi}{180} \approx 0.0011938\text{ rad}$$

#### Step 2: Compute $a$
$$\sin^2\left(\frac{\Delta \phi}{2}\right) = \sin^2(0.000005) \approx 2.5 \times 10^{-11}$$
$$\cos(\phi_1) = \cos(0.226505) \approx 0.97447$$
$$\cos(\phi_2) = \cos(0.226515) \approx 0.97447$$
$$\sin^2\left(\frac{\Delta \lambda}{2}\right) = \sin^2(0.0005969) \approx 3.563 \times 10^{-7}$$
$$a = 2.5 \times 10^{-11} + (0.97447 \times 0.97447 \times 3.563 \times 10^{-7}) \approx 3.383 \times 10^{-7}$$

#### Step 3: Compute central angle $c$
$$\sqrt{a} \approx \sqrt{3.383 \times 10^{-7}} \approx 0.0005816$$
$$\sqrt{1 - a} \approx \sqrt{0.99999966} \approx 0.9999998$$
$$c = 2 \cdot \text{atan2}(0.0005816, 0.9999998) \approx 2 \times 0.0005816 = 0.0011632\text{ rad}$$

#### Step 4: Multiply by Earth radius $R$
$$d = 6371.0 \times 0.0011632 \approx 7.41\text{ km}$$

**Validation:** The actual road distance along Old Airport Road / MG Road is approximately $9.2\text{ km}$. The Haversine distance correctly captures the theoretical minimum straight-line great-circle distance ($7.41\text{ km}$).

---

### 12.3 Actual Python Implementation
Located in [`backend/modes/bmtc/core/graph.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/backend/modes/bmtc/core/graph.py#L31-L38):

```python
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in kilometers between two coordinate pairs."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2.0) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2.0) ** 2
    return 2.0 * R * atan2(sqrt(a), sqrt(1.0 - a))
```

#### Road-Network Detour Factor
In urban environments, vehicles must travel along the road grid rather than straight lines. Where OSRM road geometry is not queried directly, UTRS multiplies the Haversine distance by an urban circuity factor:
$$d_{\text{road\_est}} = d_{\text{haversine}} \times 1.30$$

---

## Chapter 13: Graph Representation and Route Finding

### 13.1 Graph Formulation of the BMTC Bus Network

Standard public transit routing models fail when stop names are ambiguous. In Bengaluru, multiple bus stops across different localities share identical names (e.g., 'Hunasemara', 'Cross', 'Gate'). If vertices in the graph are modeled simply as `stop_name`, a shortest-path algorithm can jump across disparate parts of the city in zero seconds.

To eliminate this defect, UTRS constructs an in-memory, frequency-weighted, route-aware directed multigraph:

```
Physical Graph State:
Vertex u = (cluster_key, route_no)
```

1. **Stop Cluster Keys (`cluster_key`):** Formed by spatial clustering of stop sequences (`stop_clusters.csv`). If two stops have the same name but are separated by $> 500\text{ m}$, they receive distinct cluster keys.
2. **Frequency-Weighted Edge Weight:**  
   The impedance $W(u, v)$ for traveling between consecutive stops on route $r$ is:
   $$W(u, v) = \frac{\text{Haversine}(\text{lat}_u, \text{lon}_u, \text{lat}_v, \text{lon}_v)}{\ln(1 + \text{trips\_per\_day}_r)}$$
   - High-frequency routes (e.g., Route 500D with 120 trips/day) have $\ln(1 + 120) = \ln(121) \approx 4.79$, scaling down the edge weight by nearly $80\%$.
   - Low-frequency feeder routes (e.g., 2 trips/day) have $\ln(1 + 2) = \ln(3) \approx 1.10$, keeping edge weights higher.
   - **Result:** Dijkstra naturally favors high-frequency trunk corridors.

```
                    [Route 500D: High Frequency (trips=120)]
               CK_A ─────────────────────────────────────────► CK_B
                     Weight = Distance / ln(121) = 5km / 4.79 = 1.04

                    [Route 201F: Low Frequency (trips=2)]
               CK_A ─────────────────────────────────────────► CK_B
                     Weight = Distance / ln(3)   = 5km / 1.10 = 4.54
```

3. **Transfer Edges & Penalties:**
   - **Same-Stop Transfer:** Transferring between route $r_1$ and route $r_2$ at the *exact same* physical cluster key adds $0.0\text{ km}$ distance and an algorithmic penalty of $+2.0\text{ km}$ equivalent weight (`new_w = w_dist + 2.0`).
   - **Proximity Transfer (Walking):** Walk connections between distinct cluster keys within $1.0\text{ km}$ are indexed using a spatial grid bucket. Walk transfers add $0.05\text{ km}$ physical transfer weight plus the transfer penalty.

---

### 13.2 Dijkstra's Algorithm on the BMTC Route Graph

#### Priority Queue State Structure
Dijkstra's algorithm maintains a min-heap priority queue where each element is:
$$\text{state} = (w_{\text{dist}}, \text{transfers}, \text{node})$$
where $\text{node} = (\text{cluster\_key}, \text{route\_no})$.

#### Path Reconstruction & Invariants
- **Hard Transfer Cap:** `transfers <= MAX_TRANSFERS` (enforced as a hard constraint with default cap $= 2$).
- **Optimality:** Paths are prioritized lexicographically by weighted impedance distance ($w_{\text{dist}}$), then transfer count.

#### Dijkstra Pseudocode (BMTC Bus)
```python
def dijkstra_bmtc(src_norm: str, dst_norm: str, max_transfers: int = 2):
    src_cluster_keys = get_clusters_for_stop(src_norm)
    dst_cluster_keys = set(get_clusters_for_stop(dst_norm))
    
    pq = []  # Min-heap storing: (w_dist, transfers, (cluster_key, route_no))
    wscore = {}  # (cluster_key, route_no) -> (min_w_dist, transfers)
    parent = {}  # node -> predecessor_node
    raw_km = {}  # node -> cumulative_physical_km

    # Initialize source states across all routes serving source cluster keys
    for ck in src_cluster_keys:
        for route in stop_routes[ck]:
            node = (ck, route)
            heapq.heappush(pq, (0.0, 0, node))
            wscore[node] = (0.0, 0)
            raw_km[node] = 0.0

    best_end_node = None

    while pq:
        w_dist, transfers, node = heapq.heappop(pq)
        
        # Stale state check
        if wscore.get(node, (float('inf'), float('inf'))) < (w_dist, transfers):
            continue

        ck, current_route = node
        
        # Destination reached check
        if ck in dst_cluster_keys:
            best_end_node = node
            break

        if transfers > max_transfers:
            continue

        # 1. Traverse in-route edges (riding along the same bus)
        for neighbor_node, edge_weight in graph.get(node, []):
            edge_raw_km = raw_km_lookup[(node, neighbor_node)]
            new_w = w_dist + edge_weight
            new_t = transfers
            new_raw = raw_km[node] + edge_raw_km
            
            if wscore.get(neighbor_node, (float('inf'), float('inf'))) > (new_w, new_t):
                wscore[neighbor_node] = (new_w, new_t)
                raw_km[neighbor_node] = new_raw
                parent[neighbor_node] = node
                heapq.heappush(pq, (new_w, new_t, neighbor_node))

        # 2. Traverse transfer edges (switching to a different bus route)
        for next_node, transfer_cost in get_transfer_neighbors(ck, current_route):
            new_w = w_dist + 2.0  # +2.0 km equivalent transfer penalty
            new_t = transfers + 1
            new_raw = raw_km[node]
            
            if wscore.get(next_node, (float('inf'), float('inf'))) > (new_w, new_t):
                wscore[next_node] = (new_w, new_t)
                raw_km[next_node] = new_raw
                parent[next_node] = node
                heapq.heappush(pq, (new_w, new_t, next_node))

    if not best_end_node:
        return None  # No valid path within transfer limit

    # Reconstruct path by following parent pointers
    path = []
    curr = best_end_node
    while curr:
        path.append(curr)
        curr = parent.get(curr)
    path.reverse()
    
    return path, raw_km[best_end_node]
```

---

### 13.3 Breadth-First Search (BFS) on Namma Metro Network

Because Namma Metro operates on an unweighted topology where train movements between adjacent stations take approximately uniform time ($1.5\text{ to }2.0\text{ mins}$) and intermediate station dwells are identical, finding the shortest path (minimum station hops) is optimal using **Breadth-First Search (BFS)**.

```
Purple Line: Challaghatta ─── ... ─── [Majestic] ─── ... ─── Whitefield
                                         │ (Interchange)
Green Line:  Silk Institute ─── ... ─── [Majestic] ─── ... ─── Madavara
```

#### BFS Algorithm Logic
1. Graph is represented as an adjacency list of undirected edges between adjacent stations on Green and Purple lines.
2. A FIFO queue maintains `[path]` arrays starting at `[source]`.
3. Visited stations are recorded in a hash set.
4. When `current == destination`, the full station sequence is returned.
5. Line transitions (e.g., Green to Purple at Majestic) are detected by examining station line attributes during leg construction.

---

## Chapter 14: Fare Estimation Algorithms

### 14.1 Public Transit: BMTC Bus Tariff Formulation

BMTC fares follow a progressive distance-slab structure based on service tier:

```
Fare (Rs)
  ▲
80│                                   ┌────────── Vajra AC Slabs (Rs 12 - 85)
60│                             ┌─────┘
40│                       ┌─────┘
30│                 ┌─────┴────────────────────── Ordinary Slabs (Rs 6 - 32)
  └─────────────────┴────────────────────────► Distance (km)
  0       4         10         20         30
```

#### Ordinary Bus Fare Slabs (`ORDINARY_FARE_SLABS`)
$$\text{Fare}_{\text{ordinary}}(d) = 
\begin{cases}
6 & \text{if } d \le 2\text{ km} \\
12 & \text{if } 2 < d \le 4\text{ km} \\
18 & \text{if } 4 < d \le 6\text{ km} \\
23 & \text{if } 6 < d \le 10\text{ km} \\
24 & \text{if } 10 < d \le 14\text{ km} \\
28 & \text{if } 14 < d \le 20\text{ km} \\
30 & \text{if } 20 < d \le 30\text{ km} \\
32 & \text{if } d > 30\text{ km (Default Cap)}
\end{cases}$$

#### Vajra AC Bus Slabs (`VAJRA_FARE_SLABS`)
Vajra Volvo services charge premium rates scaling from ₹12 (up to 2 km) to ₹80 (30 km), with a maximum default of ₹85.

#### KIA Airport Express Slabs (`KIA_FARE_SLABS`)
Airport express buses operate on dedicated high-fare zones:
- $\le 10\text{ km}$: ₹150
- $\le 20\text{ km}$: ₹200
- $\le 30\text{ km}$: ₹250
- $\le 40\text{ km}$: ₹280
- Full airport run ($> 40\text{ km}$): ₹310

#### Toll Surcharges (`TOLL_STOP_SURCHARGES`)
If a bus route traverses toll infrastructure, exact surcharges are added once per segment:
- **Electronic City Flyover (ELC):** $+ \text{₹}7$
- **NICE Road:** $+ \text{₹}5$
$$\text{Total Bus Fare} = \sum_{\text{segments}} \left( \text{Fare}_{\text{slab}}(d_i) + \text{Toll}_i \right)$$

---

### 14.2 Public Transit: Namma Metro Tariff Formulation

Namma Metro fares are determined by the number of **stations crossed** rather than continuous physical kilometers, loaded from [`database/metro/fare_matrix.csv`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/database/metro/fare_matrix.csv):

| Stations Crossed ($S$) | Token Fare (₹) | Peak Smart Card Fare (₹) (5% Off) | Non-Peak Smart Card Fare (₹) (10% Off) |
| :---: | :---: | :---: | :---: |
| $0 - 2$ | ₹11.00 | ₹10.45 | ₹9.90 |
| $3 - 4$ | ₹21.00 | ₹19.95 | ₹18.90 |
| $5 - 6$ | ₹32.00 | ₹30.40 | ₹28.80 |
| $7 - 8$ | ₹42.00 | ₹39.90 | ₹37.80 |
| $9 - 10$ | ₹53.00 | ₹50.35 | ₹47.70 |
| $11 - 15$ | ₹63.00 | ₹59.85 | ₹56.70 |
| $16 - 20$ | ₹74.00 | ₹70.30 | ₹66.60 |
| $21 - 26$ | ₹84.00 | ₹79.80 | ₹75.60 |
| $\ge 27$ | ₹95.00 | ₹90.25 | ₹85.50 |

Peak hours are strictly defined as:
$$\text{Peak} = (07:30 \le t \le 10:30) \lor (16:30 \le t \le 19:30)$$

---

### 14.3 Private Ride-Hailing (Cab, Auto, Bike) Formulation

The ride-hailing pricing model implemented in [`backend/modes/cab/engines/fare_engine.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/backend/modes/cab/engines/fare_engine.py) computes estimates across GoRide, SwiftCab, ZipGo, and NammaMove:

#### Mathematical Pricing Formula
$$\text{Fare}_{\text{cab}} = \max\left( \text{MinFare}, \; \text{PreSurge} + \text{SurgeAmt} + \text{NightAmt} + \text{Fee}_{\text{booking}} + \text{Surcharge}_{\text{long\_dist}} \right)$$

Where:
1. **Billable Distance:**
   $$\Delta d = \max(0.0, \; d - D_{\text{base}})$$
2. **Pre-Surge Subtotal:**
   $$\text{PreSurge} = \text{BaseFare} + (\Delta d \times R_{\text{km}}) + (t \times R_{\text{min}})$$
3. **Surge Multiplier ($\gamma_{\text{surge}}$):**
   $$\gamma_{\text{surge}} = 1.0 + \Delta_{\text{time}} + \Delta_{\text{weather}}$$
   - **Time Multiplier ($\Delta_{\text{time}}$):**
     - For Autos: late night ($22:00 - 05:00$) adds $+0.50$.
     - For Cabs: morning peak ($08:30 - 10:30$) adds $+0.25$; evening peak ($17:30 - 20:30$) adds $+0.30$; night adds $+0.50$.
   - **Weather Multiplier ($\Delta_{\text{weather}}$):**
     - Light rain / drizzle: $+0.15$
     - Heavy rain / thunderstorm: $+0.40$
     - Extreme storm / flooding: $+0.75$
4. **Surge Amount:**
   $$\text{SurgeAmt} = \text{PreSurge} \times (\gamma_{\text{surge}} - 1.0)$$
5. **Night Surcharge:**
   $$\text{NightAmt} = (\text{PreSurge} + \text{SurgeAmt}) \times (M_{\text{night}} - 1.0)$$

---

### 14.4 Personal Vehicle Fuel Cost Formulation

$$\text{FuelLitres} = \frac{\text{Distance (km)}}{\text{Vehicle Mileage (km/L)}}$$
$$\text{FuelCost} = \text{FuelLitres} \times \text{FuelPrice (₹/L)}$$
$$\text{Total Driving Cost} = \text{FuelCost} + \text{EstParkingFee}$$

- **Defaults:** Petrol price = ₹102.0/L; Car mileage = 15.0 km/L; Bike mileage = 40.0 km/L; EV rate = ₹7.5/kWh ($0.12\text{ kWh/km}$).

---

## Chapter 15: Travel-Time and Traffic Estimation

### 15.1 Time-of-Day Speed Profiles
Bengaluru road speeds vary drastically based on arterial congestion:

$$\text{Speed}_{\text{bus}}(t) = 
\begin{cases}
10.0\text{ km/h} & \text{Peak Hours (07:00–10:00, 17:00–21:00)} \\
20.0\text{ km/h} & \text{Day Hours (10:00–17:00)} \\
35.0\text{ km/h} & \text{Night Hours (21:00–07:00)}
\end{cases}$$

For private vehicles and cabs, free-flow speeds of $35\text{ km/h}$ are reduced by dynamic delay factors:
$$\text{DelayFactor} = \max\left(1.0, \; \frac{T_{\text{actual}}}{T_{\text{free\_flow}}}\right)$$
$$\text{TrafficScore} = \max\left(0.1, \; \min\left(1.0, \; \frac{1.0}{\text{DelayFactor}}\right)\right)$$

---

## Chapter 16: Recommendation and Ranking Algorithms

### 16.1 Multi-Criteria Decision Making (MCDM) Formulation

The recommendation engine in [`backend/recommender.py`](file:///c:/Users/Harsh/Downloads/BMTC_fixed/backend/recommender.py) ranks all available transit alternatives using a normalized composite utility score $U(J_i) \in [0, 100]$:

$$U(J_i) = 100 \times \sum_{k \in \{c, t, \text{comf}, e, w, r\}} w_k \cdot f_k(J_i) \quad \text{subject to} \quad \sum_{k} w_k = 1.0$$

#### Min-Max Metric Normalization
Because cost, time, and emissions have differing physical units, each candidate is scaled relative to the candidate set:

1. **Monetary Cost Score ($f_c \in [0, 1]$):** Lower cost is better:
   $$f_c(J_i) = 1.0 - \frac{C_i - \min(C)}{\max(C) - \min(C)} \quad (\text{or } 1.0 \text{ if } \max(C) = \min(C))$$
2. **Travel Duration Score ($f_t \in [0, 1]$):** Lower time is better:
   $$f_t(J_i) = 1.0 - \frac{T_i - \min(T)}{\max(T) - \min(T)}$$
3. **Carbon Emission Score ($f_e \in [0, 1]$):** Lower CO2 is better:
   $$f_e(J_i) = 1.0 - \frac{E_i - \min(E)}{\max(E) - \min(E)}$$
   - Factors: Metro = $10\text{ g/km}$, Bus = $25\text{ g/km}$, Car = $120\text{ g/km}$, Cab = $150\text{ g/km}$, Bike = $35\text{ g/km}$, Walk = $0\text{ g/km}$.
4. **Comfort Index ($f_{\text{comf}} \in [0.1, 1.0]$):**
   - Baseline: Cab = $1.0$, Car = $0.95$, Vajra Bus = $0.85$, Metro = $0.80$, Ordinary Bus = $0.60$, Multimodal = $0.50$.
   - Transfer penalty: $-0.15 \times \text{transfers}$.
5. **Weather Suitability ($f_w \in [0.1, 1.0]$):**
   $$f_w(J_i) = \max\left(0.1, \; 1.0 - \left(\frac{\text{RainProbability}}{100} \times \text{Exposure} \times 0.85\right)\right)$$
   - Outdoor exposure index: Walking = $1.0$, Bike = $0.95$, Bus = $0.55$, Metro = $0.35$, Cab = $0.10$.
6. **Traffic Delay Score ($f_r \in [0.1, 1.0]$):** Metro = $1.0$ (immune); Road modes scale with congestion.

---

### 16.2 Preference Weight Sets

| Preference Preset | Cost ($w_c$) | Time ($w_t$) | Comfort ($w_{\text{comf}}$) | Eco ($w_e$) | Weather ($w_w$) | Traffic ($w_r$) | Primary Goal |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`cost` / `cheapest`** | **0.55** | 0.15 | 0.05 | 0.05 | 0.10 | 0.10 | Absolute lowest expenditure |
| **`time` / `fastest`** | 0.10 | **0.50** | 0.05 | 0.05 | 0.10 | **0.20** | Rapid arrival bypassing traffic |
| **`convenience`** | 0.10 | 0.15 | **0.45** | 0.05 | 0.15 | 0.10 | Door-to-door comfort, zero transfers |
| **`least_walking`** | 0.15 | 0.20 | **0.40** | 0.05 | 0.10 | 0.10 | Minimizes outdoor pedestrian legs |
| **`fewest_transfers`** | 0.20 | 0.25 | **0.35** | 0.05 | 0.05 | 0.10 | Prefers single-vehicle journeys |
| **`default`** | 0.25 | 0.25 | 0.20 | 0.10 | 0.10 | 0.10 | Balanced compromise |

---

## Chapter 17: AI and Machine Learning

### 17.1 Implementation Audit: What Exists vs. What Is Future Work
To preserve documentation integrity, we explicitly distinguish current capabilities from theoretical ML:
1. **Implemented in Code:**
   - Heuristic and mathematical multi-objective scoring (MCDM).
   - Rule-based NLP parameter and intent extraction (`ChatbotEngine`).
   - Groq Cloud LLM integration running `llama-3.3-70b-versatile`.
   - Tool-grounded system prompting preventing factual drift.
2. **Not Implemented (Future Work):**
   - No trained offline deep learning weights (e.g., PyTorch `.pt` or TensorFlow `.h5` models) are used for routing.
   - Future ML extension: A gradient-boosted regressor (XGBoost/LightGBM) trained on historical ride-hailing logs to predict surge factors dynamically.

---

## Chapter 22: Core Pseudocode Reference

### 22.1 Complete Interview-Ready Pseudocode

#### 1. Complete Application Orchestrator (`/api/compare`)
```python
function compare_journeys(source_str, destination_str, time_str, preference):
    # 1. Resolve canonical stop names and coordinates
    src_stop = resolve_stop_name(source_str)
    dst_stop = resolve_stop_name(destination_str)
    src_lat, src_lng = get_coordinates(src_stop)
    dst_lat, dst_lng = get_coordinates(dst_stop)

    # 2. Parallel candidate gathering
    parallel:
        bmtc_result = bmtc_router.find_routes(src_stop, dst_stop, time_str)
        metro_result = metro_planner.plan(src_stop, dst_stop)
        cab_result = cab_engine.estimate(src_lat, src_lng, dst_lat, dst_lng)
        veh_result = vehicle_engine.estimate(src_lat, src_lng, dst_lat, dst_lng)
        multi_result = multimodal_router.plan(src_stop, dst_stop)

    candidates = filter_available([bmtc_result, metro_result, cab_result, veh_result, multi_result])

    # 3. Context ingestion
    weather_data = weather_api.get_forecast_at_eta(dst_lat, dst_lng, time_str)

    # 4. Score and Rank
    weights = get_weights_for_preference(preference)
    ranked_options = recommender.evaluate_utility(candidates, weights, weather_data)

    # 5. Explain
    explanations = xai_engine.generate_justifications(ranked_options, weather_data, preference)

    return Response(ranked_options, explanations)
```

---

### 22.2 Two-Minute Whiteboard Shortcut Pseudocode
*(Memorize this for technical whiteboard interviews)*

```
// WHITEBOARD ROUTING PSEUDOCODE (2 MINUTES)
function plan_commute(src, dst, pref):
    // 1. Graph Search: Nodes = (cluster_key, route_no)
    dijkstra_pq.push(0, src_nodes)
    while pq not empty:
        w, transfers, (u, route) = pq.pop()
        if u == dst: break
        for (v, r) in graph[u]:
            edge_w = haversine(u, v) / ln(1 + trips[r])
            if r != route: edge_w += 2.0; transfers += 1
            if transfers <= 2: pq.push(w + edge_w, transfers, (v, r))

    // 2. Multi-Objective Ranking
    for candidate in [Bus, Metro, Cab, Car]:
        f_cost = 1.0 - (cost - min_c) / (max_c - min_c)
        f_time = 1.0 - (time - min_t) / (max_t - min_t)
        score = 100 * (w.cost * f_cost + w.time * f_time + w.comf * candidate.comfort)
    
    return sort_descending_by_score()
```

---
*(End of Part III — Proceed to [Part IV: Implementation and File Guide](file:///c:/Users/Harsh/Downloads/BMTC_fixed/docs/technical_book/04_IMPLEMENTATION_FILE_GUIDE.md))*
