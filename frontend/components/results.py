import streamlit as st

ABC_COLORS = {"A+": "#0057B8", "A": "#00B4D8", "B": "#F59E0B", "C": "#6B7280"}


def render_results(response: dict):
    st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)
    st.subheader("Resultado da Análise")

    if response.get("status") != "success":
        st.error(f"Erro no processamento: {response.get('detail', 'Erro desconhecido')}")
        return

    if response.get("warning"):
        st.warning(f"**Atenção:** {response['warning']}")

    summary = response.get("summary", {})

    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Margem Atual Ponderada</h4>
                <p>{summary.get('current_weighted_margin', 0):.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <h4>Margem Alvo Ponderada</h4>
                <p>{summary.get('target_weighted_margin', 0):.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        achieved = summary.get("achieved_weighted_margin", 0)
        target = summary.get("target_weighted_margin", 0)
        delta_color = "#16a34a" if achieved >= target - 0.01 else "#F59E0B"
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color:{delta_color};">
                <h4>Margem Atingida</h4>
                <p style="color:{delta_color};">{achieved:.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ABC breakdown table
    breakdown = summary.get("abc_breakdown", {})
    if breakdown:
        st.markdown("**Detalhamento por Classe ABC**")
        cols = st.columns(len(breakdown))
        for col, (cls, data) in zip(cols, breakdown.items()):
            color = ABC_COLORS.get(cls, "#666")
            col.markdown(
                f"""
                <div style="
                    background:{color}12;
                    border:1.5px solid {color};
                    border-radius:8px;
                    padding:0.75rem;
                    text-align:center;
                ">
                    <div style="font-size:1.2rem;font-weight:900;color:{color};">{cls}</div>
                    <div style="font-size:0.9rem;color:#333;">{data['count']} produtos</div>
                    <div style="font-size:0.85rem;color:#555;">+{data['avg_increase']:.2f}pp médio</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Download button
    download_url = response.get("download_signed_url")
    if download_url:
        st.markdown("**Arquivo com Margem Sugerida**")
        st.markdown(
            f'<a href="{download_url}" target="_blank">'
            f'<button style="background:#0057B8;color:white;border:none;padding:0.6rem 1.5rem;'
            f'border-radius:6px;font-size:1rem;font-weight:600;cursor:pointer;">'
            f'⬇ Baixar Excel com Sugestões de Margem</button></a>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<br><small style='color:#888;'>Arquivo salvo em: {response.get('processed_gcs_uri', '')}</small>",
        unsafe_allow_html=True,
    )
