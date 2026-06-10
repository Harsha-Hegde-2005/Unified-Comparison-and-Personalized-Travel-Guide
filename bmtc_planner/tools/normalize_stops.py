#!/usr/bin/env python3
"""
tools/normalize_stops.py
=========================
Cleans and normalizes stop names in bmtc_stop_level_cleaned.csv.

Run BEFORE build_stop_clusters.py:
    cd bmtc_planner
    python tools/normalize_stops.py
    python tools/build_stop_clusters.py

Problems fixed:
  1. Word-order variants   → canonical order (area word first)
     "5th Block Jayanagara" → "Jayanagara 5th Block"
  2. Case inconsistency    → smart Title Case
     "KODIHALLI", "KodIhalli" → "Kodihalli"
     "38th Cross" → "38th Cross" (ordinals stay lowercase)
  3. Abbreviation expansion
     "Jn" → "Junction", "Blk" → "Block"
  4. Double/extra spaces   → single space
  5. Tollgate/TollGate     → Tollgate
"""

import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from core.config import STOP_LEVEL_CLEANED

# ── Abbreviation expansion ────────────────────────────────────────────────────
ABBREV_MAP = {
    "jn":       "Junction",
    "jnc":      "Junction",
    "st":       "Street",
    "blk":      "Block",
    "rd":       "Road",
    "tollgate": "Tollgate",
    "tollGate": "Tollgate",
}

# ── Known acronyms — always keep UPPERCASE ────────────────────────────────────
KEEP_UPPER = {
    "bda", "hsr", "btm", "hal", "keb", "itpl", "cmrit", "sap",
    "bpl", "ypr", "rmc", "ttmc", "iskcon", "hmt", "bel", "esi",
    "pvt", "ltd", "mg", "kr", "jp", "rv", "ms", "nice",
    "bmtc", "ksrtc", "bial", "itbp",
}

# ── Ordinal pattern: 1st, 2nd, 3rd, 38th etc ─────────────────────────────────
_ORDINAL = re.compile(r"^(\d+)(st|nd|rd|th)$", re.IGNORECASE)

# ── Manual fixes for known bad word-order / casing cases ─────────────────────
MANUAL_FIXES = {
    "5th block jayanagara":              "Jayanagara 5th Block",
    "3rd block jayanagara":              "Jayanagara 3rd Block",
    "4th block jayanagara":              "Jayanagara 4th Block",
    "6th block jayanagara":              "Jayanagara 6th Block",
    "9th block jayanagara":              "Jayanagara 9th Block",
    "6th block rajajinagara":            "Rajajinagara 6th Block",
    "railway station kengeri":           "Kengeri Railway Station",
    "magadi road tollgate":              "Magadi Road Tollgate",
    "bda complex koramangala":           "Koramangala BDA Complex",
    "bda complex  koramangala":          "Koramangala BDA Complex",
    "police station ramamurthinagar":    "Ramamurthinagar Police Station",
    "ayyappa temple jalahalli cross":    "Jalahalli Cross Ayyappa Temple",
    "shopping complex hmt":              "HMT Shopping Complex",
    "jalahalli cross":                   "Jalahalli Cross",
    "jalahalli cross ayyappa temple":    "Jalahalli Cross Ayyappa Temple",
    "nagavara junction":                 "Nagavara Junction",
    "mekhri circle":                     "Mekhri Circle",
    "kodihalli":                         "Kodihalli",
    "kodihalli":                         "Kodihalli",
    "charles school":                    "Charles School",
    "iskcon temple":                     "ISKCON Temple",
    "dubasi palya cross":                "Dubasi Palya Cross",
    "kadabagere gate":                   "Kadabagere Gate",
    "rukmini nagara":                    "Rukmini Nagara",
    "wilson garden police station":      "Wilson Garden Police Station",
    "wilson garden police station":      "Wilson Garden Police Station",
    "hsr bda complex":                   "HSR BDA Complex",
    "b p l":                             "BPL",
    "ypr rmc":                           "YPR RMC",
}


def _smart_title(s: str) -> str:
    """
    Title case with two special rules:
      - Ordinals (1st, 2nd, 38th) keep lowercase suffix
      - Known acronyms (BDA, BTM…) stay ALL CAPS
    """
    tokens = s.split()
    out = []
    for t in tokens:
        prefix = "(" if t.startswith("(") else ""
        suffix = ")" if t.endswith(")") else ""
        core   = t.strip("()")
        m = _ORDINAL.match(core)
        if m:
            # Ordinal: "38th" → "38th", not "38Th"
            out.append(prefix + m.group(1) + m.group(2).lower() + suffix)
        elif core.lower() in KEEP_UPPER:
            out.append(prefix + core.upper() + suffix)
        else:
            out.append(prefix + core.title() + suffix)
    return " ".join(out)


def normalize_stop_name(raw: str) -> str:
    if not isinstance(raw, str):
        return str(raw)

    # 1. Collapse whitespace
    name = re.sub(r"\s+", " ", raw.strip())

    # 2. Manual fix (case-insensitive lookup)
    if name.lower() in MANUAL_FIXES:
        return MANUAL_FIXES[name.lower()]

    # 3. Expand abbreviations
    tokens = name.split()
    expanded = []
    for t in tokens:
        tl = t.lower().rstrip(".")
        expanded.append(ABBREV_MAP[tl] if tl in ABBREV_MAP else t)
    name = " ".join(expanded)

    # 4. Smart title case
    name = _smart_title(name)

    # 5. Final whitespace cleanup
    return re.sub(r"\s+", " ", name).strip()


if __name__ == "__main__":
    print("Loading dataset…")
    df = pd.read_csv(STOP_LEVEL_CLEANED)
    original_unique = df["stop_name"].nunique()
    print(f"  {len(df):,} rows, {original_unique} unique stop names")

    print("Normalizing stop names…")
    df["stop_name_normalized"] = df["stop_name"].apply(normalize_stop_name)

    after_unique = df["stop_name_normalized"].nunique()
    collapsed    = original_unique - after_unique
    print(f"  Before: {original_unique} unique names")
    print(f"  After:  {after_unique} unique names ({collapsed} variants collapsed)")

    # Show what changed
    changed = (
        df[df["stop_name"] != df["stop_name_normalized"]]
        [["stop_name", "stop_name_normalized"]]
        .drop_duplicates()
        .sort_values("stop_name")
    )
    print(f"\n{len(changed)} stop names changed. Sample:")
    for _, row in changed.head(40).iterrows():
        print(f"  '{row['stop_name']}' → '{row['stop_name_normalized']}'")

    # Save
    df["stop_name"] = df["stop_name_normalized"]
    df = df.drop(columns=["stop_name_normalized"])
    df["stop_norm"] = df["stop_name"].str.strip().str.lower()
    df.to_csv(STOP_LEVEL_CLEANED, index=False)
    print(f"\nSaved → {STOP_LEVEL_CLEANED}")
    print("Next: python tools/build_stop_clusters.py")