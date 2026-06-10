import sys

# Disable streamlit context warnings
import warnings
warnings.filterwarnings('ignore')

# Just build the index manually, don't import the routing module
import pandas as pd

df = pd.read_csv('data/processed/bmtc_stop_level_cleaned.csv')
df['stop_norm'] = df['stop_name'].str.strip().str.lower()

# Build index exactly like routing.py does
print("Building direct route index manually...\n", flush=True)

from features.fare import is_vajra_route

index = []
for route_no, group in df.groupby('route_no'):
    norms = list(group.sort_values('stop_sequence')['stop_norm'])
    index.append({
        'route_no': str(route_no),
        'base_route': str(route_no).replace('_REV', ''),
        'norms': norms,
    })

print(f"Total routes: {len(index)}", flush=True)

vajra = sum(1 for r in index if is_vajra_route(r['base_route']))
ordinary = len(index) - vajra

print(f"Vajra: {vajra}", flush=True)
print(f"Ordinary: {ordinary}", flush=True)

# Now test with specific stops
print(f"\nTesting route matching...", flush=True)

src_norm = "kempegowda bus station"
dst_norm = "vidhana soudha"

found_routes = []
for route_info in index:
    norms = route_info['norms']
    si = next((i for i, n in enumerate(norms) if n == src_norm), None)
    di = next((i for i, n in enumerate(norms) if n == dst_norm), None)
    if si is not None and di is not None and si < di:
        base = route_info['base_route']
        is_v = is_vajra_route(base)
        found_routes.append((base, is_v))

print(f"Found {len(found_routes)} routes from '{src_norm}' to '{dst_norm}'", flush=True)
for route, is_v in found_routes[:10]:
    print(f"  {route}: Vajra={is_v}", flush=True)
