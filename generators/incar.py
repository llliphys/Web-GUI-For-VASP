"""
generators/incar.py — INCAR file generator.

Contains:
  - INCAR_PRESETS: all preset template data (pure data, no UI logic)
  - render_incar_tab(): the main tab entry point
  - Upload, preset, and custom generation methods
  - _build_incar_content_custom(): builds INCAR text from a parameter dict

Bug fix: added missing ``gga_compat`` checkbox that was referenced but
never defined in the original code.
"""

import streamlit as st

from sections.input_generator import render_file_output


# ===========================================================================
# Section 1: Preset template data
# ===========================================================================

# Maps (category, preset_name) → INCAR file content string.
INCAR_PRESETS = {
    # ── Standard DFT ────────────────────────────────────────────────
    ("Standard DFT", "Structure Optimization"): """\
SYSTEM = Structure Optimization
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 100
NSW = 100
IBRION = 2
ISIF = 3
EDIFFG = -0.02
POTIM = 0.015
LWAVE = .FALSE.
LCHARG = .FALSE.
""",
    ("Standard DFT", "Static Calculation"): """\
SYSTEM = Static Calculation
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-6
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 100
LWAVE = .TRUE.
LCHARG = .TRUE.
""",
    ("Standard DFT", "DOS Calculation"): """\
SYSTEM = DOS Calculation
ISTART = 1
ICHARG = 10
ENCUT = 520
PREC = Accurate
EDIFF = 1E-6
ISMEAR = -5
SIGMA = 0.05
ALGO = Normal
NELM = 100
LORBIT = 11
NEDOS = 2001
EMIN = -10
EMAX = 10
LWAVE = .FALSE.
LCHARG = .FALSE.
""",
    ("Standard DFT", "Band Structure"): """\
SYSTEM = Band Structure
ISTART = 1
ICHARG = 11
ENCUT = 520
PREC = Accurate
EDIFF = 1E-6
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 100
LWAVE = .FALSE.
LCHARG = .FALSE.
""",

    # ── Phonon ──────────────────────────────────────────────────────
    ("Phonon", "DFPT Phonon"): """\
SYSTEM = DFPT Phonon
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-8
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 200
IBRION = 7
NFREE = 2
ADDGRID = .TRUE.
LREAL = .FALSE.
ISYM = 0
""",
    ("Phonon", "Finite Displacement"): """\
SYSTEM = Finite Displacement Phonon
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-8
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 200
IBRION = 5
NFREE = 2
POTIM = 0.015
ADDGRID = .TRUE.
LREAL = .FALSE.
ISYM = 0
""",

    # ── Magnetic ────────────────────────────────────────────────────
    ("Magnetic", "Ferromagnetic"): """\
SYSTEM = Ferromagnetic Calculation
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 100
ISPIN = 2
MAGMOM = 10*2.5
NSW = 100
IBRION = 2
ISIF = 3
EDIFFG = -0.02
LWAVE = .FALSE.
LCHARG = .FALSE.
""",
    ("Magnetic", "Antiferromagnetic"): """\
SYSTEM = Antiferromagnetic Calculation
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 100
ISPIN = 2
MAGMOM = 5*2.5 5*-2.5
NSW = 100
IBRION = 2
ISIF = 3
EDIFFG = -0.02
LWAVE = .FALSE.
LCHARG = .FALSE.
""",
    ("Magnetic", "Non-collinear SOC"): """\
SYSTEM = Non-collinear SOC
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 100
ISPIN = 2
LNONCOLLINEAR = .TRUE.
LSORBIT = .TRUE.
SAXIS = 0 0 1
MAGMOM = 10*0.6
NSW = 100
IBRION = 2
ISIF = 3
EDIFFG = -0.02
LWAVE = .FALSE.
LCHARG = .FALSE.
""",

    # ── DFT+U ───────────────────────────────────────────────────────
    ("DFT+U", "DFT+U (LDAU)"): """\
SYSTEM = DFT+U Calculation
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
ALGO = Normal
NELM = 100
ISPIN = 2
LDAU = .TRUE.
LDAUTYPE = 1
LDAUL = 2 2
LDAUU = 4.5 4.5
LDAUJ = 0 0
MAGMOM = 10*2.5
NSW = 100
IBRION = 2
ISIF = 3
EDIFFG = -0.02
""",

    # ── Hybrid Functional ───────────────────────────────────────────
    ("Hybrid Functional", "HSE06"): """\
SYSTEM = HSE06 Calculation
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
ALGO = Damped
NELM = 100
LHFCALC = .TRUE.
AEXX = 0.25
HFSCREEN = 0.2
PRECFOCK = Fast
NSW = 100
IBRION = 2
ISIF = 3
EDIFFG = -0.02
""",

    # ── GW / BSE ────────────────────────────────────────────────────
    ("GW/BSE", "GW"): """\
SYSTEM = GW Calculation
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
ALGO = GW0
NELM = 100
NBANDS = 200
ENCUTGW = 250
NOMEGA = 50
""",
    ("GW/BSE", "BSE"): """\
SYSTEM = BSE Calculation
ISTART = 0
ICHARG = 2
ENCUT = 520
PREC = Accurate
EDIFF = 1E-5
ISMEAR = 0
SIGMA = 0.05
ALGO = BSE
NELM = 100
LOPTICS = .TRUE.
CSHIFT = 0.1
NBANDS = 200
NBANDSO = 10
NBANDSV = 10
""",

    # ── AIMD ────────────────────────────────────────────────────────
    ("AIMD", "NVT"): """\
SYSTEM = NVT Molecular Dynamics
ISTART = 0
ICHARG = 2
ENCUT = 400
PREC = Normal
EDIFF = 1E-4
ISMEAR = 0
SIGMA = 0.05
ALGO = VeryFast
NELM = 50
IBRION = 0
NSW = 10000
POTIM = 1.0
SMASS = -1
TEBEG = 300
MDALGO = 2
""",
    ("AIMD", "NPT"): """\
SYSTEM = NPT Molecular Dynamics
ISTART = 0
ICHARG = 2
ENCUT = 400
PREC = Normal
EDIFF = 1E-4
ISMEAR = 0
SIGMA = 0.05
ALGO = VeryFast
NELM = 50
IBRION = 0
NSW = 10000
POTIM = 1.0
SMASS = -1
TEBEG = 300
MDALGO = 2
ISIF = 3
PMASS = 10
PSTRESS = 0
""",
    ("AIMD", "NVE"): """\
SYSTEM = NVE Molecular Dynamics
ISTART = 0
ICHARG = 2
ENCUT = 400
PREC = Normal
EDIFF = 1E-4
ISMEAR = 0
SIGMA = 0.05
ALGO = VeryFast
NELM = 50
IBRION = 0
NSW = 10000
POTIM = 1.0
SMASS = -1
TEBEG = 300
MDALGO = 3
LANGEVIN_GAMMA = 1 1 1
LANGEVIN_GAMMA_L = 1
""",
}

