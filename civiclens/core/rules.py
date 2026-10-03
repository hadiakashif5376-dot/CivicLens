"""Keyword rules from the original prototype.

Step 1 uses these for the *suggested* category and urgency.
Step 2 replaces them with an LLM call and keeps these as the fallback when that call fails.
"""

CATEGORY_KEYWORDS = [
    ("Drainage", ["drain", "sewage", "sewer", "wastewater", "standing water", "flood", "stagnant", "smell", "mosquito"]),
    ("Waste management", ["garbage", "trash", "rubbish", "waste", "bin", "dump"]),
    ("Roads", ["pothole", "road", "street broken", "pavement", "footpath", "crack"]),
    ("Water supply", ["water supply", "no water", "water leak", "pipe", "tap water"]),
    ("Streetlights", ["streetlight", "street light", "lamp", "electric pole", "light not working"]),
    ("Public safety", ["danger", "exposed wire", "accident", "unsafe", "hazard"]),
]
HIGH_WORDS = ["urgent", "emergency", "overflow", "flood", "exposed wire", "danger", "school", "hospital", "sewage"]
MEDIUM_WORDS = ["blocked", "broken", "leak", "no water", "pothole", "accumulating", "smell"]


def _has_any(text: str, words) -> bool:
    return any(w in text for w in words)


def suggest_category(text: str) -> str:
    t = text.lower()
    for category, words in CATEGORY_KEYWORDS:
        if _has_any(t, words):
            return category
    return "Other"


def suggest_urgency(text: str) -> str:
    t = text.lower()
    if _has_any(t, HIGH_WORDS):
        return "High"
    if _has_any(t, MEDIUM_WORDS):
        return "Medium"
    return "Low"
