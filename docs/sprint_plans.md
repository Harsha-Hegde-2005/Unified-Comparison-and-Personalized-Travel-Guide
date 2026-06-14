# UTRS Detailed Weekly Sprint Plans (June 14 – July 31, 2026)

This document establishes the detailed weekly development sprint plans for the Bangalore Unified Journey Planner (UTRS). All sprints are designed to achieve a production-ready system by July 31, 2026.

---

## 🗓️ Weekly Schedule Overview

```mermaid
gantt
    title UTRS Sprint Schedule (June 14 - July 31, 2026)
    dateFormat  YYYY-MM-DD
    section Sprints
    Sprint 1: Cabs Calibration & GMaps API  :active, s1, 2026-06-15, 2026-06-21
    Sprint 2: Multimodal Router & Walk      :s2, 2026-06-22, 2026-06-28
    Sprint 3: Conversational Chatbot Widget :s3, 2026-06-29, 2026-07-05
    Sprint 4: Weather & Explainable AI (XAI):s4, 2026-07-06, 2026-07-12
    Sprint 5: System E2E Integration        :s5, 2026-07-13, 2026-07-19
    Sprint 6: Validation & Unit Testing     :s6, 2026-07-20, 2026-07-26
    Sprint 7: UX Polish & Remote Delivery   :s7, 2026-07-27, 2026-07-31
```

---

## 🔍 In-Depth Current Engine Analysis

To guide future sprints, here is the verified approach of the three currently implemented engines:

### 1. BMTC (Bus Dijkstra Engine)
* **Approach**: Builds a location-aware frequency-weighted graph (`backend/modes/bmtc/core/graph.py`) from GTFS data where nodes represent `(stop_cluster_key, route_no)` to prevent name-collision errors at massive bus junctions (e.g. Majestic, Silk Board).
* **Weights**: Calculated using travel distance scaled by route trip frequencies to prioritize highly active corridors:
  $$\text{Weight} = \frac{\text{Distance\_km} \times \text{TypeFactor}}{\min(\ln(1 + \text{trips}), \ln(1 + 30))}$$
* **Fares**: Slab-based lookups separating ordinary and Vajra (AC) services to prevent incorrect pricing suggestions.

### 2. Bangalore Metro (BMRCL Journey Planner)
* **Approach**: Evaluates optimal connections using a Breadth-First Search (BFS) routing algorithm to minimize line changes (interchanges).
* **Distance & Time**: Uses station sequence tracking combined with a Metro Distance Engine to determine stations crossed.
* **Fares**: Looks up costs from `database/metro/fare_matrix.csv`. Smart card discounts (10% standard, 5% peak hours) are dynamically computed.

### 3. Personal Vehicles (Car & Bike Calculator)
* **Approach**: Query-driven calculations mapped to a master dataset of 500+ Indian vehicle models (`database/personal_vehicle/`).
* **Cost Estimations**: Integrates OSRM/Google Maps road distances with fuel type prices (petrol, diesel, CNG) and ARAI-rated fuel efficiencies:
  $$\text{Fuel Cost} = \frac{\text{Road Distance (km)}}{\text{ARAI Mileage (km/l)}} \times \text{Fuel Price (₹/l)} + \text{Parking Fee}$$

---

## 📝 Week-by-Week Sprint Plans

### 🗓️ Week 1: Cab Fare Engine Calibration & Google Maps API Integration
* **Objective**: Build a highly accurate cab estimation module (Ola, Uber, Rapido, Namma Yatri) that simulates real-world fare outcomes with $\ge 90\%$ accuracy without relying on official API keys.
* **Tasks**:
  * **Google Maps API Integration**: Use Google Distance Matrix API as the primary routing layer to fetch accurate road distances and duration matrices. If a developer key is absent, fallback to public OSRM (`/route/v1/driving`) or coordinate-curved Haversine equations ($D \times 1.3$).
  * **Fare Modeling**: Establish mathematical formulas modeling base charges, distance fees, time fees, and surge factors:
    $$\text{Cab Fare} = \max\left(\text{BaseFare} + D \times \text{PerKmRate} + T \times \text{PerMinuteRate}, \text{MinFare}\right) \times S_{surge}$$
    * **Ola/Uber**: Multi-tier options (Auto, Sedan, SUV) with dynamic surge $S_{surge}$ applied during peak traffic hours (08:30–10:30, 17:30–20:30) with factors between $1.25\times$ and $1.5\times$.
    * **Rapido**: Optimized single-passenger bike taxi rates and auto rates.
    * **Namma Yatri**: Config-driven flat models matching official driver-direct guidelines with night surcharge multipliers.
  * **Calibration & Accuracy Pipeline**:
    * Implement a verification script (`testing/calibrate_cabs.py`) that generates random coordinate pairs within Bangalore's bounding box (Lat: `12.85` to `13.08`, Lng: `77.45` to `77.75`).
    * Fetch actual distances, compute simulated fares, compare them against corresponding logged official app results, and run optimization regressions to keep Mean Absolute Percentage Error (MAPE) below 10%.
  * **Deliverables**: Validated `/api/cab/estimate` endpoint, calibration script, and tested pricing configurations in `database/cab/`.

---

