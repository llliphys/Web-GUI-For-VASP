"""
generators/poscar.py — POSCAR file generator.

Supports multiple generation methods:
  - Upload existing POSCAR
  - Preset materials from ASE database
  - Fetch from Materials Project API
  - Fetch from C2DB (2D materials database)
  - Fetch from PubChem (molecular structures)
  - Custom builder (manual lattice + positions)

Also contains the inline Py3Dmol structure viewer and lattice/color utilities.
"""

import io
import math
import os
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

from sections.input_generator import render_file_output

# Load environment variables from .env file
load_dotenv()


# ===========================================================================
# Public entry point
# ===========================================================================

def render_poscar_tab() -> None:
    """Render the POSCAR generator tab."""
    if "poscar_show_save_dialog" not in st.session_state:
        st.session_state.poscar_show_save_dialog = False

    poscar_method = st.radio(
        "Choose generation method:",
        ["Upload POSCAR", "Preset Materials", "Materials Project",
         "C2DB Database", "PubChem Molecules", "Custom Builder"],
        horizontal=True,
    )

    handlers = {
        "Upload POSCAR":     _poscar_from_upload,
        "Preset Materials":  _poscar_from_ase,
        "Materials Project": _poscar_from_mp,
        "C2DB Database":     _poscar_from_c2db,
        "PubChem Molecules": _poscar_from_pubchem,
        "Custom Builder":    _poscar_custom,
    }
    handler = handlers.get(poscar_method)
    if handler:
        handler()

    # Show preview + 3D viewer if content has been generated
    if "poscar_content" in st.session_state:
        render_file_output(st.session_state.poscar_content, "POSCAR", "poscar")
        _render_poscar_viewer(st.session_state.poscar_content)


# ===========================================================================
# Method 1: Upload
# ===========================================================================

def _poscar_from_upload() -> None:
    """Load POSCAR from an uploaded file (parsed with ASE)."""
    st.markdown("###### Upload Existing POSCAR")
    uploaded_file = st.file_uploader("Choose a POSCAR file", type=None,
                                     accept_multiple_files=False)
    if uploaded_file is not None:
        try:
            from ase.io import read

            file_content = uploaded_file.getvalue().decode("utf-8")
            atoms = read(io.StringIO(file_content), format="vasp")
            st.success(f"File uploaded! Structure: {atoms.get_chemical_formula()}")

            if st.button("Use This POSCAR", key="gen_uploaded_poscar",  type="primary"):
                from ase.io.vasp import write_vasp
                buf = io.StringIO()
                write_vasp(buf, atoms)
                st.session_state.poscar_content = buf.getvalue()
                st.success("POSCAR generated successfully!")

        except Exception as e:
            st.error(f"Error reading file with ASE: {str(e)}")
            st.info("Make sure the file is in valid POSCAR format")


# ===========================================================================
# Method 2: Preset materials (ASE database)
# ===========================================================================

def _poscar_from_ase() -> None:
    """Generate POSCAR from ASE built-in structures."""
    st.markdown("###### Load from ASE Database")
    try:
        from ase.build import bulk

        preset_category = st.selectbox("Category",
                                       ["Elements", "Binary Compounds", "Common Structures"])
        if preset_category == "Elements":
            _poscar_ase_elements(bulk)
        elif preset_category == "Binary Compounds":
            _poscar_ase_binary()
        elif preset_category == "Common Structures":
            _poscar_ase_common()
    except ImportError:
        st.error("ASE library not found. Please install: pip install ase")


