"""
sections/placeholder.py — Placeholder page for sections under construction.
"""

import streamlit as st


def render_placeholder(page_name: str) -> None:
    """Render a placeholder notice for pages that are not yet implemented."""
    st.markdown(f"## {page_name}")
    st.markdown(f"This is the **{page_name}** page.")
    st.info("This page is under construction. Layout image will be provided soon.")
