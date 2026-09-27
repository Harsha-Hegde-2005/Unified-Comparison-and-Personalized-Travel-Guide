"""
location_aliases.py
====================
Common Bengaluru location nicknames, misspellings, and shorthand -> canonical
search phrase. Used to normalize chatbot input before stop/station matching.

This is intentionally a plain substring-replacement map (checked longest-key
first) plus a small fuzzy-matching helper for typos that aren't in the map.
"""

import difflib
from typing import Dict, List, Optional, Tuple

# key: lowercase alias/nickname/typo a rider might type
# value: canonical phrase to substitute in its place before stop matching
ALIASES = {
    "majstic": "majestic",
    "majestic bus stand": "kempegowda bus station",
    "kbs": "kempegowda bus station",
    "silkboard": "silk board",
    "silk-board": "silk board",
    "silk bord": "silk board",
    "ecity": "electronic city",
    "e-city": "electronic city",
    "e city": "electronic city",
    "electronic city phase 1": "electronic city",
    "electronic city phase 2": "electronic city",
    "pes ec": "pes university electronic city campus",
    "pes university ec": "pes university electronic city campus",
    "pesu ec": "pes university electronic city campus",
    "mg road": "mahatma gandhi road",
    "mgroad": "mahatma gandhi road",
    "btm": "btm layout",
    "hsr": "hsr layout",
    "koramangala 5th block": "koramangala",
    "whitefield main": "whitefield",
    "kr puram": "krishnarajapuram",
    "krpuram": "krishnarajapuram",
    "yeshwantpur": "yeshwanthpur",
    "yeshwanthapura": "yeshwanthpur",
    "banashankari 6th stage": "banashankari",
    "rt nagar": "rammurthy nagar",
    "domlur brts": "domlur",
    "manyata tech park": "manyata embassy business park",
    "embassy manyata": "manyata embassy business park",
    "rmz ecoworld": "bellandur",
    "rgi airport": "kempegowda international airport",
    "bial": "kempegowda international airport",
    "kia airport": "kempegowda international airport",
    "blr airport": "kempegowda international airport",
    "bangalore airport": "kempegowda international airport",
    "city railway station": "bangalore city railway station",
    "krantivira railway station": "bangalore city railway station",
    "sbc": "bangalore city railway station",
    "yeshwantpur railway": "yeshwanthpur railway station",
    "cantt station": "bangalore cantonment railway station",
    "iisc": "indian institute of science",
    "rvce": "rv college of engineering",
    "bmsce": "bms college of engineering",
    "nit": "national institute of technology",
    # City-name misspellings/shorthand
    "banglore": "bangalore",
    "bengalooru": "bengaluru",
    "blore": "bangalore",
    "bangaluru": "bengaluru",
    "bangalore city": "bengaluru",
    # More common typo/shorthand variants
    "koramangla": "koramangala",
    "korangala": "koramangala",
    "jayanagr": "jayanagar",
    "jaynagar": "jayanagar",
    "malleshwaram": "malleswaram",
    "malleswaram west": "malleswaram",
    "whitfield": "whitefield",
    "whitefeild": "whitefield",
    "hebbal flyover": "hebbal",
    "marthahalli": "marathahalli",
    "marthalli": "marathahalli",
    "bellandur gate": "bellandur",
    "shivaji nagar": "shivajinagar",
    "vijaynagar": "vijayanagar",
    "basvangudi": "basavanagudi",
    "basavangudi": "basavanagudi",
    "jp nagar": "jayaprakash nagar",
    "jpnagar": "jayaprakash nagar",
    "kengeri": "kengeri",
    "hosur rd": "hosur road",
    "airport rd": "airport road",
    "old airport rd": "old airport road",
    "orr": "outer ring road",
    "itpl": "international tech park bangalore",
    "sarjapur rd": "sarjapur road",
    "sarjapura road": "sarjapur road",
    "hbr layout": "hbr layout",
    "vv puram": "vishveshwarapuram",
    "malleswaram 8th cross": "malleswaram",
    "hosakerehalli": "hosakerehalli",
    "hoskerehalli": "hosakerehalli",
    "hosakerehalli cross": "hosakerehalli cross",
    "hoskerehalli cross": "hosakerehalli cross",
    "hosakerehalli junction": "hosakerehalli junction",
    "hoskerehalli junction": "hosakerehalli junction",
}


# Runtime-extendable table for hub-synonym / POI aliases merged in via
# merge_extra_aliases() (e.g. "silk board" -> "Central Silk Board", or a POI
# nickname -> its canonical name). Kept separate from the hand-curated
# ALIASES (pure spelling/nickname fixes) above so the two can be applied in
# a safe, non-cascading order -- see normalize_query_text().
EXTRA_ALIASES: Dict[str, str] = {}


