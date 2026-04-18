import os

try:
    import streamlit as st
    BACKEND_URL = st.secrets.get("BACKEND_URL", os.environ.get("BACKEND_URL", "http://localhost:8080"))
except Exception:
    BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080")
