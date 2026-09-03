"""
offtopic_filter.py
===================
Lightweight keyword-based guard that politely rejects questions unrelated to
Bengaluru travel. Runs BEFORE both the Groq path and the rule-based fallback
so behavior is identical whether or not Groq is available.

This is intentionally conservative: if a message contains any travel-related
keyword, it is treated as on-topic even if it also mentions an off-topic word
(e.g. "is it worth watching a movie near Indiranagar metro" stays on-topic).
"""

from typing import List

TRAVEL_KEYWORDS: List[str] = [
    "bmtc", "metro", "namma", "bus", "cab", "auto", "ola", "uber", "rapido",
    "route", "fare", "ticket", "journey", "travel", "commute", "station",
    "stop", "budget", "rupee", "rs.", "rs ", "\u20b9", "hotel", "restaurant",
    "weather", "rain", "vehicle", "bike", "car", "fuel", "petrol", "diesel",
    "ev ", "electric vehicle", "airport", "railway", "train", "college",
    "university", "hospital", "tech park", "mall", "landmark", "tourist",
    "attraction", "reach", "go to", "distance", "nearest", "nearby",
    "directions", "how far", "how long", "traffic", "flight", "layout",
    "cross", "nagar", "road", "circle", "junction", "bengaluru", "bangalore",
]

OFFTOPIC_KEYWORDS: List[str] = [
    "write code", "write a function", "python script", "javascript code",
    "debug my", "fix this bug", "programming language", "algorithm",
    "leetcode", "sql query",
    "election", "president", "prime minister", "parliament", "political party",
    "vote for",
    "homework", "solve this equation", "math problem", "essay on", "write an essay",
    "physics problem", "chemistry formula",
    "cricket score", "ipl match", "world cup final", "who won the match",
    "football score", "premier league",
    "movie review", "bollywood gossip", "hollywood movie", "netflix series",
    "web series recommendation",
    "fashion trend", "outfit ideas", "what should i wear", "makeup tips",
    "capital of france", "who invented", "meaning of life", "define photosynthesis",
    "stock market tip", "crypto price", "bitcoin price",
]


def is_offtopic(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    if any(k in t for k in TRAVEL_KEYWORDS):
        return False
    return any(k in t for k in OFFTOPIC_KEYWORDS)


OFFTOPIC_REPLY = (
    "I'm your Bengaluru travel assistant, so I can only help with things like "
    "BMTC, Metro, cabs, routes, fares, weather, or places around the city. "
    "Ask me anything about getting around Bengaluru!"
)
