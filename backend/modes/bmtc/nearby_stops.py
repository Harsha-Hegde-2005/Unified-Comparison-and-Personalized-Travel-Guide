import sys, math
sys.path.insert(0, '.')
from features.schedule import _stop_coords_dict

target_lat, target_lon = 12.883000, 77.563807

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

nearby = []
for stop_name, (lat, lon) in _stop_coords_dict.items():
    d = haversine(target_lat, target_lon, lat, lon)
    if d <= 1.5:
        nearby.append((d, stop_name, lat, lon))
nearby.sort()
print('DST stops within 1.5km of (12.883, 77.564):')
for d, n, la, lo in nearby[:25]:
    print(f'  {d:.3f}km - {n} ({la:.5f}, {lo:.5f})')

print()
src_lat, src_lon = 12.845215, 77.660169
nearby2 = []
for stop_name, (lat, lon) in _stop_coords_dict.items():
    d = haversine(src_lat, src_lon, lat, lon)
    if d <= 1.0:
        nearby2.append((d, stop_name, lat, lon))
nearby2.sort()
print('SRC stops within 1km of (12.845, 77.660):')
for d, n, la, lo in nearby2[:15]:
    print(f'  {d:.3f}km - {n} ({la:.5f}, {lo:.5f})')

# Also look up what routes serve these nearby stops
from core.loader import _routes_by_stop

if nearby:
    closest_dst = nearby[0][1]
    print(f'\nRoutes serving closest dst stop "{closest_dst}":')
    for r in _routes_by_stop.get(closest_dst, [])[:15]:
        print(f'  {r}')
