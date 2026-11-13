# Phase 1: Comprehensive Repository Audit

## Executive Summary
This document provides an exhaustive, empirical repository audit of the **Bangalore Unified Journey Planner / Unified Transit Recommendation System (UTRS)**. Every claim in this audit is grounded directly in the inspected source code across `backend/`, `database/`, `frontend/`, `mobile_app/`, `testing/`, and `docs/`.

---

## 1. Implemented Features & Technical Architecture

### 1.1 Core Backend & Services (`backend/`)
- **Framework & Entry Point**: FastAPI (`backend/main.py`, 5,747 lines) exposing RESTful HTTP endpoints for transit planning, fare estimation, mode comparison, and conversational travel assistance.
- **Data Stores & Persistence**:
  - SQLite database (`unified_transit.db` via SQLAlchemy in `backend/db.py`) storing user sessions, search history, saved routes, and user feedback.
  - Static JSON/CSV files in `database/` storing GTFS bus schedule feeds, Metro station coordinates, slab fare definitions, cab pricing parameters, and personal vehicle fuel specifications.
- **Mode-Specific Planning Engines**:
  1. **BMTC Bus Engine** (`backend/modes/bmtc/`):
     - Priority-Queue Dijkstra Pathfinding (`core/graph.py`): Graph built from GTFS `stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`.
     - Route & Schedule Calculations (`features/routing.py`, `features/schedule.py`): Supports direct bus lookup, transfer routes (up to 1-transfer), timetable matching, and AC Vajra vs. Ordinary fare calculations (`features/fare.py`).
  2. **Namma Metro Engine** (`backend/modes/metro/`):
     - Breadth-First Search (BFS) / Shortest Station Hop routing (`engines/routing_engine.py`).
     - Distance and Fare Calculation (`engines/fare_engine.py`): Uses official station-to-station distance metrics and slab-fare CSV matrices.
  3. **Ride-Hailing / Cab Engine** (`backend/modes/cab/`):
     - Multi-Provider Fare Estimator (`engines/fare_engine.py`): Models fare structures for Ola, Uber, Rapido, and Namma Yatri across Auto, Prime/Mini Hatchbacks, and Sedan categories.
     - Distance & Duration (`engines/distance_engine.py`, `engines/time_engine.py`): Calls Google Maps Distance Matrix / OSRM APIs with a Haversine distance fallback.
  4. **Personal Vehicle Engine** (`backend/main.py`):
     - Fuel-cost estimator considering vehicle fuel type (Petrol, Diesel, CNG, EV), manufacturer mileage data (`database/personal_vehicle/`), and distance.
  5. **Multimodal Engine** (`backend/multimodal/`):
     - Cross-mode route generator (`router.py`, `interchange_matcher.py`): Connects walking legs from origin to BMTC bus stops/Metro stations, identifies interchange hubs (e.g., Silk Board, Majestic, Hebbal) within a walking threshold ($R_{\text{walk\_max}} = 500\text{m}$), and chains bus/metro legs.
- **Context & Weather Integration** (`backend/weather_helper.py`):
  - Queries live weather from Open-Meteo API (or fallback configuration).
  - Calculates outdoor exposure levels (0.0 to 1.0) and penalizes modes with high outdoor exposure during rain (e.g., walking, open bus stops) while favoring sheltered modes (Namma Metro).
  - Modifies travel speed factors ($C_{\text{speed}}$) for surface vehicles (Buses and Cabs).
- **Recommendation & XAI Ranking** (`backend/recommender.py`):
  - Monolithic scoring function `get_recommendations()` applying normalized multi-criteria weighting:
    $$\text{Score}(J_i) = w_c \cdot S_{\text{cost}} + w_t \cdot S_{\text{time}} + w_{\text{comfort}} \cdot S_{\text{comfort}} + w_{\text{eco}} \cdot S_{\text{eco}} + w_{\text{weather}} \cdot S_{\text{weather}} + w_{\text{traffic}} \cdot S_{\text{traffic}}$$
  - Computes trade-off explanations via heuristic rule matching (`generate_fallback_explanations`) or Google Gemini 1.5 Flash API calls when `GEMINI_API_KEY` is present.

---

## 2. Quantitative Dataset Inventory

| Dataset Component | Location | Source / Type | Description & Volume |
| :--- | :--- | :--- | :--- |
| **BMTC GTFS Feed** | `database/bmtc/` | GTFS TXT / CSV | Contains `stops.txt` (~2,500 stops), `routes.txt`, `trips.txt`, `stop_times.txt`, `fare_attributes.txt`. |
| **Metro Master Data** | `database/metro/` | JSON & CSV | Metro station coordinates (`metro_coords.json`), line maps (Purple, Green lines), and official distance/fare slab lookup table (`metro_fares.csv`). |
| **Cab Fare Configs** | `database/cab/` | JSON | Base fares, per-km rates, per-minute charges, night surcharges, and surge factors for Ola, Uber, Rapido, Namma Yatri (`fare_config.json`). |
| **Personal Vehicle DB** | `database/personal_vehicle/` | CSV | Vehicle catalog mapping models to fuel efficiency (km/L or kWh/km) for 150+ Indian car/bike models (`vehicle_mileage.csv`). |

