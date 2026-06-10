import pandas as pd
from features.fare import is_vajra_route

df = pd.read_csv('data/processed/bmtc_stop_level_cleaned.csv')
df['stop_norm'] = df['stop_name'].str.strip().str.lower()

# Manually build _direct_route_index like routing.py does
print("Building direct route index...\n")

direct_route_index = []
for route_no, group in df.groupby('route_no'):
    norms = list(group.sort_values('stop_sequence')['stop_norm'])
    direct_route_index.append({
        'route_no': str(route_no),
        'base_route': str(route_no).replace('_REV', ''),
        'norms': norms,
    })

print(f"Total routes in index: {len(direct_route_index)}")

vajra_count = sum(1 for r in direct_route_index if is_vajra_route(r['base_route']))
print(f"  Vajra: {vajra_count}")
print(f"  Ordinary: {len(direct_route_index) - vajra_count}\n")

# Now test with specific stops
src_raw = 'JPNagara 6th Phase'
dst_raw = 'Kempegowda Bus Station'
src_norm = src_raw.strip().lower()
dst_norm = dst_raw.strip().lower()

print(f"Searching routes from '{src_raw}' to '{dst_raw}'")
print(f"  Normalized: '{src_norm}' to '{dst_norm}'\n")

results = []
for route_info in direct_route_index:
    route_no = route_info['route_no']
    norms = route_info['norms']
    si = next((i for i, n in enumerate(norms) if n == src_norm), None)
    di = next((i for i, n in enumerate(norms) if n == dst_norm), None)
    if si is not None and di is not None and si < di:
        base = route_info['base_route']
        results.append({
            'route': base,
            'is_vajra': is_vajra_route(base),
        })

print(f"Found {len(results)} direct routes")
for r in results[:10]:
    print(f"  {r['route']}: Vajra={r['is_vajra']}")