# Mapping from category name → list of preset names (preserves UI order).
PRESET_CATEGORIES = {
    "Standard DFT":      ["Structure Optimization", "Static Calculation",
                          "DOS Calculation", "Band Structure"],
    "Phonon":            ["DFPT Phonon", "Finite Displacement"],
    "Magnetic":          ["Ferromagnetic", "Antiferromagnetic", "Non-collinear SOC"],
    "DFT+U":             ["DFT+U (LDAU)"],
    "Hybrid Functional": ["HSE06"],
    "GW/BSE":            ["GW", "BSE"],
    "AIMD":              ["NVT", "NPT", "NVE"],
}


# ===========================================================================
# Section 2: Tab entry point
# ===========================================================================

def render_incar_tab() -> None:
    """Render the INCAR generator tab (upload / preset / custom)."""
    if "incar_show_save_dialog" not in st.session_state:
        st.session_state.incar_show_save_dialog = False

    incar_method = st.radio(
        "Choose generation method:",
        ["Upload INCAR", "Preset INCAR", "Custom INCAR"],
        horizontal=True,
    )

    handlers = {
        "Upload INCAR": _incar_from_upload,
        "Preset INCAR": _incar_from_preset,
        "Custom INCAR": _incar_custom,
    }
    handler = handlers.get(incar_method)
    if handler:
        handler()

    # Show preview if content has been generated
    if "incar_content" in st.session_state:
        render_file_output(st.session_state.incar_content, "INCAR", "incar")


