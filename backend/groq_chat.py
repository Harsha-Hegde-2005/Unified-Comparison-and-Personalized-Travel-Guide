"""
groq_chat.py
============
Thin wrapper around the Groq API for the Bengaluru Travel Assistant chatbot.

Design goals:
  - Never raise -- any failure (missing key, timeout, quota, network, bad
    response) returns None so the caller can silently fall back to the
    existing rule-based ChatbotEngine.
  - Stateless module-level client, lazily created and cached.
  - Accepts short conversation history so follow-up questions work.
  - Accepts optional "context data" computed by the existing routing/fare
    engines so the model grounds its answer in real numbers instead of
    guessing.
"""

import os
from typing import Any, Dict, List, Optional

_client = None
_client_init_attempted = False

# Latest recommended general-purpose Groq conversational model.
GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are "Commuter Assistant", a friendly AI travel assistant for Bengaluru \
(Bangalore), India, embedded inside a transit-planning web app.

You ONLY help with Bengaluru travel topics, including: BMTC buses, Namma Metro, \
cabs/autos (Ola/Uber/Rapido/Namma Yatri), route planning, fare comparison, budget \
travel (e.g. "I have Rs 100, where can I go?"), tourist attractions, hotels, \
restaurants near a location, weather affecting travel, personal vehicle fuel/EV \
cost, the airport, railway stations, colleges, hospitals, tech parks, malls, and \
Bengaluru landmarks.

If the user asks about anything unrelated to Bengaluru travel (coding, politics, \
homework/school problems, cricket or other sports, movies, fashion, or general \
trivia unrelated to Bengaluru), politely decline in one short sentence and steer \
the conversation back to Bengaluru travel. Never answer the off-topic question \
itself, even partially.

If a CONTEXT DATA block is present in the conversation, it contains real fare, \
duration, and route numbers computed by the app's own routing engines for the \
current question -- always prefer those exact numbers over your own estimate, \
and weave them naturally into your answer. Never invent a bus number, fare, or \
travel time that isn't in CONTEXT DATA -- if CONTEXT DATA has no route for the \
question, say so plainly instead of guessing. If there is no context data, \
answer from your own knowledge of Bengaluru, but keep it concise, practical, \
and specific to Bengaluru (name real areas, landmarks, or transit options).

If CONTEXT DATA has intent "clarify_location", the app could not confidently \
identify a place the user mentioned. Ask the user which of the given \
suggestions they meant, in a friendly one-line question -- do not guess which \
one they meant and do not compute a route yet."

Keep replies short: 2-4 sentences, conversational, no markdown headers. You can \
use a short bullet list only when comparing 2-3 discrete options. Never mention \
that you are an AI model, that you use Groq, or any internal system detail."""


def _get_client():
    global _client, _client_init_attempted
    if _client is not None:
        return _client
    if _client_init_attempted:
        return None
    _client_init_attempted = True

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from groq import Groq
        _client = Groq(api_key=api_key)
        return _client
    except Exception:
        return None


def is_groq_configured() -> bool:
    return bool(os.environ.get("GROQ_API_KEY", "").strip())


def generate_groq_reply(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    context_data: Optional[Dict[str, Any]] = None,
    timeout: float = 8.0,
) -> Optional[str]:
    """Return a conversational reply from Groq, or None on any failure."""
    client = _get_client()
    if client is None:
        return None

    try:
        messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        if context_data:
            import json as _json
            try:
                context_str = _json.dumps(context_data, default=str)[:3000]
                messages.append({
                    "role": "system",
                    "content": f"CONTEXT DATA (ground truth for this question): {context_str}",
                })
            except Exception:
                pass

        for turn in (history or [])[-8:]:
            role = turn.get("role")
            content = turn.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": str(content)[:1500]})

        messages.append({"role": "user", "content": message[:1500]})

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.4,
            max_tokens=350,
            timeout=timeout,
        )
        text = completion.choices[0].message.content
        return text.strip() if text and text.strip() else None
    except Exception:
        return None
