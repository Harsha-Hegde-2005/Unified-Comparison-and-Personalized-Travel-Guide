import sys
import os

_BMTC = os.path.join(os.path.dirname(__file__), "..", "modes", "bmtc")
sys.path.insert(0, _BMTC)

from core.gtfs import _get_gtfs, _route_departures, _stop_ids_for_norm
from core.stops import get_route_stop_list, _route_stop_map

_get_gtfs()

print(f"Total routes in _route_departures: {len(_route_departures)}")
sample_routes = list(_route_departures.keys())[:20]
print("Sample routes:", sample_routes)

# Test 500D
print("Searching for 500D in _route_departures:")
matches = [k for k in _route_departures.keys() if "500" in k.upper()]
print("500 matches:", matches[:10])

# Test 335E
print("Searching for 335E in _route_departures:")
matches335 = [k for k in _route_departures.keys() if "335" in k.upper()]
print("335 matches:", matches335[:10])

# Check route Hebbal
stop_norms = get_route_stop_list("500D")
print("500D stop norms count:", len(stop_norms) if stop_norms else 0)