def _apply_alias_table(
    text: str,
    table: Dict[str, str],
    protected: List[Tuple[int, int]],
    guard_overlap: bool,
) -> Tuple[str, List[Tuple[int, int]]]:
    """Apply one alias table over `text`, longest-key-first.

    `protected` holds character ranges that came from an earlier stage's
    replacement. A candidate match is only allowed to touch a protected
    range if it EXACTLY spans that whole range (this is what lets a stage-2
    hub alias fully consume a stage-1 typo-fix output, e.g. "silk board" ->
    "Central Silk Board" after "silkboard" -> "silk board") -- a match that
    only partially overlaps a protected range (e.g. "pes university"
    matching just the prefix of stage-1's "pes university electronic city
    campus") is rejected, since that would corrupt an already-resolved name.
    When guard_overlap is True, this call's OWN replacements are added to
    `protected` too, preventing two same-stage aliases (e.g. "majestic" and
    "kempegowda", both hub aliases for the same station) from duplicating
    each other's output.
    """
    result = text

    def _blocking_overlap(start: int, end: int) -> bool:
        for s, e in protected:
            touches = not (end <= s or start >= e)
            if touches and not (start == s and end == e):
                return True
        return False

    def _shift_protected(from_idx: int, delta: int) -> None:
        nonlocal protected
        protected = [
            (s + delta if s >= from_idx else s, e + delta if e >= from_idx else e)
            for s, e in protected
        ]

    for alias in sorted(table.keys(), key=len, reverse=True):
        canonical = table[alias]
        lower_result = result.lower()
        search_from = 0
        while True:
            idx = lower_result.find(alias, search_from)
            if idx == -1:
                break
            end_idx = idx + len(alias)
            if _blocking_overlap(idx, end_idx):
                search_from = idx + 1
                continue
            result = result[:idx] + canonical + result[idx + len(alias):]
            delta = len(canonical) - len(alias)
            _shift_protected(end_idx, delta)
            if guard_overlap:
                protected.append((idx, idx + len(canonical)))
            lower_result = result.lower()
            search_from = idx + len(canonical)
    return result, protected


def normalize_query_text(text: str) -> str:
    """Replace known aliases/nicknames/typos in text with canonical phrases.

    Case-insensitive, longest-alias-first so multi-word aliases aren't
    partially shadowed by shorter ones. Runs in two stages: first the
    hand-curated spelling/nickname fixes (ALIASES), then the runtime-merged
    hub-synonym/POI aliases (EXTRA_ALIASES) -- so a typo fix like
    "silkboard" -> "silk board" gets a chance to feed into a hub alias like
    "silk board" -> "Central Silk Board" from the second stage, while a
    stage-1 output that already fully resolved to a specific place (e.g. a
    PES University campus) can't be partially cannibalized by an unrelated
    alias in stage 2.
    """
    if not text:
        return text

    result, protected = _apply_alias_table(text, ALIASES, [], guard_overlap=True)
    result, _ = _apply_alias_table(result, EXTRA_ALIASES, protected, guard_overlap=True)
    return result


def fuzzy_find_stop(word: str, candidates: List[str], cutoff: float = 0.82) -> Optional[str]:
    """Best-effort fuzzy match for a single token/phrase against known stop names.

    Used as a last resort when substring matching in the chatbot engine finds
    nothing -- catches typos like "Majestik" or "Indranagar".
    """
    if not word or len(word) < 4:
        return None
    matches = difflib.get_close_matches(word.lower(), [c.lower() for c in candidates], n=1, cutoff=cutoff)
    if not matches:
        return None
    match_lower = matches[0]
    for c in candidates:
        if c.lower() == match_lower:
            return c
    return None


def fuzzy_suggest_stops(word: str, candidates: List[str], n: int = 3, cutoff: float = 0.6) -> List[str]:
    """Return up to `n` plausible near-matches for a garbled/unknown phrase.

    Lower cutoff than fuzzy_find_stop() -- this is meant to power a "Did you
    mean...?" clarification prompt, not to auto-accept a match. The caller is
    responsible for never treating these as confirmed locations.
    """
    if not word or len(word) < 3:
        return []
    lower_map: Dict[str, str] = {}
    for c in candidates:
        lower_map.setdefault(c.lower(), c)
    matches = difflib.get_close_matches(word.lower(), list(lower_map.keys()), n=n, cutoff=cutoff)
    return [lower_map[m] for m in matches]


def merge_extra_aliases(extra: Dict[str, str]) -> None:
    """Merge additional alias -> canonical-name pairs (e.g. from the POI
    dataset or HUB_MAPPINGS) into EXTRA_ALIASES, applied by
    normalize_query_text() after the hand-curated spelling fixes."""
    for alias, canonical in extra.items():
        a = alias.lower().strip()
        if a and a not in ALIASES and a not in EXTRA_ALIASES:
            EXTRA_ALIASES[a] = canonical
