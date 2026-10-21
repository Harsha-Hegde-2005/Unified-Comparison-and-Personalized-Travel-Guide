"""
offtopic_filter.py
===================
Guard that politely rejects questions unrelated to travel or Bengaluru transportation.
Allows travel educational/guidance questions ("difference between BMTC and metro")
and contextual follow-ups ("what about tomorrow?", "the second option") when an
active travel conversation session exists.
"""

from typing import List, Optional

TRAVEL_KEYWORDS: List[str] = [
    "bmtc", "metro", "namma", "bus", "cab", "auto", "ola", "uber", "rapido",
    "route", "fare", "ticket", "tickets", "journey", "travel", "commute", "station",
    "stop", "budget", "rupee", "rs.", "rs ", "₹", "inr", "hotel", "hotels", "restaurant",
    "restaurants", "food", "eat", "dining", "diner", "cafe", "cafes", "coffee", "tea",
    "breakfast", "lunch", "dinner", "dosa", "idli", "biryani", "resort", "lodge", "lodging",
    "stay", "room", "rooms", "pg", "hostel", "tourist", "tourism", "sightseeing", "attraction",
    "attractions", "spot", "spots", "park", "national park", "zoo", "safari", "palace", "temple",
    "museum", "lake", "fort", "hills", "garden", "botanical", "wonderla", "bannerghatta",
    "bannerughatta", "lalbagh", "cubbon", "iskcon", "vidhana soudha", "nandi hills", "ulsoor",
    "planetarium", "open now", "is open", "opening", "closing", "hours", "timings", "timing",
    "weather", "rain", "vehicle", "bike", "car", "fuel", "petrol", "diesel",
    "ev ", "electric vehicle", "airport", "railway", "train", "college",
    "university", "hospital", "tech park", "mall", "landmark",
    "reach", "go to", "go from", "how to go", "how to reach", "distance", "nearest", "nearby",
    "directions", "how far", "how long", "traffic", "flight", "layout",
    "cross", "nagar", "road", "circle", "junction", "bengaluru", "bangalore",
    "pass", "smart card", "terminal", "vayu vajra", "schedule", "timetable",
    "itinerary", "day trip", "visit", "destination", "way to", "ways", "option", "options",
    "location", "locatoin", "where am i", "where i am", "my location", "current location", "gps"
]

GREETING_KEYWORDS: List[str] = [
    "hi", "hello", "hey", "namaskara", "namaste", "good morning", "good afternoon",
    "good evening", "greetings", "start", "help", "menu"
]

CONTEXTUAL_FOLLOWUP_KEYWORDS: List[str] = [
    "there", "here", "it", "that", "this", "the first one", "the second one",
    "the third one", "option 1", "option 2", "option 3", "cheapest", "fastest",
    "less walking", "fewer transfers", "what about", "how about", "instead",
    "tomorrow", "at 9", "by 9", "ac bus", "cab instead", "other hospital",
    "same route", "return journey", "from there", "compare with cab", "next bus timing",
    "plan 3-stop day trip", "fastest route", "cheapest route"
]

OFFTOPIC_KEYWORDS: List[str] = [
    "write code", "write a function", "python script", "javascript code",
    "debug my", "fix this bug", "programming language", "algorithm",
    "leetcode", "sql query", "c program", "c++ code", "java code",
    "election", "president", "prime minister", "parliament", "political party",
    "vote for",
    "homework", "solve this equation", "math problem", "essay on", "write an essay",
    "physics problem", "chemistry formula", "quadratic equation",
    "cricket score", "ipl match", "world cup final", "who won the match",
    "football score", "premier league",
    "movie review", "bollywood gossip", "hollywood movie", "netflix series",
    "web series recommendation", "romantic poem", "write a poem",
    "fashion trend", "outfit ideas", "what should i wear", "makeup tips",
    "capital of france", "who invented", "meaning of life", "define photosynthesis",
    "stock market tip", "crypto price", "bitcoin price",
]


def is_offtopic(text: str, has_active_session: bool = False) -> bool:
    if not text:
        return False
    t = text.lower().strip()

    # Explicit off-topic keywords take precedence
    if any(k in t for k in OFFTOPIC_KEYWORDS):
        return True

    # Greetings are ON-TOPIC
    words = t.split()
    if any(g == t or g in words for g in GREETING_KEYWORDS):
        return False

    # If message contains explicit travel, food, stay, or location terms, it is ON-TOPIC
    if any(k in t for k in TRAVEL_KEYWORDS):
        return False

    # If user asks educational/guidance question about travel/transport
    if any(k in t for k in ["difference between", "how do", "how to use", "explain metro", "explain bmtc", "guidance"]):
        return False

    # If an active travel conversation is ongoing, or if it matches follow-up terms
    if any(k in t for k in CONTEXTUAL_FOLLOWUP_KEYWORDS):
        return False

    if has_active_session:
        return False

    # If it's a general question with no travel terms and no active session context
    return True


OFFTOPIC_REPLY = (
    "I'm your travel assistant, so I can help with routes, transport, travel costs, nearby places, and trip planning. "
    "What would you like to know about your journey?"
)
