# UTRS Weekly Sprint Plans (June 14 – July 31, 2026)

This document establishes the 7-week development schedule to bring the Bangalore Unified Journey Planner (UTRS) to a complete, production-ready release by the end of July.

```mermaid
gantt
    title UTRS Weekly Sprint Schedule (June 14 - July 31, 2026)
    dateFormat  YYYY-MM-DD
    section Core Features
    Sprint 1: Cabs & Weather Core      :active, s1, 2026-06-15, 2026-06-21
    Sprint 2: Commuter Chatbot         :s2, 2026-06-22, 2026-06-28
    Sprint 3: Explainable AI Engine    :s3, 2026-06-29, 2026-07-05
    Sprint 4: Weather-Aware Routing    :s4, 2026-07-06, 2026-07-12
    Sprint 5: System Integration       :s5, 2026-07-13, 2026-07-19
    section Quality & Release
    Sprint 6: Validation & Unit Tests  :s6, 2026-07-20, 2026-07-26
    Sprint 7: UX Polish & Hand-off     :s7, 2026-07-27, 2026-07-31
```

---

## Weekly Roadmap Details

### 🗓️ Week 1: Cab Integrations Deep-Dive & Weather Engine Foundation
**Dates**: June 15 – June 21, 2026  
* **Objective**: Enhance cab routing precision and establish the baseline weather data service.
* **Tasks**:
  * **Backend**:
    * Implement OSRM (Open Source Routing Machine) or Google Maps API fallback for exact road distance/duration calculation on ride-hailing queries instead of straight-line coordinates.
    * Implement a mockable weather client under `shared/utils/weather.py` that retrieves current conditions using OpenWeatherMap or local simulated data.
  * **Frontend (React)**:
    * Create a unified Cab Estimates side panel to display Ola, Uber, Rapido, and Namma Yatri side-by-side with vehicle options (Auto, Bike, Cab, Prime).
  * **Deliverable**: Tested `/api/cab/estimate` using real distance routing and a working `/api/weather` state service.

### 🗓️ Week 2: Conversational Commuter Chatbot
**Dates**: June 22 – June 28, 2026  
* **Objective**: Introduce a natural language interface for route querying.
* **Tasks**:
  * **Backend**:
    * Create a new FastAPI route `/api/chatbot` in `unified_api.py`.
    * Build a rule-based + basic NLP parsing intent-recognizer that maps commuter commands (e.g. *"how to go from Majestic to Hosa Road cheaper?"* or *"suggest a bus route to Indiranagar"*) to parameters for `bmtc_plan` and `metro_plan`.
  * **Frontend (React)**:
    * Embed an interactive chatbot widget (floating bubble overlay) in the lower-right corner of the web interface.
  * **Deliverable**: Users can search and select routes purely through text conversations.

### 🗓️ Week 3: Explainable AI (XAI) Recommendation Engine
**Dates**: June 29 – July 5, 2026  
* **Objective**: Explain the "why" behind recommended transit modes.
* **Tasks**:
  * **Backend**:
    * Build an explanation module (`features/explainable_ai.py`) that analyzes route choices.
    * Compute heuristic comparison weights (e.g. time difference vs cost savings vs transfer fatigue).
    * Generate readable text trade-offs (e.g. *"We recommend Option 1 (Metro) because it saves 30 minutes of peak-hour traffic at Central Silk Board, despite costing ₹20 more than Option 2 (Bus)"*).
  * **Frontend (React)**:
    * Display recommendation explanations prominently at the top of route choice cards.
  * **Deliverable**: Transparent recommender system explaining decisions to commuters.

### 🗓️ Week 4: Weather-Aware Multimodal Routing
**Dates**: July 6 – July 12, 2026  
* **Objective**: Interlink weather status with transit timings, delays, and suggestions.
* **Tasks**:
  * **Backend**:
    * Map weather states (Clear, Rain, Heavy Storm, Flooding) to transit impact coefficients.
    * If severe rain is active, increase transfer walk times at interchanges (e.g., Majestic, Silk Board) by a factor of 2.5×.
    * Set bus travel speeds to decrease by 30% to simulate traffic congestion.
    * Dynamically rank Metro higher than surface bus/cab options during storms.
  * **Frontend (React)**:
    * Render alerts and warnings on the travel itinerary when weather delays are active.
  * **Deliverable**: Live weather-affected ETAs and weather-safe route suggestions.

### 🗓️ Week 5: System Integration & End-to-End Flow Checks
**Dates**: July 13 – July 19, 2026  
* **Objective**: Complete end-to-end integration and prepare for validation.
* **Tasks**:
  * Connect the React UI, Chatbot, Weather Alerts, and XAI recommendation banners into a single production bundle.
  * Optimize backend pandas loading (cache dataset queries).
  * Handle edge cases (e.g., outside operational hours, missing keys, API failures).
  * **Deliverable**: Feature freeze. Code is locked for validation.

### 🗓️ Week 6: Validation & Testing Phase - Stage 1 (Unit & Integration tests)
**Dates**: July 20 – July 26, 2026  
* **Objective**: Assert code reliability and test coverage.
* **Tasks**:
  * Write extensive unit tests in `bmtc_planner/tests` for:
    * Chatbot intent parsing accuracy.
    * Weather coefficient scaling.
    * XAI explanation formatting.
  * Build integration tests checking API responsiveness under heavy simulated loads.
  * **Deliverable**: All test suites are complete; zero blocker bugs remaining.

### 🗓️ Week 7: Validation & Testing Phase - Stage 2 (UX, Load tests, & Hand-off)
**Dates**: July 27 – July 31, 2026  
* **Objective**: Final audits, performance tuning, and delivery.
* **Tasks**:
  * Perform manual user experience validation.
  * Run load tests on the unified FastAPI server.
  * Package all installation requirements and deploy documentation.
  * Make final git tag and release branch hand-off.
  * **Deliverable**: Production-ready, fully verified UTRS repository.
