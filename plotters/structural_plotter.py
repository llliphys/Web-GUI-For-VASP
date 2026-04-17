import os
import streamlit as st
import plotly.graph_objects as go


COMMON_STYLES = """
<style>
    section[data-testid="stSidebar"] > div > div > div > ul,
    section[data-testid="stSidebar"] div[data-testid="stVerticalPageNav"],
    section[data-testid="stSidebar"] nav,
    section[data-testid="stSidebar"] [data-testid="stPageNav"],
    [data-testid="stSidebarContent"] > div > ul {
        display: none !important;
        visibility: hidden !important;
    }
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] button {
        border: 0px !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-box-shadow: none !important;
        background-color: transparent !important;
    }
    .stButton > button {
        border: none !important;
        background: none !important;
        padding: 0 !important;
        font-weight: normal !important;
        color: inherit !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        background: none !important;
        color: inherit !important;
        border: none !important;
        box-shadow: none !important;
    }
    .stButton > button:focus {
        border: none !important;
        box-shadow: none !important;
    }
    .stButton > button:active {
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        gap: 0rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0rem !important;
    }
    [data-testid="stSidebar"] > div {
        gap: 0rem !important;
    }
    section[data-testid="stSidebar"] > div > div {
        gap: 0rem !important;
    }
</style>
"""


