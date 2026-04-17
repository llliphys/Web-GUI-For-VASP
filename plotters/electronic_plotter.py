import os
import io
import tempfile
import streamlit as st
import plotly.graph_objects as go
import numpy as np


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


def render_electronic_plotter() -> None:
    st.markdown(COMMON_STYLES, unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">📊 Electronic Plotter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Visualize electronic properties (band structure, DOS, PDOS) from vasprun.xml</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    pymatgen_available = _check_pymatgen()
    if not pymatgen_available:
        st.error("pymatgen is not installed. Please install it with: pip install pymatgen")
        return
    
    col_quick, col_upload = st.columns(2)
    
    vasprun_data = None
    kpoints_file = None


    # ----------------------------
    # Left column: load from folder
    # ----------------------------
    with col_quick:
        st.markdown("#### 📂 Working Directory")
        working_dir = st.text_input(
            "Working Directory",
            value=st.session_state.get("current_folder", ""),
            key="working_dir_electronic"
        )

        if working_dir and os.path.isdir(working_dir):
            try:
                files = os.listdir(working_dir)

                vasprun_files = [f for f in files if f.lower() == "vasprun.xml"]
                kpoints_files = [f for f in files if f.lower() == "kpoints"]

                if vasprun_files:
                    selected_vasprun = st.selectbox(
                        "Select vasprun.xml",
                        vasprun_files,
                        key="quick_vasprun_select"
                    )
                    if selected_vasprun:
                        vasprun_path = os.path.join(working_dir, selected_vasprun)
                        try:
                            vasprun_data = _load_vasprun_from_file(vasprun_path)
                            st.success(f"Loaded vasprun.xml: {selected_vasprun}")
                        except Exception as e:
                            st.error(f"Error reading vasprun.xml: {e}")
                else:
                    # st.info("No vasprun.xml found in the selected folder.")
                    pass

                select_kpoints = st.checkbox(
                    "Select KPOINTS file (optional)",
                    value=False,
                    key="select_kpoints_file"
                )

                if select_kpoints:
                    if kpoints_files:
                        selected_kpoints = st.selectbox(
                            "Select KPOINTS",
                            kpoints_files,
                            key="quick_kpoints_select"
                        )
                        if selected_kpoints:
                            kpoints_path = os.path.join(working_dir, selected_kpoints)
                            try:
                                kpoints_file = _load_kpoints_from_file(kpoints_path)
                                st.success(f"Loaded KPOINTS: {selected_kpoints}")
                            except Exception as e:
                                st.error(f"Error reading KPOINTS: {e}")
                    else:
                        # st.info("No KPOINTS file found in the selected folder.")
                        pass
            except Exception as e:
                st.error(f"Error accessing folder: {e}")
        else:
            st.info("Go to 'My Projects' to select a folder.")

    # ----------------------------
    # Right column: upload files
    # ----------------------------
    with col_upload:
        st.markdown("#### 📤 Upload File")

        uploaded_vasprun = st.file_uploader(
            "Upload vasprun.xml",
            type=["xml"],
            accept_multiple_files=False,
            help="Upload a vasprun.xml file from a VASP calculation",
            key="upload_vasprun_file"
        )

        if uploaded_vasprun is not None:
            try:
                vasprun_data = _load_vasprun_from_content(uploaded_vasprun.getvalue())
                st.success(f"Uploaded vasprun.xml: {uploaded_vasprun.name}")
            except Exception as e:
                st.error(f"Error reading uploaded vasprun.xml: {e}")

        upload_kpoints = st.checkbox(
            "Upload KPOINTS file (optional)",
            value=False,
            key="upload_kpoints_checkbox"
        )

        if upload_kpoints:
            uploaded_kpoints = st.file_uploader(
                "Upload KPOINTS",
                accept_multiple_files=False,
                help="Upload a KPOINTS file from a VASP calculation",
                key="upload_kpoints_file"
            )

            if uploaded_kpoints is not None:
                try:
                    kpoints_file = _load_kpoints_from_content(uploaded_kpoints.getvalue())
                    st.success(f"Uploaded KPOINTS: {uploaded_kpoints.name}")
                except Exception as e:
                    st.error(f"Error reading uploaded KPOINTS: {e}")

    # ----------------------------
    # Validate inputs
    # ----------------------------
    if vasprun_data is None:
        st.info("Please select or upload a vasprun.xml file.")
        return

    st.markdown("---")

    plot_type = st.radio(
        "Select Plot Type",
        ["Band Structure", "Total DOS", "Projected DOS", "Projected Band Structure"],
        horizontal=True,
        key="electronic_plot_type"
    )

    st.markdown("---")

    if plot_type == "Band Structure":
        _render_band_structure(vasprun_data, kpoints_file)
    elif plot_type == "Total DOS":
        _render_dos(vasprun_data)
    elif plot_type == "Projected DOS":
        _render_pdos(vasprun_data)
    elif plot_type == "Projected Band Structure":
        _render_projected_band_structure(vasprun_data, kpoints_file)


def _check_pymatgen() -> bool:
    try:
        import pymatgen  # noqa: F401
        return True
    except ImportError:
        return False


def _load_vasprun_from_file(file_path: str):
    from pymatgen.io.vasp import Vasprun
    return Vasprun(file_path, parse_projected_eigen=True)


def _load_kpoints_from_file(file_path: str) -> str:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"KPOINTS file not found: {file_path}")
    return file_path


