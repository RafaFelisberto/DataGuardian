import re
import spacy
import json
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.predefined_recognizers import (
    EmailRecognizer,
    CreditCardRecognizer,
    IbanRecognizer,
    IpRecognizer,
    MedicalLicenseRecognizer,
)

class SensitiveDataDetector:
    def __init__(self):
        # Carrega padrões regex
        self.patterns = self._load_patterns()
        
        # Carrega modelo SpaCy (português)
        try:
            self.nlp = spacy.load("pt_core_news_sm")
        except Exception as e:
            print(f"⚠️ Modelo SpaCy não encontrado: {e}")
            self.nlp = None
        
        # Configura Presidio com reconhecedores manuais
        try:
            registry = RecognizerRegistry()
            
            # Adiciona reconhecedores manualmente
            registry.add_recognizer(EmailRecognizer())
            registry.add_recognizer(UsPhoneRecognizer())
            registry.add_recognizer(CreditCardRecognizer())
            registry.add_recognizer(IbanRecognizer())
            registry.add_recognizer(SsnRecognizer())
            registry.add_recognizer(IpRecognizer())
            registry.add_recognizer(MedicalLicenseRecognizer())
            
            # Inicializa o motor de análise
            self.presidio = AnalyzerEngine(registry=registry)
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Presidio: {e}")
            self.presidio = None

    def _load_patterns(self):
        """Carrega padrões regex de um arquivo JSON"""
        try:
            with open('models/pi_patterns.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar padrões: {e}")
            return {}

    def validate_cpf(self, cpf):
        """Valida CPF usando o algoritmo oficial"""
        cpf = re.sub(r'\D', '', cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        def calc_digit(cpf_str, peso):
            soma = sum(int(digito) * (peso - i) for i, digito in enumerate(cpf_str[:peso-1]))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto

        digito1 = calc_digit(cpf, 10)
        digito2 = calc_digit(cpf, 11)
        return cpf[-2:] == f"{digito1}{digito2}"

    def detect_regex(self, text):
        """Detecta padrões usando regex com validação adicional"""
        matches = {}
        for name, pattern in self.patterns.items():
            found = re.findall(pattern, text, re.IGNORECASE)
            if found:
                if name == "CPF" and not all(self.validate_cpf(f) for f in found):
                    continue
                matches[name] = found
        return matches

    def detect_ner_spacy(self, text):
        """Detecção de entidades com SpaCy"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents 
                if ent.label_ in ['PERSON', 'PHONE', 'EMAIL', 'DATE', 'ORG']]

    def detect_ner_presidio(self, text):
        """Detecção avançada com Presidio (suporta mais tipos de PII)"""
        if not self.presidio:
            return []
        
        try:
            # Use 'en' se o texto for em inglês, 'pt' se for em português
            results = self.presidio.analyze(text=text, language="en")
            return [(result.entity_type, text[result.start:result.end]) for result in results]
        except Exception as e:
            print(f"Erro no Presidio: {e}")
            return []