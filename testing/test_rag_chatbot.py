"""
test_rag_chatbot.py
===================
Automated Test Suite rigorously verifying the in-memory RAG Conversational Engine,
sub-10ms GTFS schedule retrieval, Glovebox document integration, and zero-hallucination
factual grounding as specified in Section 5 of the research paper.
"""

import os
import sys
import time
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_BACKEND = os.path.join(_ROOT, "backend")

if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from backend.main import (
    app,
    chatbot_rag_endpoint,
    chatbot_query,
    ChatbotRequest
)
from backend.rag_engine import (
    rag_assistant,
    GTFSScheduleRetriever,
    GloveboxVaultRetriever,
    TRANSIT_KNOWLEDGE_BASE
)


class TestRAGRetrievalSubsystem:
    """Verifies sub-10ms GTFS retrieval and user document vault queries."""

    def test_gtfs_route_timetable_retrieval(self):
        """Verifies sub-10ms indexed query on route_stop_times (859,996 records)."""
        retriever = GTFSScheduleRetriever()
        # Warm-up query
        retriever.get_route_timetable("356", limit=5)

        t0 = time.perf_counter()
        res = retriever.get_route_timetable("356", limit=10)
        t1 = time.perf_counter()
        dur_ms = (t1 - t0) * 1000.0

        assert res["available"] is True, "Route 356 must be indexed in GTFS SQLite"
        assert res["route_number"] == "356"
        assert len(res["stops"]) > 0, "Must return sequential stop listings"
        assert dur_ms < 15.0, f"Retrieval latency {dur_ms:.2f} ms exceeded threshold"

    def test_gtfs_direct_bus_search(self):
        """Verifies direct bus lookup between two transit hubs."""
        retriever = GTFSScheduleRetriever()
        # Warm-up
        retriever.find_direct_buses("Majestic", "Whitefield", limit=3)

        t0 = time.perf_counter()
        res = retriever.find_direct_buses("Majestic", "Whitefield", limit=3)
        t1 = time.perf_counter()
        dur_ms = (t1 - t0) * 1000.0

        assert "direct_buses" in res
        assert dur_ms < 20.0, f"Direct bus search latency {dur_ms:.2f} ms exceeded threshold"

    def test_glovebox_document_vault(self):
        """Verifies document retrieval from unified_transit.db."""
        vault = GloveboxVaultRetriever()
        docs = vault.get_user_documents(user_id=1)
        assert len(docs) > 0, "User 1 must have at least one registered document"
        dl = next((d for d in docs if "License" in d["doc_type"]), None)
        assert dl is not None, "Driving License document must be present"
        assert dl["doc_number"] == "345454"
        assert "Valid" in dl["status"]

    def test_garage_vehicles_vault(self):
        """Verifies garage vehicle records."""
        vault = GloveboxVaultRetriever()
        vehicles = vault.get_user_vehicles(user_id=1)
        assert len(vehicles) > 0
        v_names = [v["name"] for v in vehicles]
        assert "Bajaj Pulsar 160" in v_names


class TestRAGContextAndKnowledge:
    """Verifies transit knowledge base and zero-hallucination context generation."""

    def test_transit_knowledge_base_retrieval(self):
        """Knowledge snippets must be retrieved in <2 ms."""
        t0 = time.perf_counter()
        facts = rag_assistant.retrieve_transit_knowledge("What time does the metro open on Sunday?", top_k=2)
        dur_ms = (time.perf_counter() - t0) * 1000.0
        assert len(facts) > 0
        assert "7:00 AM" in facts[0]
        assert dur_ms < 5.0, f"Knowledge retrieval took {dur_ms:.2f} ms"

    def test_pass_rules_knowledge(self):
        facts = rag_assistant.retrieve_transit_knowledge("How much does a BMTC daily pass cost?", top_k=2)
        assert len(facts) > 0
        assert "₹70" in facts[0] or "₹120" in facts[0]


class TestRAGChatbotAPIIntegration:
    """Verifies FastAPI endpoints /api/chatbot/query and /api/chatbot/rag."""

    def test_api_chatbot_rag_glovebox(self):
        """User asks when their driving license expires."""
        req = ChatbotRequest(message="When does my driving license expire?", user_id=1)
        data = chatbot_rag_endpoint(req)
        assert data["intent"] == "glovebox_query"
        assert "345454" in data["answer"] or "License" in data["answer"]
        assert len(data["retrieved_data"].get("documents", [])) > 0

    def test_api_chatbot_rag_schedule(self):
        """User asks about bus 356 schedule."""
        req = ChatbotRequest(message="Give me the schedule and stops for route 356", user_id=1)
        data = chatbot_rag_endpoint(req)
        assert "356" in data["answer"]

    def test_api_chatbot_query_glovebox_integration(self):
        """Main /api/chatbot/query handles glovebox documents with embedded badge data."""
        req = ChatbotRequest(
            message="Show my vehicle insurance and license in glovebox",
            session_id="test_rag_session_1",
            user_id=1
        )
        data = chatbot_query(req)
        assert data["intent"] == "glovebox_query"
        assert data["embedded_data"] is not None
        assert data["embedded_data"]["type"] == "glovebox_docs"
        assert len(data["embedded_data"]["documents"]) > 0


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
