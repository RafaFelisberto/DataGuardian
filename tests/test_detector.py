import pytest
from core.detector import SensitiveDataDetector

def test_cpf_detection():
    detector = SensitiveDataDetector()
    result = detector.detect_regex("CPF: 123.456.789-09")
    assert "CPF" in result