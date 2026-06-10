import pandas as pd

# Load raw data
df = pd.read_csv('data/processed/bmtc_stop_level_cleaned.csv')

# Find all unique routes
print("Sample route stop lists:\n")

routes_to_check = ['2', 'G-2', 'BC-4A', '211AC BGM-BSK', 'V-500', 'AC-1']

for route in routes_to_check:
    route_df = df[df['route_no'] == route].sort_values('stop_sequence')
    if len(route_df) > 0:
        stops = route_df['stop_name'].tolist()
        print(f"Route {route}:")
        print(f"  Stops ({len(stops)}): {stops[:5]}... (showing first 5)")
    else:
        print(f"Route {route}: NOT FOUND")
    print()
