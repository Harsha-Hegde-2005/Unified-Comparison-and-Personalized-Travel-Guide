import requests

BASE = "http://127.0.0.1:8000"

r3 = requests.get(f"{BASE}/api/fare/calculate?mode=bmtc&source=Hebbal&destination=Silk%20Board")
print("BMTC Fare status:", r3.status_code)
print("BMTC Fare text:", r3.text)

r4 = requests.get(f"{BASE}/api/fare/calculate?mode=metro&source=Indiranagar&destination=MG%20Road")
print("Metro Fare status:", r4.status_code)
print("Metro Fare text:", r4.text)