# ===========================================================================
# Section 3: Generation methods
# ===========================================================================

def _incar_from_upload() -> None:
    """Generate INCAR from an uploaded file."""
    st.markdown("###### Upload Existing INCAR")
    uploaded_file = st.file_uploader("Choose an INCAR file", type=None,
                                     accept_multiple_files=False)
    if uploaded_file is not None:
        try:
            file_content = uploaded_file.getvalue().decode("utf-8")
            st.success("File uploaded successfully!")
            if st.button("Use This INCAR", key="gen_uploaded_incar"):
                st.session_state.incar_content = file_content
                st.success("INCAR loaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.info("Make sure the file is in valid INCAR format")


def _incar_from_preset() -> None:
    """Generate INCAR from preset templates."""
    st.markdown("###### Load from Preset Templates")

    category = st.selectbox("Category", list(PRESET_CATEGORIES.keys()))
    preset_type = st.selectbox("Preset", PRESET_CATEGORIES[category])

    if st.button("Load Preset", key="load_incar_preset"):
        st.session_state.incar_content = _get_preset_incar(category, preset_type)
        st.success(f"Loaded preset: {preset_type}")


def _get_preset_incar(category: str, preset_type: str) -> str:
    """Look up preset INCAR content by (category, preset_type) key."""
    return INCAR_PRESETS.get((category, preset_type), "")


# ===========================================================================
# Section 4: Custom INCAR builder
# ===========================================================================

def _incar_custom() -> None:
    """Render a full set of INCAR parameter widgets organised into tabs."""
    st.markdown("###### Custom INCAR Parameters")

    tabs = st.tabs([
        "Electronic Minimization",
        "Structure Optimization",
        "Output Control",
        "Electronic Band/DOS",
        "Linear Optics",
        "Magnetism",
        "DFT+U+J",
        "Hybrid/GW/BSE",
        "AIMD & Phonon",
        "Other Important",
    ])

    # Collect all parameter values into a dict (replaces 60+ positional args)
    p = {}

    # ── Tab 0: Electronic Minimization ──────────────────────────────
    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            p["system"]  = st.text_input("System Name", "My VASP Calculation")
            p["istart"]  = st.selectbox("ISTART", [0, 1, 2, 3], index=0)
            p["icharg"]  = st.selectbox("ICHARG", [0, 1, 2, 4, 10, 11, 12], index=1)
            p["encut"]   = st.text_input("ENCUT", "500")
            p["prec"]    = st.selectbox("PREC", ["Low", "Medium", "High", "Accurate"], index=3)
            p["ediff"]   = st.text_input("EDIFF", value="1E-6")
            p["nelm"]    = st.text_input("NELM", "60")
            p["nelmin"]  = st.text_input("NELMIN", "2")
        with col2:
            p["algo"]    = st.selectbox("ALGO", ["Normal", "Fast", "VeryFast",
                                                  "Conjugate", "All", "Damped"], index=0)
            p["lreal"]   = st.selectbox("LREAL", ["Auto", ".FALSE.", ".TRUE."], index=1)
            p["ismear"]  = st.selectbox("ISMEAR", [-5, -1, 0, 1], index=2)
            p["sigma"]   = st.text_input("SIGMA", "0.01")
            p["lsorbit"] = st.checkbox("LSORBIT", value=False)
            p["addgrid"] = st.checkbox("ADDGRID", value=False)
            p["lasph"]   = st.checkbox("LASPH", value=False)

    # ── Tab 1: Structure Optimization ───────────────────────────────
    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            p["nsw"]     = st.number_input("NSW (ion steps)", 0, step=1)
            p["ibrion"]  = st.selectbox("IBRION", [0, 1, 2, 3, 5, 6, 7, 8], index=2)
            p["isif"]    = st.selectbox("ISIF", [0, 1, 2, 3, 4, 5, 6, 7], index=2)
            p["ediffg"]  = st.text_input("EDIFFG (force)", "-0.01")
        with col2:
            p["potim"]   = st.text_input("POTIM", "0.015")
            p["isym"]    = st.selectbox("ISYM", [-1, 0, 2], index=1)
            p["symprec"] = st.text_input("SYMPREC", "1E-5")

    # ── Tab 2: Output Control ───────────────────────────────────────
    with tabs[2]:
        st.markdown("###### Verbosity Control (OUTCAR)")
        col1, col2 = st.columns(2)
        with col1:
            p["nwrite"] = st.selectbox("NWRITE (OUTCAR verbosity)", [0, 1, 2, 3], index=1)
            p["iprint"] = st.selectbox("IPRINT (output level)", [0, 1, 2], index=1)

        st.markdown("###### File Generation Control")
        col1, col2 = st.columns(2)
        with col1:
            p["lwave"]   = st.checkbox("LWAVE (write WAVECAR)", value=False)
            p["lcharg"]  = st.checkbox("LCHARG (write CHGCAR)", value=False)
            p["lvtot"]   = st.checkbox("LVTOT (total potential)", value=False)
        with col2:
            p["lvhar"]   = st.checkbox("LVHAR (Hartree potential)", value=False)
            p["lelf"]    = st.checkbox("LELF (electron localization)", value=False)
            p["loptics"] = st.checkbox("LOPTICS (optical props)", value=False)

        st.markdown("###### Projected DOS & Other")
        col1, col2 = st.columns(2)
        with col1:
            p["lorbit"] = st.selectbox("LORBIT (PDOS)", [0, 10, 11, 12], index=0)
        with col2:
            pass

    # ── Tab 3: Electronic Band / DOS ────────────────────────────────
    with tabs[3]:
        col1, col2 = st.columns(2)
        with col1:
            p["nedos"] = st.number_input("NEDOS", 2001, step=100)
            p["emin"]  = st.number_input("EMIN (DOS)", -10.0, step=1.0)
            p["emax"]  = st.number_input("EMAX (DOS)", 10.0, step=1.0)
        with col2:
            p["cshift"] = st.number_input("CSHIFT", 0.1, step=0.01)
            p["nbands"] = st.number_input("NBANDS", 0, step=1)
            p["iband"]  = st.text_input("IBAND (partial charge)", "")
            p["eint"]   = st.text_input("EINT (energy range)", "")

    # ── Tab 4: Linear Optics ────────────────────────────────────────
    with tabs[4]:
        col1, col2 = st.columns(2)
        with col1:
            p["lepsilon"] = st.checkbox("LEPSILON (DFPT dielectric)", value=False)
            p["lpard"]    = st.checkbox("LPARD (partial charge)", value=False)
            p["lsepb"]    = st.checkbox("LSEPB (separate by band)", value=False)
        with col2:
            p["lsepk"]  = st.checkbox("LSEPK (separate by k-point)", value=False)
            p["nbmod"]  = st.selectbox("NBMOD (local state)", [-1, 0, 1, 2, 3], index=0)
            p["lsepas"] = st.checkbox("LSEPASP (spin separated)", value=False)

    # ── Tab 5: Magnetism ────────────────────────────────────────────
    with tabs[5]:
        col1, col2 = st.columns(2)
        with col1:
            p["ispin"]  = st.selectbox("ISPIN", [1, 2], index=0)
            p["magmom"] = st.text_input("MAGMOM (e.g., 1 1 -1 -1)", "")
            p["amix"]   = st.number_input("AMIX", value=0.2, format="%.1f", placeholder=0.2)
            p["amix_mag"] = st.number_input("AMIX_MAG", value=0.8, format="%.1f", placeholder=0.8)
        with col2:
            p["lnoncollinear"] = st.checkbox("LNONCOLLINEAR", value=False)
            p["saxis"]   = st.text_input("SAXIS (spin axis, e.g., 0 0 1)", "")
            p["bmix"]    = st.number_input("BMIX", value=0.0001, format="%.4f", placeholder=0.0001)
            p["bmix_mag"] = st.number_input("BMIX_MAG", value=0.0001, format="%.4f", placeholder=0.0001)

    # ── Tab 6: DFT+U+J ─────────────────────────────────────────────
    with tabs[6]:
        col1, col2 = st.columns(2)
        with col1:
            p["ldau"]      = st.checkbox("LDAU (enable DFT+U)", value=False)
            p["ldautype"]  = st.selectbox("LDAUTYPE", [1, 2], index=0)
            p["ldaul"]     = st.text_input("LDAUL (l, e.g., 2 2)", "")
        with col2:
            p["ldauu"]     = st.text_input("LDAUU (U, e.g., 4.5 4.5)", "")
            p["ldauj"]     = st.text_input("LDAUJ (J, e.g., 0 0)", "")
            p["ldauprint"] = st.checkbox("LDAUPRINT", value=False)

    # ── Tab 7: Hybrid / GW / BSE ────────────────────────────────────
    with tabs[7]:
        col1, col2 = st.columns(2)
        with col1:
            p["lhfcalc"]  = st.checkbox("LHFCALC (hybrid functional)", value=False)
            p["aexx"]     = st.number_input("AEXX (HF ratio)", 0.25, step=0.05)
            p["hfscreen"] = st.number_input("HFSCREEN", 0.2, step=0.05)
        with col2:
            p["precfock"]    = st.selectbox("PRECFOCK", ["Low", "Normal", "Fast"], index=2)
            p["encutgw"]     = st.number_input("ENCUTGW", 250, step=10)
            p["nomega"]      = st.number_input("NOMEGA (GW freq)", 50, step=10)
            p["nmaxfockae"]  = st.number_input("NMAXFOCKAE", 0, step=1)

    # ── Tab 8: AIMD & Phonon ────────────────────────────────────────
    with tabs[8]:
        col1, col2 = st.columns(2)
        with col1:
            p["smass"]  = st.number_input("SMASS (MD)", -1, step=1)
            p["tebeg"]  = st.number_input("TEBEG (temperature)", 300.0, step=10.0)
            p["teend"]  = st.number_input("TEEND", 300.0, step=10.0)
            p["mdalgo"] = st.selectbox("MDALGO", [0, 1, 2, 3], index=0)
            p["nfree"]  = st.number_input("NFREE (finite displacement)", 2, step=1)
        with col2:
            p["langevin_gamma"]   = st.text_input("LANGEVIN_GAMMA", "")
            p["langevin_gamma_l"] = st.number_input("LANGEVIN_GAMMA_L", 1.0, step=0.1)
            p["pstress"] = st.number_input("PSTRESS", 0.0, step=0.1)
            p["pmass"]   = st.number_input("PMASS", 10.0, step=1.0)

    # ── Tab 9: Other Important ──────────────────────────────────────
    with tabs[9]:
        col1, col2 = st.columns(2)
        with col1:
            p["npar"]  = st.number_input("NPAR", 1, step=1)
            p["kpar"]  = st.number_input("KPAR", 1, step=1)
            p["ncore"] = st.number_input("NCORE", 1, step=1)
        with col2:
            p["ivdw"]       = st.number_input("IVDW (van der Waals)", 0, step=1)
            p["luse_vdw"]   = st.checkbox("LUSE_VDW", value=False)
            p["ldipol"]     = st.checkbox("LDIPOL (dipole correction)", value=False)
            p["idipol"]     = st.selectbox("IDIPOL (dipole direction)", [0, 1, 2, 3, 4], index=0)
            p["dipol"]      = st.text_input("DIPOL (dipole center)", "")
            # BUG FIX: gga_compat was referenced but never defined in the original code
            p["gga_compat"] = st.checkbox("GGA_COMPAT", value=True)

    # ── Generate button ─────────────────────────────────────────────
    if st.button("**Generate INCAR**"):
        st.session_state.incar_content = _build_incar_content_custom(p)


# ===========================================================================
# Section 5: Content builder
# ===========================================================================

def _build_incar_content_custom(p: dict) -> str:
    """
    Build INCAR file text from a parameter dictionary.

    Only non-default values are written, keeping the output minimal.
    """
    lines = []

    # ── Core electronic settings ────────────────────────────────────
    lines.append(f"SYSTEM = {p['system']}")
    lines.append(f"ISTART = {p['istart']}")
    lines.append(f"ICHARG = {p['icharg']}")
    lines.append(f"ENCUT = {p['encut']}")
    lines.append(f"PREC = {p['prec']}")
    lines.append(f"EDIFF = {p['ediff']}")
    lines.append(f"NELM = {p['nelm']}")
    if int(p["nelmin"]) > 2:
        lines.append(f"NELMIN = {p['nelmin']}")
    lines.append(f"ALGO = {p['algo']}")
    lines.append(f"LREAL = {p['lreal']}")
    lines.append(f"ISMEAR = {p['ismear']}")
    lines.append(f"SIGMA = {p['sigma']}")
    lines.append(f"ISPIN = {p['ispin']}")

    # ── Ionic relaxation ────────────────────────────────────────────
    if p["nsw"] > 0:
        lines.append(f"NSW = {p['nsw']}")
    if p["ibrion"] in [1, 2, 3, 5, 6, 7, 8]:
        lines.append(f"IBRION = {p['ibrion']}")
    if p["isif"] is not None:
        lines.append(f"ISIF = {p['isif']}")
    if p["ediffg"] != "-0.02":
        lines.append(f"EDIFFG = {p['ediffg']}")
    if p["potim"] != "0.015":
        lines.append(f"POTIM = {p['potim']}")
    if p["isym"] != -1:
        lines.append(f"ISYM = {p['isym']}")
        lines.append(f"SYMPREC = {p['symprec']}")
    if p["addgrid"]:
        lines.append("ADDGRID = .TRUE.")

    # ── Output control ──────────────────────────────────────────────
    if p["nwrite"] != 1:
        lines.append(f"NWRITE = {p['nwrite']}")
    if p["iprint"] != 1:
        lines.append(f"IPRINT = {p['iprint']}")
    if p["lwave"]:
        lines.append("LWAVE = .TRUE.")
    if p["lcharg"]:
        lines.append("LCHARG = .TRUE.")
    if p["lvtot"]:
        lines.append("LVTOT = .TRUE.")
    if p["lvhar"]:
        lines.append("LVHAR = .TRUE.")
    if p["lelf"]:
        lines.append("LELF = .TRUE.")
    if p["loptics"]:
        lines.append("LOPTICS = .TRUE.")
    if p["lorbit"] > 0:
        lines.append(f"LORBIT = {p['lorbit']}")

    # ── DOS / band settings ─────────────────────────────────────────
    if p["nedos"] > 0:
        lines.append(f"NEDOS = {p['nedos']}")
        lines.append(f"EMIN = {p['emin']}")
        lines.append(f"EMAX = {p['emax']}")
    if p["cshift"] != 0.1:
        lines.append(f"CSHIFT = {p['cshift']}")
    if p["nbands"] > 0:
        lines.append(f"NBANDS = {p['nbands']}")
    if p["iband"]:
        lines.append(f"IBAND = {p['iband']}")
    if p["eint"]:
        lines.append(f"EINT = {p['eint']}")

    # ── Linear optics ───────────────────────────────────────────────
    if p["lepsilon"]:
        lines.append("LEPSILON = .TRUE.")
    if p["lpard"]:
        lines.append("LPARD = .TRUE.")
    if p["lsepb"]:
        lines.append("LSEPB = .TRUE.")
    if p["lsepk"]:
        lines.append("LSEPK = .TRUE.")
    if p["nbmod"] != -1:
        lines.append(f"NBMOD = {p['nbmod']}")

    # ── Magnetism ───────────────────────────────────────────────────
    if p["magmom"]:
        lines.append(f"MAGMOM = {p['magmom']}")
    if p["amix"] != 0.2:
        lines.append(f"AMIX = {p['amix']}")
    if p["bmix"] != 0.0001:
        lines.append(f"BMIX = {p['bmix']}")
    if p["lnoncollinear"]:
        lines.append("LNONCOLLINEAR = .TRUE.")
    if p["lsorbit"]:
        lines.append("LSORBIT = .TRUE.")
    if p["saxis"]:
        lines.append(f"SAXIS = {p['saxis']}")

    # ── DFT+U ───────────────────────────────────────────────────────
    if p["ldau"]:
        lines.append("LDAU = .TRUE.")
        lines.append(f"LDAUTYPE = {p['ldautype']}")
        if p["ldaul"]:
            lines.append(f"LDAUL = {p['ldaul']}")
        if p["ldauu"]:
            lines.append(f"LDAUU = {p['ldauu']}")
        if p["ldauj"]:
            lines.append(f"LDAUJ = {p['ldauj']}")
        if p["ldauprint"]:
            lines.append("LDAUPRINT = .TRUE.")

    # ── Hybrid / GW / BSE ───────────────────────────────────────────
    if p["lhfcalc"]:
        lines.append("LHFCALC = .TRUE.")
        lines.append(f"AEXX = {p['aexx']}")
        lines.append(f"HFSCREEN = {p['hfscreen']}")
        lines.append(f"PRECFOCK = {p['precfock']}")
    if p["encutgw"] > 0:
        lines.append(f"ENCUTGW = {p['encutgw']}")
    if p["nomega"] > 0:
        lines.append(f"NOMEGA = {p['nomega']}")
    if p["nmaxfockae"] > 0:
        lines.append(f"NMAXFOCKAE = {p['nmaxfockae']}")

    # ── AIMD & Phonon ───────────────────────────────────────────────
    if p["ibrion"] == 0:
        if p["smass"] != -1:
            lines.append(f"SMASS = {p['smass']}")
        lines.append(f"TEBEG = {p['tebeg']}")
        if p["teend"] != p["tebeg"]:
            lines.append(f"TEEND = {p['teend']}")
        if p["mdalgo"] > 0:
            lines.append(f"MDALGO = {p['mdalgo']}")
        if p["langevin_gamma"]:
            lines.append(f"LANGEVIN_GAMMA = {p['langevin_gamma']}")
        if p["langevin_gamma_l"] != 1.0:
            lines.append(f"LANGEVIN_GAMMA_L = {p['langevin_gamma_l']}")
    if p["ibrion"] in [5, 6]:
        if p["nfree"] != 2:
            lines.append(f"NFREE = {p['nfree']}")
    if p["pstress"] != 0.0:
        lines.append(f"PSTRESS = {p['pstress']}")
    if p["pmass"] != 10.0:
        lines.append(f"PMASS = {p['pmass']}")

    # ── Parallelisation & other ─────────────────────────────────────
    if p["npar"] > 1:
        lines.append(f"NPAR = {p['npar']}")
    if p["kpar"] > 1:
        lines.append(f"KPAR = {p['kpar']}")
    if p["ncore"] > 1:
        lines.append(f"NCORE = {p['ncore']}")
    if p["lasph"]:
        lines.append("LASPH = .TRUE.")
    if not p["gga_compat"]:
        lines.append("GGA_COMPAT = .FALSE.")
    if p["ivdw"] > 0:
        lines.append(f"IVDW = {p['ivdw']}")
    if p["luse_vdw"]:
        lines.append("LUSE_VDW = .TRUE.")
    if p["ldipol"]:
        lines.append("LDIPOL = .TRUE.")
        lines.append(f"IDIPOL = {p['idipol']}")
        if p["dipol"]:
            lines.append(f"DIPOL = {p['dipol']}")

    return "\n".join(lines) + "\n"
