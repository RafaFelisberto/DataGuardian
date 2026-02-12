from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List

from .base import Match


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _validate_cpf(cpf: str) -> bool:
    cpf_digits = _digits_only(cpf)
    if len(cpf_digits) != 11 or cpf_digits == cpf_digits[0] * 11:
        return False

    def calc_digit(cpf_str: str, peso: int) -> int:
        soma = sum(int(d) * (peso - i) for i, d in enumerate(cpf_str[: peso - 1]))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    digito1 = calc_digit(cpf_digits, 10)
    digito2 = calc_digit(cpf_digits, 11)
    return cpf_digits[-2:] == f"{digito1}{digito2}"


def _validate_cnpj(cnpj: str) -> bool:
    cnpj_digits = _digits_only(cnpj)
    if len(cnpj_digits) != 14 or cnpj_digits == cnpj_digits[0] * 14:
        return False

    def calc_digit(base: str, weights: List[int]) -> str:
        s = sum(int(d) * w for d, w in zip(base, weights))
        r = s % 11
        return "0" if r < 2 else str(11 - r)

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6] + w1

    d1 = calc_digit(cnpj_digits[:12], w1)
    d2 = calc_digit(cnpj_digits[:12] + d1, w2)
    return cnpj_digits[-2:] == d1 + d2


@dataclass
class RegexDetector:
    """Fast detector based on compiled regex patterns."""

    patterns_path: str | None = None
    name: str = "regex"

    def __post_init__(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        default_path = os.path.join(base_dir, "models", "pi_patterns.json")
        path = self.patterns_path or default_path

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw: Dict[str, str] = json.load(f)
        except Exception:
            raw = {}

        self._compiled: Dict[str, re.Pattern] = {}
        for k, v in raw.items():
            try:
                self._compiled[k] = re.compile(v, flags=re.IGNORECASE)
            except re.error:
                # skip invalid patterns
                continue

    def detect(self, text: str) -> List[Match]:
        if not text:
            return []

        out: List[Match] = []
        for typ, pattern in self._compiled.items():
            found = pattern.findall(text)
            if not found:
                continue

            flat: List[str] = []
            for item in found:
                if isinstance(item, tuple):
                    flat.append("".join(item))
                else:
                    flat.append(str(item))

            # extra validation to reduce FP
            if typ == "CPF":
                flat = [v for v in flat if _validate_cpf(v)]
            elif typ == "CNPJ":
                flat = [v for v in flat if _validate_cnpj(v)]

            for v in dict.fromkeys(flat):
                out.append(Match(detector=self.name, type=typ, raw=v))

        return out
