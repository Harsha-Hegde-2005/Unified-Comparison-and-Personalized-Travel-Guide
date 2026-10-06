r"""
coordinator.py
==============
Asynchronous Multi-Agent System (MAS) Coordinator orchestrating parallel agent execution,
typed message passing, context propagation, multi-criteria utility aggregation, and XAI generation.
"""

import os
import sys
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

from research.mas.agent_interface import (
    AgentObservation,
    CandidateJourney,
    AgentMessage,
    AgentMessageType
)
from research.mas.agents import (
    UserPreferenceAgent,
    ContextAgent,
    PublicTransitAgent,
    MetroAgent,
    CabMobilityAgent,
    PersonalVehicleAgent,
    CoordinatorAgent,
    ExplainabilityAgent
)


class MultiAgentSystemCoordinator:
    """
    Central Asynchronous Multi-Agent Coordinator managing agent lifecycles,
    parallel candidate generation, typed message passing, and consensus ranking.
    """

    def __init__(
        self,
        max_workers: int = 4,
        enable_weather: bool = True,
        enable_traffic: bool = True,
        enable_preferences: bool = True,
        enable_coordination: bool = True
    ):
        self.user_agent = UserPreferenceAgent(enable_preferences=enable_preferences)
        self.context_agent = ContextAgent(enable_weather=enable_weather, enable_traffic=enable_traffic)
        self.bmtc_agent = PublicTransitAgent()
        self.metro_agent = MetroAgent()
        self.cab_agent = CabMobilityAgent()
        self.veh_agent = PersonalVehicleAgent()
        self.coord_agent = CoordinatorAgent(enable_coordination=enable_coordination)
        self.xai_agent = ExplainabilityAgent()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def warm_up(self, sample_obs: Optional[AgentObservation] = None) -> float:
        """Pre-warm GTFS and Metro database caches into memory to separate Cold-Start from Warm-Start."""
        t0 = time.perf_counter()
        if sample_obs is None:
            sample_obs = AgentObservation(source="Majestic", destination="Indiranagar")
        
        # Warm call mobility agents
        self.bmtc_agent.run(sample_obs)
        self.metro_agent.run(sample_obs)
        self.cab_agent.run(sample_obs)
        self.veh_agent.run(sample_obs)
        
        t1 = time.perf_counter()
        return (t1 - t0) * 1000.0

    def run_sequential(self, observation: AgentObservation, mode_override: str = "B4") -> Dict[str, Any]:
        """Monolithic sequential execution baseline (B4)."""
        t0 = time.perf_counter()

        self.user_agent.run(observation)
        self.context_agent.run(observation)

        bmtc_candidates = self.bmtc_agent.run(observation)
        metro_candidates = self.metro_agent.run(observation)
        cab_candidates = self.cab_agent.run(observation)
        veh_candidates = self.veh_agent.run(observation)

        all_candidates = bmtc_candidates + metro_candidates + cab_candidates + veh_candidates

        weights = self.user_agent.get_weights()
        ranked = self.coord_agent.rank_candidates(
            all_candidates,
            weights,
            self.context_agent,
            mode_override=mode_override
        )

        pref_key = observation.user_preferences.get("preference", "cost")
        explanations = self.xai_agent.generate_explanations(ranked, self.context_agent, pref_key)

        t1 = time.perf_counter()
        total_time_ms = (t1 - t0) * 1000.0

        return {
            "execution_mode": f"sequential_{mode_override.lower()}",
            "total_latency_ms": round(total_time_ms, 2),
            "agent_latencies": {
                "bmtc": self.bmtc_agent.execution_time_ms,
                "metro": self.metro_agent.execution_time_ms,
                "cab": self.cab_agent.execution_time_ms,
                "veh": self.veh_agent.execution_time_ms
            },
            "recommendations": ranked,
            "explanations": explanations
        }

    def run_parallel(self, observation: AgentObservation, mode_override: str = "B5") -> Dict[str, Any]:
        """Coordinated parallel multi-agent execution with typed message passing (B5)."""
        t0 = time.perf_counter()

        # Step 1: Pre-process user & context agents
        self.user_agent.run(observation)
        self.context_agent.run(observation)

        # Broadcast REQUEST_ROUTE message
        req_msg = self.coord_agent.send_message(
            recipient_id="mobility_agents",
            msg_type=AgentMessageType.REQUEST_ROUTE,
            payload={"source": observation.source, "destination": observation.destination}
        )

        # Step 2: Parallel execution of specialized mobility agents
        mobility_agents = [self.bmtc_agent, self.metro_agent, self.cab_agent, self.veh_agent]
        futures = [self.executor.submit(agent.run, observation) for agent in mobility_agents]

        all_candidates = []
        agent_latencies = {}
        for agent, future in zip(mobility_agents, futures):
            candidates = future.result()
            all_candidates.extend(candidates)
            agent_latencies[agent.agent_id] = agent.execution_time_ms

            # Emit CANDIDATE_ROUTE message back to coordinator
            agent.send_message(
                recipient_id=self.coord_agent.agent_id,
                msg_type=AgentMessageType.CANDIDATE_ROUTE,
                payload={"candidate_count": len(candidates)}
            )

        # Step 3: Consensus utility ranking & XAI generation
        weights = self.user_agent.get_weights()
        ranked = self.coord_agent.rank_candidates(
            all_candidates,
            weights,
            self.context_agent,
            mode_override=mode_override
        )

        pref_key = observation.user_preferences.get("preference", "cost")
        explanations = self.xai_agent.generate_explanations(ranked, self.context_agent, pref_key)

        t1 = time.perf_counter()
        total_time_ms = (t1 - t0) * 1000.0

        return {
            "execution_mode": f"parallel_{mode_override.lower()}",
            "total_latency_ms": round(total_time_ms, 2),
            "agent_latencies": agent_latencies,
            "recommendations": ranked,
            "explanations": explanations
        }
