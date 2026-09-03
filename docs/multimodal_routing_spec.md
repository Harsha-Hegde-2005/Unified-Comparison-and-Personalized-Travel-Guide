# Multimodal Journey Optimization Specification

This document details the engineering specifications for the multimodal routing engine in UTRS, which integrates BMTC buses, Namma Metro lines, Cabs, and walking legs into a single optimal route recommendation.

---

## 1. Network Integration Architecture

The multimodal router model operates as a unified coordinate-to-coordinate journey graph:

```
[Start Location Coordinates] ──► Walk leg (or local Bus / Cab)
                                     │
                                     ▼
                       [Entry Transit Hub (Metro/Bus)]
                                     │
                                     ▼  (Fast Transit: Metro/AC Bus)
                       [Exit Transit Hub (Metro/Bus)]
                                     │
                                     ▼
[End Location Coordinates]   ◄── Walk leg (or local Bus / Cab)
```

### Node Interchange Registry
Key intersection points are registered as **Interchange Hubs** in `backend/multimodal/config.py` (e.g. Majestic, Silk Board, Indiranagar, Yeshwanthpur, Hebbal). An interchange occurs when a Metro station and a BMTC stop are within a walking distance threshold ($R_{walk\_max} = 500\text{m}$).

---

## 2. Walk Linkage & Timing Models

Walking legs represent the critical link connecting the user's start/destination coordinates to transit nodes, and transit modes to each other.

* **Walking Velocity**: $V_{walk} = 5.0\text{ km/h}$ ($83\text{ meters/minute}$) under normal weather conditions.
* **Weather Degradation**: During rain, walking velocity decreases, and transfer buffer delays are scaled:
  * Light Rain: $V_{walk} = 4.25\text{ km/h}$, transfer buffer = 6 minutes.
  * Heavy Rain: $V_{walk} = 3.25\text{ km/h}$, transfer buffer = 12 minutes (discouraging long walking legs).
* **Maximum Walk Limits**: 
  * Source/destination access walking is capped at $1000\text{m}$.
  * Intermediate interchange walking is capped at $500\text{m}$. If walking distance exceeds this, a cab/auto leg is suggested as the bridge.

---

## 3. Multi-Criteria Optimal Path Search

Instead of a single "shortest path," UTRS calculates the optimal journey using a **Multi-Criteria Penalty Score** that balances travel time, monetary cost, and transfer fatigue:

$$\text{Score} = T_{total} + C_{total} \times W_{cost} + N_{transfers} \times P_{transfer} + P_{walk}$$

Where:
* $T_{total}$: Total estimated travel time in minutes (sum of walking, waiting, and vehicle transit times scaled by weather).
* $C_{total}$: Total cost in ₹ (fares of metro, bus, and cab combined).
* $W_{cost}$: Cost weighting factor ($0.5\text{ minutes/₹}$ default). Allows tuning:
  * `cost` preference: $W_{cost} = 1.5$ (favors cheap buses).
  * `time` preference: $W_{cost} = 0.1$ (favors fast cabs/metro).
* $N_{transfers}$: Number of vehicle switches/transfers.
* $P_{transfer}$: Penalty per transfer ($10\text{ minutes}$ penalty).
* $P_{walk}$: Penalty factor for walking legs $>500\text{m}$ to prevent recommending long walking routes.

---

## 4. Journey Result Schema (Response Contract)

The engine outputs options as a ranked list of `JourneyResult` objects, containing complete timings, costs, and segment details:

```json
{
  "mode": "Multimodal",
  "source": "Hosa Road",
  "destination": "Silk Board",
  "total_fare": 32,
  "total_time": 45,
  "transfers": 1,
  "legs": [
    {
      "mode": "Walk",
      "route": "Walking",
      "from": "Hosa Road Coordinates",
      "to": "Hosa Road Bus Stop",
      "fare": 0,
      "time": 6,
      "distance": 0.5,
      "instructions": "Walk 500m to Hosa Road Bus Stop"
    },
    {
      "mode": "BMTC",
      "route": "500C",
      "from": "Hosa Road Bus Stop",
      "to": "Silk Board Stop",
      "fare": 20,
      "time": 24,
      "distance": 8.2,
      "instructions": "Take bus 500C to Central Silk Board"
    },
    {
      "mode": "Walk",
      "route": "Walking",
      "from": "Silk Board Stop",
      "to": "Silk Board Destination",
      "fare": 0,
      "time": 15,
      "distance": 1.2,
      "instructions": "Walk to destination"
    }
  ]
}
```
This data structure is parsed directly by the React map renderer to draw color-coded routes (blue for BMTC, green for Metro, orange for Cabs, dotted grey for walks) on the interactive map.