def render_structural_plotter() -> None:
    """Render the Structural Plotter page."""
    st.markdown(COMMON_STYLES, unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">🔷 Structural Plotter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Visualize and analyze crystal structures</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_quick, col_upload = st.columns(2)
    
    with col_quick:
        st.markdown("#### 📂 Working Directory")
        working_dir = st.text_input("Working Directory", value=st.session_state.get("current_folder", ""), key="working_dir_struct")
        
        if working_dir and os.path.isdir(working_dir):
            try:
                files = os.listdir(working_dir)
                poscar_files = [f for f in files if f.upper() in ["POSCAR", "CONTCAR"]]
                
                if poscar_files:
                    selected_file = st.selectbox("Select structure file", poscar_files, key="quick_struct")
                    if selected_file:
                        file_path = os.path.join(working_dir, selected_file)
                        try:
                            with open(file_path, 'r') as f:
                                poscar_content = f.read()
                            _render_structure_viewer(poscar_content)
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                else:
                    st.info("No POSCAR or CONTCAR found in current folder")
            except Exception as e:
                st.error(f"Error accessing folder: {str(e)}")
        elif working_dir:
            st.error("Invalid directory path")
    
    with col_upload:
        st.markdown("#### 📤 Upload File")
        uploaded_file = st.file_uploader("Upload POSCAR or CONTCAR", type=None, accept_multiple_files=False)
        
        if uploaded_file:
            try:
                poscar_content = uploaded_file.getvalue().decode("utf-8")
                _render_structure_viewer(poscar_content)
            except Exception as e:
                st.error(f"Error reading uploaded file: {str(e)}")

def _set_py3dmol_view_along_c_axis(view, atoms) -> None:
    """Orient the py3Dmol camera to look along the c lattice vector,
    so the ab plane is shown."""
    import numpy as np
    cell = np.array(atoms.cell)

    a_vec = cell[0]
    c_vec = cell[2]

    c_norm = np.linalg.norm(c_vec)
    if c_norm < 1e-12:
        return
    view_dir = c_vec / c_norm  # look along c

    # Use a as the "up-like" reference, projected to plane normal to c
    a_proj = a_vec - np.dot(a_vec, view_dir) * view_dir
    a_norm = np.linalg.norm(a_proj)
    if a_norm < 1e-12:
        # fallback if a is nearly parallel to c
        fallback = np.array([1.0, 0.0, 0.0])
        a_proj = fallback - np.dot(fallback, view_dir) * view_dir
        a_norm = np.linalg.norm(a_proj)
        if a_norm < 1e-12:
            fallback = np.array([0.0, 1.0, 0.0])
            a_proj = fallback - np.dot(fallback, view_dir) * view_dir
            a_norm = np.linalg.norm(a_proj)

    up = a_proj / a_norm
    right = np.cross(up, view_dir)
    right /= np.linalg.norm(right)
    up = np.cross(view_dir, right)
    up /= np.linalg.norm(up)

    # 4x4 rotation/view matrix expected by 3Dmol.js / py3Dmol
    view.setView([
        float(right[0]), float(right[1]), float(right[2]), 0.0,
        float(up[0]),    float(up[1]),    float(up[2]),    0.0,
        float(view_dir[0]), float(view_dir[1]), float(view_dir[2]), 0.0,
        0.0, 0.0, 0.0, 1.0
    ])
    view.zoomTo()


def build_atoms_from_data(lattice_params, elements, positions, fractional=False):
    """
    Reconstruct ASE Atoms object.

    Parameters
    ----------
    lattice_params : dict
        {'a', 'b', 'c', 'alpha', 'beta', 'gamma'}
    elements : list[str]
    positions : list[list[float]]
    fractional : bool
        True if positions are fractional (POSCAR default)
    """

    from ase import Atoms
    from ase.geometry import cellpar_to_cell
    import numpy as np

    # Convert lattice parameters → 3x3 cell
    cell = cellpar_to_cell([
        lattice_params["a"],
        lattice_params["b"],
        lattice_params["c"],
        lattice_params["alpha"],
        lattice_params["beta"],
        lattice_params["gamma"],
    ])

    positions = np.array(positions)

    if fractional:
        atoms = Atoms(
            symbols=elements,
            scaled_positions=positions,
            cell=cell,
            pbc=True
        )
    else:
        atoms = Atoms(
            symbols=elements,
            positions=positions,
            cell=cell,
            pbc=True
        )

    return atoms


def _render_structure_viewer(poscar_content: str) -> None:
    """Render the structure viewer with py3Dmol."""
    st.markdown("---")
    st.markdown("#### Structure Viewer")
    
    try:
        import py3Dmol
        
        view, lattice_params, elements, positions = _create_py3dmol_view(poscar_content)
        
        if view:
            atoms = build_atoms_from_data(lattice_params, elements, positions)
            col_params, col_viewer = st.columns([1, 4])
            
            with col_params:
                st.markdown("**Lattice Parameters**")
                st.markdown(f"**a** = {lattice_params['a']:.4f} Å")
                st.markdown(f"**b** = {lattice_params['b']:.4f} Å")
                st.markdown(f"**c** = {lattice_params['c']:.4f} Å")
                st.markdown(f"**α** = {lattice_params['alpha']:.2f}°")
                st.markdown(f"**β** = {lattice_params['beta']:.2f}°")
                st.markdown(f"**γ** = {lattice_params['gamma']:.2f}°")
                
                st.markdown("---")
                st.markdown("**Atomic Information**")
                
                from collections import Counter
                elem_counts = Counter(elements)

                # for elem, count in elem_counts.items():
                #     color = _get_element_color(elem)
                #     st.markdown(f"**{elem}**: {count} atoms")  
                    
                for elem, count in elem_counts.items():
                    color = _get_element_color(elem)
                    st.markdown(
                        f"""
                        <span style="
                            display:inline-block;
                            width:12px;
                            height:12px;
                            background-color:{color};
                            border-radius:50%;
                            margin-right:8px;
                        "></span>
                        <strong>{elem}</strong>: {count} atoms
                        """,
                        unsafe_allow_html=True
                    )   

                st.markdown("---")
                st.markdown("**Total Atoms**: {0}".format(len(elements)))
            
            with col_viewer:

                view_mode = st.radio(
                    "Choose view mode",
                    ["3D View", "2D View"],
                    horizontal=True,
                    key="structure_view_mode",
                )

                if view_mode == "2D View":
                    _set_py3dmol_view_along_c_axis(view, atoms)
                else:
                    view.zoomTo()

                viewer_html = view._make_html()
                st.components.v1.html(viewer_html, height=600)
                
                # st.markdown("---")
                # st.markdown("**Viewing Options**")
                
                # col_ball, col_wire = st.columns(2)
                # with col_ball:
                #     style = st.radio("Style", ["Ball and Stick", "Space Filling", "Wireframe"], key="struct_style")
                # with col_wire:
                #     spin = st.checkbox("Spin structure", value=False, key="struct_spin")
                
                # if spin:
                #     view.spin(True)
                # else:
                #     view.spin(False)
                
                view.render()
        else:
            st.error("Could not parse structure file. Please check the format.")
    except ImportError:
        st.error("Py3Dmol is not installed. Please install it with: pip install py3Dmol")
    except Exception as e:
        st.error(f"Error rendering structure: {str(e)}")


def _create_py3dmol_view(poscar_content: str):
    """Create Py3Dmol viewer with structure."""
    import py3Dmol
    
    lines = [l.strip() for l in poscar_content.strip().split("\n") if l.strip()]
    
    if len(lines) < 8:
        return None, None, None, None
    
    scale = float(lines[1])
    lattice = []
    for i in range(2, 5):
        lattice.append([float(x) * scale for x in lines[i].split()])
    
    line_5 = lines[5]
    line_6 = lines[6]
    
    if line_5[0].isdigit():
        counts = [int(x) for x in line_5.split()]
        elements = line_6.split()
        coord_line_idx = 7
    else:
        elements = line_5.split()
        counts = [int(x) for x in line_6.split()]
        coord_line_idx = 7
    
    coord_type = lines[coord_line_idx].strip()
    if coord_type[0] in ("S", "s"):
        coord_line_idx += 1
        coord_type = lines[coord_line_idx].strip()
    coord_line_idx += 1
    
    total_atoms = sum(counts)
    positions = []
    for i in range(total_atoms):
        if coord_line_idx + i >= len(lines):
            break
        parts = lines[coord_line_idx + i].split()[:3]
        positions.append([float(x) for x in parts])
    
    all_elements = []
    for elem, cnt in zip(elements, counts):
        all_elements.extend([elem] * cnt)
    
    all_coords = []
    for pos in positions:
        if coord_type.startswith("C") or coord_type.startswith("c"):
            all_coords.append(pos)
        else:
            cart = [
                lattice[0][j] * pos[0] + lattice[1][j] * pos[1] + lattice[2][j] * pos[2]
                for j in range(3)
            ]
            all_coords.append(cart)
    
    lattice_params = _calculate_lattice_params(lattice)
    
    view = py3Dmol.view(width=800, height=600)
    # view.setBackgroundColor(0xeeeeee)
    view.setBackgroundColor("white")
    
    for elem, coord in zip(all_elements, all_coords):
        color = _get_element_color(elem)
        view.addSphere({
            "center": {"x": float(coord[0]), "y": float(coord[1]), "z": float(coord[2])},
            "radius": 0.5, "color": color
        })
    
    corners = [
        {"x": 0.0, "y": 0.0, "z": 0.0},
        {"x": float(lattice[0][0]), "y": float(lattice[0][1]), "z": float(lattice[0][2])},
        {"x": float(lattice[1][0]), "y": float(lattice[1][1]), "z": float(lattice[1][2])},
        {"x": float(lattice[2][0]), "y": float(lattice[2][1]), "z": float(lattice[2][2])},
        {"x": float(lattice[0][0] + lattice[1][0]), "y": float(lattice[0][1] + lattice[1][1]), "z": float(lattice[0][2] + lattice[1][2])},
        {"x": float(lattice[0][0] + lattice[2][0]), "y": float(lattice[0][1] + lattice[2][1]), "z": float(lattice[0][2] + lattice[2][2])},
        {"x": float(lattice[1][0] + lattice[2][0]), "y": float(lattice[1][1] + lattice[2][1]), "z": float(lattice[1][2] + lattice[2][2])},
        {"x": float(lattice[0][0] + lattice[1][0] + lattice[2][0]), "y": float(lattice[0][1] + lattice[1][1] + lattice[2][1]), "z": float(lattice[0][2] + lattice[1][2] + lattice[2][2])},
    ]
    
    cell_edges = [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (2, 4), (2, 6), (3, 5), (3, 6), (4, 7), (5, 7), (6, 7)]
    for i, j in cell_edges:
        view.addLine({"start": corners[i], "end": corners[j], "color": "gray", "linewidth": 2.0})
    
    view.addLine({"start": corners[0], "end": {"x": float(lattice[0][0]), "y": float(lattice[0][1]), "z": float(lattice[0][2])}, "color": "red", "linewidth": 5})
    view.addLine({"start": corners[0], "end": {"x": float(lattice[1][0]), "y": float(lattice[1][1]), "z": float(lattice[1][2])}, "color": "green", "linewidth": 5})
    view.addLine({"start": corners[0], "end": {"x": float(lattice[2][0]), "y": float(lattice[2][1]), "z": float(lattice[2][2])}, "color": "blue", "linewidth": 5})

    a_label_pos = {"x": float(lattice[0][0]) * 0.85, "y": float(lattice[0][1]) * 0.85, "z": float(lattice[0][2]) * 0.85}
    b_label_pos = {"x": float(lattice[1][0]) * 0.85, "y": float(lattice[1][1]) * 0.85, "z": float(lattice[1][2]) * 0.85}
    c_label_pos = {"x": float(lattice[2][0]) * 0.85, "y": float(lattice[2][1]) * 0.85, "z": float(lattice[2][2]) * 0.85}

    view.addLabel("a", {"position": a_label_pos, "fontSize": 25, "fontColor": "red", "backgroundColor": "white"})
    view.addLabel("b", {"position": b_label_pos, "fontSize": 25, "fontColor": "green", "backgroundColor": "white"})
    view.addLabel("c", {"position": c_label_pos, "fontSize": 25, "fontColor": "blue", "backgroundColor": "white"})
    
    view.zoomTo()
    
    return view, lattice_params, all_elements, all_coords


def _calculate_lattice_params(lattice):
    """Calculate lattice parameters from lattice vectors."""
    import math
    
    a = math.sqrt(lattice[0][0]**2 + lattice[0][1]**2 + lattice[0][2]**2)
    b = math.sqrt(lattice[1][0]**2 + lattice[1][1]**2 + lattice[1][2]**2)
    c = math.sqrt(lattice[2][0]**2 + lattice[2][1]**2 + lattice[2][2]**2)
    
    alpha = math.acos((lattice[1][0]*lattice[2][0] + lattice[1][1]*lattice[2][1] + lattice[1][2]*lattice[2][2]) / (b * c)) * 180 / math.pi
    beta = math.acos((lattice[0][0]*lattice[2][0] + lattice[0][1]*lattice[2][1] + lattice[0][2]*lattice[2][2]) / (a * c)) * 180 / math.pi
    gamma = math.acos((lattice[0][0]*lattice[1][0] + lattice[0][1]*lattice[1][1] + lattice[0][2]*lattice[1][2]) / (a * b)) * 180 / math.pi
    
    return {
        'a': a,
        'b': b,
        'c': c,
        'alpha': alpha,
        'beta': beta,
        'gamma': gamma,
    }


def _get_element_color(element: str) -> str:
    """Get color for element."""
    colors = {
        "H": "white", "He": "cyan", "Li": "purple", "Be": "green",
        "B": "tan", "C": "gray", "N": "blue", "O": "red",
        "F": "green", "Ne": "cyan", "Na": "purple", "Mg": "green",
        "Al": "gray", "Si": "tan", "P": "orange", "S": "yellow",
        "Cl": "green", "Ar": "cyan", "K": "purple", "Ca": "green",
        "Sc": "pink", "Ti": "gray", "V": "cyan", "Cr": "magenta",
        "Mn": "pink", "Fe": "orange", "Co": "pink", "Ni": "green",
        "Cu": "brown", "Zn": "gray", "Ga": "gray", "Ge": "tan",
        "As": "tan", "Se": "yellow", "Br": "darkred", "Kr": "cyan",
        "Rb": "purple", "Sr": "green", "Y": "pink", "Zr": "gray",
        "Nb": "cyan", "Mo": "magenta", "Tc": "pink", "Ru": "cyan",
        "Rh": "pink", "Pd": "brown", "Ag": "gray", "Cd": "gray",
        "In": "gray", "Sn": "gray", "Sb": "gray", "Te": "tan",
        "I": "purple", "Xe": "cyan", "Cs": "purple", "Ba": "green",
        "La": "pink", "Ce": "pink", "Pr": "pink", "Nd": "pink",
        "Pm": "pink", "Sm": "pink", "Eu": "pink", "Gd": "pink",
        "Tb": "pink", "Dy": "pink", "Ho": "pink", "Er": "pink",
        "Tm": "pink", "Yb": "pink", "Lu": "pink", "Hf": "gray",
        "Ta": "cyan", "W": "magenta", "Re": "pink", "Os": "cyan",
        "Ir": "cyan", "Pt": "brown", "Au": "yellow", "Hg": "gray",
        "Tl": "gray", "Pb": "gray", "Bi": "gray", "Po": "gray",
        "At": "gray", "Rn": "cyan", "Fr": "purple", "Ra": "green",
        "Ac": "pink", "Th": "pink", "Pa": "pink", "U": "pink",
        "Np": "pink", "Pu": "pink", "Am": "pink", "Cm": "pink",
    }
    return colors.get(element, "orange")
