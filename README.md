# Bangalore Unified Journey Planner (UTRS)

A unified transit planning system combining BMTC (buses), Bangalore Metro (trains), ride-hailing services (Ola/Uber/Rapido/Namma Yatri), and personal vehicles into a single recommendation engine for Bengaluru.

## Architecture & Core Tech Stack
- **Backend**: FastAPI (Python 3.13) serving all transit calculations under `bmtc_planner/unified_api.py`.
- **BMTC Dijkstra Engine**: Location-aware frequency-weighted graph (`core/graph.py`) with per-level transfer options.
- **Namma Metro Engine**: Green, Purple, and Yellow line journey planner.
- **Cab Engine**: Calibrated OSRM/Haversine heuristic fares matching Namma Yatri, Uber, Ola, and Rapido.
- **Personal Vehicles**: Arai mileage lookup and fuel cost estimation matching 500+ Indian car and bike models.
- **UI Options**:
  - Unified Streamlit app (`ui/multimodal_app.py`).
  - React/Vite web application calling the FastAPI backend.

---

## Project Structure
```
/BMTC_fixed/
├── bmtc_planner/              # Main project root — run everything from here
│   ├── unified_api.py         # Unified FastAPI backend (Port 8000)
│   ├── core/                  # Graph engine, GTFS schedule, CSV loader, config
│   ├── features/              # Routing optimization, fare engine, segment times
│   ├── tools/                 # Stop normalization and clustering pipelines
│   ├── tests/                 # Unit test suite
│   ├── sandbox/               # Scratch/debug scripts (test_buses, direct_test, etc.)
│   └── data/                  # Raw GTFS flat-files and processed CSVs
│
├── bmrcl_final/               # Namma Metro planner dependency
├── namma-yatri-v4/            # Namma Yatri fare engines reference
├── Personal vehicles/         # Fuel and mileage datasets (India master datasets)
│
├── shared/                    # Unified interfaces & utility modules
├── adapters/                  # BMTC & Metro adapters bridging to unified contracts
├── multimodal/                # Cross-modal router (BMTC-Metro-BMTC connections)
│
├── ui/                        # Multipage Streamlit UI
│   ├── multimodal_app.py      # Streamlit home & mode selector
│   └── pages/                 # BMTC, Metro, and Multimodal subpages
│
├── test_integration.py       # Integration verification suite
└── requirements.txt           # Unified Python package requirements
```

---

## Installation & Setup

1. **Clone the repository and install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Local Configuration**:
   Create a `.env` file inside `bmtc_planner/` if you have a Google Maps API Key:
   ```bash
   # bmtc_planner/.env
   GOOGLE_MAPS_API_KEY=your_key_here
   ```

---

## Running the Servers

### 1. Unified FastAPI Backend
From the `bmtc_planner/` directory:
```bash
cd bmtc_planner
uvicorn unified_api:app --reload --port 8000
```
This launches the REST API server at `http://localhost:8000`. You can visit the interactive docs at `http://localhost:8000/docs`.

### 2. Streamlit UI
From the workspace root:
```bash
streamlit run ui/multimodal_app.py
```
This opens the frontend dashboard at `http://localhost:8501`.

---

## Running the Test Suite

### 1. Unit Tests
All unit tests are isolated within `bmtc_planner/tests/`. To run them (uses `pytest.ini` configuration):
```bash
cd bmtc_planner
pytest
```
*Expected: 44 tests passing.*

### 2. Integration Tests
To run the end-to-end integration structure validation:
```bash
# Run from project root
python test_integration.py
```
*Expected: All layers (Shared, Adapters, Multimodal, UI, Dependencies) PASS.*

---

## Critical Design Policies
1. **FAST_QUERY_MODE must be `False`** in `bmtc_planner/core/config.py` for correct ordinary bus suggestion generation.
2. **Graph Nodes are `(cluster_key, route_no)`** to support name disambiguation for locations with identical names.
3. **Weight Formula** contains a log trip cap:
   `weight = (distance_km * type_factor) / min(log1p(trips), log1p(30))`
4. **Dijkstra Multi-option routing** stores scores using a composite key `(node, transfer_count)` to allow alternative transfers.
5. **Segment Times** are parsed from direct arrival/departures to avoid double-counting waiting buffers.
