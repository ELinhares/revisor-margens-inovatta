import json
import requests
import streamlit as st

from config import BACKEND_URL
from components.header import render_header
from components.client_form import render_client_form
from components.abc_config import render_abc_config
from components.file_uploader import render_file_uploader
from components.results import render_results

st.set_page_config(
    page_title="Revisor de Margens Inovatta",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_header()

cnpj, razao_social = render_client_form()

st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)

client_ok = bool(cnpj and razao_social and len(razao_social) >= 3)

desired_increase, max_increases = render_abc_config()

st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)

if not client_ok:
    st.info("Preencha o CNPJ e a Razão Social para prosseguir com o upload do arquivo.")
else:
    file_bytes, validation_info, column_mapping = render_file_uploader()

    if file_bytes is not None and validation_info is not None and column_mapping is not None:
        st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)
        st.subheader("4. Confirmar e Calcular")

        st.markdown(
            f"""
            **Resumo da análise a ser realizada:**
            - Cliente: **{razao_social}** (CNPJ: `{cnpj}`)
            - Acréscimo de margem desejado: **+{desired_increase:.2f}pp**
            - Restrições: A+ ≤ {max_increases['A+']}pp · A ≤ {max_increases['A']}pp · B ≤ {max_increases['B']}pp · C ≤ {max_increases['C']}pp
            - Total de produtos: **{validation_info['total_rows']}**
            """
        )

        if st.button("Confirmar e Calcular Margens Sugeridas", type="primary"):
            with st.spinner("Calculando margens sugeridas e salvando no Cloud Storage..."):
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/api/v1/process",
                        data={
                            "cnpj": cnpj,
                            "razao_social": razao_social,
                            "desired_margin_increase": str(desired_increase),
                            "max_increase_aplus": str(max_increases["A+"]),
                            "max_increase_a": str(max_increases["A"]),
                            "max_increase_b": str(max_increases["B"]),
                            "max_increase_c": str(max_increases["C"]),
                            "column_mapping_json": json.dumps(column_mapping),
                        },
                        files={"file": ("arquivo.xlsx", file_bytes, "application/octet-stream")},
                        timeout=120,
                    )

                    if resp.status_code == 200:
                        render_results(resp.json())
                    else:
                        try:
                            detail = resp.json().get("detail", resp.text)
                        except Exception:
                            detail = resp.text
                        st.error(f"Erro no processamento: {detail}")

                except requests.exceptions.ConnectionError:
                    st.error("Não foi possível conectar ao servidor. Verifique se o backend está disponível.")
                except requests.exceptions.Timeout:
                    st.error("O processamento demorou mais que o esperado. Tente novamente com um arquivo menor.")
                except Exception as exc:
                    st.error(f"Erro inesperado: {exc}")
