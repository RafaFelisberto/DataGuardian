import streamlit as st
import pandas as pd
import plotly.express as px

from core.file_processor import process_file
from core.detector import SensitiveDataDetector
from core.analyzer import AnomalyAnalyzer
from utils.encryption import DataEncryptor

# Configuração da página
st.set_page_config(page_title="DataGuardian", layout="wide")
st.title("🔍 DataGuardian - Monitor de Segurança de Dados")

MAX_ROWS_PREVIEW = 200
MAX_UNIQUE_PER_COLUMN = 200  # evita DoS por coluna gigante

uploaded_file = st.file_uploader("Carregue seu arquivo de dados", type=["csv", "json", "jsonl", "txt", "sql"])

if uploaded_file:
    st.write("✅ Arquivo carregado:", uploaded_file.name)
    st.write("📁 Tipo do arquivo:", uploaded_file.type)

    try:
        df = process_file(uploaded_file)
        if df.empty:
            st.warning("❌ Arquivo carregado está vazio ou inválido.")
            st.stop()

        show_raw = st.checkbox("Mostrar dados brutos (pode conter PII em claro)", value=False)
        with st.expander("📂 Prévia dos dados"):
            st.dataframe(df.head(MAX_ROWS_PREVIEW) if show_raw else df.head(MAX_ROWS_PREVIEW))

        detector = SensitiveDataDetector()
        findings = []

        # varredura limitada por segurança/performance
        for col in df.columns:
            series = df[col].dropna().astype(str)
            # pega valores únicos limitados
            values = series.head(MAX_ROWS_PREVIEW).unique().tolist()[:MAX_UNIQUE_PER_COLUMN]

            for text in values:
                regex_matches = detector.detect_regex(text)
                presidio_matches = detector.detect_ner_presidio(text)
                if regex_matches or presidio_matches:
                    findings.append(
                        {
                            "Coluna": col,
                            "Valor (mascarado)": detector.mask_value(text, keep_last=4),
                            "Regex": ", ".join(sorted(regex_matches.keys())) if regex_matches else "",
                            "Presidio": ", ".join(sorted({t for t, _ in presidio_matches})) if presidio_matches else "",
                        }
                    )

        if not findings:
            st.info("✅ Nenhum dado sensível foi encontrado na amostra analisada.")
            st.stop()

        findings_df = pd.DataFrame(findings)
        st.subheader("📌 Dados Sensíveis Detectados (valores mascarados)")
        st.dataframe(findings_df)

        st.subheader("📊 Distribuição de Tipos de Dados Sensíveis")
        # conta por Regex
        if "Regex" in findings_df.columns and not findings_df["Regex"].fillna("").eq("").all():
            exploded = findings_df.assign(Regex=findings_df["Regex"].str.split(", ")).explode("Regex")
            exploded = exploded[exploded["Regex"].fillna("").ne("")]
            if not exploded.empty:
                fig = px.histogram(exploded, x="Regex")
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("🔐 Criptografia")
        st.caption("Por segurança, prefira usar a chave via variável de ambiente DATAGUARDIAN_ENCRYPTION_KEY.")
        use_env = st.checkbox("Usar chave via variável de ambiente", value=True)

        try:
            encryptor = DataEncryptor(use_env_key=use_env)
        except Exception as e:
            st.error(f"Erro ao inicializar criptografia: {e}")
            st.stop()

        cols = list(df.columns)
        col_to_encrypt = st.selectbox("Selecione uma coluna para criptografar", cols)

        if st.button("Criptografar coluna"):
            encrypted_df = encryptor.encrypt_column(df, col_to_encrypt)
            st.success(f"Coluna '{col_to_encrypt}' criptografada (preview abaixo).")
            st.dataframe(encrypted_df.head(50))

        st.divider()

        st.subheader("🛡️ Detecção de Anomalias (MVP)")
        st.caption("Este módulo espera logs estruturados; aqui fica como base para evoluir (ex.: auditoria de acessos).")

        if st.button("Rodar exemplo de anomalias"):
            # exemplo simples
            logs = [
                {"timestamp": "2026-02-12 10:00:00", "user": "alice", "ip": "1.1.1.1", "access_count": 1, "data_accessed": "x" * 100, "data_type": "EMAIL"},
                {"timestamp": "2026-02-12 03:10:00", "user": "alice", "ip": "1.1.1.1", "access_count": 80, "data_accessed": "x" * 20000, "data_type": "CPF"},
            ]
            analyzer = AnomalyAnalyzer()
            results = analyzer.detect_anomalies(logs)
            st.dataframe(pd.DataFrame(results))

    except Exception as e:
        st.error(f"Erro geral: {e}")