def _load_vasprun_from_content(content: bytes):
    from pymatgen.io.vasp import Vasprun

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        vasprun = Vasprun(tmp_path, parse_projected_eigen=True)
        return vasprun
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _load_kpoints_from_content(content: bytes) -> str:
    """
    Save uploaded KPOINTS content into a persistent temp file and return its path.
    Do not delete it immediately, because downstream plotting code still needs it.
    """
    with tempfile.NamedTemporaryFile(mode="wb", suffix="_KPOINTS", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    return tmp_path
    

# def _check_pymatgen() -> bool:
#     try:
#         import pymatgen
#         return True
#     except ImportError:
#         return False

# def _load_vasprun_from_file(file_path: str):
#     from pymatgen.io.vasp import Vasprun
#     return Vasprun(file_path, parse_projected_eigen=True)

# def _load_kpoints_from_file(file_path: str) -> str:
#     if not os.path.isfile(file_path):
#         raise FileNotFoundError(f"KPOINTS file not found: {file_path}")
#     return file_path

# def _load_vasprun_from_content(content: bytes):
#     from pymatgen.io.vasp import Vasprun
#     with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as tmp:
#         tmp.write(content)
#         tmp_path = tmp.name
#     try:
#         vasprun = Vasprun(tmp_path, parse_projected_eigen=True)
#         return vasprun
#     finally:
#         try:
#             os.unlink(tmp_path)
#         except:
#             pass

# def _load_kpoints_from_content(content: bytes):
#     with tempfile.NamedTemporaryFile(mode='wb', suffix='', delete=False) as tmp:
#         tmp.write(content)
#         tmp_path = tmp.name
#     try:
#         kpoints_file = tmp_path
#         return kpoints_file
#     finally:
#         try:
#             os.unlink(tmp_path)
#         except:
#             pass


def _render_dos(vasprun) -> None: #, emin: float, emax: float, shift_fermi: bool, backend: str) -> None:
    from pymatgen.electronic_structure.core import Spin

    st.markdown("### Total Density of States")
    
    try:
        dos = vasprun.tdos
        if dos is None:
            st.error("No DOS data found in vasprun.xml")
            return 
        
        efermi = dos.efermi
        # is_spin = vasprun.is_spin
        is_spin_polarized = Spin.down in dos.densities


        col_left, col_right = st.columns(2)
        
        with col_right:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"Fermi energy: {efermi:.4f} eV | Spin polarized: {is_spin_polarized}")
            emin = st.number_input("Minimum Energy (eV)", value=-5.0, step=0.5, key="electronic_emin")
            emax = st.number_input("Maximum Energy (eV)", value=5.0, step=0.5, key="electronic_emax")
            shift_fermi = st.checkbox("Shift Fermi level to 0", value=True, key="electronic_shift_fermi")
            backend = st.selectbox("Plot Backend", ["Matplotlib (static)", "Plotly (interactive)"], key="electronic_backend")

        with col_left:
            if backend == "Matplotlib (static)":
                _plot_dos_matplotlib(dos, emin, emax, shift_fermi)
            else:
                _plot_dos_plotly(dos, emin, emax, shift_fermi)
            
    except Exception as e:
        st.error(f"Error rendering DOS: {str(e)}")


