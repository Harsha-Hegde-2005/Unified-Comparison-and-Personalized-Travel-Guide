import pandas as pd
from features.fare import is_vajra_route
from features.schedule import calculate_segment_times
from datetime import datetime

df = pd.read_csv('data/processed/bmtc_stop_level_cleaned.csv')
df['stop_norm'] = df['stop_name'].str.strip().str.lower()

# Test calculate_segment_times for a specific segment
segments = [('2', 'jpnagara 6th phase', 'kempegowda bus station', 
            ['jpnagara 6th phase', 'jp nagara 15th cross', 'rvdental college', 'marenahalli',
             'jayanagara 5th block', 'jayanagara church', 'jayanagara general hospital',
             'carmel convent jayanagara', 'pump house jayanagar east end', 'lalbagh',
             'vidhana soudha', 'cubbon park', 'trinity church', 'shoolay circle',
             'richmond town', 'richmond railway station', 'kempegowda bus station'])]

print("Testing calculate_segment_times for route 2 (ordinary bus):\n")

try:
    result = calculate_segment_times(segments, start_time=None)
    if result:
        seg = result[0]
        print(f"Route: 2")
        print(f"  Duration: {seg.get('duration')}")
        print(f"  Fare: {seg.get('fare')}")
        print(f"  Departure: {seg.get('departure')}")
        print(f"  Arrival: {seg.get('arrival')}")
        print(f"  Distance: {seg.get('distance')}")
    else:
        print("No result returned from calculate_segment_times")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
