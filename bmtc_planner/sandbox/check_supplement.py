import pandas as pd

df = pd.read_csv('data/processed/bmtc_stop_level_cleaned.csv')
rev = pd.read_csv('data/processed/reverse_routes_supplement.csv')

main_routes = set(df['route_no'].unique())
rev_routes = set(rev['route_no'].unique())

# Extract base routes (without _REV suffix)
rev_base_routes = set(r.replace('_REV', '') for r in rev_routes)

print(f"Main dataset routes: {len(main_routes)}")
print(f"Reverse supplement routes: {len(rev_routes)}")
print(f"Base routes in supplement: {len(rev_base_routes)}")

# Find routes in supplement that aren't in main dataset
only_in_rev = rev_base_routes - main_routes

print(f"\nRoutes in supplement but NOT in main dataset: {len(only_in_rev)}")
if only_in_rev:
    for r in list(only_in_rev)[:10]:
        print(f"  {r}")
