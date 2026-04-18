import streamlit as st

ABC_CURVE = {"A+": 40, "A": 40, "B": 15, "C": 5}
ABC_COLORS = {"A+": "#0057B8", "A": "#00B4D8", "B": "#F59E0B", "C": "#6B7280"}


def render_abc_config() -> tuple[float, dict[str, float]]:
    st.subheader("2. Parâmetros da Curva ABC e Margem")

    # ABC Curve display
    st.markdown("**Classificação da Curva ABC (fixo)**")
    cols = st.columns(4)
    for col, (cls, pct) in zip(cols, ABC_CURVE.items()):
        color = ABC_COLORS[cls]
        col.markdown(
            f"""
            <div style="
                background:{color}15;
                border:2px solid {color};
                border-radius:8px;
                padding:0.75rem;
                text-align:center;
            ">
                <div style="font-size:1.4rem;font-weight:900;color:{color};">{cls}</div>
                <div style="font-size:1.1rem;font-weight:600;color:{color};">{pct}%</div>
                <div style="font-size:0.75rem;color:#666;">da venda</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_desired, _ = st.columns([2, 3])
    with col_desired:
        desired_increase = st.number_input(
            "Acréscimo de Margem Total Desejado (pp) *",
            min_value=0.0,
            max_value=50.0,
            value=2.0,
            step=0.1,
            format="%.2f",
            help="Aumento em pontos percentuais na margem geral ponderada. Ex: 2.0 = +2,0pp",
            key="desired_increase",
        )

    st.markdown("**Acréscimo máximo permitido por classe (%pp)**")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        max_aplus = st.number_input("Máx A+", min_value=0.0, max_value=100.0, value=5.0, step=0.5, format="%.2f", key="max_aplus")
    with c2:
        max_a = st.number_input("Máx A", min_value=0.0, max_value=100.0, value=4.0, step=0.5, format="%.2f", key="max_a")
    with c3:
        max_b = st.number_input("Máx B", min_value=0.0, max_value=100.0, value=3.0, step=0.5, format="%.2f", key="max_b")
    with c4:
        max_c = st.number_input("Máx C", min_value=0.0, max_value=100.0, value=2.0, step=0.5, format="%.2f", key="max_c")

    max_increases = {"A+": max_aplus, "A": max_a, "B": max_b, "C": max_c}
    return desired_increase, max_increases
