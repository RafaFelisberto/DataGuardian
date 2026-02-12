import streamlit as st
import pandas as pd
import plotly.express as px

from core.file_processor import process_file
from dataguardian.config import Settings
from dataguardian.scan import scan_dataframe
from dataguardian.reporting import to_html
from utils.encryption import DataEncryptor

st.set_page_config(page_title="DataGuardian", layout="wide")
st.title("🔍 DataGuardian - Monitor de Segurança de Dados")

settings = Settings()

uploaded_file = st.file_uploader(
    "Carregue seu arquivo de dados",
    type=["csv", "json", "jsonl", "txt", "sql"],
)

if uploaded_file:
    st.write("✅ Arquivo carregado:", uploaded_file.name)

    try:
        df = process_file(uploaded_file)
        if df.empty:
            st.warning("❌ Arquivo carregado está vazio ou inválido.")
            st.stop()

        show_raw = st.checkbox("Mostrar dados brutos (pode conter PII em claro)", value=False)
        with st.expander("📂 Prévia dos dados"):
            st.dataframe(df.head(settings.max_rows_preview) if show_raw else df.head(settings.max_rows_preview))

        report = scan_dataframe(df, target=uploaded_file.name, settings=settings)

        st.subheader("🧭 Risco (resumo)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Nível", report.summary.level)
        c2.metric("Score", report.summary.score)
        c3.metric("Tipos detectados", len(report.summary.counts_by_type))

        if not report.findings:
            st.info("✅ Nenhum dado sensível foi encontrado na amostra analisada.")
            st.stop()

        # Flatten findings for UI
        rows = []
        for f in report.findings:
            rows.append(
                {
                    "Local": f.location,
                    "Valor (mascarado)": f.masked_value,
                    "Tipos": ", ".join(sorted({m.type for m in f.matches})),
                    "Detectores": ", ".join(sorted({m.detector for m in f.matches})),
                }
            )
        findings_df = pd.DataFrame(rows)

        st.subheader("📌 Achados (valores mascarados)")
        st.dataframe(findings_df)

        st.subheader("📊 Distribuição de tipos")
        exploded = findings_df.assign(Tipos=findings_df["Tipos"].str.split(", ")).explode("Tipos")
        exploded = exploded[exploded["Tipos"].fillna("").ne("")]
        if not exploded.empty:
            fig = px.histogram(exploded, x="Tipos")
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("🧾 Exportar relatório")
        col1, col2 = st.columns(2)
        col1.download_button(
            "⬇️ Baixar JSON",
            data=report.to_json(),
            file_name=f"dataguardian_{uploaded_file.name}.json",
            mime="application/json",
        )
        col2.download_button(
            "⬇️ Baixar HTML",
            data=to_html(report),
            file_name=f"dataguardian_{uploaded_file.name}.html",
            mime="text/html",
        )

        st.divider()

        st.subheader("🔐 Mitigação (criptografia)")
        st.caption("Por segurança, a chave deve vir de DATAGUARDIAN_ENCRYPTION_KEY (modo padrão).")
        allow_file_key = st.checkbox("Permitir chave em arquivo local (NÃO recomendado)", value=False)

        try:
            encryptor = DataEncryptor(use_env_key=True, allow_file_key=allow_file_key)
        except Exception as e:
            st.error(f"Erro ao inicializar criptografia: {e}")
            st.stop()

        cols = list(df.columns)
        col_to_encrypt = st.selectbox("Selecione uma coluna para criptografar", cols)

        if st.button("Criptografar coluna"):
            encrypted_df = encryptor.encrypt_column(df, col_to_encrypt)
            st.success(f"Coluna '{col_to_encrypt}' criptografada (preview abaixo).")
            st.dataframe(encrypted_df.head(50))

    except Exception as e:
        st.error(f"Erro geral: {e}")
