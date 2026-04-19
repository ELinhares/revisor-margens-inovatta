import requests
import streamlit as st
import pandas as pd

from config import BACKEND_URL

REQUIRED_COLUMNS = [
    "Código do Produto",
    "Produto",
    "Venda (R$)",
    "Margem Atual",
]

_NO_MAP = "— não mapeada —"


def _call_validate(filename: str, file_bytes: bytes) -> dict | None:
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/validate",
            files={"file": (filename, file_bytes, "application/octet-stream")},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Não foi possível conectar ao servidor. Verifique se o backend está disponível.")
    except Exception as exc:
        st.error(f"Erro na validação: {exc}")
    return None


def _render_mapping_ui(info: dict) -> dict | None:
    """
    Renders the mandatory column mapping step.
    Always shows — even when all columns are auto-detected — so the user explicitly confirms.
    Returns confirmed {file_col: required_col} mapping or None while waiting.
    """
    all_cols = info["all_columns"]
    inferred = info["inferred_mapping"]
    margin_format = info.get("margin_format", "percent")

    # Reverse: required_col → best inferred file_col
    default_for_required: dict[str, str] = {}
    for file_col, req_col in inferred.items():
        if req_col and req_col not in default_for_required:
            default_for_required[req_col] = file_col

    st.markdown("#### Relacionamento de Colunas")
    st.caption(
        "⚠️ **Etapa obrigatória.** Confirme o relacionamento entre as colunas do seu arquivo "
        "e as colunas do projeto — mesmo que o sistema tenha identificado automaticamente."
    )

    options = [_NO_MAP] + all_cols
    mapping_selections: dict[str, str] = {}
    all_mapped = True

    # Header row
    hc1, hc2, hc3 = st.columns([3, 4, 1])
    hc1.markdown(
        "<div class='mapping-table-header'>Coluna do Projeto</div>",
        unsafe_allow_html=True,
    )
    hc2.markdown(
        "<div class='mapping-table-header'>Coluna no seu Arquivo</div>",
        unsafe_allow_html=True,
    )
    hc3.markdown(
        "<div class='mapping-table-header' style='text-align:center;'>OK?</div>",
        unsafe_allow_html=True,
    )

    for req_col in REQUIRED_COLUMNS:
        default_file_col = default_for_required.get(req_col, _NO_MAP)
        default_idx = options.index(default_file_col) if default_file_col in options else 0

        c1, c2, c3 = st.columns([3, 4, 1])

        with c1:
            is_auto = default_file_col != _NO_MAP
            badge = (
                "<span style='font-size:0.7rem;background:#dcfce7;color:#166534;"
                "border-radius:3px;padding:1px 5px;margin-left:5px;'>auto</span>"
                if is_auto else ""
            )
            st.markdown(
                f"<div style='padding-top:0.45rem;font-weight:600;color:#0057B8;'>"
                f"{req_col}{badge}</div>",
                unsafe_allow_html=True,
            )

        with c2:
            selected = st.selectbox(
                label=req_col,
                options=options,
                index=default_idx,
                key=f"col_map_{req_col}",
                label_visibility="collapsed",
            )

        with c3:
            if selected == _NO_MAP:
                st.markdown(
                    "<div style='padding-top:0.45rem;color:#dc2626;"
                    "font-size:1.4rem;text-align:center;'>✗</div>",
                    unsafe_allow_html=True,
                )
                all_mapped = False
            else:
                st.markdown(
                    "<div style='padding-top:0.45rem;color:#16a34a;"
                    "font-size:1.4rem;text-align:center;'>✔</div>",
                    unsafe_allow_html=True,
                )

        if selected != _NO_MAP:
            mapping_selections[selected] = req_col

    # Unmapped file columns
    unmapped = [c for c in all_cols if c not in mapping_selections]
    if unmapped:
        with st.expander(f"Colunas não utilizadas ({len(unmapped)})", expanded=False):
            st.caption(", ".join(f"`{c}`" for c in unmapped))

    # Margin format notice
    st.markdown("<br>", unsafe_allow_html=True)
    if margin_format == "decimal":
        st.info(
            "**Formato de Margem detectado: decimal** (ex: 0.185 = 18,5%)  \n"
            "Os valores serão convertidos automaticamente para % antes da análise."
        )
    else:
        st.info(
            "**Formato de Margem detectado: percentual** (ex: 18.5 = 18,5%)  \n"
            "Nenhuma conversão necessária."
        )

    if not all_mapped:
        missing_req = [r for r in REQUIRED_COLUMNS if r not in mapping_selections.values()]
        st.warning(
            "Mapeamento incompleto. Selecione a coluna correspondente para: "
            + ", ".join(f"**{c}**" for c in missing_req)
        )

    col_btn, _ = st.columns([2, 5])
    with col_btn:
        confirmed = st.button(
            "Confirmar Mapeamento e Continuar →",
            type="primary",
            disabled=not all_mapped,
            key="confirm_mapping_btn",
        )

    if confirmed and all_mapped:
        return mapping_selections

    return None


