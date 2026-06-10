import pandas as pd

# Load trip data
trips_df = pd.read_csv('data/raw/trips.txt')
routes_df = pd.read_csv('data/raw/routes.txt')

merged = trips_df.merge(routes_df[['route_id', 'route_short_name']], on='route_id', how='left')
route_trips = merged.groupby('route_short_name').size().to_dict()

print("Route frequency distribution:\n")

from features.fare import is_vajra_route

ordinary_trips = [v for k, v in route_trips.items() if k and not is_vajra_route(k)]
vajra_trips = [v for k, v in route_trips.items() if k and is_vajra_route(k)]

print(f"Ordinary routes: {len(ordinary_trips)}")
print(f"  Min trips: {min(ordinary_trips) if ordinary_trips else 'N/A'}")
print(f"  Max trips: {max(ordinary_trips) if ordinary_trips else 'N/A'}")
print(f"  Mean trips: {sum(ordinary_trips) / len(ordinary_trips) if ordinary_trips else 'N/A':.1f}")
print(f"  Median trips: {sorted(ordinary_trips)[len(ordinary_trips)//2] if ordinary_trips else 'N/A'}")

print(f"\nVajra routes: {len(vajra_trips)}")
print(f"  Min trips: {min(vajra_trips) if vajra_trips else 'N/A'}")
print(f"  Max trips: {max(vajra_trips) if vajra_trips else 'N/A'}")
print(f"  Mean trips: {sum(vajra_trips) / len(vajra_trips) if vajra_trips else 'N/A':.1f}")
print(f"  Median trips: {sorted(vajra_trips)[len(vajra_trips)//2] if vajra_trips else 'N/A'}")

# Check for zero-trip routes
ordinary_zero = sum(1 for t in ordinary_trips if t == 0)
vajra_zero = sum(1 for t in vajra_trips if t == 0)

print(f"\nRoutes with 0 trips:")
print(f"  Ordinary: {ordinary_zero}/{len(ordinary_trips)}")
print(f"  Vajra: {vajra_zero}/{len(vajra_trips)}")
