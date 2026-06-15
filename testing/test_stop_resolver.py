import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_BACKEND = os.path.join(_ROOT, "backend")

sys.path.insert(0, _BACKEND)
sys.path.insert(0, os.path.join(_BACKEND, "modes", "bmtc"))

import pytest
from shared.utils.stop_resolver import clean_input_name, resolve_stop_name

def test_clean_input_name():
    assert clean_input_name("Cs-Hosa Road") == "Hosa Road"
    assert clean_input_name("cs-hosa road") == "hosa road"
    assert clean_input_name("CS Majestic") == "Majestic"
    assert clean_input_name("Normal Stop") == "Normal Stop"
    assert clean_input_name(None) == ""

def test_resolve_stop_name_bmtc():
    bmtc_stops = ["Kempegowda Bus Station", "Yeshawanthapura Bus Station", "Hosa Road", "Central Silk Board", "KR Puram", "Indiranagara"]
    
    # Majestic synonyms
    assert resolve_stop_name("Majestic", "bmtc", bmtc_stops=bmtc_stops) == "Kempegowda Bus Station"
    assert resolve_stop_name("KBS", "bmtc", bmtc_stops=bmtc_stops) == "Kempegowda Bus Station"
    assert resolve_stop_name("kempegowda", "bmtc", bmtc_stops=bmtc_stops) == "Kempegowda Bus Station"
    assert resolve_stop_name("Nadaprabhu Kempegowda Metro Station", "bmtc", bmtc_stops=bmtc_stops) == "Kempegowda Bus Station"
    
    # Yeshwanthpur synonyms
    assert resolve_stop_name("Yeshwanthpur", "bmtc", bmtc_stops=bmtc_stops) == "Yeshawanthapura Bus Station"
    assert resolve_stop_name("yeshwanthpur metro", "bmtc", bmtc_stops=bmtc_stops) == "Yeshawanthapura Bus Station"
    
    # Hosa Road
    assert resolve_stop_name("Cs-Hosa Road", "bmtc", bmtc_stops=bmtc_stops) == "Hosa Road"
    
    # Case insensitive match against list
    assert resolve_stop_name("kr puram", "bmtc", bmtc_stops=bmtc_stops) == "KR Puram"

def test_resolve_stop_name_metro():
    metro_stations = ["Majestic", "Yeshwanthpur", "Hosa Road", "Central Silk Board", "Krishnarajapura", "Indiranagar"]
    
    # Majestic synonyms
    assert resolve_stop_name("Kempegowda Bus Station", "metro", metro_stations=metro_stations) == "Majestic"
    assert resolve_stop_name("KBS", "metro", metro_stations=metro_stations) == "Majestic"
    assert resolve_stop_name("majestic", "metro", metro_stations=metro_stations) == "Majestic"
    
    # Yeshwanthpur synonyms
    assert resolve_stop_name("Yeshawanthapura Bus Station", "metro", metro_stations=metro_stations) == "Yeshwanthpur"
    
    # Hosa Road
    assert resolve_stop_name("Cs-Hosa Road", "metro", metro_stations=metro_stations) == "Hosa Road"
    
    # Krishnarajapura
    assert resolve_stop_name("kr puram", "metro", metro_stations=metro_stations) == "Krishnarajapura"