def render_file_uploader() -> tuple:
    """
    Returns (file_bytes, validation_info, column_mapping) when confirmed.
    Returns (None, None, None) while waiting.
    """
    st.subheader("3. Upload e Mapeamento de Colunas")
    st.markdown(
        "Faça upload do arquivo Excel. O sistema detectará as colunas automaticamente — "
        "você deverá **confirmar o mapeamento** antes de prosseguir."
    )

    uploaded = st.file_uploader(
        "Selecione o arquivo Excel (.xlsx)",
        type=["xlsx", "xls"],
        key="excel_upload",
    )

    # Reset session state when file changes
    file_key = f"{uploaded.name}_{uploaded.size}" if uploaded else None
    if st.session_state.get("_last_file_key") != file_key:
        for k in ["_validate_info", "_confirmed_mapping", "_last_file_key", "_file_bytes"]:
            st.session_state.pop(k, None)
        st.session_state["_last_file_key"] = file_key

    if uploaded is None:
        return None, None, None

    if "_file_bytes" not in st.session_state:
        st.session_state["_file_bytes"] = uploaded.read()
    file_bytes: bytes = st.session_state["_file_bytes"]

    if "_validate_info" not in st.session_state:
        with st.spinner("Lendo colunas do arquivo..."):
            info = _call_validate(uploaded.name, file_bytes)
        if info is None:
            return None, None, None
        st.session_state["_validate_info"] = info

    info = st.session_state["_validate_info"]

    # Stats bar
    st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Linhas no arquivo", info["total_rows"])
    c2.metric("Colunas detectadas", len(info["all_columns"]))
    auto_count = sum(1 for v in info["inferred_mapping"].values() if v)
    c3.metric("Mapeamentos automáticos", f"{auto_count} / {len(REQUIRED_COLUMNS)}")

    st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)

    # Already confirmed: show read-only summary
    if "_confirmed_mapping" in st.session_state:
        mapping = st.session_state["_confirmed_mapping"]
        margin_format = info.get("margin_format", "percent")

        st.markdown("#### Mapeamento Confirmado")

        hc1, hc2 = st.columns(2)
        hc1.markdown("**Coluna do Projeto**")
        hc2.markdown("**Coluna no Arquivo**")

        for file_col, req_col in mapping.items():
            r1, r2 = st.columns(2)
            r1.markdown(
                f"<div class='mapping-row' style='font-weight:600;color:#0057B8;'>{req_col}</div>",
                unsafe_allow_html=True,
            )
            r2.markdown(
                f"<div class='mapping-row'>{file_col}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        fmt_label = "decimal → convertido para %" if margin_format == "decimal" else "percentual"
        st.success(
            f"✔ Mapeamento confirmado · "
            f"Margem Atual: formato **{fmt_label}**"
        )

        if info.get("preview"):
            with st.expander("Pré-visualização (5 primeiras linhas)", expanded=False):
                st.dataframe(pd.DataFrame(info["preview"]), use_container_width=True)

        col_reset, _ = st.columns([2, 5])
        if col_reset.button("Alterar mapeamento", key="reset_mapping_btn"):
            st.session_state.pop("_confirmed_mapping", None)
            st.rerun()

        return file_bytes, info, mapping

    # Show mandatory mapping UI
    confirmed_mapping = _render_mapping_ui(info)
    if confirmed_mapping:
        st.session_state["_confirmed_mapping"] = confirmed_mapping
        st.rerun()

    return None, None, None
