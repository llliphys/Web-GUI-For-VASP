"""
sections/my_projects.py — Project browser page.

Provides folder navigation, folder creation/replacement, and file previewing.
"""

import os
import shutil

import streamlit as st

from styles import COMMON_STYLES


# ===========================================================================
# Public entry point
# ===========================================================================

def render_my_projects() -> None:
    """Render the My Projects page with folder browser and file previews."""
    st.markdown(COMMON_STYLES, unsafe_allow_html=True)

    current_dir = st.session_state.current_folder
    is_root = (current_dir == os.getcwd())

    # Handle pending folder navigation (set by other pages)
    if "navigate_to_folder" in st.session_state and st.session_state.navigate_to_folder:
        st.session_state.current_folder = st.session_state.navigate_to_folder
        st.session_state.navigate_to_folder = None
        st.rerun()

    # ── Page header with back button ────────────────────────────────
    col_title, col_tmp, col_back = st.columns([3, 1, 1])

    with col_title:
        folder_name = os.path.basename(current_dir) if not is_root else "My Projects"
        st.markdown(f'<h1 class="main-header">📁 {folder_name}</h1>', unsafe_allow_html=True)
        if is_root:
            st.markdown('<p class="sub-header">Manage and organize your VASP projects</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="sub-header">Path: {current_dir}</p>', unsafe_allow_html=True)

        with col_back:
            if not is_root:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⬅️ Back", key="back_button"):
                    st.session_state.current_folder = os.path.dirname(current_dir)
                    st.session_state.pending_replace = None

    st.markdown("---")
    _render_project_controls(current_dir)
    _render_folder_list(current_dir)


# ===========================================================================
# Project controls (new folder / replace confirmation)
# ===========================================================================

def _render_project_controls(current_dir: str) -> None:
    """Render the new-folder input and replace-confirmation dialog."""
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        project_name = st.text_input("Enter folder name...", key="new_project_name")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ New Folder"):
            _handle_new_folder(current_dir, project_name)

    # Show replace confirmation when a duplicate name is detected
    if st.session_state.pending_replace:
        st.warning(f"⚠️ A folder named '{st.session_state.pending_replace}' already exists. Do you want to replace it?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, Replace"):
                _replace_folder(current_dir, st.session_state.pending_replace)
        with col_no:
            if st.button("No, Keep Existing"):
                st.info("Operation cancelled.")
                st.session_state.pending_replace = None


def _handle_new_folder(current_dir: str, project_name: str) -> None:
    """Create a new folder, or flag for replacement if it already exists."""
    if not project_name:
        return
    new_folder_path = os.path.join(current_dir, project_name)
    if os.path.exists(new_folder_path):
        st.session_state.pending_replace = project_name
    else:
        os.makedirs(new_folder_path, exist_ok=True)
        st.success(f"Folder '{project_name}' created successfully!")


def _replace_folder(current_dir: str, folder_name: str) -> None:
    """Delete and recreate an existing folder."""
    folder_to_replace = os.path.join(current_dir, folder_name)
    shutil.rmtree(folder_to_replace, ignore_errors=True)
    os.makedirs(folder_to_replace)
    st.success(f"Folder '{folder_name}' replaced successfully!")
    st.session_state.pending_replace = None


# ===========================================================================
# Folder / file listing
# ===========================================================================

def _render_folder_list(current_dir: str) -> None:
    """List folders (as navigation buttons) and files (as expandable previews)."""
    try:
        existing_items = sorted(os.listdir(current_dir))
    except OSError:
        st.error("Cannot access this directory")
        existing_items = []

    if not existing_items:
        return

    for idx, item in enumerate(existing_items):
        item_path = os.path.join(current_dir, item)
        is_dir = os.path.isdir(item_path)

        if is_dir:
            if st.button(f"📁 {item}", key=f"folder_{idx}"):
                st.session_state.current_folder = item_path
        else:
            with st.expander(f"📄 {item}"):
                render_file_preview(item_path)


# ===========================================================================
# File preview (shared utility – also used by run_simulation page)
# ===========================================================================

def render_file_preview(file_path: str) -> None:
    """Read and display the text content of a file in a code block."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
        st.code(content)
    except Exception:
        st.warning("Cannot preview this file")
