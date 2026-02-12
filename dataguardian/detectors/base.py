from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol


@dataclass(frozen=True)
class Match:
    detector: str
    type: str
    raw: str


class Detector(Protocol):
    name: str

    def detect(self, text: str) -> List[Match]:
        ...
