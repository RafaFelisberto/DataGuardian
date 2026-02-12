from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .detectors.base import Match


_DEFAULT_WEIGHTS: Dict[str, int] = {
    # High
    "CREDIT_CARD": 10,
    "CreditCard": 10,
    "CREDIT_CARD_NUMBER": 10,
    "CPF": 9,
    "CNPJ": 9,
    "PASSWORD": 9,
    "API_KEY": 9,
    "TOKEN": 9,
    # Medium
    "EMAIL": 6,
    "Email": 6,
    "IP_ADDRESS": 5,
    "PHONE": 5,
    "IBAN": 6,
}


@dataclass(frozen=True)
class RiskSummary:
    score: int
    level: str
    counts_by_type: Dict[str, int]


def normalize_type(t: str) -> str:
    return (t or "").strip().upper()


def score_matches(matches: Iterable[Match]) -> RiskSummary:
    counts: Dict[str, int] = {}
    score = 0
    for m in matches:
        t = normalize_type(m.type)
        counts[t] = counts.get(t, 0) + 1
        score += _DEFAULT_WEIGHTS.get(t, 3)

    # volume penalty (helps show seriousness on dumps)
    total = sum(counts.values())
    if total >= 50:
        score += 30
    elif total >= 10:
        score += 10

    if score >= 60:
        level = "CRITICAL"
    elif score >= 25:
        level = "HIGH"
    elif score >= 10:
        level = "MEDIUM"
    else:
        level = "LOW"

    return RiskSummary(score=score, level=level, counts_by_type=counts)
