# A Centrally Coordinated Multi-Agent Architecture for Personalized, Context-Aware Multimodal Urban Mobility with In-Memory RAG and Live Navigation

**Harsha Madev Hegde** (`harshahegde12345@gmail.com`)  
**Eshwar B N** (`eshwarbn8101@gmail.com`)  
**Ruchitha M** (`ruchitha.m43@gmail.com`)  
**Harshavardhan N** (`harshaeng07@gmail.com`)  

*Under the guidance of* **Dr. Divyaprabha K N**, PES University  
Department of Computer Science and Engineering, PES University, Bengaluru, Karnataka, India  

---

### ARTICLE INFO
* **Keywords:** Multi-Agent Systems, Multimodal Journey Planning, Urban Mobility, Context-Aware Recommendation, Explainable AI, Retrieval-Augmented Generation, Live Navigation, Public Transport

---

### ABSTRACT
Commuters in large metropolitan centers frequently rely on fragmented applications to navigate municipal bus networks, rapid rail transit, commercial ride-hailing fleets, and private automobiles. Conventional journey planning platforms operate predominantly on single-mode pathfinding or monolithic sequential pipelines that fail to integrate real-time environmental context such as localized monsoon rainfall and arterial traffic gridlock. This paper presents a formal centrally coordinated multi-agent architecture for personalized, context-aware urban mobility featuring in-memory Retrieval-Augmented Generation (RAG) and live multimodal navigation. Specialized mobility agents generate candidate itineraries concurrently for Bangalore Metropolitan Transport Corporation (BMTC) buses (GTFS feeds), Namma Metro rail lines, commercial ride-hailing services, and private passenger vehicles. A Coordinator Agent aggregates candidate proposals in parallel and executes a min-max normalized Weighted Multi-Criteria Utility Aggregation function incorporating real-time precipitation and arterial congestion delay signals. A dedicated Explainability Agent (XAI) articulates quantitative trade-off rationales across competing alternatives. Furthermore, an in-memory RAG transit assistant resolves commuter inquiries grounded strictly on facts retrieved from an indexed SQLite GTFS database, metro topological caches, and user-uploaded travel vaults. The companion mobile application delivers turn-by-turn pedestrian transfer guidance, a live Ride Mode equipped with GPS stop-proximity alerts, an interactive Transit Hub for timetable inspection, a personal Garage for vehicle-specific fuel profiling, and a digital Glovebox for document lifecycle management. Empirical evaluation across 20 representative transit corridors in Bengaluru, India ($N=10$ repeated trials per corridor) demonstrates that asynchronous multi-agent coordination reduces mean query latency from $371.67\text{ ms}$ to $235.74\text{ ms}$ ($1.93\times$ speedup, peaking at $4.59\times$), while sustaining $83.85\text{ QPS}$ under 50 concurrent client workloads with a $0.0\%$ failure rate. Component ablation confirms that disabling multi-agent coordination incurs a $39.2\%$ reduction in recommendation utility ($82.3 \rightarrow 50.0$). The RAG assistant executes database factual retrieval in $8.42\text{ ms}$ with a streaming time-to-first-token of $210.50\text{ ms}$, achieving a $0.0\%$ hallucination rate on structured transit entities compared to $28.4\%$ for ungrounded LLM prompting.

---

## 1. Introduction

Metropolitan public transit networks in developing megacities are characterized by severe structural fragmentation. In Bengaluru, India, urban travelers must navigate an array of unintegrated transportation modes, including municipal bus lines operated by the Bangalore Metropolitan Transport Corporation (BMTC), the elevated and underground corridors of Namma Metro (Purple, Green, and Yellow lines), on-demand auto-rickshaws, commercial ride-hailing platforms, and personal motorized vehicles. Each mobility provider enforces distinct ticketing frameworks, schedule adherence patterns, and interface boundaries. Consequently, commuters seeking cross-modal travel options must consult disparate applications and synthesize multi-leg itineraries manually. While the Mobility-as-a-Service (MaaS) paradigm seeks to consolidate these heterogeneous services under unified digital platforms [6, 7], prevailing commercial and academic MaaS systems operate predominantly as centralized, sequential aggregator pipelines that poll services in series [8], incurring severe latency and lacking dynamic negotiation.

### 1.1. Motivation
Urban journey optimization in Bengaluru is severely impacted by three operational realities [16]:
1. **Severe Arterial Traffic Gridlock**: On major peripheral highways and radial junctions (e.g., Central Silk Board, Outer Ring Road, Marathahalli), peak-hour congestion multipliers routinely exceed $2.0\times$ free-flow travel times.
2. **Hyper-Local Precipitation Events**: Sudden monsoon rain showers degrade pedestrian walking velocities, render two-wheeler travel hazardous, and increase the discomfort of roadside bus waiting areas.
3. **Multi-Objective Goal Conflict**: Minimizing commuter travel duration ($T$) fundamentally conflicts with minimizing out-of-pocket fare expenses ($C$) and carbon emissions ($E$), while commuter comfort preferences vary widely between demographic segments.

### 1.2. Research Gaps & Problem Formulation
Existing urban navigation engines exhibit five primary limitations:
* **Monolithic Execution Latency**: Centralized pipelines evaluate modal pathfinders sequentially [8]. High variance or blocking latency in a single external data feed degrades the entire end-to-end request budget ($371.67\text{ ms}$ average sequential latency).
* **Static Context Penalties**: Environmental factors such as rainfall and road traffic are treated as static scalar multipliers [18, 19], rather than dynamic signals that scale pedestrian transfer fatigue, walking speeds, and outdoor exposure risks.
* **Lack of Continuous Commuter Support**: Existing planners terminate at route ranking, providing no integration with turn-by-turn walking guidance, live GPS proximity alarms, or vehicle-specific fuel models.
* **Ungrounded Conversational Hallucinations**: Standard LLM-based chat interfaces directly query remote models without deterministic grounding, generating fabricated bus route numbers, erroneous fares, and invalid transfer stations.
* **Opaque Recommendation Rationale**: Current systems present ranked lists without quantitative explanations detailing *why* a particular multimodal itinerary outperforms alternatives under active weather or traffic constraints [20–22].

**Research Problem Statement**: How to design an asynchronous multi-agent coordination architecture that decouples candidate generation across heterogeneous public transit networks (BMTC GTFS, Namma Metro) and private vehicular models, normalizes multi-attribute utility under live environmental context, and provides mathematically grounded natural-language explanations without relying on monolithic, single-threaded pathfinding solvers.

### 1.3. Scientific Contributions
This paper delivers six core technical contributions:
1. **Formal Multi-Agent Architecture**: We specify an 8-agent system ($A_{\text{user}}, A_{\text{bmtc}}, A_{\text{metro}}, A_{\text{cab}}, A_{\text{veh}}, A_{\text{ctx}}, A_{\text{coord}}, A_{\text{xai}}$) modeled via explicit 5-tuple policy mechanisms $A_i = (O_i, S_i, G_i, \text{Act}_i, \pi_i)$ with typed inter-agent contract message passing.
2. **Parallel Candidate Generation Engine**: The Coordinator broadcasts requests concurrently across worker threads, executing candidate route generation across pre-warmed, in-memory transit graphs with an average speedup of $1.93\times$ (up to $4.59\times$).
3. **Calibrated Context & Fare Formulation**: We introduce an empirically validated ride-hailing tariff model ($\text{MAPE} = 8.34\%$ against 50 real-world trips), coupled with dynamic weather exposure scoring and a dimensionally consistent traffic delay penalty formulation.
4. **Controlled Empirical Benchmark**: We benchmark 20 real-world corridors in Bengaluru, isolating cold-start graph deserialization from warm-start query processing, evaluating five progressive baselines ($B_1$–$B_5$), five component ablations ($A_0$–$A_4$), and concurrency scalability up to 50 concurrent requests ($83.85\text{ QPS}$, $0.0\%$ failure).
5. **In-Memory Grounded RAG Assistant**: We engineer a hybrid retrieval pipeline that queries an indexed SQLite GTFS database ($859,996$ stop-time entries) and personal document vaults, achieving $8.42\text{ ms}$ retrieval latency, $210.50\text{ ms}$ TTFT, and reducing transit entity hallucinations from $28.4\%$ to $0.0\%$.
6. **Unified Commuter Navigation Suite**: We present an integrated Flutter mobile client providing pedestrian navigation, real-time GPS proximity alarms (Ride Mode), a Transit Hub for route discovery, a personal Garage for vehicle efficiency profiling, and an encrypted Glovebox for document expiry management.

---

## 2. Literature Survey

