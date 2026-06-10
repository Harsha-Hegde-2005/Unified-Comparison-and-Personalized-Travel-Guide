import pandas as pd

df = pd.read_csv('data/processed/bmtc_stop_level_cleaned.csv')

# Get all Vajra routes
from features.fare import is_vajra_route

all_routes = df['route_no'].unique()
vajra_routes = [r for r in all_routes if is_vajra_route(r)]

print(f"Total Vajra routes: {len(vajra_routes)}\n")

print("First 10 Vajra routes and their stop counts:")
for route in vajra_routes[:10]:
    route_df = df[df['route_no'] == route]
    stops = len(route_df['stop_name'].unique())
    print(f"  {route}: {stops} stops")
