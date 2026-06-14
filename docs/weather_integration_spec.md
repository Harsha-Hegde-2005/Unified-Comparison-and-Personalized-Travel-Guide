# Weather Integration Specification

This document details the engineering specifications for integrating real-time weather conditions into UTRS routing, timing, and travel recommendations.

---

## 1. Concept & Objectives
Bengaluru weather (especially heavy monsoon rainfall) has a drastic impact on road traffic speed, walking transfers, and waterlogging at key transit junctions (like Silk Board, Hebbal, or Majestic).

### Goals
* Integrate live weather fetching from APIs or simulated configs.
* Dynamically adjust travel speeds for surface vehicles (Buses and Cabs).
* Increase walking transfer buffer times during rain.
* Recommend weather-resilient transport modes (favoring underground/elevated Metro over surface buses/walks).

---

## 2. Weather Status & Speed Modifiers

We classify weather into four status levels and apply coefficients ($C_{speed}$) to travel calculations:

| Weather Level | Visual Icon | Speed Coefficient ($C_{speed}$) | Walk Transfer Buffer | Impact Description |
| :--- | :---: | :---: | :---: | :--- |
| **Clear / Cloudy** | ☀️ / ☁️ | $1.0\times$ (normal) | 3 mins | No adjustments. Buses run at baseline speeds. |
| **Light Rain** | 🌧️ | $0.85\times$ (slight delay) | 6 mins | Minor congestion. Street walk speeds decrease by 15%. |
| **Heavy Rain** | ⛈️ | $0.65\times$ (severe delays) | 12 mins | Water logging on major arterials. Cabs face peak surge. |
| **Storm / Flooding** | 🚨 | $0.45\times$ (road gridlock) | 20 mins | Major junctions waterlogged. Avoid surface transport. |

---

## 3. Core Engine Adjustments

### Adjusted Bus & Cab Travel Time
The time calculation formula for road legs is updated to divide speed by the weather coefficient:
$$T_{travel} = \frac{\text{Distance}}{\text{Speed}_{TOD} \times C_{speed}} \times 60$$

### Walk Transfer Buffers
When planning a multimodal transfer (BMTC to Metro or vice-versa), the default walking interchange time is scaled:
$$T_{transfer\_walk} = T_{base\_walk} \times (1.0 + \text{DelayFactor}_{weather})$$

### Router Mode Penalization
During **Heavy Rain** or **Storm/Flooding**:
* Walking legs longer than 300 meters are heavily penalized in the Dijkstra score, discouraging transfers.
* Metro is tagged with a convenience bonus (negative penalty) because tracks are immune to traffic and platforms are sheltered.

---

## 4. API & UI Integration

### API Endpoint Modifications
The `/api/compare` and `/api/health` endpoints return a `weather` key:
```json
"weather": {
  "status": "Heavy Rain",
  "temperature_c": 22.4,
  "icon": "rain",
  "speed_multiplier": 0.65,
  "alerts": [
    "Heavy congestion expected on Outer Ring Road due to waterlogging.",
    "Walking transfers at Silk Board increased by 9 minutes."
  ]
}
```

### UI Presentation
* **Global Weather Widget**: A small dashboard indicator showing current Bengaluru weather.
* **Weather Alert Banners**: Rendered at the top of the route planning screen if weather level is $\ge$ **Heavy Rain** (e.g., *"🌧️ Heavy Rain: Surface routes face 35% delays. Metro highly recommended."*).
* **Card Warnings**: Individual route options display delay tags (e.g., *"Includes 15 min weather delay"*).
