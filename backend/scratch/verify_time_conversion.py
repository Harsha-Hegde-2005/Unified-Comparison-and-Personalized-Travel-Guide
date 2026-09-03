import json
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

with open("scratch/cleaned_benchmark.json") as f:
    data = json.load(f)

for date in list(data.keys())[:1]:
    for slot in data[date]:
        time_str = data[date][slot][0]["time"]
        hour, minute = [int(x) for x in time_str.split(":")]
        
        # 12-hour to 24-hour conversion based on slot
        hour_24 = hour
        if slot == "afternoon" and hour < 12:
            hour_24 += 12
        elif slot == "evening" and hour < 12:
            hour_24 += 12
        elif slot == "night" and hour < 12:
            hour_24 += 12
            
        print(f"Slot: {slot:<10} | Time in JSON: {time_str} | Converted Hour: {hour_24:02d}:{minute:02d}")
