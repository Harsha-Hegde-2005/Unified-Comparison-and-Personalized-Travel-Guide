import sys
sys.stdout.flush()

# Silence streamlit warnings
import warnings
warnings.filterwarnings('ignore')

import streamlit as st
from features.routing import _direct_route_index
from features.fare import is_vajra_route

print("\n=== _direct_route_index Analysis ===\n", flush=True)

vajra_count = 0
ordinary_count = 0
for route_info in _direct_route_index:
    base = route_info['base_route']
    if is_vajra_route(base):
        vajra_count += 1
    else:
        ordinary_count += 1

print(f"Total routes in _direct_route_index: {len(_direct_route_index)}", flush=True)
print(f"  Vajra: {vajra_count}", flush=True)
print(f"  Ordinary: {ordinary_count}", flush=True)

# Show first 10
print(f"\nFirst 10 routes in _direct_route_index:", flush=True)
for i, route_info in enumerate(_direct_route_index[:10]):
    base = route_info['base_route']
    is_v = is_vajra_route(base)
    print(f"  {i+1}. {base} ({'Vajra' if is_v else 'Ordinary'}), stops: {len(route_info['norms'])}", flush=True)

# Show some ordinary routes
print(f"\nSample ordinary routes from index:", flush=True)
ordinary = [r for r in _direct_route_index if not is_vajra_route(r['base_route'])]
for route_info in ordinary[:5]:
    print(f"  {route_info['base_route']}", flush=True)
