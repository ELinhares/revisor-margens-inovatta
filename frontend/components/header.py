import os
import streamlit as st

APP_VERSION = "1.3.0"

INOVATTA_CSS = """
<style>
    :root {
        --primary: #0057B8;
        --accent:  #00B4D8;
        --bg:      #F4F8FF;
        --card-bg: #FFFFFF;
        --text:    #1A1A2E;
        --border:  #C8D8F0;
    }

    .stApp { background-color: var(--bg); }

    section[data-testid="stSidebar"] { background-color: #EBF2FF; }

    h1, h2, h3 { color: var(--primary) !important; }

    .stButton > button[kind="primary"] {
        background-color: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1.5rem !important;
        transition: background-color 0.2s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: var(--accent) !important;
    }
    .stButton > button[kind="secondary"] {
        border: 2px solid var(--primary) !important;
        color: var(--primary) !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    .stDataFrame {
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
    }
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input {
        border-color: var(--border) !important;
    }
    .stNumberInput > div > div > input:focus,
    .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(0, 87, 184, 0.2) !important;
    }
    .metric-card {
        background: var(--card-bg);
        border-left: 4px solid var(--primary);
        padding: 1rem 1.25rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .metric-card h4 {
        margin: 0 0 0.25rem 0;
        font-size: 0.85rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-card p {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--primary);
    }
    .status-ok   { color: #16a34a; font-weight: 600; }
    .status-error { color: #dc2626; font-weight: 600; }
    hr.inovatta-divider {
        border: none;
        border-top: 2px solid var(--border);
        margin: 1.5rem 0;
    }
    .app-version {
        font-size: 0.78rem;
        font-weight: 700;
        color: #ffffff;
        background-color: #0057B8;
        text-align: center;
        padding: 0.25rem 0.6rem;
        border-radius: 12px;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .mapping-table-header {
        background: #0057B8;
        color: white;
        font-weight: 700;
        font-size: 0.85rem;
        padding: 0.5rem 0.75rem;
        border-radius: 5px 5px 0 0;
    }
    .mapping-row {
        background: white;
        border-bottom: 1px solid #e5eaf3;
        padding: 0.35rem 0.75rem;
        font-size: 0.875rem;
    }
</style>
"""


def render_header():
    st.markdown(INOVATTA_CSS, unsafe_allow_html=True)

    logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logo_inovatta.png")
    logo_path = os.path.normpath(logo_path)

    col_logo, col_title, col_version = st.columns([1, 4, 1])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.markdown(
                '<div style="font-size:2rem;font-weight:900;color:#0057B8;">INOVATTA</div>',
                unsafe_allow_html=True,
            )

    with col_title:
        st.markdown(
            """
            <div style="padding-top:0.5rem;">
                <h1 style="margin:0;font-size:1.8rem;">Revisor de Margens Inovatta</h1>
                <p style="margin:0;color:#666;font-size:0.95rem;">
                    Análise de Curva ABC e Sugestão de Margens por Produto
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_version:
        st.markdown(
            f'<div style="text-align:right;padding-top:0.4rem;">'
            f'<span class="app-version">v{APP_VERSION}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="inovatta-divider" />', unsafe_allow_html=True)
