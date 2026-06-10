# BMTC Smart Planner

Bengaluru bus route planner with Dijkstra-based routing, GTFS schedule data,
time-of-day speed modelling, official fare slabs, and toll surcharges.

## Project structure

```
bmtc_planner/
├── data/
│   ├── raw/          ← GTFS flat-files (stops.txt, trips.txt, routes.txt, stop_times.txt)
│   └── processed/    ← Cleaned CSVs (bmtc_stop_level_cleaned.csv, reverse_routes_supplement.csv)
├── core/             ← Shared infrastructure — loader, graph, GTFS index, config
├── features/         ← Business logic — routing, fare, schedule, journey planning
├── ui/               ← Streamlit app — components, map, styles, session state
├── tools/            ← CLI maintenance scripts (audit, verify, merge)
├── tests/            ← pytest test suite
├── main.py           ← Entry point: streamlit run main.py
└── requirements.txt
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Place GTFS files (`stops.txt`, `trips.txt`, `routes.txt`, `stop_times.txt`) in `data/raw/`
and cleaned CSVs in `data/processed/` before running.

## Run the app

```bash
streamlit run main.py
```

## Run tests

```bash
pytest tests/ -v
pytest tests/ --cov=core --cov=features --cov-report=term-missing
```

## Maintenance CLI tools

```bash
# Audit current dataset against GTFS
python -m tools.route_audit

# Find routes serving a specific stop
python -m tools.route_finder "Shivajinagar" --top 10

# Validate data quality
python -m tools.verify_data
python -m tools.validator --route 500C

# Download and merge missing GTFS routes
python -m tools.merger
```

## Architecture

Data flows in one direction — `data/ → core/ → features/ → ui/`.
The `tools/` and `tests/` packages depend on `core/` and `features/`
but are never imported by the running app.

| Layer | Responsibility |
|---|---|
| `core/config.py` | All constants — paths, speeds, fares, colours |
| `core/loader.py` | Load stops CSV, normalise stop names, canonical map |
| `core/graph.py` | Haversine, frequency-weighted graph, Dijkstra |
| `core/gtfs.py` | GTFS lazy loader, GTFS-backed bus suggestions |
| `core/stops.py` | Route stop lists, fuzzy route search |
| `features/fare.py` | BMTC fare slabs + toll surcharges |
| `features/schedule.py` | Time-of-day speed, per-segment timing |
| `features/routing.py` | Direct buses, comprehensive search, guide generator |
| `features/journey.py` | Public API: plan_journey_ui, plan_journey_with_time_preference |
| `ui/styles.py` | CSS injection, topbar, section labels |
| `ui/state.py` | st.session_state key management |
| `ui/components.py` | Stop lists, segment cards, summary metrics, bus cards |
| `ui/map_view.py` | Folium map builder and renderer |
| `ui/app.py` | Page layout, wires all ui/ modules together |

