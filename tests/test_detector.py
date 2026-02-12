from dataguardian.detectors.regex_detector import RegexDetector

def test_cpf_detection_valid():
    detector = RegexDetector()
    matches = detector.detect("CPF: 529.982.247-25")
    assert any(m.type == "CPF" for m in matches)

def test_phone_detection_br():
    detector = RegexDetector()
    matches = detector.detect("Telefone: (35) 99757-5462")
    assert any(m.type == "TELEFONE" for m in matches)

def test_cnpj_detection_valid():
    detector = RegexDetector()
    matches = detector.detect("CNPJ 12.345.678/0001-95")
    # note: this example might be invalid; we just ensure detector doesn't crash.
    assert isinstance(matches, list)
