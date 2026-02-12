import re
import json
import os
from typing import Dict, List, Tuple, Any, Optional

import spacy

# Presidio é opcional: o app não deve quebrar se não estiver instalado
try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.predefined_recognizers import (
        EmailRecognizer,
        CreditCardRecognizer,
        IbanRecognizer,
        IpRecognizer,
        MedicalLicenseRecognizer,
    )
    PRESIDIO_AVAILABLE = True
except Exception:
    AnalyzerEngine = None  # type: ignore
    RecognizerRegistry = None  # type: ignore
    PRESIDIO_AVAILABLE = False




class SensitiveDataDetector:
    def __init__(self) -> None:
        # Carrega padrões regex
        self.patterns: Dict[str, str] = self._load_patterns()

        # Carrega modelo SpaCy (português)
        try:
            self.nlp = spacy.load("pt_core_news_sm")
        except Exception as e:
            print(f"⚠️ Modelo SpaCy não encontrado: {e}")
            self.nlp = None

        # Configura Presidio com reconhecedores estáveis (opcional)
        self.presidio: Optional[Any] = None
        if PRESIDIO_AVAILABLE:
            try:
                registry = RecognizerRegistry()

                # Adiciona reconhecedores disponíveis e "seguros" (não dependem de recognizers EUA)
                registry.add_recognizer(EmailRecognizer())
                registry.add_recognizer(CreditCardRecognizer())
                registry.add_recognizer(IbanRecognizer())
                registry.add_recognizer(IpRecognizer())
                registry.add_recognizer(MedicalLicenseRecognizer())

                self.presidio = AnalyzerEngine(registry=registry)
            except Exception as e:
                print(f"⚠️ Erro ao inicializar Presidio: {e}")
                self.presidio = None

    def _load_patterns(self) -> Dict[str, str]:
        """Carrega padrões regex de um arquivo JSON (caminho relativo ao projeto)."""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            patterns_path = os.path.join(base_dir, "models", "pi_patterns.json")
            with open(patterns_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar padrões: {e}")
            return {}

    @staticmethod
    def _digits_only(value: str) -> str:
        return re.sub(r"\D", "", value or "")

    def validate_cpf(self, cpf: str) -> bool:
        """Valida CPF usando o algoritmo oficial."""
        cpf_digits = self._digits_only(cpf)
        if len(cpf_digits) != 11 or cpf_digits == cpf_digits[0] * 11:
            return False

        def calc_digit(cpf_str: str, peso: int) -> int:
            soma = sum(int(d) * (peso - i) for i, d in enumerate(cpf_str[: peso - 1]))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto

        digito1 = calc_digit(cpf_digits, 10)
        digito2 = calc_digit(cpf_digits, 11)
        return cpf_digits[-2:] == f"{digito1}{digito2}"

    def validate_cnpj(self, cnpj: str) -> bool:
        """Valida CNPJ (algoritmo de dígitos verificadores)."""
        cnpj_digits = self._digits_only(cnpj)
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

    def detect_regex(self, text: str) -> Dict[str, List[str]]:
        """Detecta padrões usando regex com validação adicional."""
        matches: Dict[str, List[str]] = {}
        if not text:
            return matches

        for name, pattern in self.patterns.items():
            try:
                found = re.findall(pattern, text, flags=re.IGNORECASE)
            except re.error:
                continue

            if not found:
                continue

            # Normaliza retorno do findall (pode vir tupla em regex com grupos)
            flat: List[str] = []
            for item in found:
                if isinstance(item, tuple):
                    flat.append("".join(item))
                else:
                    flat.append(str(item))

            # Validações específicas
            if name == "CPF":
                flat = [v for v in flat if self.validate_cpf(v)]
                if not flat:
                    continue
            if name == "CNPJ":
                flat = [v for v in flat if self.validate_cnpj(v)]
                if not flat:
                    continue

            matches[name] = list(dict.fromkeys(flat))  # remove duplicados preservando ordem

        return matches

    def detect_ner_spacy(self, text: str) -> List[Tuple[str, str]]:
        """Detecção de entidades com SpaCy."""
        if not self.nlp or not text:
            return []

        doc = self.nlp(text)
        # labels variam por modelo; filtramos apenas algumas úteis
        allow = {"PER", "PERSON", "ORG", "LOC", "GPE", "DATE"}
        out: List[Tuple[str, str]] = []
        for ent in doc.ents:
            if ent.label_ in allow:
                out.append((ent.text, ent.label_))
        return out

    def detect_ner_presidio(self, text: str) -> List[Tuple[str, str]]:
        """Detecção avançada com Presidio (opcional)."""
        if not self.presidio or not text:
            return []

        try:
            # Presidio trabalha bem com 'en'. Para pt, muitos recognizers não existem por padrão.
            results = self.presidio.analyze(text=text, language="en")
            return [(r.entity_type, text[r.start : r.end]) for r in results]
        except Exception as e:
            print(f"Erro no Presidio: {e}")
            return []

    @staticmethod
    def mask_value(value: str, keep_last: int = 4) -> str:
        """Mascaramento simples para evitar exibir PII em claro na UI."""
        if value is None:
            return value
        s = str(value)
        if len(s) <= keep_last:
            return "*" * len(s)
        return "*" * (len(s) - keep_last) + s[-keep_last:]