def _plot_dos_matplotlib(dos, emin: float, emax: float, shift_fermi: bool) -> None:
    import matplotlib.pyplot as plt
    from pymatgen.electronic_structure.core import Spin

    import matplotlib
    matplotlib.rcParams['font.size'] = 12
    matplotlib.rcParams['axes.labelsize'] = 12
    matplotlib.rcParams['axes.titlesize'] = 12
    matplotlib.rcParams['xtick.labelsize'] = 12
    matplotlib.rcParams['ytick.labelsize'] = 12
    matplotlib.rcParams['legend.fontsize'] = 12
    matplotlib.rcParams['axes.linewidth'] = 1
    matplotlib.rcParams['xtick.major.width'] = 1
    matplotlib.rcParams['ytick.major.width'] = 1
    matplotlib.rcParams['xtick.major.size'] = 4
    matplotlib.rcParams['ytick.major.size'] = 4
    
    try:
        efermi = dos.efermi
        energies = dos.energies
        densities = dos.densities
        
        is_spin_polarized = Spin.down in densities
        
        if shift_fermi:
            energy_plot = energies - efermi
            fermi_x = 0
        else:
            energy_plot = energies
            fermi_x = efermi
        
        fig, ax = plt.subplots()
        
        all_dos = []
        if is_spin_polarized:
            spin_colors = {Spin.up: 'blue', Spin.down: 'red'}
            spin_labels = {Spin.up: 'Spin Up', Spin.down: 'Spin Dn'}
            for spin, dos_vals in densities.items():
                all_dos.append(dos_vals)
                ax.plot(energy_plot, dos_vals, color=spin_colors.get(spin, 'blue'), 
                       linewidth=1, label=spin_labels.get(spin, spin))
            dos_values = np.concatenate(all_dos) if all_dos else np.array([0.0])
        else:
            if isinstance(densities, dict):
                dos_values = list(densities.values())[0]
            else:
                dos_values = densities
            ax.plot(energy_plot, dos_values, color='blue', linewidth=1, label='Total DOS')

        ymin = float(np.min(dos_values))
        ymax = float(np.max(dos_values))

        ax.set_xlim(emin, emax)
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel("Energy (eV)")
        ax.set_ylabel("DOS (states/eV)")
        ax.tick_params(axis='both')
        ax.axvline(x=fermi_x, color='k', linestyle='--', linewidth=1)
        ax.grid(True, alpha=0.3)

        if is_spin_polarized: ax.legend(loc=1)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        
    except Exception as e:
        st.error(f"Error creating matplotlib plot: {str(e)}")


def _render_band_structure(vasprun, kpoints_file) -> None: #, emin: float, emax: float, shift_fermi: bool, backend: str) -> None:
    from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine

    st.markdown("### Band Structure")
    
    try:

        if kpoints_file is None:
            bs = vasprun.get_band_structure() 
        else:
            bs = vasprun.get_band_structure(kpoints_filename=kpoints_file, line_mode=True) 

        if bs is None:
            st.error("No band structure data found in vasprun.xml")
            return
        
        efermi = bs.efermi
        is_spin_polarized = bs.is_spin_polarized
        is_line_bs = isinstance(bs, BandStructureSymmLine)
        
        st.markdown("""
        **Note:** BSPlotter requires band structure along symmetry lines (line-mode k-points).
        To generate proper band structure: Use KPOINTS with line-mode (reciprocal cell) 
        or set ICHARG=11 (band structure from CHGCAR).
        """)

        col_left, col_right = st.columns(2)

        with col_right:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"Fermi energy: {efermi:.4f} eV | Spin polarized: {is_spin_polarized}")
            emin = st.number_input("Minimum Energy (eV)", value=-5.0, step=0.5, key="electronic_emin")
            emax = st.number_input("Maximum Energy (eV)", value=5.0, step=0.5, key="electronic_emax")
            shift_fermi = st.checkbox("Shift Fermi level to 0", value=True, key="electronic_shift_fermi")
            backend = st.selectbox("Plot Backend", ["Matplotlib (static)", "Plotly (interactive)"], key="electronic_backend")

        with col_left:
            if backend == "Matplotlib (static)":
                _plot_bs_matplotlib(bs, emin, emax, shift_fermi)
            else:
                _plot_bs_plotly(bs, emin, emax, shift_fermi)
            
    except Exception as e:
        st.error(f"Error rendering band structure: {str(e)}")


def _plot_bs_matplotlib(bs, emin: float, emax: float, shift_fermi: bool) -> None:
    import matplotlib.pyplot as plt
    from pymatgen.electronic_structure.core import Spin
    import matplotlib

    matplotlib.rcParams['font.size'] = 12
    matplotlib.rcParams['axes.labelsize'] = 12
    matplotlib.rcParams['axes.titlesize'] = 12
    matplotlib.rcParams['xtick.labelsize'] = 12
    matplotlib.rcParams['ytick.labelsize'] = 12
    matplotlib.rcParams['legend.fontsize'] = 12
    matplotlib.rcParams['axes.linewidth'] = 1
    matplotlib.rcParams['xtick.major.width'] = 1
    matplotlib.rcParams['ytick.major.width'] = 1
    matplotlib.rcParams['xtick.major.size'] = 4
    matplotlib.rcParams['ytick.major.size'] = 4
    
    try:
        efermi = bs.efermi
        kdist, tick_positions, tick_labels, is_line_bs = _get_k_axis_and_ticks(bs)

        fig, ax = plt.subplots() #(figsize=(6,3))
        
        if bs.is_spin_polarized:
            spin_colors = {Spin.up: 'blue', Spin.down: 'red'}
            spin_labels = {Spin.up: 'Spin Up', Spin.down: 'Spin Dn'}
            for spin, bands in bs.bands.items():
                for i in range(bands.shape[0]):
                    energies = bands[i, :]
                    if shift_fermi: 
                        energies = energies - efermi
                    ax.plot(kdist, energies, color=spin_colors.get(spin, 'blue'), linewidth=1, alpha=0.5)
                ax.plot([], [], color=spin_colors.get(spin, 'blue'), linewidth=1, alpha=0.5, label=spin_labels.get(spin, f'{spin}'))
        else:
            bands = bs.bands
            for i in range(bands.shape[0]):
                energies = bands[i, :]
                if shift_fermi: 
                    energies = energies - efermi
                ax.plot(kdist, energies, color='blue', linewidth=1, alpha=0.5)
        
        if is_line_bs and tick_positions:
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(["$\mathrm{%s}$" % tick_label for tick_label in tick_labels])
            for xpos in tick_positions:
                ax.axvline(x=xpos, color="gray", linewidth=1, alpha=0.35)

        ax.set_xlim(kdist[0], kdist[-1])
        ax.set_ylim(emin, emax)
        ax.set_xlabel("K-path" if is_line_bs else "K-point index")
        ax.set_ylabel("Energy (eV)")
        ax.grid(True, alpha=0.35)
        
        if shift_fermi:
            ax.axhline(y=0, color='k', linestyle='--', linewidth=1, alpha=0.5)
        else:
            ax.axhline(y=efermi, color='k', linestyle='--', linewidth=1, alpha=0.5)
        
        if bs.is_spin_polarized: 
            ax.legend(loc=1)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        
    except Exception as e:
        st.error(f"Error creating matplotlib plot: {str(e)}")


