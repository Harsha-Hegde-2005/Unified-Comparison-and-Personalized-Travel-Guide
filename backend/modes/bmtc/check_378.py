import sys
sys.path.insert(0, '.')
from core.loader import _direct_route_index_map, _routes_by_stop_norm

# Check if reverse of 378-family exists
for r in ['378-E', '378-E_REV', '378-B', '378-B_REV', '378-D', '378-D_REV', 'V-378', 'V-378_REV',
          '378 BEML5-ELC', '378 BEML5-ELC_REV']:
    exists = r in _direct_route_index_map
    if exists:
        info = _direct_route_index_map[r]
        norms = info['norms']
        print(f'{r}: FOUND - {len(norms)} stops, {norms[0]} -> {norms[-1]}')
    else:
        print(f'{r}: MISSING')

# Check what routes serve bhel/siemens and konanakunte
print()
print('Routes at bhel:', list(_routes_by_stop_norm.get('bhel', []))[:10])
print('Routes at siemens:', list(_routes_by_stop_norm.get('siemens', []))[:10])
print('Routes at beereshwara nagara:', list(_routes_by_stop_norm.get('beereshwara nagara', []))[:10])
print('Routes at konanakunte:', list(_routes_by_stop_norm.get('konanakunte', []))[:10])
print('Routes at sowdamini kalyana mantapa:', list(_routes_by_stop_norm.get('sowdamini kalyana mantapa', []))[:10])