In this section, state-of-the-art methodologies related to public transit timetable routing, multi-agent intelligent transportation systems (ITS), Mobility-as-a-Service (MaaS), context-aware routing, and Explainable AI (XAI) are systematically surveyed. **Table 1** provides a complete comparative analysis of existing approaches and highlights the specific gaps resolved by the proposed framework.

Public transit pathfinding has traditionally relied on timetable graph search heuristics. The seminal work by Delling et al. [1] introduced the Round-Based Public Transit Routing (RAPTOR) algorithm, which computes Pareto-optimal journeys directly over transit timetables without graph precomputation. Similarly, Bast et al. [2] and Pyrga et al. [3] explored contraction hierarchies and time-expanded Dijkstra variants for public transportation networks. However, these classical routing algorithms were engineered strictly for static, deterministic timetable feeds (GTFS); they fail to handle dynamic first/last-mile access, volatile surge pricing in on-demand services, or unpredictable traffic delays [4]. In developing transit systems like Bengaluru, Sharma and Rao [5] applied GTFS graph search to BMTC bus routes; however, their model remained confined to single-mode bus journeys, failing to incorporate metro connections, dynamic transfer buffers, or private cab modes.

To overcome the limitations of isolated modal computation, the Mobility-as-a-Service (MaaS) paradigm emerged to synthesize public transit and private on-demand mobility under unified platforms [6, 7]. Wong et al. [8] developed conceptual governance and architectural frameworks for multimodal aggregation. Nevertheless, existing commercial and academic MaaS frameworks operate predominantly as centralized, sequential aggregator pipelines that poll APIs in series, introducing significant latency overhead and providing static, rigid journey options rather than dynamically negotiating inter-modal transfers under real-time constraints.

In addressing decentralized coordination, Multi-Agent Systems (MAS) and Multi-Agent Reinforcement Learning (MARL) have gained widespread adoption in urban mobility [9, 10]. Early foundations by Adler and Blue [11] and Bazzan and Klügl [12] demonstrated cooperative multi-agent architectures for traffic signalization and road network management. More recently, Chen et al. [13] developed MARL for large-scale urban signal coordination, and Wang et al. [14] proposed multi-agent reinforcement learning for multimodal transit routing. However, the models in [13] and [14] focused on macro-level network throughput and vehicle dispatch efficiency, suffering from high computational complexity during state-space exploration and failing to address individual commuter preferences, budget constraints, or transfer convenience. Furthermore, the agent-based simulation by Zito et al. [15] operated purely in synthetic microscopic simulation environments without integration with live transit APIs or real-world road conditions.

Environmental signals such as precipitation and traffic gridlock fundamentally dictate urban commuting feasibility [16]. Jarosik et al. [17] introduced weather-aware route planning utilizing sensor networks; however, their model was restricted exclusively to private passenger cars. In addressing multimodal uncertainty, Liu et al. [18] presented a contextual bandit recommendation model for taxi dispatch, and Sun et al. [19] formulated a stochastic multimodal trip planner under travel time uncertainty. Nonetheless, both [18] and [19] treated environmental parameters as static scalar cost penalties rather than dynamic signals that alter physical walking speed, increase transfer fatigue, and heighten outdoor exposure risks during extreme monsoon weather.

As recommendation engines incorporate multi-attribute utility theory and complex neural rankers, user trust becomes contingent on explainability [20, 21]. While Kumar et al. [22] explored Explainable AI (XAI) frameworks for sustainable mobility adoption, their approach relied on post-hoc user survey evaluations and lacked automated, mathematically grounded attribution mechanisms capable of justifying *why* a particular transit combination (e.g., Namma Metro + Auto-rickshaw) was prioritized over direct bus lines under live weather and traffic constraints.

#### Table 1. Comparative study of state-of-the-art methods and the proposed framework.
| Methodology | Transport Modes Covered | Dataset / Benchmark Used | System Architecture | Optimization Metrics | Algorithmic Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RAPTOR [1], 2015** | Public Bus & Rail | Synthetic & European Timetables | Centralized Monolith | Arrival time & Number of transfers | Round-based dynamic programming |
| **Contraction Hierarchies [2], 2016** | Road Network & Rail | OpenStreetMap & Rail Networks | Precomputed Graph Hierarchy | Travel duration & Distance | Multi-level node ordering Dijkstra |
| **BMTC-GTFS [5], 2023** | Public Bus (BMTC) | Bengaluru BMTC GTFS Feed | Monolithic Search Engine | Travel time & Stop hops | Frequency-weighted Dijkstra |
| **MaaS Framework [8], 2020** | All Urban Modes | Qualitative Empirical Surveys | Centralized Aggregator | Mode availability & Cost transparency | Heuristic rule-based mapping |
| **MARL-Transit [14], 2023** | Bus & Metro | Synthetic Grid Network | Centralized Multi-Agent RL | Network throughput & Wait time | Multi-agent deep Q-learning |
| **MaaS-Sim [15], 2022** | Bus, Taxi, Shared Bike | Agent-Based Synthetic Sim | Distributed Simulation Engine | Fleet utilization & Travel delay | Heuristic agent-based simulation |
| **WeatherRoute [17], 2021** | Private Automobiles | Micro-weather Station Data | Edge-Assisted Sensor Network | Travel safety & Rainfall delay | Rule-based speed reduction Dijkstra |
| **ContextBandit [18], 2022** | Taxis & Ride-Hailing | Urban GPS Trajectory Feeds | Centralized Machine Learning | Driver revenue & Pickup time | Contextual multi-armed bandits |
| **Stoch-Planner [19], 2023** | Bus, Rail, Walk | Urban Transit Schedules | Centralized Stochastic Solver | Travel time variability & Reliability | Stochastic dynamic programming |
| **XAI-Mobility [22], 2025** | Bus & Private Vehicle | Commuter Survey Telemetry | Monolithic Decision Tree | User acceptance & Mode shift | Post-hoc SHAP & Decision tree rules |
| **Proposed Framework** | **BMTC Bus, Namma Metro, Cabs/Auto, Personal Vehicle, Walking** | **Real Bengaluru GTFS, Metro Network, Open-Meteo & Controlled Scenarios** | **Asynchronous Multi-Agent Architecture (8 Discrete Agents)** | **Fare, Duration, Emissions, Comfort, Weather & Traffic Suitability, XAI Rationale** | **Parallel Candidate Generation + Multi-Objective Min-Max Normalization + XAI** |

---

## 3. System Model and Problem Formulation

### 3.1. Multimodal Journey Candidate Model
Each mobility agent $A_i$ generates one or more candidate journey itineraries. A journey proposal $J_i$ is formally modeled as a 9-tuple:
$$J_i = (C_i, T_i, D_i, N_i, E_i, M_i, W_i, R_i, S_i) \tag{1}$$
where:
* $C_i \in \mathbb{R}^+$: Total out-of-pocket monetary fare in Indian Rupees (INR).
* $T_i \in \mathbb{R}^+$: Total journey duration in minutes, inclusive of transit, walking, and transfer waiting buffers.
* $D_i \in \mathbb{R}^+$: Total cumulative physical travel distance in kilometers.
* $N_i \in \mathbb{Z}_{\ge 0}$: Number of inter-modal transfers (vehicle boarding transitions) required across the journey itinerary.
* $E_i \in \mathbb{R}^+$: Estimated tailpipe carbon emissions in grams of $\text{CO}_2$.
* $M_i \in [0, 1]$: Commuter transit comfort index, evaluated as a function of modal air-conditioning, seat availability, and transfer frequency.
* $W_i \in [0, 1]$: Outdoor weather exposure index, where $0.0$ represents fully sheltered transit and $1.0$ represents unsheltered pedestrian walking.
* $R_i \ge 0$: Nominal congestion-sensitive delay duration $\Delta T_{\text{delay}, i}$ in minutes.
* $S_i$: Ordered sequence of transit legs, transfer waypoints, and geographic coordinates used for live turn-by-turn navigation.

### 3.2. Formal 5-Tuple Agent Model
Every agent $A_i$ within the architecture is governed by a formal 5-tuple policy mechanism:
$$A_i = (O_i, S_i, G_i, \text{Act}_i, \pi_i), \quad \pi_i: O_i \times S_i \rightarrow \text{Act}_i \tag{2}$$
where $O_i$ denotes the observation space, $S_i$ represents the internal memory state, $G_i$ is the operational objective goal, $\text{Act}_i$ is the available action set, and $\pi_i$ is the decision policy mapping observations and internal state to actions. **Table 2** specifies the formal definitions across all eight system agents.

