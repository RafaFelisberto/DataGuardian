import pytest
from core.detector import SensitiveDataDetector

def test_cpf_detection_valid():
    detector = SensitiveDataDetector()
    result = detector.detect_regex("CPF: 529.982.247-25")
    assert "CPF" in result

def test_phone_detection_br():
    detector = SensitiveDataDetector()
    result = detector.detect_regex("Telefone: (35) 99757-5462")
    assert "TELEFONE" in result