def _poscar_ase_elements(bulk_fn) -> None:
    """Generate POSCAR for a single element with ASE bulk()."""
    element = st.selectbox("Element", [
        "Si", "Ge", "C", "Fe", "Cu", "Ag", "Au", "Al", "Pt", "Pd",
        "Na", "K", "Mg", "Ca", "Ti", "V", "Cr", "Mn", "Co", "Ni",
        "Zn", "Mo", "W",
    ])
    crystal_structure = st.selectbox("Crystal Structure",
                                     ["fcc", "bcc", "hcp", "diamond"])
    a = st.number_input("Lattice Constant a (Å)", 3.0, step=0.01)
    st.markdown("###### Miller Indices (for surfaces)")
    st.text_input("Miller Indices", "1 0 0")

    if st.button("Generate from ASE"):
        try:
            atoms = bulk_fn(element, crystal_structure, a=a)
            st.session_state.poscar_content = _atoms_to_poscar(
                atoms, f"ASE: {element} {crystal_structure}")
            st.success(f"Generated {element} in {crystal_structure} structure!")
        except Exception as e:
            st.error(f"Error: {str(e)}")


def _poscar_ase_binary() -> None:
    """Generate a simple template POSCAR for binary compounds."""
    compound = st.selectbox("Compound",
                            ["SiC", "GaAs", "GaN", "ZnO", "TiO2",
                             "Fe2O3", "Al2O3", "SiO2"])
    structure_type = st.selectbox("Structure Type",
                                  ["zincblende", "wurtzite", "rocksalt", "perovskite"])
    a = st.number_input("Lattice Constant a (Å)", 4.0, step=0.01)

    if st.button("Generate Compound"):
        st.info(f"Generating {compound} with {structure_type} structure...")
        st.session_state.poscar_content = (
            f"# {compound} - {structure_type}\n1.0\n"
            f"{a} 0.0 0.0\n0.0 {a} 0.0\n0.0 0.0 {a}\n"
            f"{compound}\n1\nCartesian\n0.0 0.0 0.0\n"
        )
        st.success(f"Generated {compound} structure template!")


def _poscar_ase_common() -> None:
    """Generate POSCAR for common crystal structures."""
    common_struct = st.selectbox("Common Structure", [
        "FCC Cu", "BCC Fe", "HCP Mg", "Diamond Si",
        "NaCl", "CsCl", "ZnS",
    ])
    if st.button("Load Structure"):
        structures = {
            "FCC Cu":     {"a": 3.61, "elem": "Cu",    "count": 4},
            "BCC Fe":     {"a": 2.87, "elem": "Fe",    "count": 2},
            "HCP Mg":     {"a": 3.21, "c": 5.21, "elem": "Mg", "count": 2},
            "Diamond Si": {"a": 5.43, "elem": "Si",    "count": 8},
            "NaCl":       {"a": 5.64, "elem": "Na Cl", "count": "1 1"},
            "CsCl":       {"a": 4.11, "elem": "Cs Cl", "count": "1 1"},
            "ZnS":        {"a": 5.41, "elem": "Zn S",  "count": "1 1"},
        }
        s = structures[common_struct]

        if "c" in s:
            content = (
                f"{common_struct}\n1.0\n"
                f"{s['a']} 0.0 0.0\n0.0 {s['a']} 0.0\n0.0 0.0 {s['c']}\n"
                f"{s['elem']}\n{s['count']}\nDirect\n"
                f"0.0 0.0 0.0\n0.5 0.5 0.5\n"
            )
        else:
            content = (
                f"{common_struct}\n1.0\n"
                f"{s['a']} 0.0 0.0\n0.0 {s['a']} 0.0\n0.0 0.0 {s['a']}\n"
                f"{s['elem']}\n{s['count']}\nCartesian\n0.0 0.0 0.0\n"
            )
            if s["count"] == 4:
                content += "0.5 0.5 0.0\n0.5 0.0 0.5\n0.0 0.5 0.5\n"
            elif s["count"] == 8:
                content += (
                    "0.25 0.25 0.25\n0.75 0.75 0.25\n"
                    "0.75 0.25 0.75\n0.25 0.75 0.75\n"
                    "0.5 0.5 0.0\n0.5 0.0 0.5\n"
                    "0.0 0.5 0.5\n0.0 0.0 0.0\n"
                )
        st.session_state.poscar_content = content
        st.success(f"Loaded {common_struct}!")