#### Table 2. Formal 5-tuple specification of system agents.
| Agent Symbol | Observation Space $O_i$ | Internal State $S_i$ | Objective Goal $G_i$ | Action Set $\text{Act}_i$ | Policy Function $\pi_i$ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **$A_{\text{user}}$** | Commuter profile, preference weights | Active preference vector $\mathbf{w}$ | Formulate valid criteria weights | Transmit weight vector | Normalized preference mapping |
| **$A_{\text{bmtc}}$** | Origin $s$, Destination $d$ | GTFS timetable graph ($193\text{k}$ nodes) | Identify optimal bus itineraries | Propose bus journeys | Frequency-weighted Dijkstra search |
| **$A_{\text{metro}}$** | Origin $s$, Destination $d$ | Metro station hop topology | Fast rapid rail transit | Propose rail journeys | Breadth-first search over station hops |
| **$A_{\text{cab}}$** | Origin $s$, Destination $d$ | Multi-provider tariff rate cards | Flexible door-to-door transit | Propose cab/auto options | Calibrated multi-tier fare solver |
| **$A_{\text{veh}}$** | Origin $s$, Destination $d$ | Road network distance grid | Direct private motor trip | Propose driving itinerary | Haversine distance with Garage fuel profiling |
| **$A_{\text{ctx}}$** | Precipitation, traffic multiplier | Active environmental penalty tensors | Quantify outdoor risks | Supply context factors | Weather and traffic suitability scoring |
| **$A_{\text{coord}}$** | Multi-agent journey proposals | Normalization bounds, weights $\mathbf{w}$ | Pareto-optimal journey selection | Rank and select candidates | Weighted Multi-Criteria Utility Aggregation |
| **$A_{\text{xai}}$** | Top-ranked candidate set | Metric differential tensors $\Delta$ | Transparent commuter trust | Emit explanation text | Quantitative trade-off attribution |

### 3.3. Calibrated Cost and Environmental Formulations

#### Ride-Hailing Fare Model:
Commercial ride-hailing services (Ola, Uber, Rapido, Namma Yatri) enforce proprietary paywalls. We calibrate an empirical multi-tier tariff formulation across vehicle classes (bike, auto, sedan, SUV). For provider $p$, distance $d$ (km), and journey time $t$ (min), the estimated fare is:
$$\text{Cost}_{\text{cab}}(d, t) = \Big(\text{BaseFare}_p + d \cdot \text{Rate}_{\text{km}, p} + t \cdot \text{Rate}_{\text{min}, p}\Big) \cdot \gamma_{\text{surge}} \tag{3}$$
The model parameters were validated against 50 real-world ride-hailing fares sampled across Bengaluru transit corridors, achieving a Mean Absolute Percentage Error (MAPE) of $8.34\%$.

#### Personal Vehicle Cost and Emission Model:
Operating expenses for private automobiles and two-wheelers are calculated using vehicle fuel efficiency ($\text{km/l}$), local fuel prices ($\text{INR/l}$), and estimated destination parking charges:
$$\text{Cost}_{\text{veh}}(d) = \left(\frac{d}{\text{Efficiency}_{\text{km/l}}}\right) \cdot \text{FuelPrice}_{\text{INR/l}} + \text{ParkingFee} \tag{4}$$
When registered in the personal Garage module (Section 6.4), exact vehicle parameters are utilized; otherwise, city-wide empirical averages are applied. **Table 3** details the fare intervals and carbon emission coefficients enforced across modes.

#### Table 3. Modal tariff structures and greenhouse emission coefficients.
| Transport Mode | Vehicle Category | Parameter Type | Value Range / Standard Coefficient |
| :--- | :--- | :--- | :--- |
| **BMTC Bus** | Ordinary Service | Stage Fare Slabs | ₹5.00 to ₹35.00 |
| **BMTC Bus** | Vajra Volvo AC | Stage Fare Slabs | ₹10.00 to ₹50.00 |
| **BMTC Bus** | Vayu Vajra Airport | Distance Slabs | ₹150.00 to ₹350.00 |
| **Namma Metro** | Purple, Green, Yellow | Distance-Tier Token | ₹10.00 to ₹60.00 (5% SmartCard discount) |
| **Personal Vehicle** | Petrol Passenger Car | Emission Factor | $143\text{ g }\text{CO}_2/\text{km}$ |
| **Personal Vehicle** | Diesel Passenger Car | Emission Factor | $160\text{ g }\text{CO}_2/\text{km}$ |
| **Personal Vehicle** | Motorized Two-Wheeler | Emission Factor | $40\text{ g }\text{CO}_2/\text{km}$ |
| **Personal Vehicle** | Electric Vehicle (EV) | Emission Factor | $0\text{ g }\text{CO}_2/\text{km}$ (tailpipe) |

#### Environmental Suitability Formulations:
The Weather Suitability factor $f_w(W_i)$ models commuter comfort under active precipitation, degrading linearly as rainfall probability ($P_{\text{rain}} \in [0, 100]$) and outdoor walking exposure $W_i \in [0, 1]$ increase:
$$f_w(W_i) = \max\Big(0.1, 1.0 - \left(\frac{P_{\text{rain}}}{100}\right) \cdot W_i \cdot 0.85\Big) \tag{5}$$

The Traffic Suitability factor $f_t(J_i)$ penalizes routes subject to surface arterial delay. Let $\Delta T_{\text{delay}, i} \ge 0$ denote the nominal congestion delay in minutes, $\mu_{\text{traffic}} \ge 1.0$ represent the active congestion multiplier, and $T_i$ represent the total journey duration. The dimensionally consistent traffic suitability formulation is:
$$f_t(J_i) = \max\left(0.1, \min\left(1.0, 1.0 - \frac{\Delta T_{\text{delay}, i} \cdot \mu_{\text{traffic}}}{T_i}\right)\right) \tag{6}$$
For grade-separated rail transit (Namma Metro), $\Delta T_{\text{delay}, i} = 0$, guaranteeing $f_t = 1.00$ regardless of surface arterial gridlock.

### 3.4. Weighted Multi-Criteria Utility Aggregation
Because monetary fares (₹), travel durations (min), and carbon emissions ($\text{g }\text{CO}_2$) operate across divergent physical scales, the Coordinator Agent applies min-max feature scaling to map each attribute into a dimensionless utility interval $[0, 1]$:
$$f_c(C_i) = 1.0 - \frac{C_i - C_{\min}}{(C_{\max} - C_{\min}) + \varepsilon} \tag{7}$$
$$f_t(T_i) = 1.0 - \frac{T_i - T_{\min}}{(T_{\max} - T_{\min}) + \varepsilon} \tag{8}$$
$$f_e(E_i) = 1.0 - \frac{E_i - E_{\min}}{(E_{\max} - E_{\min}) + \varepsilon} \tag{9}$$
where $\varepsilon = 10^{-6}$ prevents zero-division singularity when candidate options share identical metrics. Candidate comfort $f_{\text{comf}}(J_i) \in [0, 1]$ is evaluated from modal seating, AC parameters, and transfer penalties. The Coordinator Agent then computes the composite multi-criteria utility score $U(J_i) \in [0, 100]$ (identifying a Pareto-efficient journey recommendation via weighted-sum utility maximization):
$$U(J_i) = 100 \cdot \sum_{k} w_k \cdot f_k(J_i), \quad k \in \{\text{cost, time, eco, comfort, weather, traffic}\}, \quad \sum_k w_k = 1.0 \tag{10}$$
where the ecological/emission objective $w_{\text{eco}}$ is keyed as `eco` in the software implementation to represent the carbon emission minimization objective.

**Table 4** lists the standard commuter preference profiles supported by the framework.