def _plot_dos_plotly(dos, emin: float, emax: float, shift_fermi: bool) -> None:
    from pymatgen.electronic_structure.core import Spin

    efermi = dos.efermi
    
    energies = dos.energies
    densities = dos.densities
    
    fig = go.Figure()

    is_spin_polarized = Spin.down in densities
    
    if is_spin_polarized:
        spin_colors = {1: 'blue', -1: 'red'}
        spin_names = {1: 'Spin Up', -1: 'Spin Dn'}
        for spin, dos_vals in densities.items():
            energies_plot = energies - efermi if shift_fermi else energies
            fig.add_trace(go.Scatter(
                x=energies_plot,
                y=dos_vals,
                mode='lines',
                # fill='tozeroy',
                name=spin_names.get(spin, f'Spin {spin}'),
                line=dict(color=spin_colors.get(spin, 'blue'), width=1.5)
            ))
    else:
        if isinstance(densities, dict):
            dos_values = list(densities.values())[0]
        else:
            dos_values = densities
        
        energies_plot = energies - efermi if shift_fermi else energies
        
        fig.add_trace(go.Scatter(
            x=energies_plot,
            y=dos_values,
            mode='lines',
            # fill='tozeroy',
            name='Total DOS',
            line=dict(color='blue', width=1.5)
        ))
    
    fig.update_layout(
        # title="Total Density of States",
        font=dict(size=14),
        xaxis=dict(
            title=dict(text="Energy (eV)", font=dict(size=16), standoff=15),
            tickfont=dict(size=16),
            range=[emin, emax]
        ),
        yaxis=dict(
            title=dict(text="DOS (states/eV)", font=dict(size=16), standoff=15),
            tickfont=dict(size=16)
        ),
        legend=dict(font=dict(size=14)),
        plot_bgcolor='rgba(240,240,240,1)',
        paper_bgcolor='rgba(240,240,240,1)'
    )
    
    fermi_x = 0 if shift_fermi else efermi
    fermi_label = "Fermi Level" if shift_fermi else f"E_F = {efermi:.2f} eV"
    fig.add_vline(x=fermi_x, line_dash="dash", line_color="black") #, annotation_text=fermi_label)
    
    # st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(fig, width="stretch")


