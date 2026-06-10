import streamlit as st
from core.loader import stops_df, ALL_STOPS
from features.routing import get_all_direct_buses, _direct_route_index
from features.fare import is_vajra_route

print("\n=== DEBUGGING ONLY VAJRA BUSES ISSUE ===\n")

# Check _direct_route_index
print(f"Total routes in _direct_route_index: {len(_direct_route_index)}")
vajra_in_index = sum(1 for r in _direct_route_index if is_vajra_route(r['base_route']))
ordinary_in_index = sum(1 for r in _direct_route_index if not is_vajra_route(r['base_route']))
print(f"  Vajra routes: {vajra_in_index}")
print(f"  Ordinary routes: {ordinary_in_index}")

# Check first 20 routes
print(f"\nFirst 20 routes in index:")
for i, r in enumerate(_direct_route_index[:20]):
    is_v = is_vajra_route(r['base_route'])
    print(f"  {r['base_route']}: {'Vajra' if is_v else 'Ordinary'}, stops={len(r['norms'])}")

# Try a few different stop pairs
test_pairs = [
    ('vidhana soudha', 'silk board'),
    ('kempegowda station', 'mg road'),
    ('rajajinagar', 'hebbal'),
]

for src, dst in test_pairs:
    print(f"\n--- Testing {src} → {dst} ---")
    buses = get_all_direct_buses(src.lower(), dst.lower())
    print(f"Found {len(buses)} direct buses")
    for b in buses[:5]:
        is_v = is_vajra_route(b['route'])
        print(f"  {b['route']}: {'Vajra' if is_v else 'Ordinary'}, fare={b.get('fare')}")


