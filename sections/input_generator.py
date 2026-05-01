"""
sections/input_generator.py — Input Generator page.

Provides a tabbed interface for generating VASP input files:
INCAR, POSCAR, POTCAR, and KPOINTS.

Also contains unified helper functions for file output preview,
download, and save-to-project (shared by all four generator tabs).
"""

import os

import streamlit as st

from utils.styles import COMMON_STYLES


# ===========================================================================
# Public entry point
# ===========================================================================

def render_input_generator() -> None:
    """Render the Input Generator page with four tab buttons.

    Generator modules are imported lazily inside this function to avoid
    circular imports (each generator imports render_file_output from here).
    """
    from generators.incar import render_incar_tab
    from generators.poscar import render_poscar_tab
    from generators.potcar import render_potcar_tab
    from generators.kpoints import render_kpoints_tab

    st.markdown(COMMON_STYLES, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">📄 Input Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate VASP input files (INCAR, POSCAR, POTCAR, KPOINTS)</p>',
                unsafe_allow_html=True)

    # ── Tab selector (four columns of buttons) ──────────────────────
    col1, col2, col3, col4 = st.columns(4)
    tab_buttons = [
        (col1, "**INCAR**",   "INCAR"),
        (col2, "**POSCAR**",  "POSCAR"),
        (col3, "**POTCAR**",  "POTCAR"),
        (col4, "**KPOINTS**", "KPOINTS"),
    ]
    for col, label, tab_name in tab_buttons:
        with col:
            if st.button(label):
                st.session_state.input_tab = tab_name

    st.markdown("---")

    # ── Dispatch to the selected tab renderer ───────────────────────
    tab_handlers = {
        "INCAR":   render_incar_tab,
        "POSCAR":  render_poscar_tab,
        "POTCAR":  render_potcar_tab,
        "KPOINTS": render_kpoints_tab,
    }
    handler = tab_handlers.get(st.session_state.input_tab)
    if handler:
        handler()


# ===========================================================================
# Unified file output helpers (used by all four generator tabs)
# ===========================================================================

def render_file_output(content: str, filename: str, state_key: str) -> None:
    """
    Render a file preview block with download and save-to-project buttons.

    Parameters
    ----------
    content : str
        The file content to display.
    filename : str
        The output filename (e.g. "INCAR", "POSCAR").
    state_key : str
        The session-state prefix for this file type (e.g. "incar", "poscar").
        Used to namespace widget keys and the save-dialog flag.
    """
    st.markdown("---")
    st.markdown(f"#### {filename} Preview")

    # Escape HTML entities for safe rendering in the dark-themed preview box
    preview = (content
               .replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
               .replace("\n", "<br>"))
    st.markdown(f'<div class="file-preview">{preview}</div>', unsafe_allow_html=True)

    # ── Download and Save buttons ───────────────────────────────────
    save_dialog_key = f"{state_key}_show_save_dialog"
    if save_dialog_key not in st.session_state:
        st.session_state[save_dialog_key] = False

    col_dl, col_sv = st.columns(2)
    with col_dl:
        st.download_button(f"📥 Download {filename}", content, filename, "text/plain")
    with col_sv:
        if st.button("💾 Save to Project", key=f"save_{state_key}_btn"):
            st.session_state[save_dialog_key] = True

        if st.session_state[save_dialog_key]:
            _render_save_dialog(content, filename, state_key)


def _render_save_dialog(content: str, filename: str, state_key: str) -> None:
    """
    Render the inline save-to-project dialog.

    Creates the project folder if needed and writes the file into it.
    """
    save_dialog_key = f"{state_key}_show_save_dialog"
    content_key = f"{state_key}_content"

    col_name, col_save = st.columns([3, 1])
    with col_name:
        project_name = st.text_input("Project Name", key=f"{state_key}_project_name")
    with col_save:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save", key=f"confirm_{state_key}_save"):
            if not project_name:
                st.warning("Please enter a project name")
            else:
                project_path = os.path.join(st.session_state.my_projects_root, project_name)
                os.makedirs(project_path, exist_ok=True)

                file_path = os.path.join(project_path, filename)
                with open(file_path, "w") as f:
                    f.write(content)

                st.success(f"{filename} saved to project '{project_name}'!")
                st.session_state[save_dialog_key] = False
                st.rerun()