def _plot_bs_plotly(bs, emin: float, emax: float, shift_fermi: bool) -> None:
    from pymatgen.electronic_structure.core import Spin

    efermi = bs.efermi
    kdist, tick_positions, tick_labels, is_line_bs = _get_k_axis_and_ticks(bs)
    
    fig = go.Figure()

    tick_config = dict(
        tickmode='array' if is_line_bs and tick_positions else 'auto',
        tickvals=tick_positions if tick_positions else None,
        ticktext=tick_labels if tick_labels else None
    )
    
    if bs.is_spin_polarized:
        spin_data = bs.bands
        spin_names = {Spin.up: 'Spin Up', Spin.down: 'Spin Dn'}
        spin_colors = {Spin.up: 'blue', Spin.down: 'red'}
        
        for spin, bands in spin_data.items():
            for i in range(bands.shape[0]):
                energies = bands[i, :]
                if shift_fermi:
                    energies = energies - efermi
                spin_label = f"({spin_names.get(spin, spin)})"
                fig.add_trace(go.Scatter(
                    x=kdist, #list(range(len(energies))),
                    y=energies,
                    mode='lines',
                    name=f'Band {i+1}{spin_label}',
                    line=dict(color=spin_colors.get(spin, 'blue'), width=1.5),
                    showlegend=False
                ))
    else:
        bands = bs.bands
        for i in range(bands.shape[0]):
            energies = bands[i, :]
            if shift_fermi:
                energies = energies - efermi
            fig.add_trace(go.Scatter(
                x=kdist, #list(range(len(energies))),
                y=energies,
                mode='lines',
                name=f'Band {i+1}',
                line=dict(color='blue', width=1.5),
                showlegend=False
            ))
    
    xaxis_label = "K-path" if is_line_bs else "K-point index"
    
    fig.update_layout(
        # title="Band Structure",
        font=dict(size=18),
        xaxis=dict(
            title=dict(text=xaxis_label, font=dict(size=18), standoff=15),
            tickfont=dict(size=16),
            **tick_config
        ),
        yaxis=dict(
            title=dict(text="Energy (eV)", font=dict(size=18), standoff=15),
            tickfont=dict(size=16),
            range=[emin, emax]
        ),
        legend=dict(font=dict(size=16)),
        plot_bgcolor='rgba(240,240,240,1)',
        paper_bgcolor='rgba(240,240,240,1)',
    )
    
    if shift_fermi:
        fig.add_hline(y=0, line_dash="dash", line_color="black", showlegend=False) #annotation_text="Fermi Level", showlegend=False)
    else:
        fig.add_hline(y=efermi, line_dash="dash", line_color="black", showlegend=False) #annotation_text=f"E_F = {efermi:.2f} eV", showlegend=False)
    
    # st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(fig, width="stretch")


def _render_pdos(vasprun) -> None: #, emin: float, emax: float, shift_fermi: bool, backend: str) -> None:
    from pymatgen.electronic_structure.core import Spin

    st.markdown("### Projected Density of States")

    try:
        structure = vasprun.final_structure
        elements = [site.specie.symbol for site in structure.sites]
        unique_elements = sorted(set(elements))

        dos = vasprun.tdos
        efermi = dos.efermi
        is_spin_polarized = Spin.down in dos.densities

        col_left, col_right = st.columns(2)
        
        with col_right:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(f"Fermi energy: {efermi:.4f} eV | Spin polarized: {is_spin_polarized}")
            selected_elements = st.multiselect(
                "Select elements",
                unique_elements,
                default=unique_elements[:1] if unique_elements else None,
                key="pdos_elements"
            )
            orbital_options = ["s", "p", "d", "f"]
            selected_orbitals = st.multiselect(
                "Select orbitals",
                orbital_options,
                default=["s"],
                key="pdos_orbitals"
            )
            emin = st.number_input("Minimum Energy (eV)", value=-5.0, step=0.5, key="electronic_emin")
            emax = st.number_input("Maximum Energy (eV)", value=5.0, step=0.5, key="electronic_emax")
            shift_fermi = st.checkbox("Shift Fermi level to 0", value=True, key="electronic_shift_fermi")
            backend = st.selectbox("Plot Backend", ["Matplotlib (static)", "Plotly (interactive)"], key="electronic_backend")

        with col_left:
            if backend == "Matplotlib (static)":
                _plot_pdos_matplotlib(vasprun, selected_elements, selected_orbitals, emin, emax, shift_fermi)
            else:
                _plot_pdos_plotly(vasprun, selected_elements, selected_orbitals, emin, emax, shift_fermi)
            
    except Exception as e:
        st.error(f"Error rendering PDOS: {str(e)}")


