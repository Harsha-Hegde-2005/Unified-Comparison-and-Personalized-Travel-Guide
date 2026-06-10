import pandas as pd
from features.fare import is_vajra_route

# Load the data directly
df = pd.read_csv('data/processed/bmtc_stop_level_cleaned.csv')

# Check distribution
print("\n=== Direct Data Analysis ===\n")

# Count Vajra vs Ordinary by checking route names
vajra_count = 0
ordinary_count = 0
for route in df['route_no'].unique():
    if is_vajra_route(route):
        vajra_count += 1
    else:
        ordinary_count += 1

print(f"Total unique routes in CSV: {df['route_no'].nunique()}")
print(f"  Vajra: {vajra_count}")
print(f"  Ordinary: {ordinary_count}")

# Sample some ordinary routes and check their stops
print(f"\nSample ordinary routes and their stop counts:")
ordinary_routes = [r for r in df['route_no'].unique()[:50] if not is_vajra_route(r)]
for route in ordinary_routes[:5]:
    stops = len(df[df['route_no'] == route]['stop_name'].unique())
    print(f"  {route}: {stops} stops")

# Sample some Vajra routes
print(f"\nSample Vajra routes and their stop counts:")
vajra_routes = [r for r in df['route_no'].unique() if is_vajra_route(r)]
for route in vajra_routes[:5]:
    stops = len(df[df['route_no'] == route]['stop_name'].unique())
    print(f"  {route}: {stops} stops")