# ===========================================================================
# Method 3: Materials Project
# ===========================================================================

def _poscar_from_mp() -> None:
    """Fetch a structure from the Materials Project API."""
    st.markdown("###### Fetch from Materials Project")
    st.info("Get structures from Materials Project (https://materialsproject.org)")

    # Load default API key from environment variable
    default_mp_key = os.environ.get("MP_API_KEY", "")

    mp_api_key = st.text_input(
        "Materials Project API Key", type="password",
        value=default_mp_key,
        help="Get from materialsproject.org or set MP_API_KEY in the .env file",
    )
    mp_search_type = st.radio("Search by", ["Material Formula", "Material ID"])

    if mp_search_type == "Material Formula":
        _mp_search_formula(mp_api_key)
    else:
        _mp_search_by_id(mp_api_key)


def _mp_search_formula(mp_api_key: str) -> None:
    """Search Materials Project by chemical formula."""
    mp_formula = st.text_input("Material Formula (e.g., Si, Fe2O3, CaTiO3)", "Fe2O3")

    if "mp_search_results" not in st.session_state:
        st.session_state.mp_search_results = []
    if "mp_api_key" not in st.session_state:
        st.session_state.mp_api_key = ""

    if st.button("Search Formula"):
        if not mp_api_key:
            st.warning("Please enter your API key")
            return
        st.session_state.mp_api_key = mp_api_key
        with st.spinner("Searching..."):
            try:
                from mp_api.client import MPRester
                import pandas as pd

                mpr = MPRester(mp_api_key)
                docs = mpr.summary.search(formula=mp_formula)

                if not docs:
                    st.session_state.mp_search_results = []
                    st.warning("No materials found. Try a different formula format.")
                    return

                st.success(f"Found {len(docs)} materials for {mp_formula}")
                search_results = []
                for doc in docs:
                    search_results.append({
                        "Material ID":    doc.material_id,
                        "Band Gap (eV)":  str(doc.band_gap),
                        "Crystal System": str(doc.symmetry.crystal_system),
                        "Symmetry Symbol": str(doc.symmetry.symbol),
                        "Point Group":    str(doc.symmetry.point_group),
                        "Formula":        doc.formula_pretty,
                        "Is Stable":      doc.is_stable,
                        "Is Metal":       doc.is_metal,
                    })

                st.session_state.mp_search_results = search_results
                df = pd.DataFrame(search_results)
                st.dataframe(df)

            except ImportError:
                st.error("Please install: pip install mp-api")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Let user pick from search results
    if st.session_state.mp_search_results:
        mp_id_options = [s["Material ID"] for s in st.session_state.mp_search_results]
        selected_id = st.selectbox("Select Material ID to load:",
                                   mp_id_options, key="mp_selectbox")
        if st.button("Load Selected Structure", key="mp_load_btn"):
            _mp_load_structure(selected_id)


def _mp_search_by_id(mp_api_key: str) -> None:
    """Fetch a single structure from Materials Project by ID."""
    mp_material_id = st.text_input("Material ID (e.g., mp-149, mp-1234)", "mp-149")

    if st.button("Fetch by ID"):
        if not mp_api_key:
            st.warning("Please enter your API key")
            return
        with st.spinner("Fetching..."):
            _mp_load_structure(mp_material_id, mp_api_key)


def _mp_load_structure(material_id: str, api_key: Optional[str] = None) -> None:
    """Download a structure from Materials Project and convert to POSCAR."""
    try:
        from mp_api.client import MPRester
        from ase.io.vasp import write_vasp

        key = api_key or st.session_state.mp_api_key
        mpr = MPRester(key)
        structure = mpr.get_structure_by_material_id(material_id)
        atoms = structure.to_ase_atoms()

        buf = io.StringIO()
        write_vasp(buf, atoms)
        st.session_state.poscar_content = buf.getvalue()
        st.success(f"Successfully loaded: {material_id}")
    except ImportError:
        st.error("Please install: pip install mp-api")
    except Exception as e:
        st.error(f"Error: {str(e)}")