def _plot_pdos_matplotlib(vasprun, elements: list, orbitals: list,
                          emin: float, emax: float, shift_fermi: bool) -> None:

    import numpy as np
    import matplotlib.pyplot as plt
    from pymatgen.electronic_structure.core import Spin, Orbital

    try:
        structure = vasprun.final_structure
        pdos_data = vasprun.pdos
        energies = vasprun.tdos.energies
        efermi = vasprun.efermi

        if pdos_data is None:
            st.error("No projected DOS data found. Ensure LORBIT = 11 is set in INCAR.")
            return

        # --- Spin detection ---
        is_spin_polarized = Spin.down in vasprun.tdos.densities

        # --- Energy alignment ---
        if shift_fermi:
            energy_plot = energies - efermi
            fermi_x = 0.0
        else:
            energy_plot = energies
            fermi_x = efermi

        # --- Map elements to site indices ---
        element_indices = {}
        for idx, site in enumerate(structure.sites):
            elem = site.specie.symbol
            if elem not in element_indices:
                element_indices[elem] = []
            element_indices[elem].append(idx)

        # st.write("Element statistics:")
        # for element, indices in element_indices.items():
        #     print(f"{element}: {len(indices)} atoms at indices {indices}")

        # --- Plot setup ---
        fig, ax = plt.subplots()

        color_list = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
            '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
        ]
        colors = color_list * 10

        color_count = -1
        # --- Main PDOS loop ---
        for i, element in enumerate(elements):

            if element not in element_indices:
                continue

            indices = element_indices[element]

            for orbital in orbitals:

                color_count += 1

                # Initialize accumulator
                if is_spin_polarized:
                    combined = {
                        Spin.up: np.zeros_like(energies),
                        Spin.down: np.zeros_like(energies),
                    }
                else:
                    combined = np.zeros_like(energies)

                for idx in indices:

                    site_pdos = pdos_data[idx]

                    print(site_pdos[Orbital.dxy])

                    if orbital.lower() == "s":
                        orbs = [Orbital.s]
                    if orbital.lower() == "p":
                        orbs = [Orbital.px, Orbital.py, Orbital.pz]
                    if orbital.lower() == "d":
                        orbs = [Orbital.dxy, Orbital.dxz, Orbital.dyz, Orbital.dx2, Orbital.dz2]

                    if is_spin_polarized:
                        for spin in [Spin.up, Spin.down]:
                            for orb in orbs:
                                orb_dos = site_pdos[orb]
                                combined[spin] += np.array(orb_dos[spin])
                    else:
                        for orb in orbs:
                            orb_dos = site_pdos[orb]
                            combined += np.array(orb_dos[Spin.up])

                # --- Plot ---
                if is_spin_polarized:
                    ax.plot(
                        energy_plot,
                        combined[Spin.up],
                        color=colors[color_count],
                        label=f"{element}: {orbital} (Spin Up)"
                    )
                    ax.plot(
                        energy_plot,
                        -combined[Spin.down],  # flipped for symmetry
                        color=colors[color_count],
                        linestyle="--",
                        label=f"{element}: {orbital} (Spin Dn)"
                    )
                else:
                    ax.plot(
                        energy_plot,
                        combined,
                        color=colors[color_count],
                        label=f"{element}: {orbital}"
                    )

        # --- Styling ---
        ax.set_xlim(emin, emax)
        ax.set_xlabel("Energy (eV)")
        ax.set_ylabel("DOS (states/eV)")
        ax.axvline(x=fermi_x, linestyle="--", color="k", alpha=0.5)
        ax.legend(loc=1)
        ax.grid(alpha=0.3)

        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    except Exception as e:
        st.error(f"Error creating matplotlib PDOS plot: {str(e)}")


def _plot_pdos_plotly(vasprun, elements: list, orbitals: list, emin: float, emax: float, shift_fermi: bool) -> None:
    pass


def _render_projected_band_structure(
    vasprun,
) -> None:
    st.markdown("### Projected Band Structure")

    try:
        bs = vasprun.get_band_structure()
        efermi = bs.efermi
        structure = vasprun.final_structure

        if not hasattr(bs, "projections"):
            st.error(
                "No projected band-structure data found. "
                "Please parse vasprun.xml with parse_projected_eigen=True "
                "and ensure LORBIT = 11 in INCAR."
            )
            return

        unique_elements = sorted({site.specie.symbol for site in structure.sites})

        col_left, col_right = st.columns(2)

        with col_right:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info(
                f"Fermi energy: {efermi:.4f} eV | "
                f"Spin polarized: {bs.is_spin_polarized}"
            )

            selected_elements = st.multiselect(
                "Select elements",
                unique_elements,
                default=unique_elements[:1] if unique_elements else [],
                key="pbs_elements",
            )

            orbital_options = ["s", "p", "d", "f"]
            selected_orbitals = st.multiselect(
                "Select orbitals",
                orbital_options,
                default=["d"] if "d" in orbital_options else ["s"],
                key="pbs_orbitals",
            )

            emin = st.number_input("Minimum Energy (eV)", value=-5.0, step=0.5, key="electronic_emin")
            emax = st.number_input("Maximum Energy (eV)", value=5.0, step=0.5, key="electronic_emax")
            shift_fermi = st.checkbox("Shift Fermi level to 0", value=True, key="electronic_shift_fermi")
            backend = st.selectbox("Plot Backend", ["Matplotlib (static)", "Plotly (interactive)"], key="plot_backend")

        if not selected_elements:
            st.warning("Please select at least one element.")
            return
        if not selected_orbitals:
            st.warning("Please select at least one orbital.")
            return

        with col_left:
            if backend == "Matplotlib (static)":
                _plot_pbs_matplotlib(
                    bs=bs,
                    elements=selected_elements,
                    orbitals=selected_orbitals,
                    emin=emin,
                    emax=emax,
                    shift_fermi=shift_fermi,
                )
            else:
                _plot_pbs_plotly(
                    bs=bs,
                    elements=selected_elements,
                    orbitals=selected_orbitals,
                    emin=emin,
                    emax=emax,
                    shift_fermi=shift_fermi,
                )

    except Exception as e:
        st.error(f"Error rendering projected band structure: {str(e)}")


def _build_projection_request(elements: list[str], orbitals: list[str]) -> dict:
    """
    Build the input dictionary required by:
    bs.get_projections_on_elements_and_orbitals(...)
    Example:
        {"Mo": ["d"], "S": ["p"]}
    """
    return {elem: orbitals[:] for elem in elements}


