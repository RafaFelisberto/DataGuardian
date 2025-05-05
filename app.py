import streamlit as st
import pandas as pd
import plotly.express as px
from core.detector import SensitiveDataDetector

st.set_page_config(page_title="DataGuardian", layout="wide")
st.title("🔍 DataGuardian - Monitor de Segurança de Dados")

uploaded_file = st.file_uploader("Carregue seu arquivo de dados", 
                              type=["csv", "json", "txt", "sql"])

if uploaded_file:
    df = process_file(uploaded_file)  # Função de file_processor.py
    detector = SensitiveDataDetector()
    
    # Detecção de dados sensíveis
    findings = []
    for col in df.columns:
        for text in df[col].astype(str).unique():
            regex_matches = detector.detect_regex(text)
            presidio_matches = detector.detect_presidio(text)
            if regex_matches or presidio_matches:
                findings.append({
                    "Coluna": col,
                    "Valor": text,
                    "Regex": regex_matches.keys(),
                    "Presidio": presidio_matches
                })
    
    # Visualização interativa
    st.subheader("📌 Encontrados Dados Sensíveis")
    st.dataframe(pd.DataFrame(findings))
    
    # Gráfico de distribuição
    st.subheader("📊 Distribuição de Dados Sensíveis")
    fig = px.treemap(pd.DataFrame(findings), path=["Regex", "Presidio"], 
                    title="Tipos de Dados Sensíveis Detectados")
    st.plotly_chart(fig)
    
    # Filtro por tipo de dado
    selected_type = st.sidebar.selectbox("Tipo de Dado", ["Todos", "CPF", "E-mail", "Senha"])
    filtered = [f for f in findings if selected_type in f["Regex"] or 
                any(selected_type in item for item in f["Presidio"])]