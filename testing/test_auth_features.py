import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, get_db
from main import app

# Setup test SQLite database
TEST_DATABASE_URL = "sqlite:///./test_unified_transit.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup tables and database file
    Base.metadata.drop_all(bind=engine)
    try:
        if os.path.exists("./test_unified_transit.db"):
            os.remove("./test_unified_transit.db")
    except Exception as e:
        print(f"Error deleting test db file: {e}")

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_user_signup_and_login():
    # 1. Test User Signup
    resp = client.post("/api/auth/signup", json={"username": "testuser", "password": "password123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["username"] == "testuser"

    # Test Duplicate Signup
    resp2 = client.post("/api/auth/signup", json={"username": "testuser", "password": "different_password"})
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Username already exists"

    # 2. Test User Login
    resp_login = client.post("/api/auth/login", json={"username": "testuser", "password": "password123"})
    assert resp_login.status_code == 200
    login_data = resp_login.json()
    assert "access_token" in login_data
    assert login_data["username"] == "testuser"

    # Test Login with Wrong Password
    resp_login_fail = client.post("/api/auth/login", json={"username": "testuser", "password": "wrong_password"})
    assert resp_login_fail.status_code == 401


def test_multi_user_isolation_and_crud():
    # Sign up and log in User A
    resp_a = client.post("/api/auth/signup", json={"username": "usera", "password": "passworda"})
    assert resp_a.status_code == 200
    token_a = resp_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Sign up and log in User B
    resp_b = client.post("/api/auth/signup", json={"username": "userb", "password": "passwordb"})
    assert resp_b.status_code == 200
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A adds a vehicle
    resp_veh_a = client.post("/api/user/vehicles", json={"name": "Tesla Model 3", "fuel_type": "EV", "efficiency": 6.5}, headers=headers_a)
    assert resp_veh_a.status_code == 200
    veh_a_id = resp_veh_a.json()["vehicle_id"]

    # 2. User B gets vehicles (should be empty, isolation check)
    resp_vehs_b = client.get("/api/user/vehicles", headers=headers_b)
    assert resp_vehs_b.status_code == 200
    assert len(resp_vehs_b.json()) == 0

    # User A gets vehicles (should have 1 vehicle)
    resp_vehs_a = client.get("/api/user/vehicles", headers=headers_a)
    assert resp_vehs_a.status_code == 200
    assert len(resp_vehs_a.json()) == 1
    assert resp_vehs_a.json()[0]["name"] == "Tesla Model 3"

    # 3. User B tries to delete User A's vehicle (should fail/404)
    resp_del_fail = client.delete(f"/api/user/vehicles/{veh_a_id}", headers=headers_b)
    assert resp_del_fail.status_code == 404

    # User A deletes their vehicle (should succeed)
    resp_del_success = client.delete(f"/api/user/vehicles/{veh_a_id}", headers=headers_a)
    assert resp_del_success.status_code == 200

    # 4. Document uploads isolation
    # We will upload a dummy file for User A
    import io
    dummy_file = io.BytesIO(b"dummy document content")
    resp_doc_a = client.post(
        "/api/user/documents",
        data={"doc_type": "Driving License", "doc_number": "DL12345", "expiry_date": "2030-12-31"},
        files={"file": ("license.jpg", dummy_file, "image/jpeg")},
        headers=headers_a
    )
    assert resp_doc_a.status_code == 200
    doc_a_id = resp_doc_a.json()["document_id"]

    # User B gets documents (should be empty, isolation check)
    resp_docs_b = client.get("/api/user/documents", headers=headers_b)
    assert resp_docs_b.status_code == 200
    assert len(resp_docs_b.json()) == 0

    # User A gets documents (should have 1 document)
    resp_docs_a = client.get("/api/user/documents", headers=headers_a)
    assert resp_docs_a.status_code == 200
    assert len(resp_docs_a.json()) == 1
    assert resp_docs_a.json()[0]["doc_number"] == "DL12345"

    # User B tries to delete User A's document (should fail/404)
    resp_doc_del_fail = client.delete(f"/api/user/documents/{doc_a_id}", headers=headers_b)
    assert resp_doc_del_fail.status_code == 404

    # User A deletes their document (should succeed)
    resp_doc_del_success = client.delete(f"/api/user/documents/{doc_a_id}", headers=headers_a)
    assert resp_doc_del_success.status_code == 200


def test_custom_mileage_cost_estimation():
    # Request vehicle cost estimation with a custom EV
    resp = client.post("/api/vehicle/estimate", json={
        "vehicle": "custom: My EV | EV | 6.0",
        "source_lat": 12.9716,
        "source_lng": 77.5946,
        "dest_lat": 12.9279,
        "dest_lng": 77.6271
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert data["fuel"] == "Electric"
    assert data["mileage"] == 6.0
    assert data["cost"] > 0
    # Custom EV electricity price is 7.00 per kWh
    # Distance is roughly 7.3 km
    # Cost should be around (7.3 / 6.0) * 7.00 = 8.5
    assert data["cost"] < 25.0

    # Request vehicle cost estimation with a custom Petrol car
    resp_petrol = client.post("/api/vehicle/estimate", json={
        "vehicle": "custom: My Sedan | Petrol | 12.0",
        "source_lat": 12.9716,
        "source_lng": 77.5946,
        "dest_lat": 12.9279,
        "dest_lng": 77.6271
    })
    assert resp_petrol.status_code == 200
    data_petrol = resp_petrol.json()
    assert data_petrol["available"] is True
    assert data_petrol["fuel"] == "Petrol"
    assert data_petrol["mileage"] == 12.0
    # Custom Petrol price is 102.94 per L
    # Distance is roughly 7.3 km
    # Cost should be around (7.3 / 12.0) * 102.94 = 62.6
    assert data_petrol["cost"] > 30.0


def test_user_journey_and_dashboard():
    # 1. Sign up and log in a new user
    resp = client.post("/api/auth/signup", json={"username": "journey_user2", "password": "password123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get initial dashboard (should be empty/zeros)
    resp_dash = client.get("/api/user/dashboard", headers=headers)
    assert resp_dash.status_code == 200
    dash_data = resp_dash.json()
    assert len(dash_data["recent"]) == 0
    assert len(dash_data["saved"]) == 0
    stats_map = {s["label"]: s["val"] for s in dash_data["stats"]}
    assert stats_map["Journeys"] == "0"
    assert stats_map["Saved"] == "₹0"
    assert stats_map["Time saved"] == "0 hr"
    assert stats_map["Avg cost"] == "₹0"

    # 3. Perform a plan journey search (saves to history, is_saved = False)
    resp_search = client.post("/api/user/journey", json={
        "from_stop": "Majestic",
        "to_stop": "Indiranagar",
        "mode": "search",
        "cost": 0,
        "duration": 0,
        "distance": 0.0,
        "date": "15 Jun",
        "is_saved": False
    }, headers=headers)
    assert resp_search.status_code == 200

    # Verify that search history doesn't affect statistics
    resp_dash_search = client.get("/api/user/dashboard", headers=headers)
    dash_search = resp_dash_search.json()
    assert len(dash_search["recent"]) == 1
    assert len(dash_search["saved"]) == 0
    assert dash_search["recent"][0]["from"] == "Majestic"
    stats_map_s = {s["label"]: s["val"] for s in dash_search["stats"]}
    assert stats_map_s["Journeys"] == "0"

    # 4. Save a specific Metro route with custom name "Office" (is_saved = True)
    resp_save = client.post("/api/user/journey", json={
        "from_stop": "Indiranagar",
        "to_stop": "Whitefield",
        "mode": "metro",
        "cost": 35,
        "duration": 25,
        "distance": 12.0,
        "date": "15 Jun",
        "is_saved": True,
        "custom_name": "Office"
    }, headers=headers)
    assert resp_save.status_code == 200
    save_id = resp_save.json()["journey_id"]

    # 5. Fetch dashboard and check stats are updated based ONLY on saved route
    resp_dash_updated = client.get("/api/user/dashboard", headers=headers)
    assert resp_dash_updated.status_code == 200
    dash_updated = resp_dash_updated.json()
    assert len(dash_updated["recent"]) == 1
    assert len(dash_updated["saved"]) == 1
    assert dash_updated["saved"][0]["custom_name"] == "Office"
    assert dash_updated["saved"][0]["from"] == "Indiranagar"

    stats_updated = {s["label"]: s["val"] for s in dash_updated["stats"]}
    assert stats_updated["Journeys"] == "1"
    assert stats_updated["Saved"] == "₹150"
    assert stats_updated["Time saved"] == "0.5 hr"
    assert stats_updated["Avg cost"] == "₹35"

    # 6. Delete the saved route and verify stats reset
    resp_delete = client.delete(f"/api/user/journey/{save_id}", headers=headers)
    assert resp_delete.status_code == 200

    resp_dash_final = client.get("/api/user/dashboard", headers=headers)
    dash_final = resp_dash_final.json()
    assert len(dash_final["saved"]) == 0
    stats_final = {s["label"]: s["val"] for s in dash_final["stats"]}
    assert stats_final["Journeys"] == "0"
    assert stats_final["Saved"] == "₹0"