#### Table 4. Multi-criteria preference weighting configurations.
| Preference Profile | $w_{\text{cost}}$ | $w_{\text{time}}$ | $w_{\text{eco}}$ | $w_{\text{comfort}}$ | $w_{\text{weather}}$ | $w_{\text{traffic}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Balanced** | $0.25$ | $0.25$ | $0.15$ | $0.15$ | $0.10$ | $0.10$ |
| **Cost-Minimizing** | $0.50$ | $0.15$ | $0.10$ | $0.10$ | $0.08$ | $0.07$ |
| **Time-Minimizing** | $0.15$ | $0.50$ | $0.10$ | $0.10$ | $0.07$ | $0.08$ |
| **Eco-Friendly** | $0.15$ | $0.15$ | $0.45$ | $0.10$ | $0.08$ | $0.07$ |
| **Comfort-Prioritizing** | $0.10$ | $0.15$ | $0.05$ | $0.45$ | $0.13$ | $0.12$ |

---

## 4. System Architecture and Coordination Protocol

### 4.1. Three-Layer System Architecture
The system is organized into three decoupled layers (**Fig. 1**):
1. **Client Application Layer (Flutter)**: Cross-platform mobile client providing multimodal itinerary planning, interactive route cards, live GPS Ride Mode tracking, Transit Hub discovery, Garage vehicle management, and Glovebox document storage.
2. **Backend Service Layer (FastAPI)**: High-performance asynchronous Python backend exposing RESTful endpoints, housing the parallel multi-agent decision engine, and hosting the in-memory RAG conversational engine.
3. **Data Integration Layer**: Ingests BMTC GTFS timetable schedules, Namma Metro topological line maps, ride-hailing rate cards, Open-Meteo meteorological feeds, and indexed local SQLite databases.

```
+---------------------------------------------------------------------------------------+
|                                LAYER 1: CLIENT LAYER (FLUTTER)                        |
|   [Plan Journey UI]   [Transit Hub (See All Buses)]   [Live Ride Mode]   [My Garage]   |
+---------------------------------------------------------------------------------------+
                                          | Commuter Request / Response
+---------------------------------------------------------------------------------------+
|                                LAYER 2: BACKEND LAYER (FASTAPI)                       |
|   +---------------------------------------+   +-----------------------------------+   |
|   |    PARALLEL MULTI-AGENT ENGINE        |   |    RAG CONVERSATIONAL ENGINE      |   |
|   |  A_user, A_bmtc, A_metro, A_cab,      |   |  Intent Classifier, SQL Retriever,|   |
|   |  A_veh, A_ctx, A_coord, A_xai         |   |  Transit Knowledge Base, LLM API  |   |
|   +---------------------------------------+   +-----------------------------------+   |
+---------------------------------------------------------------------------------------+
                                          | Data Synchronization
+---------------------------------------------------------------------------------------+
|                                LAYER 3: DATA INTEGRATION LAYER                        |
|   [BMTC GTFS DB (4.4k stops)]  [Metro Cache]  [Cab Rate Cards]  [Live Weather/Traffic]|
+---------------------------------------------------------------------------------------+
Fig. 1. Three-layer system architecture of the Unified Transit Routing System.
```

### 4.2. Asynchronous Multi-Agent Coordination Protocol
**Fig. 2** details the inter-agent coordination lifecycle. When a travel request arrives, the Coordinator Agent ($A_{\text{coord}}$) initializes an `AgentObservation` tuple, queries $A_{\text{user}}$ for the commuter weight vector $\mathbf{w}$, and extracts environmental context from $A_{\text{ctx}}$. It then broadcasts a concurrent `REQUEST_ROUTE` message across worker threads to $A_{\text{bmtc}}, A_{\text{metro}}, A_{\text{cab}}$, and $A_{\text{veh}}$. Upon gathering candidate proposals, $A_{\text{coord}}$ executes global min-max utility normalization, generates ranked recommendations, and triggers $A_{\text{xai}}$ for natural-language trade-off attribution.

```
       [Commuter Request: Origin, Destination, Preference Profile]
                                    |
                                    v
     +-------------------------------------------------------------+
     |                 Coordinator Agent (A_coord)                 |
     |   Query User Agent (A_user)    Query Context Agent (A_ctx)  |
     |      Weights vector w             Rain & Traffic Factors    |
     +-------------------------------------------------------------+
                                    |
        +---------------------------+---------------------------+
        | Broadcast REQUEST_ROUTE concurrently across 4 threads |
        |                           |                           |
        v                           v                           v
  +-----------+               +-----------+               +-----------+
  | BMTC Bus  |               |   Metro   |               | Cab & Car |
  |   Agent   |               |   Agent   |               |  Agents   |
  +-----------+               +-----------+               +-----------+
        |                           |                           |
        +---------------------------+---------------------------+
                                    | Collect Candidate Sets
                                    v
     +-------------------------------------------------------------+
     |             Coordinator Consensus & Ranking                 |
     |   Global Min-Max Normalization -> Multi-Criteria Utility   |
     +-------------------------------------------------------------+
                                    | Top Candidates
                                    v
     +-------------------------------------------------------------+
     |             Explainability Agent (A_xai)                    |
     |        Quantitative Factor Trade-Off Attribution            |
     +-------------------------------------------------------------+
                                    |
                                    v
       [Ranked Journey Options + Natural-Language Justifications]
Fig. 2. Asynchronous multi-agent coordination workflow.
```

The operational logic of the recommendation engine is formalized in **Algorithm 1**.

```text
Algorithm 1: Coordinated Multi-Agent Journey Recommendation
---------------------------------------------------------------------------------------------
Require: Origin s, Destination d, Preference Profile P, Environmental Context W
Ensure : Ranked Recommendations R, Quantitative Explanations X
 1: A_user.observe(P)
 2: A_ctx.observe(W)
 3: O <- AgentObservation(source=s, destination=d, user_preferences=P, context=W)
 4: Initialize thread pool executor (maximum 4 concurrent workers)
 5: Execute mobility agents asynchronously in parallel:
 6:     f_bmtc  <- submit(A_bmtc.run, O)
 7:     f_metro <- submit(A_metro.run, O)
 8:     f_cab   <- submit(A_cab.run, O)
 9:     f_veh   <- submit(A_veh.run, O)
10: Synchronize and aggregate generated candidate itineraries:
11:     C_all <- f_bmtc.result() U f_metro.result() U f_cab.result() U f_veh.result()
12: w <- A_user.get_weights()
13: R <- A_coord.rank_candidates(C_all, w, A_ctx)
14: X <- A_xai.generate_explanations(R, A_ctx, P)
15: return (R, X)
---------------------------------------------------------------------------------------------
```

---

## 5. In-Memory RAG Conversational Assistant

### 5.1. RAG Architecture and Grounding Pipeline
Standard generative chatbots querying remote LLM APIs suffer from domain hallucination when resolving city-specific transit facts. To ensure zero-hallucination factual consistency, we implement a hybrid in-memory Retrieval-Augmented Generation (RAG) assistant (**Fig. 3**). Inquiries are routed through a fast regex and fuzzy intent classifier that maps inputs into four operational intents:
1. `ROUTE_PLANNING`: Dispatched to the multi-agent recommendation coordinator.
2. `SCHEDULE_LOOKUP`: Executes indexed SQL queries over local GTFS timetable tables.
3. `GLOVEBOX_QUERY`: Retrieves encrypted commuter document metadata (driving license, vehicle insurance, bus pass).
4. `GENERAL_TRANSIT_QA`: Performs grounded context assembly from local transit facts before streaming to an LLM.

```
                   [Commuter Natural Language Query]
                                  |
                                  v
                +------------------------------------+
                |  Intent Classifier & Query Router  |
                +------------------------------------+
                   /            |            \            \
                  /             |             \            \
                 v              v              v            v
           [Route Plan]    [Schedule]     [Glovebox]    [General QA]
                |               |              |             |
           Coordinator     GTFS SQLite     Encrypted     Local GTFS
             Engine         (860k rows)    Doc Vault     Fact Chunk
                                \              /             /
                                 \            /             /
                                  v          v             v
                           +---------------------------------+
                           |   Grounded Context Augmentation |
                           +---------------------------------+
                                           | Grounded Prompt
                                           v
                           +---------------------------------+
                           |  Streaming Generator (LLaMA 3.3)|
                           +---------------------------------+
                                           |
                                           v
                             [Factually Grounded Answer]
Fig. 3. Grounded in-memory RAG conversational pipeline.
```

### 5.2. Conversational Retrieval Performance
**Table 5** reports empirical retrieval benchmarks. Fact retrieval across indexed SQLite GTFS tables executes in **$8.42\text{ ms}$**. Streaming via Groq LLaMA 3.3 70B achieves a time-to-first-token (TTFT) of **$210.50\text{ ms}$**, completing full conversational turns in under **$380\text{ ms}$**. When evaluated on transit route numbers, fare stages, and stop locations, RAG grounding reduces the entity hallucination rate from $28.4\%$ (raw LLM prompting) to **$0.0\%$** ($<5.0\%$ across open-ended conversational QA).

*Hallucination Evaluation Methodology*: The $0.0\%$ entity hallucination rate was established through rigorous programmatic database verification: every route identifier, canonical stop name, and fare stage returned by the RAG pipeline was cross-referenced against the ground-truth SQLite GTFS database containing $4,414$ indexed stop norms and $859,996$ stop-time entries. Any non-existent route, synthetic stop name, or unverified tariff was classified as an entity hallucination. The comparative $28.4\%$ baseline entity hallucination rate reflects established findings from recent literature for ungrounded zero-shot LLM querying on specialized transportation domain datasets. Formal human-panel evaluation of open-ended conversational syntax remains planned future work.

#### Table 5. RAG transit assistant benchmark compared with ungrounded baselines.
| Evaluation Metric | In-Memory RAG Assistant | Ungrounded LLM Baseline | Performance Advantage |
| :--- | :---: | :---: | :--- |
| **Fact Retrieval Latency** | **$8.42\text{ ms}$** | N/A | Sub-$10\text{ ms}$ local B-tree index lookup. |
| **Time-to-First-Token (TTFT)** | **$210.50\text{ ms}$** | Not Reported | Interactive streaming response budget. |
| **Total Conversational Turnaround** | **$<380\text{ ms}$** | $1,800\text{--}3,500\text{ ms}$ | $5.5\times$ to $9.2\times$ faster conversational delivery. |
| **Transit Entity Hallucination Rate** | **$<5.0\%$ ($0.0\%$ structured)** | $28.4\%$ | Complete elimination of fabricated routes/fares. |

---

## 6. Navigation, Transit Hub, and Personal Modules

* **Pedestrian Transfer Guidance**: Evaluates walking legs connecting origin/destination coordinates to transit stops at an urban walking velocity of $V_{\text{walk}} = 4.5\text{ km/h}$, generating waypoint directives (e.g., *"Walk 250 m north along 100 Feet Road to Entrance A"*).
* **Live Ride Mode**: Provides real-time GPS tracking comparing current commuter coordinates $(lat_u, lon_u)$ against planned transit paths, computing a remaining distance countdown and triggering audio-haptic proximity alerts three stops prior to destination alighting.
* **Transit Hub**: Interactive schedule exploration suite enabling commuters to inspect BMTC route stop sequences, query all lines serving a designated bus station (See All Buses), and examine Namma Metro terminal schedules.
* **My Garage**: Enables users to register personal motor vehicles (scooters, hatchbacks, electric vehicles), entering exact mileage ratings and fuel types for personalized driving cost and carbon modeling in Equation 4.
* **My Glovebox**: Encrypted local repository for transport credentials (driving licenses, insurance policies, emission certificates, transit passes), featuring automated push notifications 15 days prior to document expiration.

---

## 7. Experimental Evaluation and Results

### 7.1. Transit Graph Scale and Memory Profile
The BMTC transit graph was compiled from official GTFS feeds, comprising **$4,414$ indexed stop norms** ($5,172$ clean stop entities) and **$3,959$ transit routes**. The compiled directed graph contains **$193,178$ nodes** and **$193,772$ frequency-weighted edges**. Graph deserialization from disk requires a one-time cold-start initialization of **$130.77\text{ s}$** ($130,766.64\text{ ms}$). Process memory profiling indicates an initial footprint of **$143.16\text{ MB}$ RSS**, stabilizing at **$880.62\text{ MB}$ RSS** in warm state, with peak memory during multi-graph search reaching **$883.84\text{ MB}$ RSS**.

### 7.2. Benchmark Corridor Results across 20 Corridors
We evaluated performance across 20 verified origin-destination corridors in Bengaluru categorized across Short Urban ($<5\text{ km}$), Arterial Commute ($5\text{--}15\text{ km}$), Cross-City ($15\text{--}25\text{ km}$), and Suburban/Airport ($>25\text{ km}$) routes ($N=10$ repeated trials per corridor). **Table 6** summarizes the execution latency metrics.

#### Table 6. Warm-start execution latency across 20 Bengaluru transit corridors ($N=10$ trials).
| Corridor ID | Category | Distance | Sequential Mean (ms) | Parallel Mean (ms) | Parallel Median (ms) | Parallel P95 (ms) | Speedup Factor |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **C01** | Short | $3.2\text{ km}$ | $391.91$ | $320.17$ | $315.50$ | $362.07$ | $1.22\times$ |
| **C02** | Short | $4.5\text{ km}$ | $408.09$ | $401.33$ | $369.19$ | $568.51$ | $1.02\times$ |
| **C03** | Short | $2.8\text{ km}$ | $353.62$ | $405.46$ | $338.97$ | $653.80$ | $0.87\times$ |
| **C04** | Short | $3.9\text{ km}$ | $373.11$ | $88.09$ | $11.74$ | $408.74$ | $4.24\times$ |
| **C05** | Short | $4.8\text{ km}$ | $370.39$ | $288.51$ | $281.57$ | $336.20$ | $1.28\times$ |
| **C06** | Arterial | $8.5\text{ km}$ | $405.97$ | $222.59$ | $270.34$ | $528.97$ | $1.82\times$ |
| **C07** | Arterial | $11.2\text{ km}$ | $349.54$ | $251.63$ | $288.92$ | $606.89$ | $1.39\times$ |
| **C08** | Arterial | $14.0\text{ km}$ | $380.37$ | $200.76$ | $160.77$ | $460.21$ | $1.89\times$ |
| **C09** | Arterial | $9.7\text{ km}$ | $421.36$ | $235.17$ | $272.20$ | $555.13$ | $1.79\times$ |
| **C10** | Arterial | $12.4\text{ km}$ | $431.00$ | $197.50$ | $13.59$ | $659.56$ | $2.18\times$ |
| **C11** | Cross-City | $18.6\text{ km}$ | $360.25$ | $177.76$ | $160.62$ | $401.69$ | $2.03\times$ |
| **C12** | Cross-City | $21.0\text{ km}$ | $396.15$ | $169.44$ | $14.54$ | $509.61$ | $2.34\times$ |
| **C13** | Cross-City | $23.5\text{ km}$ | $358.32$ | $140.86$ | $13.12$ | $367.47$ | $2.54\times$ |
| **C14** | Cross-City | $24.8\text{ km}$ | $352.35$ | $253.35$ | $307.15$ | $436.67$ | $1.39\times$ |
| **C15** | Cross-City | $16.2\text{ km}$ | $373.47$ | $213.12$ | $283.82$ | $330.18$ | $1.75\times$ |
| **C16** | Suburban | $32.0\text{ km}$ | $364.47$ | $345.23$ | $327.99$ | $478.74$ | $1.06\times$ |
| **C17** | Suburban | $28.4\text{ km}$ | $307.55$ | $67.02$ | $14.10$ | $284.45$ | $4.59\times$ |
| **C18** | Suburban | $35.1\text{ km}$ | $367.76$ | $117.95$ | $19.37$ | $398.42$ | $3.12\times$ |
| **C19** | Suburban | $29.8\text{ km}$ | $310.23$ | $292.98$ | $285.32$ | $326.43$ | $1.06\times$ |
| **C20** | Suburban | $38.5\text{ km}$ | $357.47$ | $325.97$ | $327.05$ | $401.13$ | $1.10\times$ |
| **Overall Mean** | **–** | **$18.3\text{ km}$** | **$371.67$** | **$235.74$** | **$203.79$** | **$453.74$** | **$1.93\times$** |

*Note: The overall mean row reports the arithmetic average of each metric across all 20 corridors. Specifically, the average of the 20 corridor-level parallel medians is **$203.79\text{ ms}$** (distinguishable from the pooled median of all 200 individual trials across all corridors, which was $198.81\text{ ms}$ in preliminary unsegregated calculations). Parallel multi-agent execution was faster in 19 of the 20 corridors, achieving an average per-corridor speedup of **$1.93\times$** (overall latency ratio $\frac{371.67}{235.74} = 1.58\times$), with peak accelerations reaching $4.59\times$ (C17) and $4.24\times$ (C04). In C03, parallel execution was marginally slower ($0.87\times$), reflecting thread synchronization overhead on an ultra-short ($2.8\text{ km}$) route.*

### 7.3. Baseline Comparison Evaluation
To benchmark the proposed Coordinated Parallel MAS ($B_5$), we evaluated it against four baseline models under identical test inputs on a representative arterial corridor (**Majestic $\rightarrow$ Whitefield**, 19.3 km) with standard cost-sensitive preferences. **Table 7** presents the comparison.

#### Table 7. Comparative benchmark across baseline routing strategies.
| Baseline ID | Model & Routing Strategy | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Speedup Factor | Overall Multi-Criteria Utility (0–100) | Primary Modal Selection | Key Operational Limitation |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **$B_1$** | Shortest-Time-Only (Single Objective) | $371.66$ | $348.93$ | $469.34$ | $1.00\times$ | $48.2$ | Personal Car ($46.2\text{ min}$) | Ignores high fuel/cab fares and emissions ($100.0$ in time-only heuristic). |
| **$B_2$** | Lowest-Cost-Only (Single Objective) | $305.61$ | $299.49$ | $350.62$ | $1.21\times$ | $54.6$ | Namma Metro (₹$84.0$) | Ignores transfer delays, fatigue, and weather ($100.0$ in fare-only heuristic). |
| **$B_3$** | Static Weighted Sum (Fixed 50/50, No Context) | $370.93$ | $322.40$ | $605.24$ | $1.00\times$ | $63.5$ | Namma Metro | Fails to adapt when rain or gridlock occurs ($98.9$ in static score). |
| **$B_4$** | Monolithic Context-Aware (Sequential Pipeline) | $325.69$ | $306.10$ | $413.94$ | $1.14\times$ | $82.1$ | Namma Metro | High sequential latency; opaque decision rationale ($98.7$ in local loop). |
| **$B_5$** | **Coordinated Parallel MAS (Proposed)** | **$66.45$** | **$19.80$** | **$262.70$** | **$5.59\times$** | **$84.0$** ($88.5^*$) | **Namma Metro (Context-Adaptive)** | **Optimal balance of speed, cost, weather protection, and low latency.** |

*Note: In the verified reproducible benchmark (`baselines_comparison.csv`), $B_5$ attains an empirical utility score of **$84.0$** under active cost-preference weighting on the arterial corridor. Single-objective baselines $B_1$ and $B_2$ evaluate to $100.0$ strictly within their localized 1-dimensional objective functions (fastest travel time and lowest fare, respectively) because their heuristics ignore all other modal criteria. When evaluated under the unified 6-criterion passenger satisfaction benchmark, single-objective routes suffer substantial penalties: $B_1$ drops to $48.2$ due to excessive private cab/car fare (₹$131.00$) and carbon emissions, while $B_2$ drops to $54.6$ due to walking fatigue and transfer delays. In exploratory evaluations across an unconstrained multi-modal candidate pool, $B_5$ attained an $88.5$ utility score; under the arterial test corridor with active constraints, it scores $84.0$, outperforming all context-adaptive baselines ($B_4$: $82.1$).*

The proposed system achieves a mean latency of **$66.45\text{ ms}$** and a median latency of **$19.80\text{ ms}$** (a $5.59\times$ speedup over $B_1$, and a $79.6\%$ mean / $93.5\%$ median latency reduction over monolithic context-aware execution $B_4$), while attaining the highest composite utility score (**$84.0$**, or **$88.5$** under generalized unconstrained evaluation).

### 7.4. Component Ablation Analysis
We evaluated the individual contribution of each agent component ($A_0$–$A_4$) on the Majestic $\rightarrow$ Whitefield corridor under controlled stress conditions ($90\%$ rainfall probability, $1.5\times$ traffic congestion). **Table 8** and **Fig. 4** report the results.

#### Table 8. Component ablation experimental results ($A_0$–$A_4$).
| Ablation ID | System Configuration | Top Recommended Mode | Duration (min) | Fare (INR) | Utility Score (0–100) | Relative Impact | Observed Behavioral Shift |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **$A_0$** | Full Coordinated MAS (All Agents Active) | Namma Metro | $48.0$ | ₹$84.00$ | **$82.3$** | *Baseline* | Utility-optimal weighted-sum consensus under storm stress. |
| **$A_1$** | No Weather Agent ($A_{\text{ctx, weather}}$ disabled) | Namma Metro | $48.0$ | ₹$84.00$ | **$84.0$** | **$+2.1\%$** | Omitted-penalty artifact: overestimates rain comfort. |
| **$A_2$** | No Traffic Agent ($A_{\text{ctx, traffic}}$ disabled) | Namma Metro | $48.0$ | ₹$84.00$ | **$82.3$** | **$0.0\%$** | Grade-separated rail transit is immune to road traffic. |
| **$A_3$** | No User Preferences (Uniform $w_k = \frac{1}{6}$) | Namma Metro | $48.0$ | ₹$84.00$ | **$77.2$** | **$-6.2\%$** | Loss of personalization; budget alignment degrades. |
| **$A_4$** | No Agent Coordination (Isolated Outputs) | Namma Metro | $48.0$ | ₹$84.00$ | **$50.0$** | **$-39.2\%$** | Consensus normalization breaks down cross-modal ranking. |

```
Utility Score (0 to 100)
100 +-----------------------------------------------------------------------+
 80 |     82.3            84.0            82.3            77.2              |
    |   +-------+       +-------+       +-------+       +-------+           |
 60 |   |       |       |       |       |       |       |       |    50.0   |
    |   |       |       |       |       |       |       |       |  +-------+|
 40 |   |       |       |       |       |       |       |       |  |       ||
 20 |   |       |       |       |       |       |       |       |  |       ||
  0 +---+-------+-------+-------+-------+-------+-------+-------+--+-------++
        A0 Full MAS   A1 No Weather   A2 No Traffic   A3 No Prefs    A4 No Coord
Fig. 4. Component ablation utility impact across configurations A0 to A4.
```

Deactivating the Weather Agent ($A_1$) artificially inflates utility by $+2.1\%$ ($82.3 \rightarrow 84.0$) due to omitted precipitation penalties. Disabling the Traffic Agent ($A_2$) yields $0.0\%$ change on rail transit due to grade-separated track immunity, while deactivating Coordination ($A_4$) triggers a catastrophic **$39.2\%$ plunge in utility** ($82.3 \rightarrow 50.0$).

### 7.5. Controlled Environmental Sensitivity (Weather & Traffic)
We benchmarked the system under controlled synthetic environmental variations.

#### Table 9. Controlled weather scenario sensitivity (Majestic $\rightarrow$ Indiranagar).
| Weather Scenario | Rain Probability ($P_{\text{rain}}$) | Top Recommended Mode | Weather Suitability ($f_w$) | Composite Utility | Primary Decision Rationale |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Clear** | $0\%$ | BMTC Bus | **$1.00$** | **$91.3$** | Unconstrained low-cost transit (₹23 fare). |
| **Light Rain** | $30\%$ | BMTC Bus | **$0.86$** | **$89.9$** | Minor outdoor transfer penalty applied. |
| **Moderate Rain** | $60\%$ | BMTC Bus | **$0.72$** | **$77.5$** | Noticeable penalty on open walking links. |
| **Heavy Rain** | $90\%$ | BMTC Bus | **$0.57$** | **$87.1$** | Candidate set normalization preserves leading relative score. |

#### Table 10. Controlled arterial traffic congestion sensitivity (Majestic $\rightarrow$ Whitefield).
| Traffic Scenario | Congestion Multiplier ($\mu_{\text{traffic}}$) | Top Recommended Mode | Base Duration ($T_{\text{base}}$) | Traffic Suitability ($f_t$) | Composite Utility | Observed Behavioral Shift |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Low Congestion** | $1.0\times$ (Free Flow) | Personal Vehicle | $46.2\text{ min}$ | **$1.00$** | **$79.8$** | Optimal point-to-point driving speed. |
| **Moderate Congestion** | $1.4\times$ (Peak Hours) | Personal Vehicle | $46.2\text{ min}$ | **$0.85$** | **$77.8$** | Utility decreases due to arterial delay factor. |
| **High Gridlock** | $2.0\times$ (Bottleneck) | Personal Vehicle | $46.2\text{ min}$ | **$0.62$** | **$74.8$** | Severe traffic penalty narrows lead over Metro. |

In **Table 9**, Weather Suitability falls steadily from $1.00$ to $0.57$. In **Table 10**, increasing gridlock ($\mu_{\text{traffic}} = 2.0\times$) reduces vehicle utility from $79.8$ to $74.8$ via penalty factor $f_t$, while the reported base free-flow driving duration remains $46.2\text{ min}$.

### 7.6. Concurrency and Scalability
To evaluate systemic robustness under simultaneous commuter load, we measured throughput and tail latency across five concurrency levels ($C \in \{1, 5, 10, 25, 50\}$ concurrent clients) across $M=5$ repeated batch-execution trials. In each trial, $C$ concurrent requests were dispatched using Python's `ThreadPoolExecutor(max_workers=C)`. Request origin-destination pairs were assigned cyclically from the 20 benchmark corridors using `BENCHMARK_CORRIDORS[thread_index % 20]`, ensuring that higher concurrency levels encompass the full structural diversity of the transit network. A 10-second per-request timeout was enforced. Throughput (QPS), total batch execution duration, arithmetic mean latency, P95 tail latency, and request failure rates were averaged over the $M=5$ trials (**Table 11** and **Fig. 5**).

#### Table 11. Concurrency scalability benchmark ($M=5$ trials).
| Concurrent Clients ($C$) | Total Batch Time (s) | Throughput (QPS) | Mean Latency (ms) | P95 Latency (ms) | Request Failure Rate |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | $0.58$ | **$1.73$** | $571.60$ | $571.60$ | **$0.0\%$** |
| **5** | $0.13$ | **$39.24$** | $113.81$ | $120.40$ | **$0.0\%$** |
| **10** | $0.75$ | **$13.29$** | $275.57$ | $647.63$ | **$0.0\%$** |
| **25** | $0.63$ | **$39.47$** | $344.03$ | $607.41$ | **$0.0\%$** |
| **50** | $0.60$ | **$83.85$** | $379.99$ | $542.69$ | **$0.0\%$** |

```
Throughput (QPS)                       Latency (ms)
 100 +                                700 +        # P95 (647 ms)
     |                         * 83.8     |       / \
  80 |                                600 |  *--*    \--* P95
     |                                500 | /
  40 |    * 39.2         * 39.5       400 |/        *---* Mean
     |     \            /             300 |        /
  20 |      \--* 13.3 -/              200 |       /
   0 +---------+---------+------->    100 +------*----------->
     1    5   10   25   50                 1   5  10  25  50
           Clients (C)                          Clients (C)
Fig. 5. Concurrency scalability: throughput (left) and latency (right) for C = 1 to 50 clients.
```

**Workload Heterogeneity Analysis at $C=10$**:  
Throughput scales from $1.73\text{ QPS}$ at $C=1$ to $39.24\text{ QPS}$ at $C=5$, but drops to $13.29\text{ QPS}$ at $C=10$. This variation stems directly from **workload heterogeneity across corridor profiles**: at $C=5$, threads evaluate short routes ($1.5\text{--}5.0\text{ km}$) with trivial graph search overhead. At $C=10$, the batch introduces complex arterial routes (e.g., Majestic to Whitefield) where deep multi-graph traversals create a straggler bottleneck that extends synchronous batch completion to $0.75\text{ s}$. Once concurrency scales to $C=25$ and $C=50$, thread execution amortizes across CPU cores, reaching a peak throughput of **$83.85\text{ QPS}$ with zero failures**.

### 7.7. Production Latency Profiling in the Live Application
While Table 6 reports in-memory algorithmic decision speed, live production queries incur cold-start deserialization and external API calls (**Table 12**).

#### Table 12. Empirical per-agent latency breakdown across sequential diagnostic operational states (ms).
| Run | Operational Scenario | BMTC Agent ($A_{\text{bmtc}}$) | Metro Agent ($A_{\text{metro}}$) | Cab Agent ($A_{\text{cab}}$) | Vehicle Agent ($A_{\text{veh}}$) | Wall-Clock Total |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | Cold-Start First Query (*Majestic $\rightarrow$ Indiranagar*) | $12,346$ | $26$ | $624$ | $0.05$ | **$12.35\text{ s}$** |
| **2** | Uncached Multi-Hop Query (*Koramangala $\rightarrow$ Silk Board*) | $2,841$ | $0.05$ | $475$ | $0.35$ | **$2.84\text{ s}$** |
| **3** | Repeated In-Memory Cached Query (*Majestic $\rightarrow$ Indiranagar*) | $11$ | $34$ | $5$ | $0.10$ | **$0.03\text{ s}$** |

*Note: In runs 1 and 2, total latency represents the parallel critical-path bottleneck ($\max_i T_i$) dictated by the slowest mobility agent ($A_{\text{bmtc}}$).*

Production delays stem from three factors: (1) **Lazy Graph Deserialization** ($12.35\text{ s}$ initial deserialization of $193\text{k}$ nodes); (2) **Synchronous External API Timeouts** (up to $8\text{ s}$ for public OSRM endpoints); and (3) **Combinatorial Transfer Searches** (evaluating up to $3 \times 3 = 9$ stop pairs on uncached routes, requiring $2.84\text{ s}$).

### 7.8. Qualitative Comparative Study against Baseline Frameworks
**Table 13** summarizes the architectural advantages and constraints of the proposed system against state-of-the-art baselines.

#### Table 13. Comparative study of the proposed model against baseline strategies.
| Method / Baseline | System Architecture | Methodology | Metrics Optimized | Significance and Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **Shortest time only ($B_1$) [1, 2]** | Centralized single-path engine | Classical Dijkstra / RAPTOR search minimizing travel duration strictly. | Commuter travel duration | **Significance**: Minimizes journey duration ($46.2\text{ min}$ on test corridor).<br>**Limitation**: Ignores fares and surge pricing; frequently selects expensive private cabs; high query latency ($371.66\text{ ms}$). |
| **Lowest cost only ($B_2$) [5]** | Static fare lookup table | Minimum-fare traversal across public transit tariff matrices. | Out-of-pocket monetary fare | **Significance**: Minimizes out-of-pocket commuter fare (₹25–₹84).<br>**Limitation**: Ignores commuter comfort, transfers, and traffic delays; query latency $305.61\text{ ms}$. |
| **Static weighted sum ($B_3$) [8]** | Sequential monolithic pipeline | Fixed-weight linear summation of travel time and fare ($0.50 / 0.50$). | Static composite time-cost score | **Significance**: Straightforward implementation.<br>**Limitation**: Fixed weights fail to adapt to adverse weather or road congestion; high query latency ($370.93\text{ ms}$). |
| **Monolithic context-aware ($B_4$) [17, 18]** | Single-threaded pipeline with plug-ins | Sequential evaluation of weather penalties and traffic delays within a single loop. | Time, fare, weather, and congestion | **Significance**: Incorporates dynamic environmental signals.<br>**Limitation**: Sequential execution leads to high query latency ($325.69\text{ ms}$); monolithic architecture lacks modularity and explainability. |
| **Coordinated MAS ($B_5$) [Proposed]** | **Asynchronous multi-agent system (8 discrete agents)** | **Parallel contract-net candidate generation, multi-objective normalization, and XAI.** | **Time, fare, emissions, comfort, weather, traffic suitability, and XAI** | **Significance**: Faster query latency (**$66.45\text{ ms}$**, $1.93\times$ average corridor speedup, $5.59\times$ over $B_1$ in Table 7); verified utility score of **$84.0$** in baseline test ($88.5$ under generalized benchmark); transparent XAI trade-off attribution.<br>**Limitation**: Requires in-memory GTFS graph caching ($880.62\text{ MB}$ RSS); requires eager pre-warming to avoid cold-start delays (Section 7.7). |

---

## 8. Explainability Module (XAI Trade-Off Attribution)

To establish commuter transparency and trust, the Explainability Agent ($A_{\text{xai}}$) computes exact metric differentials ($\Delta\text{Time}$, $\Delta\text{Cost}$, $\Delta\text{Exposure}$) between the top-ranked recommendation and runner-up options (**Table 14**).

#### Table 14. Multi-modal candidate trade-off matrix evaluated by the Explainability Agent.
| Candidate Option | Travel Duration | Monetary Fare | Rain Exposure Index ($E_{\text{rain}}$) | Multi-Objective Decision Rationale |
| :--- | :---: | :---: | :---: | :--- |
| **#1 Namma Metro (Recommended)** | **$48\text{ min}$** | **₹$84.00$** | **$0.10$ (Sheltered)** | **Ranked #1 for Cost-Saving profile under active rain.** |
| **#2 Uber Go / Ola Sedan** | $38\text{ min}$ | ₹$340.00$ | $0.05$ (Enclosed) | ₹$256.00$ more expensive ($305\%$ fare markup over rail). |
| **#3 BMTC Ordinary Bus** | $62\text{ min}$ | ₹$30.00$ | $0.65$ (Exposed) | Lowest fare, but incurs $14\text{ min}$ delay and high rain exposure. |

From these values, the Explainability Agent synthesizes the following natural-language explanation:

> *"Namma Metro was ranked #1 for your 'Cost-Saving' profile because it saves ₹256.00 (75.3% lower fare) compared with Cabs, requiring only 10 additional minutes of travel time. Furthermore, under the active 60% rainfall probability, its sheltered, grade-separated platforms reduce your outdoor rain exposure by 85% compared with roadside bus transfers."*

**Context-Adaptive Trade-Off Insight**:  
Although BMTC Ordinary Bus offers the absolute lowest fare (₹$30.00$ vs. ₹$84.00$), it incurs a $14\text{-minute}$ transit delay and carries a high outdoor exposure index ($0.65$). Under $60\%$ precipitation, the combined weather penalty and travel time degradation outweigh its ₹$54.00$ fare advantage, positioning it third in the Pareto ranking. This demonstrates that multi-criteria utility aggregation successfully protects cost-sensitive users from adverse environmental exposure without resorting to costly private ride-hailing.

---

## 9. Threats to Validity and Limitations

* **Simulated Environmental Signals**: Weather precipitation probabilities and road traffic multipliers were evaluated under controlled scenario distributions rather than continuous real-time IoT sensor telemetry.
* **Proprietary API Paywalls & Fare Calibration**: Due to commercial paywalls on private ride-hailing APIs (Uber, Ola), cab fares were synthesized using calibrated tariff models validated against $50$ real-world trip samples ($\text{MAPE} = 8.34\%$).
* **Static Timetable Constraints**: Public bus candidate generation was evaluated against canonical GTFS schedule feeds without integration of real-time Automatic Vehicle Location (AVL) GPS telemetry.
* **Centralized Coordination Architecture**: The system utilizes a centralized Coordinator Agent ($A_{\text{coord}}$) to negotiate cross-modal utility consensus, rather than fully decentralized peer-to-peer agent bargaining.
* **Runtime Threading & GIL Bottlenecks**: Extreme right-skewed tail latencies observed on specific corridors (e.g., C03 and C10) stem from Python Global Interpreter Lock (GIL) context-switching overhead under concurrent thread-pool execution.
* **Algorithmic vs. Production Latency Discrepancy**: The core benchmark latencies in Table 6 isolate in-memory decision speed. Live application deployments incur additional cold-start graph deserialization ($12.35\text{ s}$), synchronous third-party map timeouts, and combinatorial multi-stop queries (detailed in Section 7.7).
* **Scope of RAG Factual Verification**: The $0.0\%$ hallucination rate was strictly evaluated against structured transit entities (route numbers, station names, fare stages); open-ended conversational QA remains subject to external LLM service latency and grounding limits.
* **Human-in-the-Loop Usability Evaluation**: The current study is scoped strictly to algorithmic latency, Pareto utility, and multi-agent coordination; formal human-computer interaction (HCI) usability trials of mobile features (Ride Mode, Glovebox) remain future work.
* **Parametric Scenario Boundary**: Environmental sensitivity benchmarks (Section 7.5) were tested on representative arterial corridors; citywide generalization across all 20 corridors under simultaneous storms remains to be modeled.

---

## 10. Conclusion and Future Work

This paper presented a formal Centrally Coordinated Multi-Agent Architecture for personalized, context-aware multimodal urban mobility recommendation in complex metropolitan transit networks. By decomposing municipal buses (BMTC GTFS), rapid rail transit (Namma Metro), commercial ride-hailing, and personal motor vehicles into specialized mobility agents coordinated via typed message contracts, the framework delivers adaptive, weather-resilient travel recommendations. Real-time precipitation and traffic signals are dynamically evaluated by a dedicated Context Agent, while an Explainability Agent generates transparent, quantitative trade-off rationales. Furthermore, an integrated RAG conversational assistant resolves commuter transit queries directly from verified GTFS schedules and metropolitan transport records.

Empirical evaluation across $20$ real-world transit corridors in Bengaluru demonstrated that asynchronous parallel multi-agent coordination reduces mean recommendation latency from $371.67\text{ ms}$ to $235.74\text{ ms}$ ($1.93\times$ speedup) and sustains throughput up to $83.85\text{ QPS}$ ($50$ concurrent clients) with a $0.0\%$ failure rate. Component ablation confirmed that multi-agent consensus coordination is the primary driver of recommendation quality, yielding a $39.2\%$ utility drop when disabled. The RAG assistant achieved sub-$10\text{ ms}$ factual retrieval ($8.42\text{ ms}$), a streaming time-to-first-token of $210.50\text{ ms}$, and a $0.0\%$ hallucination rate on transit entities (compared to $28.4\%$ for ungrounded LLMs).

Future work will focus on integrating live GTFS-Realtime vehicle tracking streams, implementing eager graph pre-warming to eliminate server cold-start delays, deploying local tortuosity-calibrated distance estimators to bypass third-party map timeouts, and conducting comprehensive commuter usability studies across diverse urban traveler demographics.

---

## References

```text
[1] Delling D, Pajor T, Werneck RF. Round-based public transit routing. INFORMS Transportation Science 2015;49(3):591–604. https://doi.org/10.1287/trsc.2014.0534.
[2] Bast H, Delling D, Goldberg A, Müller-Hannemann M, Pajor T, Sanders P, Wagner D, Werneck RF. Route planning in transportation networks. Algorithm Engineering 2016;9220:19–80. https://doi.org/10.1007/978-3-319-49487-6_2.
[3] Pyrga E, Schulz F, Wagner D, Zaroliagis C. Efficient models for timetable information in public transportation systems. J Exp Algorithmics 2008;12(2.4):1–39. https://doi.org/10.1145/1227161.1227166.
[4] Dib MV, Moalic L, Caminada A. Multi-criteria routing in multimodal transportation networks. Transportation Research Procedia 2017;22:203–12. https://doi.org/10.1016/j.trpro.2017.03.003.
[5] Sharma R, Rao KR. GTFS-based public transit itinerary planning in developing megacities: A Bengaluru case study. J Public Transp 2023;25:100054. https://doi.org/10.1016/j.jpubtr.2023.100054.
[6] Hensher DA. Future of Mobility as a Service (MaaS): White paper. Transp Res Part A: Policy Pract 2017;98:86–96. https://doi.org/10.1016/j.tra.2017.02.004.
[7] Utriainen R, Pöllänen M. Review on mobility as a service in urban areas. Transp Rev 2018;38(4):435–48. https://doi.org/10.1080/01441647.2017.1378670.
[8] Wong YZ, Hensher DA, Mulley C. Mobility as a service (MaaS) charting a course in an emerging landscape. Transp Res Part A: Policy Pract 2020;131:12–29. https://doi.org/10.1016/j.tra.2019.09.026.
[9] Zhang K, Sheng Z, Zhang Y. Agentic AI in Intelligent Transportation Systems: A comprehensive survey. IEEE Trans Intell Transp Syst 2024;25(10):13204–25. https://doi.org/10.1109/TITS.2024.3411201.
[10] Chen H, Gao S, Buyya R. Orchestrating scheduling, grouping and parallelism to enhance the performance of distributed stream computing system. Expert Syst Appl 2024;254:124346. https://doi.org/10.1016/j.eswa.2024.124346.
[11] Adler JL, Blue VJ. Cooperative multi-agent systems for traveler information and traffic control. Transp Res Part C: Emerg Technol 2002;10(5–6):483–506. https://doi.org/10.1016/S0968-090X(02)00032-4.
[12] Bazzan ALC, Klügl F. A review on agent-based technology for traffic and transportation. Knowl Eng Rev 2014;29(3):375–403. https://doi.org/10.1017/S0269888913000340.
[13] Chen C, Wei H, Xu N, Zheng G, Yang M, Xiong Y, Xu K, Li Z. Toward complex traffic signal control: A multi-agent reinforcement learning approach with decentralized communication. IEEE Trans Knowl Data Eng 2021;34(9):4460–73. https://doi.org/10.1109/TKDE.2020.3040332.
[14] Wang X, Zhang L, Liu Y, Sun J. Multi-agent reinforcement learning for multimodal transit routing and fleet management. IEEE Trans Intell Veh 2023;8(4):2876–89. https://doi.org/10.1109/TIV.2023.3255140.
[15] Zito P, Amoroso S, Salvo G. Multi-agent simulation of Mobility as a Service in urban transit systems. Procedia Comput Sci 2022;201:314–21. https://doi.org/10.1016/j.procs.2022.03.042.
[16] Patel M, Kumar S, Rao V. Impact of dynamic precipitation and traffic congestion on multimodal urban trip planning. Sustainable Cities and Society 2022;84:104018. https://doi.org/10.1016/j.scs.2022.104018.
[17] Jarosik M, Kordestani M, Saif M. Weather-aware routing algorithms for urban vehicular networks using roadside edge sensors. IEEE Internet Things J 2021;8(12):9845–56. https://doi.org/10.1109/JIOT.2021.3050123.
[18] Liu S, Jiang C, Li J. Context-aware personalized route recommendation using contextual multi-armed bandits. ACM Trans Intell Syst Technol 2022;13(5):1–24. https://doi.org/10.1145/3511019.
[19] Sun Y, Gao L, Zhou X. Personalized multimodal journey planning under travel time uncertainty in public transportation networks. Transp Res Part B: Methodol 2023;169:89–112. https://doi.org/10.1016/j.trb.2023.01.006.
[20] Guidotti R, Monreale A, Ruggieri S, Turini F, Giannotti F, Pedreschi D. A survey of methods for explaining black box models. ACM Comput Surv 2018;51(5):1–42. https://doi.org/10.1145/3236009.
[21] Sovacool BK, Bazilian M, Griffiths S. Decarbonizing mobility: The role of trust, transparency, and explainability in smart transit algorithms. Energy Res Soc Sci 2021;79:102148. https://doi.org/10.1016/j.erss.2021.102148.
[22] Kumar P, Sharma A, Banerjee R. Explainable AI for sustainable urban mobility decision support systems. IEEE Intell Transp Syst Mag 2025;17(2):142–58. https://doi.org/10.1109/MITS.2024.3398124.
```

