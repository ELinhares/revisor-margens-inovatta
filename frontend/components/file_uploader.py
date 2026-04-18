import requests
import streamlit as st

from config import BACKEND_URL


def render_file_uploader() -> tuple:
    """Returns (uploaded_file_bytes, validation_info_or_None)."""
    st.subheader("3. Upload do Arquivo Excel")

    st.markdown(
        """
        **Colunas obrigatórias no arquivo:**
        `Código do Produto` · `Produto` · `Venda (R$)` · `Margem Atual`
        """,
    )

    uploaded = st.file_uploader(
        "Selecione o arquivo Excel (.xlsx)",
        type=["xlsx", "xls"],
        key="excel_upload",
        help="O arquivo deve conter as 4 colunas obrigatórias listadas acima.",
    )

    if uploaded is None:
        return None, None

    file_bytes = uploaded.read()

    with st.spinner("Validando arquivo..."):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/v1/validate",
                files={"file": (uploaded.name, file_bytes, "application/octet-stream")},
                timeout=30,
            )
            resp.raise_for_status()
            info = resp.json()
        except requests.exceptions.ConnectionError:
            st.error("Não foi possível conectar ao servidor. Verifique se o backend está disponível.")
            return None, None
        except Exception as exc:
            st.error(f"Erro na validação: {exc}")
            return None, None

    st.markdown("**Resultado da Validação**")

    col_a, col_b = st.columns(2)
    with col_a:
        if info["status"] == "ok":
            st.markdown('<p class="status-ok">✔ Arquivo lido corretamente</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-error">✘ Problemas encontrados</p>', unsafe_allow_html=True)

    with col_b:
        st.markdown(f"**{info['total_rows']}** produtos encontrados")

    # Column check
    col_found, col_missing = st.columns(2)
    with col_found:
        if info["columns_found"]:
            st.success("Colunas identificadas: " + ", ".join(f"`{c}`" for c in info["columns_found"]))
    with col_missing:
        if info["missing_columns"]:
            st.error("Colunas ausentes: " + ", ".join(f"`{c}`" for c in info["missing_columns"]))

    if info["status"] == "ok" and info["preview"]:
        with st.expander("Pré-visualização dos dados (5 primeiras linhas)", expanded=True):
            import pandas as pd
            st.dataframe(pd.DataFrame(info["preview"]), use_container_width=True)

    if info["status"] != "ok":
        st.warning("Corrija as colunas ausentes e faça o upload novamente.")
        return None, None

    return file_bytes, info
