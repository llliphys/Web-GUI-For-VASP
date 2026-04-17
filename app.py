"""
app.py — Main entry point for the VASP GUI application.

This is a thin orchestration layer that:
  1. Configures the Streamlit page.
  2. Initialises session state.
  3. Handles URL query parameters.
  4. Renders the sidebar navigation.
  5. Routes to the selected page renderer.

All page content, styles, and generator logic live in dedicated modules
under sections/, generators/, plotters/, and styles.py.

Run with:  streamlit run app.py
"""

import os
import urllib.parse

import streamlit as st

# ── Page renderers ──────────────────────────────────────────────────────────
from sections.home import render_home
from sections.my_projects import render_my_projects
from sections.input_generator import render_input_generator
from sections.run_simulation import render_run_simulation
from sections.placeholder import render_placeholder
from plotters.structural_plotter import render_structural_plotter
from plotters.electronic_plotter import render_electronic_plotter
from plotters.phononic_plotter import render_phononic_plotter


# ===========================================================================
# Streamlit page configuration (must be the first st.* call)
# ===========================================================================

st.set_page_config(
    page_title="VASP GUI",
    # page_icon="🔬",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ===========================================================================
# Session-state initialisation
# ===========================================================================

def _init_session_state() -> None:
    """Set default values for all top-level session-state keys."""
    defaults = {
        "current_page":     "Home",
        "pending_replace":  None,
        "current_folder":   os.getcwd(),
        "my_projects_root": os.getcwd(),
        "input_tab":        "INCAR",
        "show_save_dialog": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _handle_query_params() -> None:
    """If the URL contains a ?folder=… parameter, navigate to that folder."""
    try:
        query_params = st.query_params
        if "folder" not in query_params:
            return
        folder_path = urllib.parse.unquote(query_params["folder"])
        if not os.path.isdir(folder_path):
            return
        if folder_path == st.session_state.get("current_folder"):
            return
        st.session_state.current_folder = folder_path
        st.session_state.current_page = "My Projects"
        st.query_params.clear()
    except Exception:
        pass


# Run initialisation on every script execution
_init_session_state()
_handle_query_params()


# ===========================================================================
# Sidebar navigation
# ===========================================================================

def _render_sidebar() -> None:
    """Render the sidebar with navigation buttons and quick links."""
    with st.sidebar:
        # Primary navigation
        nav_items = [
            ("🏠 **Home Page**",    "Home"),
            ("📁 My Projects",      "My Projects"),
            ("📄 Input Generator",  "Input Generator"),
            ("▶️ Run Simulation",   "Run Simulation"),
        ]
        for label, page in nav_items:
            if st.button(label):
                st.session_state.current_page = page

        st.markdown("---")

        # Plotter navigation
        plotter_items = [
            ("🔷 Structural Plotter", "Structural Plotter"),
            ("📊 Electronic Plotter", "Electronic Plotter"),
            ("📈 Phononic Plotter",   "Phononic Plotter"),
        ]
        for label, page in plotter_items:
            if st.button(label, key=f"nav_{page}"):
                st.session_state.current_page = page

        st.markdown("---")
        # st.markdown("📋 About the App")
        st.markdown("### About the App")
        st.markdown("<br>", unsafe_allow_html=True)
        # st.markdown("""This web GUI for VASP is developed by Dr. Longlong Li 
        #             whose interesets include physical modelling, scientific computing, 
        #             and machine learning, and research software.""")
        st.markdown(f"""
        <div style="font-size: {15}px; text-align: justify;"> 
        This web GUI for VASP is developed by Dr. Longlong Li 
        who is working on physical modelling, scientific computing, 
        machine learning, workflow automation, and research software.
        Welcome developers and users to share their contributions.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Quick links
        st.markdown("### Quick Links")
        st.markdown("- [VASP Wiki](https://www.vasp.at/wiki/index.php/The_VASP_Manual)")
        st.markdown("- [Pymatgen](https://pymatgen.org)")
        st.markdown("- [ASE](https://wiki.fysik.dtu.dk/ase/)")
        st.markdown("- [Streamlit](https://streamlit.io)")


# ===========================================================================
# Page routing
# ===========================================================================

# Maps page name → renderer callable.
_PAGE_RENDERERS = {
    "Home":               render_home,
    "My Projects":        render_my_projects,
    "Input Generator":    render_input_generator,
    "Run Simulation":     render_run_simulation,
    "Structural Plotter": render_structural_plotter,
    "Electronic Plotter": render_electronic_plotter,
    "Phononic Plotter":   render_phononic_plotter,
    "About the App":      lambda: render_placeholder("About the App"),
}


# ===========================================================================
# Main
# ===========================================================================

def main() -> None:
    """Application entry point: render sidebar, then dispatch to page."""
    _render_sidebar()

    current_page = st.session_state.current_page
    renderer = _PAGE_RENDERERS.get(current_page)
    if renderer:
        renderer()


if __name__ == "__main__":
    main()