---

## 3. Evaluation of Agentic & Multi-Agent Capabilities

### 3.1 Scientific Integrity Finding
> **CRITICAL FINDING**: The existing repository **DOES NOT** implement a genuine Multi-Agent System (MAS).

### 3.2 Detailed Architectural Analysis
1. **Monolithic Control Flow**: The backend execution is strictly synchronous and centralized inside FastAPI route handlers. A request to `/api/compare` sequentially invokes `get_all_buses_comprehensive()`, `MetroPlanner.plan()`, `CabPlanner.estimate()`, `PersonalVehicle.estimate()`, and finally passes all results into `recommender.get_recommendations()`.
2. **Absence of Autonomous Agent Abstractions**:
   - There are no independent agent event loops or background tasks.
   - There are no message queues, agent-to-agent communication protocols (e.g., FIPA ACL, blackboard systems, contract-net protocols), or decentralized state machines.
   - Individual travel modes are plain Python modules/functions that take parameters and return data structures.
3. **No Independent Decision Policies**:
   - Routing logic computes static shortest paths or heuristic lookups without autonomous goal optimization, negotiation, or environment belief updating.

---

## 4. Minimum Required Technical Architectural Extension

To turn the current monolithic backend into a scientifically defensible **Coordinated Multi-Agent Journey Recommendation System** suitable for ADCOM 2027 Track 3 ("Multi-Agent Systems and Decentralized Intelligence"), we must construct a lightweight, high-performance **Multi-Agent Framework** (`research/mas/`).

### 4.1 Proposed Multi-Agent Architecture
The system will be restructured into 8 discrete, autonomous agents defined formally by the tuple:
$$A_i = (O_i, S_i, G_i, A_i, \pi_i)$$
where $O_i$ represents environmental observations, $S_i$ is internal state/context, $G_i$ is explicit objective goals, $A_i$ is the set of executable actions, and $\pi_i$ is the decision policy mapping observations and internal state to candidate actions.

1. **User Preference Agent ($A_{\text{user}}$)**: Ingests user constraints, time/cost trade-off willingness, eco-sensitivity, and updates personal weighting vectors dynamically.
2. **Public Transit Agent ($A_{\text{bmtc}}$)**: Manages BMTC bus graph queries, schedule matching, and AC vs. Ordinary bus trade-offs.
3. **Metro Agent ($A_{\text{metro}}$)**: Manages Namma Metro graph hops, station accessibility, and congestion-free rapid transit alternatives.
4. **Cab Mobility Agent ($A_{\text{cab}}$)**: Solves ride-hailing pricing models, surge estimation, and door-to-door direct routing.
5. **Personal Vehicle Agent ($A_{\text{veh}}$)**: Computes driving routes, fuel consumption, parking overheads, and vehicle operational costs.
6. **Context Agent ($A_{\text{ctx}}$)**: Observes live traffic congestion (OSRM/Google Maps) and weather forecasts (Open-Meteo), computing outdoor exposure & environmental penalties.
7. **Coordinator / Recommendation Agent ($A_{\text{coord}}$)**: Executes a multi-agent contract-net / consensus negotiation protocol, normalizes candidate proposals, and computes Pareto-optimal multi-objective rankings.
8. **Explainability Agent ($A_{\text{xai}}$)**: Analyzes dominant preference drivers and environmental factors to produce structured, mathematical XAI justifications.

---

## 5. Summary of Implemented vs. Proposed Artifacts

- **IMPLEMENTED (Existing Repo)**:
  - BMTC GTFS Dijkstra & timetable algorithms.
  - Namma Metro station graph BFS & slab fare model.
  - Multi-provider cab fare & OSRM/Google Maps distance calculators.
  - Personal vehicle fuel cost calculator.
  - Multimodal transfer matcher & walking link timing.
  - Live weather integration & outdoor exposure heuristic.
  - FastAPI endpoints & React/Vite/Flutter frontend clients.
- **PROPOSED & TO BE IMPLEMENTED FOR EXPERIMENTS (Research Extension)**:
  - Formal Multi-Agent System (MAS) architecture framework (`research/mas/`).
  - Asynchronous agent coordination contract & message broker.
  - Decentralized candidate generation & agent policy evaluation $\pi_i$.
  - Empirical benchmarking scripts (`research/scripts/`) to measure latency, throughput, memory, Pareto ranking accuracy, and ablation impact.
