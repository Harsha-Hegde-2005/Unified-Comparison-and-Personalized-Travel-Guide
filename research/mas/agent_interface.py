r"""
agent_interface.py
==================
Formal definition of the Multi-Agent System (MAS) primitives for urban transit decision support.

Each agent in the system is defined by the 5-tuple:
    A_i = (O_i, S_i, G_i, A_i, \pi_i)

where:
    O_i : Observation space (inputs received from user, environment, or other agents)
    S_i : Internal state & knowledge context
    G_i : Explicit agent objective goal
    A_i : Executable action space (output candidate proposals or annotations)
    \pi_i : Autonomous decision policy mapping (O_i, S_i) -> A_i
"""

import time
from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


class AgentMessageType(Enum):
    """Typed Agent Message Contract Identifiers."""
    REQUEST_ROUTE = "REQUEST_ROUTE"
    CANDIDATE_ROUTE = "CANDIDATE_ROUTE"
    CONTEXT_UPDATE = "CONTEXT_UPDATE"
    UTILITY_UPDATE = "UTILITY_UPDATE"
    NEGOTIATION_RESPONSE = "NEGOTIATION_RESPONSE"
    FINAL_RECOMMENDATION = "FINAL_RECOMMENDATION"
    EXPLANATION = "EXPLANATION"


@dataclass
class AgentMessage:
    """Explicit Typed Message Container for Agent Interaction."""
    sender_id: str
    recipient_id: str
    msg_type: AgentMessageType
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentObservation:
    """Observation payload received by an agent (O_i)."""
    source: str
    destination: str
    source_coords: Optional[tuple[float, float]] = None
    dest_coords: Optional[tuple[float, float]] = None
    departure_time: Optional[str] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    environmental_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidateJourney:
    """Action payload representing a proposed journey alternative (A_i)."""
    agent_id: str
    mode: str
    cost: float
    time_min: float
    distance_km: float
    transfers: int
    emissions_g_co2: float
    comfort_score: float  # 0.0 to 1.0
    weather_exposure: float  # 0.0 to 1.0
    traffic_delay_min: float
    raw_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract Base Class for all autonomous transit decision agents."""

    def __init__(self, agent_id: str, goal: str, role: str = "agent"):
        self.agent_id = agent_id
        self.goal = goal
        self.role = role  # agent, coordinator, service_component
        self.state: Dict[str, Any] = {}
        self.execution_time_ms: float = 0.0
        self.message_inbox: List[AgentMessage] = []
        self.message_outbox: List[AgentMessage] = []

    @abstractmethod
    def observe(self, observation: AgentObservation) -> None:
        """Update agent internal state S_i based on incoming observation O_i."""
        pass

    @abstractmethod
    def evaluate_policy(self) -> List[CandidateJourney]:
        """Execute decision policy \pi_i to generate action proposals A_i."""
        pass

    def send_message(self, recipient_id: str, msg_type: AgentMessageType, payload: Dict[str, Any]) -> AgentMessage:
        """Construct and emit a typed agent message."""
        msg = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            msg_type=msg_type,
            payload=payload
        )
        self.message_outbox.append(msg)
        return msg

    def receive_message(self, msg: AgentMessage) -> None:
        """Receive an incoming typed agent message into inbox."""
        self.message_inbox.append(msg)

    def run(self, observation: AgentObservation) -> List[CandidateJourney]:
        """Wrapper method executing observe() and evaluate_policy() with performance profiling."""
        t0 = time.perf_counter()
        self.observe(observation)
        actions = self.evaluate_policy()
        t1 = time.perf_counter()
        self.execution_time_ms = (t1 - t0) * 1000.0
        return actions
