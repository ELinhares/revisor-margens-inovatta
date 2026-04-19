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
    Renders the column mapping interface.
    Returns the confirmed mapping {file_col: required_col} or None if not confirmed.
    """
    all_cols = info["all_columns"]
    inferred = info["inferred_mapping"]

    st.markdown("#### Mapeamento de Colunas")
    st.caption(
        "O sistema identificou automaticamente as colunas abaixo. "
        "Confirme ou corrija o mapeamento antes de prosseguir."
    )

    # Build reverse map: required_col → file_col (inferred default)
    default_for_required: dict[str, str] = {}
    for file_col, req_col in inferred.items():
        if req_col and req_col not in default_for_required:
            default_for_required[req_col] = file_col

    options = [_NO_MAP] + all_cols

    mapping_selections: dict[str, str] = {}
    all_mapped = True

    for req_col in REQUIRED_COLUMNS:
        default_file_col = default_for_required.get(req_col, _NO_MAP)
        default_idx = options.index(default_file_col) if default_file_col in options else 0

        col_label, col_select, col_status = st.columns([3, 4, 1])

        with col_label:
            st.markdown(
                f"<div style='padding-top:0.45rem;font-weight:600;color:#0057B8;'>"
                f"{req_col}</div>",
                unsafe_allow_html=True,
            )

        with col_select:
            selected = st.selectbox(
                label=req_col,
                options=options,
                index=default_idx,
                key=f"col_map_{req_col}",
                label_visibility="collapsed",
            )

        with col_status:
            if selected == _NO_MAP:
                st.markdown(
                    "<div style='padding-top:0.45rem;color:#dc2626;font-size:1.3rem;'>✗</div>",
                    unsafe_allow_html=True,
                )
                all_mapped = False
            else:
                st.markdown(
                    "<div style='padding-top:0.45rem;color:#16a34a;font-size:1.3rem;'>✔</div>",
                    unsafe_allow_html=True,
                )

        if selected != _NO_MAP:
            mapping_selections[selected] = req_col

    # Warn about unmapped required columns
    if not all_mapped:
        missing = [r for r in REQUIRED_COLUMNS if r not in mapping_selections.values()]
        st.warning(f"Colunas obrigatórias ainda não mapeadas: {', '.join(f'**{c}**' for c in missing)}")

    # Show remaining file columns not mapped to anything
    unmapped_file_cols = [c for c in all_cols if c not in mapping_selections]
    if unmapped_file_cols:
        with st.expander(f"Colunas do arquivo não utilizadas ({len(unmapped_file_cols)})", expanded=False):
            st.caption(", ".join(f"`{c}`" for c in unmapped_file_cols))

    st.markdown("<br>", unsafe_allow_html=True)

    col_btn, col_info = st.columns([2, 5])
    with col_btn:
        confirmed = st.button(
            "Confirmar Mapeamento",
            type="primary",
            disabled=not all_mapped,
            key="confirm_mapping_btn",
        )

    if confirmed and all_mapped:
        return mapping_selections

    return None


def render_file_uploader() -> tuple:
    """
    Returns (file_bytes, validation_info, column_mapping) when mapping confirmed.
    Returns (None, None, None) while waiting for user action.
    """
    st.subheader("3. Upload do Arquivo Excel")
    st.markdown(
        "Faça upload do arquivo Excel. O sistema identificará as colunas "
        "automaticamente e permitirá confirmar o mapeamento antes de calcular."
    )

    uploaded = st.file_uploader(
        "Selecione o arquivo Excel (.xlsx)",
        type=["xlsx", "xls"],
        key="excel_upload",
    )

    # Reset state when file is removed or changed
    file_key = f"{uploaded.name}_{uploaded.size}" if uploaded else None
    if st.session_state.get("_last_file_key") != file_key:
        for k in ["_validate_info", "_confirmed_mapping", "_last_file_key", "_file_bytes"]:
            st.session_state.pop(k, None)
        st.session_state["_last_file_key"] = file_key

    if uploaded is None:
        return None, None, None

    # Read file once and cache in session_state
    if "_file_bytes" not in st.session_state:
        st.session_state["_file_bytes"] = uploaded.read()

    file_bytes: bytes = st.session_state["_file_bytes"]

    # Call /validate once per file
    if "_validate_info" not in st.session_state:
        with st.spinner("Lendo colunas do arquivo..."):
            info = _call_validate(uploaded.name, file_bytes)
        if info is None:
            return None, None, None
        st.session_state["_validate_info"] = info

    info = st.session_state["_validate_info"]

    # Summary line
    st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Linhas no arquivo", info["total_rows"])
    c2.metric("Colunas detectadas", len(info["all_columns"]))

    # All columns detected
    with st.expander("Colunas detectadas no arquivo", expanded=True):
        cols_per_row = 4
        all_cols = info["all_columns"]
        inferred = info["inferred_mapping"]
        rows = [all_cols[i:i+cols_per_row] for i in range(0, len(all_cols), cols_per_row)]
        for row in rows:
            grid = st.columns(cols_per_row)
            for cell, col_name in zip(grid, row):
                mapped_to = inferred.get(col_name)
                if mapped_to:
                    cell.markdown(
                        f"<div style='border:1px solid #0057B8;border-radius:5px;"
                        f"padding:0.4rem 0.6rem;margin:2px;font-size:0.85rem;'>"
                        f"<b>{col_name}</b><br>"
                        f"<span style='color:#0057B8;font-size:0.75rem;'>→ {mapped_to}</span></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    cell.markdown(
                        f"<div style='border:1px solid #ccc;border-radius:5px;"
                        f"padding:0.4rem 0.6rem;margin:2px;font-size:0.85rem;color:#888;'>"
                        f"{col_name}</div>",
                        unsafe_allow_html=True,
                    )

    st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)

    # If already confirmed, show summary and allow proceeding
    if "_confirmed_mapping" in st.session_state:
        mapping = st.session_state["_confirmed_mapping"]
        st.success(
            "✔ Mapeamento confirmado: "
            + " · ".join(f"`{v}` ← `{k}`" for k, v in mapping.items())
        )

        # Preview with confirmed mapping
        if info.get("preview"):
            with st.expander("Pré-visualização (5 primeiras linhas)", expanded=False):
                st.dataframe(pd.DataFrame(info["preview"]), use_container_width=True)

        col_reset, _ = st.columns([2, 5])
        if col_reset.button("Alterar mapeamento", key="reset_mapping_btn"):
            st.session_state.pop("_confirmed_mapping", None)
            st.rerun()

        return file_bytes, info, mapping

    # Show mapping UI
    confirmed_mapping = _render_mapping_ui(info)
    if confirmed_mapping:
        st.session_state["_confirmed_mapping"] = confirmed_mapping
        st.rerun()

    return None, None, None