# ===========================================================================
# Method 4: C2DB (2D materials)
# ===========================================================================

def _poscar_from_c2db() -> None:
    """Fetch a 2D material from the C2DB database."""
    st.markdown("###### Fetch from C2DB (Computational 2D Materials)")
    st.info("Get 2D materials from the C2DB database (https://cmr.fysik.dtu.dk)")

    c2db_material = st.text_input("C2DB ID (e.g., MoS2@aldehyd)", "MoS2@aldehyd")

    if st.button("Search C2DB"):
        with st.spinner("Searching C2DB..."):
            try:
                import urllib.request
                import json

                url = (f"https://cmr.fysik.dtu.dk/api/v1/c2db/"
                       f"{c2db_material.replace('@', '%40')}")
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                response = urllib.request.urlopen(req, timeout=10)
                data = json.loads(response.read().decode())

                st.json(data)
                st.info("C2DB structure data retrieved.")

                cell = data.get("cell", {})
                a = cell.get("a", 3.18)
                b = cell.get("b", 3.18)
                c = cell.get("c", 20.0)

                atoms_data = data.get("atoms", [])
                if atoms_data:
                    st.session_state.poscar_content = _build_poscar_from_c2db(
                        c2db_material, a, b, c, atoms_data)
                    st.success("Generated POSCAR")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("---")
    st.markdown("##### Common 2D Materials Quick Access")
    _render_2d_materials_section()


def _build_poscar_from_c2db(name: str, a: float, b: float, c: float,
                            atoms_data: list) -> str:
    """Build POSCAR from C2DB API response data."""
    symbols = [atom["symbol"] for atom in atoms_data]
    positions = [atom["position"] for atom in atoms_data]
    unique_symbols, counts = _count_elements(symbols)

    lines = [
        f"C2DB: {name}", "1.0",
        f"{a:.10f} 0.0 0.0",
        f"0.0 {b:.10f} 0.0",
        f"0.0 0.0 {c:.10f}",
        " ".join(unique_symbols),
        " ".join(str(c) for c in counts),
        "Cartesian",
    ]
    for pos in positions:
        lines.append(f"{pos[0]:.10f} {pos[1]:.10f} {pos[2]:.10f}")
    return "\n".join(lines) + "\n"


def _render_2d_materials_section() -> None:
    """Render quick-access selector for common 2D materials."""
    common_2d = st.selectbox("Select common 2D material", [
        "MoS2", "WS2", "MoSe2", "WSe2", "h-BN",
        "Graphene", "Phosphorene", "Silicene",
    ])
    col1, col2 = st.columns(2)
    with col1:
        a_2d = st.number_input("a (Å)", 3.18, step=0.01, key="a_2d")
    with col2:
        c_2d = st.number_input("c (Å)", 20.0, step=0.1, key="c_2d")

    if st.button("Generate 2D Structure"):
        st.session_state.poscar_content = _build_2d_poscar(common_2d, a_2d, c_2d)
        st.success(f"Generated {common_2d} structure!")


