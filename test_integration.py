"""
Testing Guide for Unified Bangalore Journey Planner

Run this script to validate the integration structure.
"""

import sys
import os
from datetime import datetime


def log(msg, status="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = "[INFO]" if status == "INFO" else f"[{status}]"
    print(f"{ts} {prefix} {msg}")


def test_shared_layer():
    """Test shared layer imports and utilities."""
    log("Testing shared layer...")
    try:
        from shared.interfaces.journey_plan import BaseJourneyPlanner, JourneyResult
        from shared.utils.distance import haversine_distance, find_nearby_stops
        from shared.utils.time import format_time, add_buffer_time
        from shared.config import WALKING_RADIUS_M, TRANSFER_BUFFER_MIN

        # Test haversine
        dist = haversine_distance(12.9667, 77.5667, 13.0011, 77.5920)
        assert dist > 4000 and dist < 6000, f"Unexpected distance: {dist}"

        # Test time formatting
        assert "2 hrs" in format_time(125), "Time format failed"

        # Test buffer
        assert add_buffer_time(10, 5) == 15, "Buffer calculation failed"

        log("Shared layer OK", "PASS")
        return True
    except Exception as e:
        log(f"Shared layer failed: {e}", "FAIL")
        return False


def test_adapters():
    """Test adapter imports."""
    log("Testing adapters...")
    try:
        from adapters.bmtc_adapter import BMTCAdapter
        from adapters.metro_adapter import MetroAdapter

        log("BMTC and Metro adapters imported", "PASS")
        return True
    except Exception as e:
        log(f"Adapter import failed: {e}", "FAIL")
        return False


def test_multimodal():
    """Test multimodal router structure."""
    log("Testing multimodal router...")
    try:
        from multimodal.router import MultimodalRouter
        from multimodal.interchange_matcher import InterchangeMatcher
        from multimodal.config import INTERCHANGE_POINTS

        assert len(INTERCHANGE_POINTS) > 5, "Insufficient interchange points"
        log(f"Interchange points loaded: {len(INTERCHANGE_POINTS)}", "PASS")
        return True
    except Exception as e:
        log(f"Multimodal router failed: {e}", "FAIL")
        return False


def test_ui_structure():
    """Test UI file structure."""
    log("Testing UI structure...")
    try:
        required_files = [
            "ui/__init__.py",
            "ui/multimodal_app.py",
            "ui/styles.py",
            "ui/pages/__init__.py",
            "ui/pages/bmtc_only.py",
            "ui/pages/metro_only.py",
            "ui/pages/multimodal.py",
        ]

        missing = [f for f in required_files if not os.path.exists(f)]

        if missing:
            log(f"Missing UI files: {missing}", "FAIL")
            return False

        log(f"All {len(required_files)} UI files present", "PASS")
        return True
    except Exception as e:
        log(f"UI structure check failed: {e}", "FAIL")
        return False


def test_dependencies():
    """Check if key dependencies are available."""
    log("Checking dependencies...")
    required = ["pandas", "numpy", "streamlit", "requests"]
    missing = []

    for dep in required:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)

    if missing:
        log(f"Missing packages: {missing}. Run: pip install -r requirements.txt", "WARN")
        return False

    log("All dependencies available", "PASS")
    return True


def main():
    print("\n" + "=" * 60)
    print("BANGALORE UNIFIED JOURNEY PLANNER - INTEGRATION TEST")
    print("=" * 60 + "\n")

    results = {
        "Shared Layer": test_shared_layer(),
        "Adapters": test_adapters(),
        "Multimodal Router": test_multimodal(),
        "UI Structure": test_ui_structure(),
        "Dependencies": test_dependencies(),
    }

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "OK" if result else "XX"
        print(f"[{symbol}] {test_name}")

    all_pass = all(results.values())

    print("\n" + "=" * 60)
    if all_pass:
        print("Integration test PASSED!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the app: streamlit run ui/multimodal_app.py")
        print("3. Test each transport mode")
        return 0
    else:
        print("Integration test FAILED!")
        print("Fix issues listed above and re-run test.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
