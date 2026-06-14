# Bangalore Unified Journey Planner (UTRS)

A unified transit planning system combining **BMTC** (buses), **Namma Metro** (trains), **Ride-Hailing services** (Ola, Uber, Rapido, and Namma Yatri), and **Personal Vehicles** into a single multi-criteria journey optimizer for Bengaluru.

---

## 📂 Repository Structure

The project has been restructured into four clean, descriptive top-level folders:

```
/Unified-fare-comparison-framework-and-personalized-travel-guide/
├── frontend/                     # Vite + React UI Application
│   ├── src/                      # Source code (App.jsx, main.jsx, css, etc.)
│   └── package.json              # Frontend scripts and dependencies
│
├── backend/                      # FastAPI Python Web Backend
│   ├── main.py                   # Central FastAPI entry point (Port 8000)
│   ├── shared/                   # Common transit interfaces & time/distance utilities
│   ├── adapters/                 # Adapters bridging transit engines to unified contracts
│   ├── multimodal/               # Cross-mode optimizer combining BMTC + Metro + Walks
│   └── modes/                    # Individual travel planner engines
│       ├── bmtc/                 # BMTC Dijkstra graph builder and scheduling Features
│       ├── metro/                # Namma Metro BFS routing and slab fare estimators
│       └── cab/                  # Ride-hailing fare models and calibrations
│
├── database/                     # Centralized Datasets Hub
│   ├── bmtc/                     # Raw GTFS files & processed routes/stops CSVs
│   ├── metro/                    # Metro station master JSON and slab-fare CSV
│   ├── cab/                      # Namma Yatri and commercial cab fare configurations
│   └── personal_vehicle/         # Master mileage & vehicle dataset CSV files
│
├── testing/                      # Centralized Quality Assurance Suites
│   ├── conftest.py               # Shared pytest fixtures (in-memory mock data)
│   ├── test_integration.py       # Integration structural assertions
│   └── test_*.py                 # Unit tests (routing, stops, fare, schedules, API)
│
├── docs/                         # Specifications, Sprint Plans, and Roadmaps
├── pytest.ini                    # Pytest settings and import paths configuration
└── requirements.txt              # Backend python package dependencies list
```

---

## 🚀 How to Run the Project

### 1. Prerequisite Dependencies
Ensure Python (3.11+) and Node.js (18+) are installed on your machine.
Clone the repository and install the backend libraries:
```bash
pip install -r requirements.txt
```

### 2. Configure Google Maps API (Optional but Recommended)
For high-accuracy road routing and vehicle lookups, create a `.env` file at the workspace root:
```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```
*Note: If no key is set, the system seamlessly falls back to the public Open Source Routing Machine (OSRM) API for cabs, and Haversine distance heuristics for vehicles.*

### 3. Run the Backend REST API
Launch the FastAPI development server:
```bash
uvicorn backend.main:app --reload --port 8000
```
* The API will run at: `http://localhost:8000`
* Interactive API Documentation (Swagger UI) is available at: `http://localhost:8000/docs`

### 4. Run the React Frontend
Navigate to the frontend directory and start the Vite dev server:
```bash
cd frontend
npm install
npm run dev
```
* The UI dashboard will launch at: `http://localhost:5173`

---

## 🧪 Running Tests

### 1. Pytest Unit Tests
Run the entire unit testing suite covering routing logic, schedules, and fare formulas:
```bash
pytest
```

### 2. Integration Pipeline Verification
Run the integration check to confirm directory layouts, shared import interfaces, and library availability:
```bash
python testing/test_integration.py
```

---

## 🛠️ Developer Workflow Guidelines

To maintain code quality and prevent module resolution or database load failures, adhere to these practices:

### 1. Directory Responsibility
* **Raw/Processed Data**: Store all CSV, JSON, or text datasets inside `database/<mode_name>/`.
* **Algorithmic Logic**: Encapsulate all algorithms under `backend/modes/<mode_name>/`.
* **UI Features**: Write all React pages and styles inside `frontend/src/`.
* **Testing Cases**: Add unit tests checking specific modes directly inside `testing/` prefixing filenames with `test_`.

### 2. Resolving Files Safely (No Hardcoded Paths)
Do **not** use absolute file system paths. Always construct paths relative to the current file using `os.path.dirname`:
```python
import os
# Find workspace database root from a module
_HERE = os.path.dirname(os.path.abspath(__file__))
# Example: traversing up to workspace and into database
DATABASE_DIR = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "database"))
```

### 3. Importing Code Cleanly
* To keep mode packages modular and portable, use relative imports inside a sub-package (e.g. `from .engines import routing_engine` inside a planner).
* When importing cross-module utilities, use backend-relative imports (e.g. `from backend.shared.utils.distance import haversine_distance`).
* Avoid using global namespace imports that override system packages. Keep `sys.path` modifications isolated to main scripts or test entry points (`testing/conftest.py`).

### 4. Git Alignment & Branching
* Keep the `main` branch stable. Develop new modes and features in isolated `feature/<feature_name>` branches.
* Before pushing a branch, make sure `pytest` passes with **100% success** and run `python testing/test_integration.py` to ensure other developers can clone your work seamlessly.