# 2D material template data: element string, count string, fractional positions.
_2D_STRUCTURES = {
    "MoS2":        {"elem": "Mo S",  "count": "1 2",
                    "pos": [[0, 0, 0], [0.333, 0.667, 0.25], [0.667, 0.333, 0.25]]},
    "WS2":         {"elem": "W S",   "count": "1 2",
                    "pos": [[0, 0, 0], [0.333, 0.667, 0.25], [0.667, 0.333, 0.25]]},
    "MoSe2":       {"elem": "Mo Se", "count": "1 2",
                    "pos": [[0, 0, 0], [0.333, 0.667, 0.25], [0.667, 0.333, 0.25]]},
    "WSe2":        {"elem": "W Se",  "count": "1 2",
                    "pos": [[0, 0, 0], [0.333, 0.667, 0.25], [0.667, 0.333, 0.25]]},
    "h-BN":        {"elem": "B N",   "count": "1 1",
                    "pos": [[0, 0, 0], [0.333, 0.667, 0.25]]},
    "Graphene":    {"elem": "C",     "count": "2",
                    "pos": [[0, 0, 0], [0.333, 0.667, 0]]},
    "Phosphorene": {"elem": "P",     "count": "4",
                    "pos": [[0, 0, 0], [0.5, 0.25, 0], [0.5, 0.75, 0], [0, 0.5, 0]]},
    "Silicene":    {"elem": "Si",    "count": "2",
                    "pos": [[0, 0, 0], [0.333, 0.667, 0]]},
}


def _build_2d_poscar(material: str, a: float, c: float) -> str:
    """Build POSCAR for a 2D material with hexagonal lattice."""
    s = _2D_STRUCTURES[material]
    lines = [
        f"{material} (2D material)", "1.0",
        f"{a:.10f} 0.0 0.0",
        f"{-a / 2:.10f} {a * 0.866:.10f} 0.0",
        f"0.0 0.0 {c:.10f}",
        s["elem"], s["count"], "Direct",
    ]
    for pos in s["pos"]:
        lines.append(f"{pos[0]:.10f} {pos[1]:.10f} {pos[2]:.10f}")
    return "\n".join(lines) + "\n"


# ===========================================================================
# Method 5: PubChem (molecules)
# ===========================================================================

def _poscar_from_pubchem() -> None:
    """Fetch a molecular structure from PubChem."""
    st.markdown("###### Fetch from PubChem (Molecules)")
    st.info("Get molecular structures from PubChem (https://pubchem.ncbi.nlm.nih.gov)")

    pubchem_id = st.text_input("PubChem CID (e.g., 2244 for aspirin)", "2244")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Add PBE pseudopotentials info", value=True)
    with col2:
        vacuum = st.number_input("Vacuum (Å)", 10.0, step=1.0)

    if st.button("Fetch from PubChem"):
        with st.spinner("Fetching molecule..."):
            _fetch_pubchem_molecule(pubchem_id, vacuum)

    st.markdown("---")
    st.markdown("##### Common Molecules Quick Access")
    _render_common_molecules()


def _fetch_pubchem_molecule(cid: str, vacuum: float) -> None:
    """Download molecule info from PubChem and build a POSCAR."""
    try:
        import urllib.request
        import json
        from ase.build import molecule
        from ase.io.vasp import write_vasp

        url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}"
               f"/property/IsomericSMILES,IUPACName/JSON")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode())

        props = data["PropertyTable"]["Properties"][0]
        smiles = props.get("IsomericSMILES", "")
        name = props.get("IUPACName", "Unknown")
        st.success(f"Found: {name}")
        st.code(smiles, language="text")

        try:
            atoms = molecule(smiles)
            cell_dim = atoms.get_cell()
            a = cell_dim[0][0] if cell_dim[0][0] > 0 else vacuum
            b = cell_dim[1][1] if cell_dim[1][1] > 0 else vacuum
            c = cell_dim[2][2] if cell_dim[2][2] > 0 else vacuum
            atoms.set_cell([a, 0, 0, 0, b, 0, 0, 0, c])
            atoms.center()

            buf = io.StringIO()
            write_vasp(buf, atoms)
            st.session_state.poscar_content = buf.getvalue()
            st.success(f"Molecule loaded: {atoms.get_chemical_formula()}")
        except Exception:
            poscar_content = (
                f"PubChem: {name} (CID: {cid})\n1.0\n"
                f"{vacuum:.1f} 0.0 0.0\n0.0 {vacuum:.1f} 0.0\n0.0 0.0 {vacuum:.1f}\n"
                f"# SMILES: {smiles}\n# Note: Please verify atomic positions manually\n"
            )
            st.session_state.poscar_content = poscar_content
            st.info("Basic structure generated. Please verify atomic positions.")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def _render_common_molecules() -> None:
    """Render quick-access selector for common molecules."""
    common_molecules = st.selectbox("Select common molecule", [
        "H2O", "CO2", "CH4", "C2H6", "C2H4", "C6H6", "NH3", "N2", "O2", "H2",
    ])
    if st.button("Load Molecule"):
        try:
            from ase.build import molecule
            from ase.io.vasp import write_vasp

            atoms = molecule(common_molecules)
            vacuum = 10.0
            atoms.set_cell([vacuum, 0, 0, 0, vacuum, 0, 0, 0, vacuum])
            atoms.center()

            buf = io.StringIO()
            write_vasp(buf, atoms)
            st.session_state.poscar_content = buf.getvalue()
            st.success(f"Loaded {common_molecules}: {atoms.get_chemical_formula()}")
        except Exception as e:
            st.error(f"Error: {str(e)}")


