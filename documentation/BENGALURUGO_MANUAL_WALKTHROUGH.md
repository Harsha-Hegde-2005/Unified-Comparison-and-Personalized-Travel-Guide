# 🚌 BengaluruGo · Comprehensive Project Manual & Video Walkthrough Guide

> **Bengaluru's Unified Multi-Modal Transit Guide & Intelligent Commuter Ecosystem**  
> **Platform Version:** 2.0 (Verified & Production Ready)  
> **Live Web Application:** [https://unified-comparison-and-personalized-travel-guide-dgjgdvfzy.vercel.app/](https://unified-comparison-and-personalized-travel-guide-dgjgdvfzy.vercel.app/)  
> **Mobile Browser Demonstration Video:** [BengaluruGo_Mobile_Demo_Walkthrough.mp4](file:///c:/Users/Harsh/Downloads/BMTC_fixed/documentation/demo_video/BengaluruGo_Mobile_Demo_Walkthrough.mp4)  
> **Interactive Mobile Player & Manual:** [bengalurugo_walkthrough_manual.html](file:///c:/Users/Harsh/Downloads/BMTC_fixed/documentation/demo_video/bengalurugo_walkthrough_manual.html)  

---

## 📋 Table of Contents
1. [Executive Summary & Core Mission](#1-executive-summary--core-mission)
2. [Full Feature Matrix & Architectural Breakdown](#2-full-feature-matrix--architectural-breakdown)
3. [Video Walkthrough & Demonstration Script (Chapter-by-Chapter)](#3-video-walkthrough--demonstration-script)
   - [Chapter 1: Welcome to BengaluruGo & Overview](#chapter-1-welcome-to-bengalurugo--overview)
   - [Chapter 2: Authentication & Secure Profile Vault](#chapter-2-authentication--secure-profile-vault)
   - [Chapter 3: 1-Page Non-Scrollable Home Dashboard](#chapter-3-1-page-non-scrollable-home-dashboard)
   - [Chapter 4: Saved Places & Recent Searches](#chapter-4-saved-places--recent-searches)
   - [Chapter 5: My Garage & Vehicle Costing](#chapter-5-my-garage--vehicle-costing)
   - [Chapter 6: Digital Glovebox & In-App Document Viewer](#chapter-6-digital-glovebox--in-app-document-viewer)
   - [Chapter 7: Multi-Modal Route Planner & Comparison Matrix](#chapter-7-multi-modal-route-planner--comparison-matrix)
   - [Chapter 8: Dedicated Mode View & "See All Buses"](#chapter-8-dedicated-mode-view--see-all-buses)
   - [Chapter 9: Interactive Leaflet GPS Map & Linear Schematic](#chapter-9-interactive-leaflet-gps-map--linear-schematic)
   - [Chapter 10: Active Ride Mode & 2-Way Turn-by-Turn Navigation](#chapter-10-active-ride-mode--2-way-turn-by-turn-navigation)
   - [Chapter 11: Transit Intelligence Utilities & Weather Advisory](#chapter-11-transit-intelligence-utilities--weather-advisory)
   - [Chapter 12: AI Transit Assistant Chatbot & Production Summary](#chapter-12-ai-transit-assistant-chatbot--production-summary)
4. [Mathematical Formulations & Algorithmic Foundations](#4-mathematical-formulations--algorithmic-foundations)
5. [Operational User Guide & Step-by-Step Instructions](#5-operational-user-guide--step-by-step-instructions)
6. [API Specification & Backend Contracts](#6-api-specification--backend-contracts)

---

## 1. Executive Summary & Core Mission

Urban mobility in Bengaluru poses complex commute challenges due to traffic bottlenecks, fragmented transit information, and rapid suburban sprawl. Commuters frequently face an agonizing decision: *Should I take a BMTC bus, hop on Namma Metro, book an auto/cab, or drive my own vehicle?*

**BengaluruGo** solves this fragmentation by offering a **Unified Multi-Modal Transit Guide** that aggregates:
1. **BMTC Buses**: 500+ routes, Volvo AC Vajra, non-AC, schedule frequencies, and stage fare tiers.
2. **Namma Metro (BMRCL)**: Purple and Green lines, platform numbering, and interchange routing at Kempegowda/Majestic.
3. **On-Demand Cabs & Auto-Rickshaws**: Dynamic fare estimation for Auto, Uber/Ola Mini, Prime, and Bike Taxis with surge factor transparency.
4. **Personal Vehicles (Car/Bike/EV)**: Personalized fuel consumption, parking, and toll calculations via the integrated **My Garage**.
5. **Eco-Friendly Active Mobility**: Cycling and walking trajectories with calorie burn estimations and zero-carbon ratings.
6. **Smart Multimodal Combos**: Intelligent transfers (Bus + Metro + First/Last-Mile Walk).

---

## 2. Full Feature Matrix & Architectural Breakdown

| Subsystem | Web Stack (React 19 + Vite) | Mobile Stack (Flutter + Dart) | Backend Service (FastAPI) |
| :--- | :--- | :--- | :--- |
| **Authentication** | JWT Bearer, localStorage token sync | Secure Storage, Biometric ready | OAuth2 Password Bearer, BCrypt hashing |
| **Dashboard** | 1-Page Non-scrollable layout, Dynamic greeting | Single-screen Material 3, Dynamic greeting | User Profile & Preferences API |
| **Route Planner** | Predictive Stop Suggestion dropdown | Search delegate with fuzzy match | GTFS Graph Traversal, Dijkstra/BFS |
| **Scoring Engine** | Client Pareto filter (Fastest/Cheapest/Comfort) | Multi-Criteria Sorting sliders | Weighted Pareto Multi-Objective Optimization |
| **Vehicle Vault** | My Garage & Digital Glovebox | Local SQLite Vehicle & Document DB | Multi-part Document Store, Base64 streaming |
| **Document Viewer**| Built-in modal PDF & Image viewer | In-app PDF preview & gallery intent | Secure file download & MIME validation |
| **Mapping Engine** | Leaflet.js, OpenStreetMap, Carto Dark | Google Maps / Flutter Map plugin | GeoJSON polyline generator |
| **Navigation** | 2-Way direction, Intermediate boarding | Background GPS, Audio TTS alerts | Real-time distance matrix & step slicer |
| **Transit Tools** | Timetables, Route Lookup, Stage Fare Calc | Native bottom navigation bar | Full BMTC route & stage fare repository |
| **AI Assistant** | Floating widget with natural language parsing | Dedicated chat tab with intent parsing | LLM / NLP intent & entity extractor |

---

## 3. Video Walkthrough & Demonstration Script

### Chapter 1: Welcome to BengaluruGo & Overview
- **Visuals:** High-tech opening title card with the BengaluruGo brand icon (purple and pink gradient) and unified cityscape.
- **Narrator Audio:**  
  *"Welcome to BengaluruGo! This comprehensive video manual provides an in-depth walkthrough of Bengaluru's Unified Multi-Modal Transit Guide. BengaluruGo is engineered to eliminate commute guesswork by bringing bus, metro, cabs, personal vehicles, and eco-friendly walking into one single, intelligent platform."*
- **Key Manual Takeaways:**
  - Designed for real Bengaluru commuters navigating diverse transport networks.
  - Built with React 19 web frontend, Flutter mobile client, and high-performance FastAPI backend.

### Chapter 2: Authentication & Secure Profile Vault
- **Visuals:** Landing page presentation highlighting the modern hero banner, dual-mode Auth modal with smooth transitions between Login and Register tabs.
- **Narrator Audio:**  
  *"In Chapter 2, we explore Authentication and Security. New commuters are greeted with an intuitive landing page. Commuters can sign in or create an account in seconds. Security is fortified with BCrypt-hashed credentials and JWT tokens that persist sessions across browser refreshes."*
- **Key Manual Takeaways:**
  - Token is securely saved in `localStorage.setItem('token', token)`.
  - Seamless fallback for guests allows exploring transit routes before registering.

### Chapter 3: 1-Page Non-Scrollable Home Dashboard
- **Visuals:** The desktop and mobile Home screens displaying the dynamic clock-aware greeting, landmark cityscape graphic, prominent "Plan Journey" button, and 6 central feature tiles.
- **Narrator Audio:**  
  *"Chapter 3 showcases the refreshed 1-Page Home Dashboard. With a non-scrollable desktop viewport, commuters see all essential functions instantly. Notice the dynamic greeting that updates from Good Morning to Good Afternoon or Good Evening, and the prominent Plan Journey button placed right beside the greeting."*
- **Key Manual Takeaways:**
  - Dynamic `getGreeting()` function queries local device time (`< 12` morning, `< 17` afternoon, else evening).
  - Feature tiles (Saved Places, Recent Searches, Garage, Glovebox, Quick Actions, Settings) open full modular views.

### Chapter 4: Saved Places & Recent Searches
- **Visuals:** Opening the Saved Places drawer, bookmarking "Work" (Bagmane Tech Park) and "Home" (Jayanagar), and clicking a chip to auto-trigger journey planning.
- **Narrator Audio:**  
  *"In Chapter 4, we examine Saved Places and Recent Searches. Everyday routes can be bookmarked as Home, Work, or College. Clicking any saved bookmark immediately populates the journey planner, eliminating repetitive typing."*
- **Key Manual Takeaways:**
  - One-click trigger fires `onSelectRoute(src, dst)` directly into the comparison engine.
  - Recent searches audit trail maintains chronological recall of previous queries.

### Chapter 5: My Garage & Vehicle Costing
- **Visuals:** Adding a petrol car (14 km/L) and an Electric Scooter (Ather 450X), highlighting live mileage calculations and EV carbon reduction metrics.
- **Narrator Audio:**  
  *"Chapter 5 highlights My Garage. Commuters can register their personal cars, bikes, or electric vehicles. BengaluruGo computes exact running costs per kilometer based on live fuel prices and mileage, allowing you to directly compare private driving costs against public transit."*
- **Key Manual Takeaways:**
  - Formula: $\text{Fuel Cost} = \left(\frac{\text{Distance}}{\text{Mileage}}\right) \times \text{Fuel Price} + \text{Toll}$.
  - Supports EV tracking with energy consumption ($\text{kWh/km}$) and green carbon offset credits.

### Chapter 6: Digital Glovebox & In-App Document Viewer
- **Visuals:** Accessing vehicle documents, previewing an uploaded Registration Certificate (RC) PDF and Insurance card inside the embedded modal viewer.
- **Narrator Audio:**  
  *"Chapter 6 introduces the Digital Glovebox. Keep your vehicle RC, Insurance, Emission Certificate, and Driving License securely in one place. Crucially, BengaluruGo features a built-in document viewer, allowing you to open and review PDF and image files right inside the app without needing external software."*
- **Key Manual Takeaways:**
  - Embedded `<iframe>` and `<embed>` tag handles PDF streaming without pop-up blockers.
  - Expiry alert badges highlight documents approaching renewal deadlines.

### Chapter 7: Multi-Modal Route Planner & Comparison Matrix
- **Visuals:** Typing "Silk Board" to "Majestic", autocomplete suggestions appearing, selecting "Cheapest" filter, and inspecting side-by-side comparison cards.
- **Narrator Audio:**  
  *"In Chapter 7, we enter the Multi-Modal Comparison Engine. Using Pareto multi-criteria scoring, the system evaluates all available travel modes. Commuters can toggle between Cheapest, Fastest, and Comfortable to instantly see which mode best satisfies their personal constraints."*
- **Key Manual Takeaways:**
  - Autocomplete queries 500+ BMTC and Namma Metro stations.
  - Displays transfer counts, walk duration, and carbon emissions in grams.

### Chapter 8: Dedicated Mode View & "See All Buses" Detail
- **Visuals:** Clicking on the BMTC Bus result card, transitioning to the dedicated bus sub-page, and clicking "See All Buses" to view alternative bus routes (500-D, 500-CA, KIA-9).
- **Narrator Audio:**  
  *"Chapter 8 explores Dedicated Mode Pages. Clicking any result card opens an exclusive deep-dive page. For BMTC buses, commuters get route guidelines, fare stages, and a dedicated 'See All Buses' button that lists every alternative bus route running on that exact corridor."*
- **Key Manual Takeaways:**
  - Metro view indicates exact platform numbers (e.g. Platform 2 Eastbound) and Majestic transfer walk times.
  - Cab fare cards display transparent estimates without obtrusive advisory clutter.

### Chapter 9: Interactive Leaflet GPS Map & Linear Schematic
- **Visuals:** Toggling between the geospatial Leaflet route map (with purple GPS polyline and stop markers) and the linear subway-style stop schematic.
- **Narrator Audio:**  
  *"Chapter 9 demonstrates our Dual Route Visualizer. Commuters can view their journey on an interactive geospatial GPS map with customizable layers like OpenStreetMap and Dark Mode, or switch to a clean, subway-style linear schematic that highlights upcoming stops sequentially."*
- **Key Manual Takeaways:**
  - Highlighting major Bengaluru congestion hotspots (Silk Board junction, Tin Factory, Hebbal flyover).
  - Clicking any pin displays stop name, arrival ETA, and transfer guidelines.

### Chapter 10: Active Ride Mode & 2-Way Turn-by-Turn Navigation
- **Visuals:** Clicking "Ride Mode", toggling the "⇄ Switch Direction" button, selecting an intermediate boarding stop from the dropdown, and witnessing live stop progress.
- **Narrator Audio:**  
  *"Chapter 10 presents Active Ride Mode. Designed for real commuters, it features true two-way bidirectional navigation, allowing you to flip between forward and return journeys with one tap. Furthermore, if you board at an intermediate stop along the route, simply select your boarding point, and the system automatically recalibrates remaining stops."*
- **Key Manual Takeaways:**
  - Slices stops sequence array from intermediate boarding index to terminus.
  - Unified single navigation bar combines Ride Mode, Start Navigation, and Save Route into one cohesive control.

### Chapter 11: Transit Intelligence Utilities & Weather Advisory
- **Visuals:** Accessing the Features modal, inspecting BMTC bus timetables, searching Route 500D in Route Lookup, checking stage fares, and viewing the smart rain fallback alert.
- **Narrator Audio:**  
  *"Chapter 11 covers Transit Intelligence Utilities. Look up complete bus timetables, inspect route stop sequences, calculate exact stage fares, and locate nearby bus stops within 1 kilometer. Additionally, real-time weather integration alerts you to heavy rain and suggests resilient alternatives like cabs."*
- **Key Manual Takeaways:**
  - Full BMTC stage fare calculation matrix based on distance slabs.
  - Precipitation monitoring proactively triggers walk/cab advice during transit delays.

### Chapter 12: AI Transit Assistant Chatbot & Production Summary
- **Visuals:** Clicking the floating chatbot icon, entering "How to reach Whitefield from Majestic by bus?", seeing the bot parse the query and offer a 1-tap journey setup.
- **Narrator Audio:**  
  *"In Chapter 12, we conclude with our AI Transit Assistant and Production Architecture. The conversational chatbot understands natural language queries and configures journeys automatically. With zero runtime errors, verified builds, and continuous deployment on Vercel, BengaluruGo is ready to redefine urban mobility across Bengaluru."*
- **Key Manual Takeaways:**
  - Floating NLP assistant parses natural origin, destination, and mode constraints.
  - Fully tested on mobile and desktop viewports with zero syntax or runtime crashes.

---

## 4. Mathematical Formulations & Algorithmic Foundations

### 4.1 Pareto Multi-Objective Optimization
The transit recommendation engine uses Pareto dominance to prune suboptimal routes across multiple conflicting dimensions:
$$\min \left( \text{Cost}, \text{Time}, \text{Transfers}, \text{Carbon} \right)$$

A route $R_A$ dominates route $R_B$ ($R_A \succ R_B$) if and only if:
$$\forall i \in \{\text{Cost}, \text{Time}, \text{Transfers}, \text{Carbon}\}, \quad M_i(R_A) \le M_i(R_B) \quad \land \quad \exists j, \quad M_j(R_A) < M_j(R_B)$$

### 4.2 Composite Multi-Criteria Utility Function
For ranked preferences (Fastest, Cheapest, Comfortable):
$$U(R) = w_{\text{cost}} \cdot S_{\text{cost}}(R) + w_{\text{time}} \cdot S_{\text{time}}(R) + w_{\text{comfort}} \cdot S_{\text{comfort}}(R) + w_{\text{eco}} \cdot S_{\text{eco}}(R)$$
Where:
- **Fastest:** $w_{\text{time}} = 0.60, \quad w_{\text{cost}} = 0.20, \quad w_{\text{comfort}} = 0.10, \quad w_{\text{eco}} = 0.10$
- **Cheapest:** $w_{\text{cost}} = 0.65, \quad w_{\text{time}} = 0.20, \quad w_{\text{comfort}} = 0.05, \quad w_{\text{eco}} = 0.10$
- **Comfortable:** $w_{\text{comfort}} = 0.50, \quad w_{\text{time}} = 0.25, \quad w_{\text{cost}} = 0.15, \quad w_{\text{eco}} = 0.10$

### 4.3 Haversine Great-Circle Proximity Calculation
$$\Delta \sigma = 2 \arcsin \left( \sqrt{ \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right) } \right)$$
$$d = R_{\text{earth}} \cdot \Delta \sigma \quad (R_{\text{earth}} \approx 6371 \text{ km})$$

---

## 5. Operational User Guide & Step-by-Step Instructions

### How to Plan a Multi-Modal Journey:
1. Open the [BengaluruGo Web App](https://unified-comparison-and-personalized-travel-guide-dgjgdvfzy.vercel.app/).
2. On the Home page, click the **"🚀 Plan Journey"** button located beside the dynamic greeting.
3. In the Source field, begin typing your origin stop (e.g., *Silk Board*) and select from the dropdown.
4. In the Destination field, type your target stop (e.g., *Majestic*) and select from the dropdown.
5. Select your priority: **Cheapest (💰)**, **Fastest (⚡)**, or **Comfortable (🎯)**.
6. Review the multi-modal cards: BMTC Bus, Namma Metro, Cab, Auto, Drive, Bike, and Multimodal.

### How to Use Dedicated Mode & "See All Buses":
1. On the comparison results page, click the **BMTC** result card.
2. A dedicated page opens showing only BMTC details: route numbers, fare stages, and guidelines.
3. Click the **"See All Buses"** button to view every alternative bus scheduled along that corridor.
4. Click **"Start Navigation"** to open Ride Mode.

### How to Navigate with 2-Way Ride Mode & Intermediate Boarding:
1. In the Ride Mode modal, verify the source and destination.
2. If traveling in reverse, click the **"⇄ Switch Direction"** button to flip the route to $B \rightarrow A$.
3. If boarding midway along the route, open the **"Boarding Stop"** dropdown and select your current intermediate stop.
4. The stop counter and arrival progress bar recalibrate instantly to track your journey to completion.

### How to View Uploaded Vehicle Documents:
1. On the Home page, click the **"Digital Glovebox"** tile.
2. You will see cards for RC, Insurance, PUC, and Driving License.
3. Click the **"View Document"** button on any uploaded file.
4. The integrated non-blocking document viewer displays the PDF or high-resolution image directly within the app.

---

## 6. API Specification & Backend Contracts

| Endpoint | Method | Description | Request Payload | Response Attributes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/compare` | `POST` | Multi-modal route computation | `{ source, destination, time, preference }` | `{ results: { bus, metro, cab, drive, walk, multimodal }, recommendations }` |
| `/api/stops/suggest` | `GET` | Autocomplete transit stops | `query?q=Silk` | `[ { name, lat, lng, type } ]` |
| `/api/bmtc/route/{no}` | `GET` | Route stop sequence & buses | `path: route_no` | `{ route, stops: [...], buses: [...], frequency }` |
| `/api/user/garage` | `GET` | Retrieve saved vehicles | Headers: Bearer Token | `[ { id, make, model, fuel_type, mileage } ]` |
| `/api/user/documents` | `GET` | Retrieve glovebox documents | Headers: Bearer Token | `[ { id, doc_type, expiry, file_url, mime_type } ]` |
| `/api/weather/alerts` | `GET` | Real-time weather delays | `query?city=bengaluru` | `{ condition, rain_mm, delay_risk, fallback_advice }` |
| `/api/chat/assistant` | `POST` | Natural language bot query | `{ query: "Fastest way to airport" }` | `{ reply, parsed_trip: { src, dst, mode } }` |

---
*Created for the BengaluruGo Unified Multi-Modal Transit Guide Demonstration & Verification.*