def _get_k_axis_and_ticks(bs):
    """
    Return:
        x: k-point axis
        tick_positions: high-symmetry positions
        tick_labels: high-symmetry labels
        is_line_bs: whether the band structure is along a symmetry line
    """
    import numpy as np
    from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine

    is_line_bs = isinstance(bs, BandStructureSymmLine)

    if is_line_bs and hasattr(bs, "distance"):
        kdist = np.array(bs.distance)
    else:
        nk = bs.bands[list(bs.bands.keys())[0]].shape[1]
        kdist = np.arange(nk, dtype=float)

    tick_positions = []
    tick_labels = []

    if is_line_bs:
        raw_labels = []
        for kp in bs.kpoints:
            lbl = getattr(kp, "label", None)

            if lbl is None or str(lbl).strip() == "":
                raw_labels.append("")
                continue

            lbl = str(lbl).strip().strip("$")

            if lbl.upper() in ["\\GAMMA", "GAMMA", "\\G", "\G", "G"]: # ["\\Gamma", "Gamma", "GAMMA", "gamma", "γ", "Γ"]:
                lbl = r"\Gamma"

            raw_labels.append(f"{lbl}")

        last_label = None
        for i, lbl in enumerate(raw_labels):
            if lbl != "" and lbl != last_label:
                tick_positions.append(kdist[i])
                tick_labels.append(lbl)
                last_label = lbl

    return kdist, tick_positions, tick_labels, is_line_bs

def _normalize_marker_sizes(weights, min_size=5.0, max_size=50.0):
    weights = np.asarray(weights, dtype=float)
    wmax = np.max(weights) if weights.size else 0.0

    if wmax <= 1e-12:
        return np.full_like(weights, min_size, dtype=float)

    scaled = weights / wmax
    return min_size + (max_size - min_size) * scaled


def _projection_series_for_combo(proj_data, spin, iband, element, orbital, nkpoints):
    """
    Extract projection weights for one (element, orbital) combination along k-path.
    """
    weights = np.zeros(nkpoints, dtype=float)

    for ik in range(nkpoints):
        val = 0.0
        try:
            val = proj_data[spin][iband][ik][element][orbital]
        except Exception:
            val = 0.0
        weights[ik] = float(val)

    return weights


def _plot_pbs_matplotlib(
    bs,
    elements: list,
    orbitals: list,
    emin: float,
    emax: float,
    shift_fermi: bool,
) -> None:
    import matplotlib.pyplot as plt
    from pymatgen.electronic_structure.core import Spin


    try:
        projection_request = _build_projection_request(elements, orbitals)
        proj_data = bs.get_projections_on_elements_and_orbitals(projection_request)

        x, tick_positions, tick_labels, is_line_bs = _get_k_axis_and_ticks(bs)
        efermi = bs.efermi

        combo_colors = {
            ("s"): "#1f77b4",
            ("p"): "#ff7f0e",
            ("d"): "#2ca02c",
            ("f"): "#d62728",
        }
        spin_line_colors = {
            Spin.up: "blue",
            Spin.down: "red",
        }

        fig, ax = plt.subplots(figsize=(8, 6))

        # draw thin band lines first
        for spin, bands in bs.bands.items():
            line_color = spin_line_colors.get(spin, "black")
            for iband in range(bands.shape[0]):
                energies = bands[iband, :]
                if shift_fermi:
                    energies = energies - efermi

                ax.plot(
                    x,
                    energies,
                    color=line_color,
                    linewidth=1,
                    alpha=0.35,
                    zorder=1,
                )

        # overlay fat-band markers for each element-orbital combination
        legend_added = set()

        for spin, bands in bs.bands.items():
            for elem in elements:
                for orb in orbitals:
                    marker_color = combo_colors.get(orb, "black")

                    for iband in range(bands.shape[0]):
                        energies = bands[iband, :]
                        if shift_fermi:
                            energies = energies - efermi

                        weights = _projection_series_for_combo(
                            proj_data=proj_data,
                            spin=spin,
                            iband=iband,
                            element=elem,
                            orbital=orb,
                            nkpoints=len(x),
                        )

                        sizes = _normalize_marker_sizes(
                            weights,
                            min_size=1,
                            max_size=100,
                        )

                        label = f"{elem}-{orb}"
                        show_label = label not in legend_added
                        if show_label:
                            legend_added.add(label)

                        ax.scatter(
                            x,
                            energies,
                            s=sizes,
                            c=marker_color,
                            alpha=0.55,
                            edgecolors="none",
                            label=label if show_label else None,
                            zorder=2,
                        )

        if is_line_bs and tick_positions:
            ax.set_xticks(tick_positions)
            ax.set_xticklabels(tick_labels)
            for xpos in tick_positions:
                ax.axvline(x=xpos, color="gray", linewidth=1, alpha=0.35)

        ax.set_xlim(x[0], x[-1])
        ax.set_ylim(emin, emax)
        ax.set_xlabel("K-path" if is_line_bs else "K-point index")
        ax.set_ylabel("Energy (eV)")
        ax.grid(True, alpha=0.35)

        if shift_fermi:
            ax.axhline(0.0, color="black", linestyle="--", linewidth=1.0, alpha=0.8)
        else:
            ax.axhline(efermi, color="black", linestyle="--", linewidth=1.0, alpha=0.8)

        ax.legend(fontsize=9, frameon=True)
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

    except Exception as e:
        st.error(f"Error creating matplotlib projected band structure plot: {str(e)}")