# ===========================================================================
# Method 6: Custom builder
# ===========================================================================

def _poscar_custom() -> None:
    """Build a POSCAR manually with user-specified lattice and positions."""
    st.markdown("###### Lattice Parameters")
    st.markdown("###### Elements & Composition")

    num_elements = st.number_input("Number of Elements", min_value=1, max_value=10)

    elements = []
    counts = []
    positions_by_element = []

    for i in range(int(num_elements)):
        col_elem, col_count = st.columns([1, 1])
        with col_elem:
            elem = st.text_input(f"Element {i + 1}", "Si", key=f"elem_{i}")
        with col_count:
            count = st.number_input(f"Count {i + 1}", min_value=1, key=f"count_{i}")
        elements.append(elem)
        counts.append(int(count))

    coordinate_type = st.selectbox("Coordinate Type", ["Cartesian", "Direct"])
    st.markdown("###### Atomic Positions")
    st.caption("Enter positions one per line: x y z (optional: S or F for selective dynamics)")

    for i, (elem, cnt) in enumerate(zip(elements, counts)):
        default_pos = "\n".join(["0.0 0.0 0.0" for _ in range(cnt)])
        with st.expander(f"Positions for {elem} ({cnt} atoms)"):
            pos_text = st.text_area(
                f"Positions for {elem}", default_pos, height=150, key=f"pos_{i}",
                help=f"Enter {cnt} lines with format: x y z "
                     f"(or x y z S/F/F/F for selective dynamics)",
            )
            positions_by_element.append(pos_text)

    if st.button("Generate POSCAR"):
        try:
            st.session_state.poscar_content = _build_custom_poscar(
                elements, counts, positions_by_element, coordinate_type)
            st.success("POSCAR generated successfully!")
        except Exception as e:
            st.error(f"Error generating POSCAR: {str(e)}")


def _build_custom_poscar(elements: list, counts: list,
                         positions_by_element: list,
                         coordinate_type: str) -> str:
    """Assemble POSCAR text from user-supplied lattice, elements, and positions."""
    lines = [
        "Custom Structure", "1.0",
        "3.0 0.0 0.0", "0.0 3.0 0.0", "0.0 0.0 3.0",
        " ".join(elements),
        " ".join(str(c) for c in counts),
        coordinate_type,
    ]
    for pos_text in positions_by_element:
        for line in pos_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                if len(parts) >= 6:
                    lines.append(f"{x:.10f} {y:.10f} {z:.10f} "
                                 f"{parts[3]} {parts[4]} {parts[5]}")
                else:
                    lines.append(f"{x:.10f} {y:.10f} {z:.10f}")
    return "\n".join(lines) + "\n"


# ===========================================================================
# Shared conversion utilities
# ===========================================================================

