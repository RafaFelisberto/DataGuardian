import streamlit as st
import pandas as pd
from core.file_processor import process_file
from core.detector import SensitiveDataDetector

st.set_page_config(page_title="DataGuardian", layout="wide")
st.title("🔍 DataGuardian - Monitor de Segurança de Dados")

uploaded_file = st.file_uploader("Carregue seu arquivo de dados", 
                              type=["csv", "json", "txt", "sql"])

if uploaded_file:
    with st.spinner("Processando arquivo..."):
        df = process_file(uploaded_file)
        
        detector = SensitiveDataDetector()
        findings = []
        
        for col in df.columns:
            for text in df[col].astype(str).unique():
                regex_matches = detector.detect_regex(text)
                ner_matches = detector.detect_ner(text)
                if regex_matches or ner_matches:
                    findings.append({
                        "Coluna": col,
                        "Valor": text,
                        "Padrões Detectados": regex_matches.keys(),
                        "NLP": ner_matches
                    })
        
        st.subheader("📌 Encontrados Dados Sensíveis")
        st.dataframe(pd.DataFrame(findings))
        
        # Análise de anomalias
        if 'access_log' in df.columns:
            analyzer = AnomalyAnalyzer()
            anomalies = analyzer.detect_access_anomalies(df['access_log'])
            st.subheader("🚨 Anomalias Detectadas")
            st.write(f"{sum(anomalies == -1)} possíveis anomalias encontradas")