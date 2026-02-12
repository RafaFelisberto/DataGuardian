from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .base import Match

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.predefined_recognizers import (
        EmailRecognizer,
        CreditCardRecognizer,
        IbanRecognizer,
        IpRecognizer,
        MedicalLicenseRecognizer,
    )

    _PRESIDIO_AVAILABLE = True
except Exception:
    AnalyzerEngine = None  # type: ignore
    RecognizerRegistry = None  # type: ignore
    _PRESIDIO_AVAILABLE = False


@dataclass
class PresidioDetector:
    """Optional detector using Microsoft Presidio.

    NOTE: Most default recognizers are English-oriented. We keep it as a useful
    add-on, not the main source of truth.
    """

    name: str = "presidio"

    def __post_init__(self) -> None:
        self._engine = None
        if not _PRESIDIO_AVAILABLE:
            return

        try:
            registry = RecognizerRegistry()
            registry.add_recognizer(EmailRecognizer())
            registry.add_recognizer(CreditCardRecognizer())
            registry.add_recognizer(IbanRecognizer())
            registry.add_recognizer(IpRecognizer())
            registry.add_recognizer(MedicalLicenseRecognizer())
            self._engine = AnalyzerEngine(registry=registry)
        except Exception:
            self._engine = None

    @property
    def available(self) -> bool:
        return self._engine is not None

    def detect(self, text: str) -> List[Match]:
        if not self._engine or not text:
            return []
        try:
            results = self._engine.analyze(text=text, language="en")
            out: List[Match] = []
            for r in results:
                out.append(Match(detector=self.name, type=r.entity_type, raw=text[r.start : r.end]))
            return out
        except Exception:
            return []
