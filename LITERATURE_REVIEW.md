# Phase 3: Scholarly Literature Review & Research Gap Analysis

## Executive Summary
This document presents a rigorous academic literature review synthesizing research across Multi-Agent Systems (MAS), Multimodal Journey Planning, Mobility-as-a-Service (MaaS), Context-Awareness, Personalization, and Explainable AI (XAI) in urban transportation.

---

## 1. Domain-by-Domain Literature Synthesis

### 1.1 Multi-Agent Systems (MAS) & Agentic AI in Transportation
Agent-based modeling has long served as a core paradigm for decentralized decision-making in urban transit \cite{adler2002cooperative, bazzan2014review}. Recent advancements leverage agentic AI and multi-agent reinforcement learning (MARL) for dynamic traffic signal control and fleet management \cite{chen2021multi, zhang2024agentic}. Wang et al. \cite{wang2023multi} demonstrated MARL for multimodal transit routing, but focused primarily on macro-level network throughput rather than individualized, multi-objective commuter decision support.

### 1.2 Multimodal Journey Planning & Graph Search
Public transit routing relies heavily on efficient graph search algorithms such as RAPTOR \cite{delling2015round} and time-expanded/time-dependent Dijkstra variants \cite{bast2016route, pyrga2008efficient}. While these algorithms perform exceptionally well for static timetable feeds (e.g., GTFS), they struggle when integrating dynamic private mobility services (cabs, personal vehicles) with volatile fares and real-time traffic delays \cite{sharma2023gtfs}.

### 1.3 Mobility-as-a-Service (MaaS) & Heterogeneous Integration
The MaaS paradigm seeks to unify public transit (bus, rail) and private mobility (ride-hailing, micromobility) under a single interface \cite{hensher2017future, wong2020mobility, utriainen2018review}. However, current MaaS implementations operate primarily as centralized aggregation platforms that present fixed, isolated mode options rather than dynamically negotiating multi-modal transfers under real-time weather and traffic conditions.

### 1.4 Context-Aware & Personalized Route Recommendation
Contextual factors such as weather forecast and traffic congestion dramatically influence urban commuting \cite{jarosik2021weather, patel2022dynamic}. Liu et al. \cite{liu2022context} and Sun et al. \cite{sun2023personalized} incorporated user preferences and travel time uncertainty into route selection. However, existing context-aware recommenders treat weather and traffic as static cost penalties rather than active environmental signals that dynamically re-weight outdoor exposure risks and transfer safety.

### 1.5 Explainable AI (XAI) in Transportation Decision Support
As recommendation models incorporate multi-criteria utility functions and neural classifiers, explainability becomes essential for user trust \cite{ribeiro2016why, lundberg2017unified, guidotti2018survey}. Sovacool et al. \cite{sovacool2021decarbonizing} and Kumar et al. \cite{kumar2025explainable} highlighted the importance of XAI in sustainable mobility. Yet, current ITS platforms rarely provide quantitative, trade-off-driven explanations detailing *why* one mode outperformed another under specific weather and traffic constraints.

---

## 2. Literature Comparison Matrix

| Reference & Year | Problem Focus | Methodology | Modes Covered | Context Awareness | Personalization | MAS Arch.? | XAI Support? | Benchmark Realism | Primary Limitations |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Adler & Blue (2002)** \cite{adler2002cooperative} | MAS Traffic Management | Cooperative Agents | Road Traffic | Low | Low | Yes | No | Synthetic | No public transit or cab integration |
| **Delling et al. (2015)** \cite{delling2015round} | Public Transit Routing | RAPTOR Graph Search | Bus, Rail | None | None | No | No | Real GTFS | Cannot handle dynamic cab fares or weather |
| **Bast et al. (2016)** \cite{bast2016route} | Network Route Planning | Dijkstra / Contraction | Transit / Road | Low | None | No | No | Real Networks | High static pre-computation overhead |
| **Wong et al. (2020)** \cite{wong2020mobility} | MaaS Governance | Qualitative Framework | All Modes | Medium | Low | No | No | Policy Survey | Architectural & algorithmic gaps |
| **Jarosik et al. (2021)** \cite{jarosik2021weather} | Weather-Aware Routing | Sensor Data + Rules | Private Car | High (Weather) | Low | No | No | Sensor Data | Restricted to private vehicles only |
| **Chen et al. (2021)** \cite{chen2021multi} | Traffic Signal Control | MARL | Grid Traffic | High (Traffic) | None | Yes | No | Simulation | Focuses on signal control, not commuter journeys |
| **Liu et al. (2022)** \cite{liu2022context} | Personalized Routing | Contextual Bandits | Car / Taxi | Medium | High | No | Low | Taxi Trajectories | Ignores GTFS schedules & public transit |
| **Zito et al. (2022)** \cite{zito2022agent} | MaaS Agent Simulation | Agent-Based Sim. | Bus, Taxi, Bike | Low | Medium | Yes | No | Synthetic | Micro-simulation without live XAI or APIs |
| **Sun et al. (2023)** \cite{sun2023personalized} | Multimodal Planning | Stochastic Opt. | Bus, Metro, Walk | Low | High | No | No | Transit Data | Lacks live weather exposure modeling & cab pricing |
| **Wang et al. (2023)** \cite{wang2023multi} | Multimodal Routing | MARL | Bus, Metro | Medium | Low | Yes | No | Synthetic Grid | Scalability issues & black-box decisions |
| **Sharma & Rao (2023)** \cite{sharma2023gtfs} | Indian Transit Planning | GTFS Timetable Search | BMTC Bus, Walk | None | Low | No | No | Real Bengaluru GTFS | Single-mode, no cabs, weather, or XAI |
| **Zhang et al. (2024)** \cite{zhang2024agentic} | Agentic AI in ITS | Survey | All Modes | High | Medium | Yes | Low | Literature Review | Survey paper without empirical system implementation |
| **Kumar et al. (2025)** \cite{kumar2025explainable} | XAI Decision Support | Decision Trees / LLMs | Car, Bus | Medium | Medium | Yes | High | User Survey | Lacks multimodal GTFS graph solver & cab pricing |
| **Proposed System (2027)** | **Coordinated Urban Journey MAS** | **Decentralized MAS + Multi-Objective Normalization + XAI** | **BMTC, Metro, Cabs, Private, Walk** | **High (Live Rain & Traffic)** | **High (6 Weight Profiles)** | **Yes (8 Discrete Agents)** | **High (Data-Driven XAI)** | **Real Bengaluru GTFS + Metro + Cab APIs** | **Evaluated in present study** |

---

## 3. Identified Research Gap Statement

> **Defensible Research Gap**:
> Existing intelligent transportation systems and MaaS platforms either focus exclusively on static public transit timetable routing (e.g., RAPTOR, GTFS-Dijkstra) or single-mode traffic optimization (MARL signal control), failing to integrate **heterogeneous public transit (buses, metro), private ride-hailing (cabs, auto-rickshaws), and personal vehicles** into a unified decision framework. Furthermore, existing systems treat real-time contextual signals (weather, traffic delays) and personal preferences as static static scalar penalties rather than active environmental observations coordinated by discrete, specialized agents. Finally, current systems lack quantitative, trade-off-aware Explainable AI (XAI) mechanisms that justify *why* a specific multimodal route is recommended over alternatives under adverse weather or traffic conditions.