### 🗓️ Week 2: Multimodal Router & Walk Integration
* **Objective**: Link BMTC buses, Metro lines, Cabs, and walking legs into a single multimodal routing graph.
* **Tasks**:
  * **Interchange Graph**: Construct an interchange router (`backend/multimodal/router.py`) that identifies nearby transit stations (within a $500\text{m}$ walking radius) using `InterchangeMatcher`.
  * **Multi-Criteria Path Optimization**: Evaluate optimal transit combinations:
    * **Leg 1**: Walk/Cab/Bus to closest Metro entrance.
    * **Leg 2**: Metro transit between entry and exit hubs.
    * **Leg 3**: Walk/Cab/Bus from Metro exit to destination.
  * **Walk & Cost Trade-offs**: Sum individual fares and transit times. Introduce a variable transfer walking penalty (e.g. 5 mins base buffer per mode change) and allow users to select routing preferences (`cost` vs `time` vs `convenience`).
  * **Deliverables**: Tested `/api/compare` endpoint returning unified multimodal options with accurate walking steps, total fares, and transit ETAs.

---

### 🗓️ Week 3: Conversational Commuter Chatbot Widget
* **Objective**: Build a natural language widget capable of answering complex travel, budget, weather, and personal vehicle queries.
* **Tasks**:
  * **NLP Intent Classification**: Build a regex/keyword intent classifier in the backend (`/api/chatbot`) mapping text prompts to routing parameters.
  * **Query Support Capabilities**:
    * *Routing Request*: *"Take me from Majestic to Silk Board"* $\rightarrow$ Call `plan_multimodal`.
    * *Budget Constraints*: *"I only have ₹50, how can I go from Majestic to Whitefield?"* $\rightarrow$ Filter compare results for `cost <= 50`, returning ordinary BMTC bus options.
    * *Weather Questions*: *"Is it going to rain today at 4 pm?"* $\rightarrow$ Retrieve forecasts and warn about delays.
    * *Personal Vehicle Comparison*: *"Shall I take my bike to Indiranagar?"* $\rightarrow$ Compare personal vehicle driving cost & ETA against bus/metro options.
  * **Frontend**: Build a floating chat bubble React widget in the bottom-right corner with autocomplete suggestion chips.
  * **Deliverables**: Interactive conversational chatbot widget fully integrated with the travel planners.

---

### 🗓️ Week 4: Explainable AI (XAI) & Weather-Aware Routing
* **Objective**: Scale routing parameters dynamically by weather state and explain time-cost tradeoffs to the commuter.
* **Tasks**:
  * **Weather-Aware Speeds**: Adjust travel speeds and walk times based on simulated weather metrics:
    * **Clear/Cloudy**: $1.0\times$ speed, $3\text{m}$ walk transfer.
    * **Light Rain**: $0.85\times$ speed, $6\text{m}$ walk transfer.
    * **Heavy Rain / Storm**: $0.65\times$ speed, $12\text{m}$ walk transfer (plus $1.5\times$ cab surge multiplier and a penalty on walk legs $>300\text{m}$ to discourage transfer walks).
  * **Explainable AI (XAI)**: Compute cost-per-hour saved when recommending a faster but more expensive route:
    $$\text{Cost-per-hour saved} = \frac{\text{Cost}_{Metro} - \text{Cost}_{Bus}}{\text{Time}_{Bus} - \text{Time}_{Metro}} \times 60$$
    * Generate dynamic textual explanations: *"We recommend taking the Metro because it saves you 35 mins of Outer Ring Road traffic for only ₹18 extra compared to the bus."*
  * **Deliverables**: Weather-scaled route suggestions, XAI description blocks rendered in React UI cards.

---

### 🗓️ Week 5: End-to-End System Integration
* **Objective**: Unify the Vite/React UI, chatbot, weather alerts, and explanation banners into a single cohesive production release.
* **Tasks**:
  * Bind the frontend map visualizations with chatbot route selections.
  * Cache database queries to minimize API latency on complex transit calculations.
  * Implement error boundaries and fallbacks for missing Google Maps keys or API downtimes.
  * **Deliverables**: Completed feature integration, code-freeze, and readiness for automated testing.

---

### 🗓️ Week 6: Validation & Automated Testing
* **Objective**: Write comprehensive automated unit and integration tests to ensure UTRS stability.
* **Tasks**:
  * Write unit tests under `testing/` covering:
    * Chatbot NLP intent classification matching accuracy.
    * Cab fare calibration regression test cases (validating MAPE $\le 10\%$).
    * Multimodal path cost calculations.
  * Run automated load tests on the backend FastAPI server to ensure stable performance.
  * **Deliverables**: 100% test coverage for all transit algorithms, and zero critical defects.

---

### 🗓️ Week 7: UX Polish, Performance Audits, & Hand-off
* **Objective**: Optimize loading speeds, review visual guidelines, and package files for delivery.
* **Tasks**:
  * Perform user experience validation (smooth animations, map responsiveness, chatbot card render).
  * Compile build assets for React production hosting (`npm run build`).
  * Finalize all documentation, write release tags, and push final commits to the origin remote.
  * **Deliverables**: Production-ready, fully verified Bangalore Unified Journey Planner repository.
