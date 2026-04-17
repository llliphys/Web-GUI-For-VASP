"""
generators/kpoints.py — KPOINTS file generator.

Supports uploading an existing KPOINTS file or creating one from scratch:
  - K-Mesh (Monkhorst-Pack / Gamma-centered)
  - K-Line (band-structure high-symmetry path)
"""

import streamlit as st

from sections.input_generator import render_file_output


# ===========================================================================
# Public entry point
# ===========================================================================

def render_kpoints_tab() -> None:
    """Render the KPOINTS generator tab."""
    if "kpoints_show_save_dialog" not in st.session_state:
        st.session_state.kpoints_show_save_dialog = False

    kpoints_method = st.radio(
        "Choose generation method:",
        ["Upload KPOINTS", "Create KPOINTS"],
        horizontal=True,
    )

    handlers = {
        "Upload KPOINTS": _kpoints_from_upload,
        "Create KPOINTS": _kpoints_create,
    }
    handler = handlers.get(kpoints_method)
    if handler:
        handler()

    # Show preview if content has been generated
    if "kpoints_content" in st.session_state:
        render_file_output(st.session_state.kpoints_content, "KPOINTS", "kpoints")


# ===========================================================================
# Upload method
# ===========================================================================

def _kpoints_from_upload() -> None:
    """Load KPOINTS from an uploaded file."""
    st.markdown("###### Upload Existing KPOINTS")
    uploaded_file = st.file_uploader("Choose a KPOINTS file", type=None,
                                     accept_multiple_files=False)
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            st.success("File uploaded successfully!")
            if st.button("Use This KPOINTS", key="gen_uploaded_kpoints"):
                st.session_state.kpoints_content = file_content
                st.success("KPOINTS loaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.info("Make sure the file is in valid KPOINTS format")


# ===========================================================================
# Create method (mesh or line)
# ===========================================================================

def _kpoints_create() -> None:
    """Choose between K-Mesh and K-Line modes."""
    st.markdown("###### Create KPOINTS")

    kpoints_mode = st.radio(
        "K-point generation mode:",
        ["K-Mesh ( Monkhorst-Pack / Gamma-centered )", "K-Line (Band Structure)"],
        horizontal=True,
    )

    if kpoints_mode.startswith("K-Mesh"):
        _kpoints_create_mesh()
    else:
        _kpoints_create_line()


# ---------------------------------------------------------------------------
# Mesh builder
# ---------------------------------------------------------------------------

def _kpoints_create_mesh() -> None:
    """Create KPOINTS with a regular mesh (Monkhorst-Pack or Gamma-centered)."""
    kpt_method = st.selectbox("K-point Generation Method",
                              ["Monkhorst-Pack", "Gamma-centered"])

    kx = st.number_input("K-points along a*", value=6, min_value=1)
    ky = st.number_input("K-points along b*", value=6, min_value=1)
    kz = st.number_input("K-points along c*", value=1, min_value=1)
    shift = st.text_input("K-mesh shift", value="0 0 0")

    if st.button("Generate KPOINTS", key="gen_kpoints_mesh"):
        st.session_state.kpoints_content = _build_kpoints_mesh(kpt_method, kx, ky, kz, shift)


def _build_kpoints_mesh(method: str, kx: int, ky: int, kz: int, shift: str) -> str:
    """Build KPOINTS file content for a regular k-mesh."""
    shift_str = " ".join(shift.split())
    scheme = "Monkhorst-Pack" if method == "Monkhorst-Pack" else "Gamma"
    return f"K-point Mesh\n0\n{scheme}\n{kx} {ky} {kz}\n{shift_str}\n"


# ---------------------------------------------------------------------------
# Line builder (band structure)
# ---------------------------------------------------------------------------

def _kpoints_create_line() -> None:
    """Create KPOINTS for band-structure calculations (line mode)."""
    st.info("Enter the high-symmetry k-points for band structure calculation.")

    col1, col2 = st.columns(2)
    with col1:
        num_kpoints = st.number_input("Number of k-points", value=80,
                                      min_value=20, step=20)
    with col2:
        comment_line = st.text_input("Comment line (e.g., K-point Path)",
                                     "K-point Path")

    num_kpaths = st.number_input("Number of k-paths (1, 2, 3, ...)",
                                 value=1, min_value=1)

    st.markdown("###### High-Symmetry K-Points")

    kpoints_list = []
    for i in range(2 * int(num_kpaths)):
        col1, col2 = st.columns(2)
        with col1:
            label = st.text_input(f"Label (e.g., Г, X, Y, M, K, S)",
                                  value=f"K{i+1}", key=f"klabel_{i}")
        with col2:
            coords = st.text_input(f"Coordinates (e.g., 0 0 0 or 0.5 0.5 0.5)",
                                   value="0 0 0", key=f"kcoord_{i}")
        kpoints_list.append((label, coords))

    if st.button("Generate KPOINTS", key="gen_kpoints_line"):
        st.session_state.kpoints_content = _build_kpoints_line(
            comment_line, num_kpoints, kpoints_list)


def _build_kpoints_line(comment: str, num_kpoints: int, kpoints: list) -> str:
    """Build KPOINTS file content for band-structure line mode."""
    lines = [comment, f"{num_kpoints}", "Line-mode", "Reciprocal"]

    for i in range(0, len(kpoints) - 1, 2):
        label1, coords1 = kpoints[i]
        if i + 1 < len(kpoints):
            label2, coords2 = kpoints[i + 1]
            lines.append(f"{coords1}    !{label1} ")
            lines.append(f"{coords2}    !{label2} ")
            lines.append("")

    return "\n".join(lines) + "\n"
