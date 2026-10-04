"""Chooses the suggested category, urgency and summary for a new complaint.

Groq is tried first when a key is set. Keyword rules are the fallback, and also act as a safety floor:
the urgency is never lower than the rules would give, so a model that underrates a hazard cannot hide it.
"""
from dataclasses import dataclass
from typing import Optional

from .. import ai, rules

_RANK = {"Low": 0, "Medium": 1, "High": 2}


@dataclass(frozen=True)
class Triage:
    category: str
    urgency: str
    summary: Optional[str]
    source: str  # "ai" or "rules"
    model: Optional[str] = None
    note: Optional[str] = None  # why the AI was not used, when it was tried and failed


def suggest(text: str, api_key: str = "", model: str = ai.DEFAULT_MODEL) -> Triage:
    rule_category = rules.suggest_category(text)
    rule_urgency = rules.suggest_urgency(text)
    if not api_key:
        return Triage(rule_category, rule_urgency, None, "rules")
    try:
        result = ai.classify(text, api_key, model)
    except ai.AiError as exc:
        return Triage(rule_category, rule_urgency, None, "rules", note=str(exc)[:200])
    urgency = max(result.urgency, rule_urgency, key=lambda u: _RANK[u])
    return Triage(result.category, urgency, result.summary, "ai", model=model)
