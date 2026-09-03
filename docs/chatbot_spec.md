# Commuter Chatbot Widget & NLP Engine Specification

This document details the conversational intent parsing, parameter extraction, and engine-bridging logic for the UTRS Chatbot assistant.

---

## 1. Intent Classification Matrix

The chatbot uses a rule-based Natural Language Processing (NLP) pipeline to classify user messages into distinct conversational intents:

| User Query Example | Recognized Intent | Extracted Parameters | Target Endpoint / Handler |
| :--- | :--- | :--- | :--- |
| *"How long does it take to go from Majestic to Silk Board?"* | `journey_time` | `source="Majestic"`, `destination="Silk Board"` | Query `/api/compare` $\rightarrow$ Extract time of best option |
| *"How much will it cost to go from Hosa Road to Indiranagar?"* | `journey_cost` | `source="Hosa Road"`, `destination="Indiranagar"` | Query `/api/compare` $\rightarrow$ Extract fare of best option |
| *"I have only ₹60. How can I reach Whitefield from Majestic?"* | `budget_constrained` | `source="Majestic"`, `destination="Whitefield"`, `budget=60` | Query `/api/compare` $\rightarrow$ Filter options where $\text{cost} \le \text{budget}$ |
| *"Is it going to rain today at 4 pm?"* | `weather_query` | `time="16:00"` | Query simulated weather timeline for rain status |
| *"Shall I take my bike to Electronic City today?"* | `vehicle_vs_transit` | `destination="Electronic City"`, `vtype="bike"` | Compare Personal Bike fuel/time vs Metro/Bus routing |

---

## 2. Intent Handlers & Algorithm Layout

### 1. Journey Cost and Time (`journey_time` & `journey_cost`)
* **Logic**: Parse `source` and `destination` stops using fuzzy stop names lookup.
* **Execution**: Calls the main multimodal comparisons method (`plan_multimodal(source, destination)`).
* **Response Generation**: Formats a conversational text:
  * *"Taking the Green Line Metro is the fastest option: it takes 35 minutes and costs ₹42."*
  * Renders the interactive route card directly under the message bubble.

### 2. Budget Constraints (`budget_constrained`)
* **Logic**: Extracts the numeric currency amount (e.g. `₹50`, `50 rupees`, `50 bucks`) and parses source/dest locations.
* **Execution**:
  1. Requests all route estimates from the backend `/api/compare` engine.
  2. Filters results: `filtered_options = [opt for opt in options if opt.cost <= budget]`.
  3. If `filtered_options` is empty:
     * Suggests the cheapest available option: *"Your budget is too low for a direct trip. The cheapest option is BMTC ordinary bus at ₹25, which is ₹5 over your budget. Walk details: ..."*.
  4. If matches exist, ranks them by travel speed and suggests them.

### 3. Weather Forecast checks (`weather_query`)
* **Logic**: Detects weather keywords (*rain, shower, storm, clear, weather*) and extracts time parameter (defaults to "current").
* **Execution**: Queries the mock/API weather forecast sequence for the specific hour.
* **Response Generation**:
  * *"Yes, heavy rain is forecast at 4:00 PM today. Road speeds will drop by 35%. I recommend taking the Metro rather than a cab or bus to avoid traffic gridlock."*

### 4. Vehicle vs Transit Recommendations (`vehicle_vs_transit`)
* **Logic**: Triggered when the user asks whether to drive their car/bike or use public transit.
* **Execution**:
  1. Looks up the user's specific vehicle model (or uses default Bike/Car) and fetches fuel consumption details.
  2. Queries Google Maps/OSRM for driving road distance to destination.
  3. Calculates Fuel Cost + Parking:
     $$\text{Driving Cost} = \frac{D}{\text{Mileage}} \times \text{Fuel Price} + \text{Parking}$$
  4. Queries `/api/compare` for public transit (BMTC + Metro) time and fare.
  5. If current weather is **Heavy Rain** or peak commute congestion is active:
     * Bike is discouraged due to safety and rain delays.
     * Metro is suggested: *"I recommend public transit (Metro) today. Driving your bike will cost ₹85 and take 45 mins in heavy rain. The Metro costs ₹30, is sheltered, and takes only 30 mins."*
  6. If clear, compares driving cost vs transit.

---

## 3. NLP Parameter Parser Flow

```
   [User Input Text] 
          │
          ▼
   [Fuzzy Stop Name Lookup]  ──► Matches against canonical ALL_STOPS list
          │
          ▼
   [Numeric Extraction]      ──► Extracts budget limits (Regex: \b(?:rs\.?|₹)?\s*(\d+)\b)
          │
          ▼
   [Weather & Time Scanners] ──► Scans time formats (e.g. "4 pm", "16:00")
          │
          ▼
[Execute Specific Intent Handler]
```

---

## 4. UI Rendering in React
* **Floating Widget**: Floating toggle button on the bottom right.
* **Prompt Chips**: Suggests quick chips to trigger queries instantly:
  * *"Cheapest route under ₹40"*
  * *"Will it rain at 4 PM today?"*
  * *"Should I take my bike?"*
* **Response Bubbles**: Styled chat bubbles. It supports embedding React components directly (such as structured transit itineraries and maps focus links).