def _atoms_to_poscar(atoms, comment: str = "") -> str:
    """Convert an ASE Atoms object to POSCAR-format text."""
    lines = [comment, "1.0"]
    for i in range(3):
        lines.append(f"{atoms.cell[i][0]:.10f} {atoms.cell[i][1]:.10f} "
                     f"{atoms.cell[i][2]:.10f}")

    symbols = atoms.get_chemical_symbols()
    unique_symbols, counts = _count_elements(symbols)
    lines.append(" ".join(unique_symbols))
    lines.append(" ".join(str(c) for c in counts))
    lines.append("Direct")

    for pos in atoms.get_scaled_positions():
        lines.append(f"{pos[0]:.10f} {pos[1]:.10f} {pos[2]:.10f}")
    return "\n".join(lines) + "\n"


def _count_elements(symbols: list) -> tuple:
    """Return (unique_symbols, counts) preserving first-occurrence order."""
    unique_symbols = []
    counts = []
    for sym in symbols:
        if sym not in unique_symbols:
            unique_symbols.append(sym)
            counts.append(symbols.count(sym))
    return unique_symbols, counts


# ===========================================================================
# Inline 3D structure viewer (Py3Dmol)
# ===========================================================================

def _render_poscar_viewer(poscar_content: str) -> None:
    """Show an interactive 3D visualisation of the POSCAR structure."""
    st.markdown("---")
    st.markdown("#### Structure Viewer")

    try:
        import py3Dmol

        view, lattice_params = _create_py3dmol_view(poscar_content)
        if view:
            viewer_html = view._make_html()

            col_params, col_viewer = st.columns([1, 4])
            with col_params:
                st.markdown("**Lattice Parameters**")
                st.markdown(f"**a** = {lattice_params['a']:.4f} Å")
                st.markdown(f"**b** = {lattice_params['b']:.4f} Å")
                st.markdown(f"**c** = {lattice_params['c']:.4f} Å")
                st.markdown(f"**α** = {lattice_params['alpha']:.2f}°")
                st.markdown(f"**β** = {lattice_params['beta']:.2f}°")
                st.markdown(f"**γ** = {lattice_params['gamma']:.2f}°")
            with col_viewer:
                st.components.v1.html(viewer_html, height=500)
        else:
            st.info("Could not parse POSCAR for visualization")
    except ImportError:
        st.error("Py3Dmol is not installed. Please install it with: pip install py3Dmol")
    except Exception as e:
        st.error(f"Error rendering structure: {str(e)}")


