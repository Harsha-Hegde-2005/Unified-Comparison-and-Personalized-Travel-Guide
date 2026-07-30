import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_every_configured_metro_station_has_coordinates():
    lines = json.loads((ROOT / "database/metro/station_master.json").read_text())["lines"]
    stations = {station for line in lines.values() for station in line}
    coords = json.loads((ROOT / "database/metro/metro_coords.json").read_text())

    assert set(coords) == stations
    assert coords["Dasarahalli"] == {"lat": 13.043542, "lng": 77.512379}
    assert all(-90 <= point["lat"] <= 90 and -180 <= point["lng"] <= 180 for point in coords.values())
