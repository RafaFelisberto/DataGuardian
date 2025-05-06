import streamlit as st
import pandas as pd
import plotly.express as px
from core.file_processor import process_file
from core.detector import SensitiveDataDetector
from core.analyzer import AnomalyAnalyzer
from utils.encryption import DataEncryptor
import datetime

# Configuração da página
st.set_page_config(page_title="DataGuardian", layout="wide")
st.title("🔍 DataGuardian - Monitor de Segurança de Dados")

# Upload do arquivo
uploaded_file = st.file_uploader("Carregue seu arquivo de dados", type=["csv", "json", "txt", "sql"])

if uploaded_file:
    st.write("✅ Arquivo carregado:", uploaded_file.name)
    st.write("📁 Tipo do arquivo:", uploaded_file.type)
    try:
        # Processa o arquivo
        df = process_file(uploaded_file)
        if df.empty:
            st.warning("❌ Arquivo carregado está vazio ou inválido.")
            st.stop()

        # Exibe os dados brutos
        with st.expander("📂 Ver Dados Carregados"):
            st.dataframe(df.head(100))

        # Detecção de dados sensíveis
        detector = SensitiveDataDetector()
        findings = []

        for col in df.columns:
            for text in df[col].astype(str).unique():
                regex_matches = detector.detect_regex(text)
                presidio_matches = detector.detect_ner_presidio(text)
                if regex_matches or presidio_matches:
                    findings.append({
                        "Coluna": col,
                        "Valor": text,
                        "Regex": list(regex_matches.keys()),
                        "Presidio": [f"{t}:{v}" for t, v in presidio_matches]
                    })

        if not findings:
            st.info("✅ Nenhum dado sensível foi encontrado.")
            st.stop()

        # Exibe os dados sensíveis encontrados
        findings_df = pd.DataFrame(findings)
        st.subheader("📌 Dados Sensíveis Detectados")
        st.dataframe(findings_df)

        # Visualização: Distribuição de tipos de dados
        st.subheader("📊 Distribuição de Dados Sensíveis")
        if not findings_df.empty:
            findings_df["Tipo"] = findings_df["Regex"].apply(lambda x: ", ".join(x) if x else "NLP")
            fig = px.histogram(findings_df, x="Tipo", title="Tipos de Dados Sensíveis Encontrados")
            st.plotly_chart(fig)

            # Treemap por tipo de dado
            fig_tree = px.treemap(findings_df, path=["Tipo"], title="Distribuição Hierárquica de Dados")
            st.plotly_chart(fig_tree)

        # Filtro por tipo de dado
        st.sidebar.subheader("🔎 Filtros")
        data_types = ["Todos"] + sorted(set(findings_df["Tipo"].str.split(", ").explode()))
        selected_type = st.sidebar.selectbox("Filtrar por Tipo de Dado", data_types)

        if selected_type != "Todos":
            filtered_df = findings_df[findings_df["Tipo"].str.contains(selected_type)]
            if not filtered_df.empty:
                st.subheader(f"🔍 Resultados Filtrados: {selected_type}")
                st.dataframe(filtered_df)
            else:
                st.warning(f"⚠️ Nenhum dado encontrado do tipo '{selected_type}'.")

        # Detecção de Anomalias
        st.subheader("🚨 Análise de Acesso Suspeito")
        if "timestamp" in df.columns:
            access_logs = [{
                "timestamp": ts,
                "user": "usuario_teste",
                "ip": "127.0.0.1",
                "access_count": 1,
                "data_accessed": row.to_string(),
                "data_type": "CPF" if "cpf" in row.to_string().lower() else "UNKNOWN"
            } for _, row in df.iterrows() for ts in [row.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))]]

            analyzer = AnomalyAnalyzer()
            anomalies = analyzer.detect_anomalies(access_logs)

            anomaly_records = [a for a in anomalies if a["anomaly"]]
            if anomaly_records:
                st.warning(f"⚠️ Foram encontradas {len(anomaly_records)} anomalias de acesso!")
                for i, record in enumerate(anomaly_records):
                    with st.expander(f"Anomalia #{i+1} - Score: {record['score']:.2f}"):
                        st.json(record)
            else:
                st.success("✅ Nenhuma anomalia de acesso detectada.")
        else:
            st.info("ℹ️ Não foi possível analisar anomalias: coluna 'timestamp' não encontrada.")

        # Criptografia de Dados Sensíveis
        st.subheader("🔒 Criptografia de Dados")
        encryptor = DataEncryptor(use_env_key=False)
        sensitive_columns = st.multiselect("Selecione colunas para criptografar", options=df.columns)

        if st.button("Criptografar Dados"):
            encrypted_df = df.copy()
            for col in sensitive_columns:
                encrypted_df = encryptor.encrypt_column(encrypted_df, col)
            st.session_state["encrypted_df"] = encrypted_df
            st.success("✅ Dados sensíveis criptografados com sucesso!")

        if "encrypted_df" in st.session_state:
            st.subheader("🔓 Dados Criptografados")
            st.dataframe(st.session_state["encrypted_df"].head(100))

            if st.button("Descriptografar Dados"):
                decrypted_df = st.session_state["encrypted_df"].copy()
                for col in sensitive_columns:
                    decrypted_df = encryptor.decrypt_column(decrypted_df, col)
                st.session_state["decrypted_df"] = decrypted_df
                st.success("🔓 Dados descriptografados com sucesso!")

        if "decrypted_df" in st.session_state:
            st.subheader("📂 Dados Descriptografados")
            st.dataframe(st.session_state["decrypted_df"].head(100))

    except Exception as e:
        st.error(f"❌ Ocorreu um erro: {e}")
        st.exception(e)

else:
    st.info("📥 Por favor, carregue um arquivo para começar a análise.")