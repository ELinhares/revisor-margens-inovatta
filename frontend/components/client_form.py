import re
import streamlit as st


def _format_cnpj(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    return raw


def _validate_cnpj(cnpj: str) -> bool:
    digits = re.sub(r"\D", "", cnpj)
    return len(digits) == 14


def render_client_form() -> tuple[str, str]:
    st.subheader("1. Identificação do Cliente")

    col1, col2 = st.columns(2)
    with col1:
        cnpj_raw = st.text_input(
            "CNPJ *",
            placeholder="00.000.000/0000-00",
            help="Informe o CNPJ do cliente (apenas números ou com formatação).",
            key="cnpj_input",
        )
    with col2:
        razao_social = st.text_input(
            "Razão Social / Nome do Cliente *",
            placeholder="Ex: Empresa Exemplo Ltda",
            key="razao_social_input",
        )

    cnpj_valid = _validate_cnpj(cnpj_raw)
    razao_valid = len(razao_social.strip()) >= 3

    if cnpj_raw and not cnpj_valid:
        st.error("CNPJ inválido. Informe os 14 dígitos numéricos.")

    if razao_social and not razao_valid:
        st.warning("Razão Social deve ter pelo menos 3 caracteres.")

    cnpj_formatted = _format_cnpj(cnpj_raw) if cnpj_valid else ""

    return cnpj_formatted, razao_social.strip()