def _plot_pbs_plotly(
    bs,
    elements: list,
    orbitals: list,
    emin: float,
    emax: float,
    shift_fermi: bool,
) -> None:
    from pymatgen.electronic_structure.core import Spin

    try:
        projection_request = _build_projection_request(elements, orbitals)
        proj_data = bs.get_projections_on_elements_and_orbitals(projection_request)

        x, tick_positions, tick_labels, is_line_bs = _get_k_axis_and_ticks(bs)
        efermi = bs.efermi

        combo_colors = {
            "s": "#1f77b4",
            "p": "#ff7f0e",
            "d": "#2ca02c",
            "f": "#d62728",
        }
        spin_names = {
            Spin.up: "Spin Up",
            Spin.down: "Spin Down",
        }
        spin_line_colors = {
            Spin.up: "blue",
            Spin.down: "red",
        }

        fig = go.Figure()

        # thin band lines
        for spin, bands in bs.bands.items():
            line_color = spin_line_colors.get(spin, "black")
            for iband in range(bands.shape[0]):
                energies = bands[iband, :]
                if shift_fermi:
                    energies = energies - efermi

                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=energies,
                        mode="lines",
                        line=dict(color=line_color, width=1),
                        opacity=0.30,
                        name=spin_names.get(spin, str(spin)),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

        # fat-band markers
        legend_added = set()

        for spin, bands in bs.bands.items():
            for elem in elements:
                for orb in orbitals:
                    label = f"{elem}-{orb}"
                    marker_color = combo_colors.get(orb, "black")

                    show_legend = label not in legend_added
                    if show_legend:
                        legend_added.add(label)

                    for iband in range(bands.shape[0]):
                        energies = bands[iband, :]
                        if shift_fermi:
                            energies = energies - efermi

                        weights = _projection_series_for_combo(
                            proj_data=proj_data,
                            spin=spin,
                            iband=iband,
                            element=elem,
                            orbital=orb,
                            nkpoints=len(x),
                        )

                        sizes = _normalize_marker_sizes(
                            weights,
                            min_size=1,
                            max_size=10,
                        )

                        hover_text = [
                            (
                                f"{label}<br>"
                                f"{spin_names.get(spin, str(spin))}<br>"
                                f"k index: {ik}<br>"
                                f"Energy: {energies[ik]:.3f} eV<br>"
                                f"Weight: {weights[ik]:.4f}"
                            )
                            for ik in range(len(x))
                        ]

                        fig.add_trace(
                            go.Scatter(
                                x=x,
                                y=energies,
                                mode="markers",
                                marker=dict(
                                    size=sizes,
                                    color=marker_color,
                                    opacity=0.60,
                                    line=dict(width=0),
                                ),
                                name=label,
                                legendgroup=label,
                                showlegend=show_legend and iband == 0,
                                text=hover_text,
                                hoverinfo="text",
                            )
                        )

        if shift_fermi:
            fermi_y = 0.0
            # fermi_label = "E_F = 0 eV"
        else:
            fermi_y = efermi
            # fermi_label = f"E_F = {efermi:.3f} eV"

        fig.add_hline(
            y=fermi_y,
            line_dash="dash",
            line_color="black",
            # annotation_text=fermi_label,
        )

        xaxis = dict(
            title="K-path" if is_line_bs else "K-point index",
            tickmode="array" if tick_positions else "auto",
            tickvals=tick_positions if tick_positions else None,
            ticktext=tick_labels if tick_labels else None,
            tickfont=dict(size=14),
            title_font=dict(size=16),
        )

        yaxis = dict(
            title="Energy (eV)",
            range=[emin, emax],
            tickfont=dict(size=14),
            title_font=dict(size=16),
        )

        fig.update_layout(
            # title="Element- and Orbital-Resolved Band Structure",
            xaxis=xaxis,
            yaxis=yaxis,
            width=900,
            height=650,
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(font=dict(size=12)),
            margin=dict(l=60, r=30, t=60, b=60),
        )

        if tick_positions:
            for xpos in tick_positions:
                fig.add_vline(
                    x=xpos,
                    line_width=0.5,
                    line_color="gray",
                    opacity=0.25,
                )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating Plotly projected band structure plot: {str(e)}")