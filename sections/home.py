"""
sections/home.py — Home page of the VASP GUI application.

Displays a welcome message, feature list, quick-start guide, and tips.
"""

import streamlit as st

from utils.styles import COMMON_STYLES


def render_home() -> None:
    """Render the home page with welcome info, features, and quick-start guide."""
    st.markdown(COMMON_STYLES, unsafe_allow_html=True)

    # ── Center-align the main header and sub-header ─────────────────
    st.markdown("""
        <style>
        .main-header, .sub-header {
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header"> WGUI4VASP </h1>', unsafe_allow_html=True)
    # st.markdown('<p class="sub-header">A web-based GUI tool for VASP simulation</p>', unsafe_allow_html=True)
    st.markdown('<h6 class="sub-header">A Web-based GUI tool for VASP simulation</h6>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Two-column layout: welcome + quick-start ────────────────────
    col_left, _, col_right = st.columns([5, 1, 5])

    with col_left:
        _render_welcome_section()

    with col_right:
        _render_quickstart_section()

    st.markdown("---")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

font_size = 15

def _render_welcome_section() -> None:
    """Render the welcome message and feature list."""
    st.markdown("## Welcome! 👋")
    st.markdown(f"""
    <div style="font-size: {font_size}px; text-align: justify;"> 
    Welcome to <b>WGUI4VASP</b>, a practical Web-based GUI tool designed for generating inputs for and visualizing outputs from the VASP software.
    Whether you are a student or researcher, GUI4VASP provides an easy-to-use interface to facilitate your computational materials research using VASP.
    </div>
    """, unsafe_allow_html=True)

    # st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 🎯 Features")
    # features = [
    #     "📁 **Project Management**: Organize and manage your VASP projects easily",
    #     "📄 **Input Generator**: Create VASP input files with guided wizards",
    #     "▶️ **Run Simulation**: Execute VASP calculations directly from the interface",
    #     "🔷 **Structural Plotter**: Visualize crystal structures in interactive 3D",
    #     "📊 **Electronic Plotter**: Analyze electronic properties and band structures",
    #     "📈 **Phonon Plotter**: Plot and analyze phonon dispersion and density of states",
    # ]
    features = [
        "📁 <b>Project Management</b>: Organize and manage your VASP projects easily",
        "📄 <b>Input Generator</b>: Create VASP input files with guided wizards",
        "▶️ <b>Run Simulation</b>: Execute VASP calculations directly from the interface",
        "🔷 <b>Structural Plotter</b>: Visualize crystal structures in interactive 3D",
        "📊 <b>Electronic Plotter</b>: Analyze electronic properties and band structures",
        "📈 <b>Phonon Plotter</b>: Plot and analyze phonon dispersion and density of states",
    ]
    for feature in features:
        # st.markdown(feature)
        st.markdown(f"""
        <div style="font-size: {font_size}px; text-align: justify; margin-bottom: 10px;"> 
        {feature}
        </div>
        """, unsafe_allow_html=True)
        

def _render_quickstart_section() -> None:
    """Render the quick-start guide and tips."""
    st.markdown("### 📝 Quick Start") # Quick Start Guide 
    st.markdown(f"""
    <div style="font-size: {font_size}px; text-align: justify;"> 
    Follow these simple steps to start using <b>WGUI4VASP</b>:
     </div>
    """, unsafe_allow_html=True)
   
    steps = [
        (
            "Navigate to any page from the sidebar menu",
            "Select the generation or analysis tool from the sidebar on the left.",
        ),
        (
            "Upload your VASP files (POSCAR, CONTCAR, etc.)",
            "Use the file browser to select and upload/download your VASP files.",
        ),
        (
            "Visualize and analyze your results",
            "Make real-time plots, adjust parameters, and analyze your findings.",
        ),
    ]

    # for i, (title, description) in enumerate(steps, 1):
    #     st.markdown(f"""
    #     <div>
    #         <h5><span class="step-number">{i}</span> {title}</h5>
    #         <h6 style="margin-left: 4px; color: #666;">{description}</h6>
    #     </div>
    #     """, unsafe_allow_html=True)

    for i, (title, description) in enumerate(steps, 1):
        st.markdown(f"""
        <div>
            <h6 style="margin-bottom: -15px;">
                <span class="step-number">{i}</span> {title}
            </h6>
            <h7 style="margin-left: 45px; color: #666;">
                {description}
            </h7>
        </div>
        """, unsafe_allow_html=True)


    st.markdown("### 💡 Tips")
    # st.markdown("""
    # - **Supported Files**: POSCAR, CONTCAR, EIGENVAL, DOSCAR, OUTCAR
    # - **Recommended**: Use CONTCAR for structure visualization
    # - **Large Files**: For big systems, be patient during file parsing
    # """)
    st.markdown(f"""
    <div style="font-size: {font_size}px; text-align: justify;"> 
        <ul style="list-style-type: disc;">
            <li><b>Supported Files</b>: POSCAR, CONTCAR, EIGENVAL, DOSCAR, OUTCAR</li>
            <li><b>Recommended</b>: Use CONTCAR for structure visualization</li>
            <li><b>Large Files</b>: For big systems, be patient during file parsing</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