def _create_py3dmol_view(poscar_content: str):
    """
    Parse POSCAR text and build a Py3Dmol view with atoms, unit cell, and
    lattice-vector arrows.  Returns (view, lattice_params) or (None, None).
    """
    try:
        import py3Dmol

        lines = [l.strip() for l in poscar_content.strip().split("\n") if l.strip()]
        if len(lines) < 8:
            return None, None

        # ── Parse lattice vectors ───────────────────────────────────
        scale = float(lines[1])
        lattice = []
        for i in range(2, 5):
            lattice.append([float(x) * scale for x in lines[i].split()])

        # ── Parse element names and counts ──────────────────────────
        line_5, line_6 = lines[5], lines[6]
        if line_5[0].isdigit():
            counts = [int(x) for x in line_5.split()]
            elements = line_6.split()
        else:
            elements = line_5.split()
            counts = [int(x) for x in line_6.split()]

        # ── Determine coordinate type (skip selective-dynamics line) ─
        coord_line_idx = 7
        coord_type = lines[coord_line_idx].strip()
        if coord_type[0] in ("S", "s"):
            coord_line_idx += 1
            coord_type = lines[coord_line_idx].strip()
        coord_line_idx += 1

        # ── Read atomic positions ───────────────────────────────────
        total_atoms = sum(counts)
        positions = []
        for i in range(total_atoms):
            if coord_line_idx + i >= len(lines):
                break
            parts = lines[coord_line_idx + i].split()[:3]
            positions.append([float(x) for x in parts])

        # Build flat element list (e.g. ["Si","Si","O","O","O"])
        all_elements = []
        for elem, cnt in zip(elements, counts):
            all_elements.extend([elem] * cnt)

        # Convert fractional → Cartesian if needed
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

        # ── Build Py3Dmol scene ─────────────────────────────────────
        view = py3Dmol.view(width=800, height=600)
        # view.setBackgroundColor(0xeeeeee)
        view.setBackgroundColor("white")

        # Atoms
        for elem, coord in zip(all_elements, all_coords):
            color = _get_element_color(elem)
            view.addSphere({
                "center": {"x": float(coord[0]), "y": float(coord[1]),
                            "z": float(coord[2])},
                "radius": 0.5, "color": color,
            })

        # Unit-cell edges
        corners = _unit_cell_corners(lattice)
        cell_edges = [
            (0, 1), (0, 2), (0, 3), (1, 4), (1, 5),
            (2, 4), (2, 6), (3, 5), (3, 6), (4, 7), (5, 7), (6, 7),
        ]
        for i, j in cell_edges:
            view.addLine({"start": corners[i], "end": corners[j],
                          "color": "gray", "linewidth": 3})

        # # Lattice-vector arrows (red = a, green = b, blue = c)
        # arrow_scale = 1.0
        # for idx, color in enumerate(["red", "green", "blue"]):
        #     view.addLine({
        #         "start": corners[0],
        #         "end": {"x": float(lattice[idx][0]) * arrow_scale,
        #                 "y": float(lattice[idx][1]) * arrow_scale,
        #                 "z": float(lattice[idx][2]) * arrow_scale},
        #         "color": color, "linewidth": 3.0,
        #     })


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
        return view, lattice_params

    except Exception:
        return None, None


def _unit_cell_corners(lattice: list) -> list:
    """Return the 8 corner points of the parallelepiped unit cell."""
    a, b, c = lattice[0], lattice[1], lattice[2]
    return [
        {"x": 0.0, "y": 0.0, "z": 0.0},
        {"x": float(a[0]), "y": float(a[1]), "z": float(a[2])},
        {"x": float(b[0]), "y": float(b[1]), "z": float(b[2])},
        {"x": float(c[0]), "y": float(c[1]), "z": float(c[2])},
        {"x": float(a[0] + b[0]), "y": float(a[1] + b[1]), "z": float(a[2] + b[2])},
        {"x": float(a[0] + c[0]), "y": float(a[1] + c[1]), "z": float(a[2] + c[2])},
        {"x": float(b[0] + c[0]), "y": float(b[1] + c[1]), "z": float(b[2] + c[2])},
        {"x": float(a[0] + b[0] + c[0]), "y": float(a[1] + b[1] + c[1]),
         "z": float(a[2] + b[2] + c[2])},
    ]


# ===========================================================================
# Lattice-parameter and element-color utilities
# ===========================================================================

def _calculate_lattice_params(lattice: list) -> dict:
    """Compute a, b, c lengths and alpha, beta, gamma angles from lattice vectors."""
    def _norm(v):
        return math.sqrt(sum(x ** 2 for x in v))

    def _dot(v1, v2):
        return sum(x1 * x2 for x1, x2 in zip(v1, v2))

    def _angle(v1, v2):
        cos_a = _dot(v1, v2) / (_norm(v1) * _norm(v2))
        cos_a = max(-1.0, min(1.0, cos_a))
        return math.acos(cos_a) * 180.0 / math.pi

    return {
        "a": _norm(lattice[0]),
        "b": _norm(lattice[1]),
        "c": _norm(lattice[2]),
        "alpha": _angle(lattice[1], lattice[2]),
        "beta":  _angle(lattice[0], lattice[2]),
        "gamma": _angle(lattice[0], lattice[1]),
    }


# CPK-style element → colour mapping.
_ELEMENT_COLORS = {
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


def _get_element_color(element: str) -> str:
    """Return the CPK colour for *element*, defaulting to orange."""
    return _ELEMENT_COLORS.get(element, "orange")
