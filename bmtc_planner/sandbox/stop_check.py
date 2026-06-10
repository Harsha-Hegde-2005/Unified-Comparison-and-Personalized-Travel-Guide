import pandas as pd
from features.fare import is_vajra_route

df = pd.read_csv('data/processed/bmtc_stop_level_cleaned.csv')

# Normalize stop names the same way the code does
df['stop_norm'] = df['stop_name'].str.strip().str.lower()

# Find some common stop pairs that exist in the data
print("Finding stop pairs...\n")

unique_stops = df['stop_name'].unique()
print(f"Total unique stops in CSV: {len(unique_stops)}")

# Get a sample stop  
sample_stops = unique_stops[:5]
print(f"Sample stops: {sample_stops}\n")

# For route '2' (ordinary), let's see what direct connections exist
print("Checking Route '2' (ordinary bus):")
route_2_df = df[df['route_no'] == '2'].sort_values('stop_sequence')
route_2_stops = route_2_df['stop_name'].unique()
print(f"  Stops: {len(route_2_stops)}")
if len(route_2_stops) > 0:
    print(f"  First stop: {route_2_stops[0]}")
    print(f"  Last stop: {route_2_stops[-1]}")
    if len(route_2_stops) > 1:
        src = route_2_stops[0].lower()
        dst = route_2_stops[-1].lower()
        print(f"  Can route from '{route_2_stops[0]}' to '{route_2_stops[-1]}'")
print()

# For a Vajra route, let's check too
vajra_routes = [r for r in df['route_no'].unique() if is_vajra_route(r)]
if vajra_routes:
    vajra_route = vajra_routes[0]
    print(f"Checking Route '{vajra_route}' (Vajra bus):")
    vajra_df = df[df['route_no'] == vajra_route].sort_values('stop_sequence')
    vajra_stops = vajra_df['stop_name'].unique()
    print(f"  Stops: {len(vajra_stops)}")
    if len(vajra_stops) > 0:
        print(f"  First stop: {vajra_stops[0]}")
        print(f"  Last stop: {vajra_stops[-1]}")
