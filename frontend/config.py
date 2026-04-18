import os


def _get_backend_url() -> str:
    try:
        import streamlit as st
        val = st.secrets.get("BACKEND_URL")
        if val:
            return val
    except Exception:
        pass
    return os.environ.get("BACKEND_URL", "http://localhost:8080")


BACKEND_URL = _get_backend_url()
