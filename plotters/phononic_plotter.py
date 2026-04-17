import os
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


def render_phononic_plotter() -> None:
    """Render the Phononic Plotter page."""
    st.markdown(COMMON_STYLES, unsafe_allow_html=True)
    st.markdown('<h1 class="main-header">📈 Phononic Plotter</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Visualize phonon band structure and density of states</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_quick, col_upload = st.columns(2)
    
    with col_quick:
        st.markdown("#### 📂 Working Directory")
        working_dir = st.text_input("Working Directory", value=st.session_state.get("current_folder", ""), key="working_dir_phonon")
        
        if working_dir and os.path.isdir(working_dir):
            try:
                files = os.listdir(working_dir)
                phonon_files = [f for f in files if "vasprun" in f.lower() and "xml" in f.lower()]
                
                if phonon_files:
                    selected_file = st.selectbox("Select vasprun.xml", phonon_files, key="quick_phonon")
                    if selected_file:
                        file_path = os.path.join(working_dir, selected_file)
                        try:
                            with open(file_path, 'r') as f:
                                vasprun_content = f.read()
                            _process_phonon_file(vasprun_content)
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
                else:
                    st.info("No vasprun.xml found in current folder")
            except Exception as e:
                st.error(f"Error accessing folder: {str(e)}")
        else:
            st.info("Go to 'My Projects' to select a folder")
    
    with col_upload:
        st.markdown("#### 📤 Upload File")
        uploaded_file = st.file_uploader(
            "Upload vasprun.xml (from phonon calculation)",
            type=["xml"],
            accept_multiple_files=False,
            help="Upload vasprun.xml from DFPT phonon calculation"
        )
        
        if uploaded_file:
            try:
                vasprun_content = uploaded_file.getvalue().decode("utf-8")
                _process_phonon_file(vasprun_content)
            except Exception as e:
                st.error(f"Error reading uploaded file: {str(e)}")


def _process_phonon_file(vasprun_content: str) -> None:
    """Process vasprun.xml and display phonon plots."""
    st.markdown("---")
    
    plot_type = st.radio(
        "Select plot type:",
        ["Phonon Dispersion", "Phonon DOS"],
        horizontal=True
    )
    
    if plot_type == "Phonon Dispersion":
        _plot_phonon_dispersion(vasprun_content)
    else:
        _plot_phonon_dos(vasprun_content)


def _plot_phonon_dispersion(vasprun_content: str) -> None:
    """Plot phonon dispersion from vasprun.xml."""
    st.markdown("#### Phonon Dispersion")
    
    try:
        st.info("Phonon dispersion plotting from vasprun.xml requires XML parsing.")
        
        preview_size = min(3000, len(vasprun_content))
        preview_text = vasprun_content[:preview_size]
        
        st.text_area("vasprun.xml Preview", preview_text + "\n...[truncated]...", height=300)
        
        st.warning("""
        **How to plot phonon dispersion:**
        
        1. Phonon dispersion data is stored in the `<eigenvalues>` section of vasprun.xml
        2. Each k-point has 3N phonon frequencies (where N = number of atoms)
        3. For dispersion plotting, you need k-point path information
        
        **Current limitation:** This viewer can parse basic structure but needs 
        additional setup for full dispersion plotting with proper k-path labels.
        
        **Suggestions:**
        - Use Phonopy for phonon calculations and visualization
        - Export band structure data separately
        - Provide pre-processed phonon data files
        """)
        
        st.markdown("---")
        st.markdown("#### Manual Data Input")
        
        col_data1, col_data2 = st.columns(2)
        with col_data1:
            uploaded_freq = st.file_uploader("Upload frequency data (optional)", type=["txt", "csv"])
        with col_data2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("Supported format: Two-column (k-point, frequency)")
        
        if uploaded_freq:
            try:
                freq_content = uploaded_freq.getvalue().decode("utf-8")
                _plot_manual_phonon_dispersion(freq_content)
            except Exception as e:
                st.error(f"Error reading frequency file: {str(e)}")
        
    except Exception as e:
        st.error(f"Error processing vasprun.xml: {str(e)}")


def _plot_phonon_dos(vasprun_content: str) -> None:
    """Plot phonon DOS from vasprun.xml."""
    st.markdown("#### Phonon Density of States")
    
    try:
        st.info("Phonon DOS plotting from vasprun.xml requires XML parsing.")
        
        preview_size = min(3000, len(vasprun_content))
        preview_text = vasprun_content[:preview_size]
        
        st.text_area("vasprun.xml Preview", preview_text + "\n...[truncated]...", height=300)
        
        st.warning("""
        **How to plot phonon DOS:**
        
        1. Phonon DOS requires calculating total and partial phonon densities
        2. Data is typically in the `<phonon>` or `<dos>` section of vasprun.xml
        3. Each atom contributes to partial DOS
        
        **Current limitation:** This viewer can display XML structure but needs 
        additional parsing for complete DOS plotting.
        
        **Suggestions:**
        - Use Phonopy to generate complete phonon DOS
        - Export phonon DOS data from external tools
        - Provide pre-processed phonon DOS files
        """)
        
        st.markdown("---")
        st.markdown("#### Manual Data Input")
        
        col_data1, col_data2 = st.columns(2)
        with col_data1:
            uploaded_dos = st.file_uploader("Upload phonon DOS data (optional)", type=["txt", "csv"])
        with col_data2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("Supported format: Two-column (frequency, DOS)")
        
        if uploaded_dos:
            try:
                dos_content = uploaded_dos.getvalue().decode("utf-8")
                _plot_manual_phonon_dos(dos_content)
            except Exception as e:
                st.error(f"Error reading DOS file: {str(e)}")
        
    except Exception as e:
        st.error(f"Error processing vasprun.xml: {str(e)}")


def _plot_manual_phonon_dispersion(freq_content: str) -> None:
    """Plot phonon dispersion from manually uploaded data."""
    try:
        lines = freq_content.strip().split("\n")
        
        data = []
        for line in lines:
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    try:
                        kpt = float(parts[0].strip())
                        freq = float(parts[1].strip())
                        data.append((kpt, freq))
                    except:
                        continue
        
        if not data:
            st.error("Could not parse frequency data")
            return
        
        kpoints = sorted(set([d[0] for d in data]))
        frequencies = sorted(set([d[1] for d in data]))
        
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            fmin = st.number_input("Minimum frequency (THz)", value=min(frequencies), step=0.1)
        with col_ctrl2:
            fmax = st.number_input("Maximum frequency (THz)", value=max(frequencies), step=0.1)
        
        fig = go.Figure()
        
        unique_bands = sorted(set([d[1] for d in data]))
        
        for band in unique_bands:
            band_data = [(d[0], d[1]) for d in data if d[1] == band]
            band_data.sort(key=lambda x: x[0])
            
            fig.add_trace(go.Scatter(
                x=[d[0] for d in band_data],
                y=[d[1] for d in band_data],
                mode='lines',
                name=f'Band {unique_bands.index(band)+1}',
                showlegend=False
            ))
        
        fig.update_layout(
            title="Phonon Dispersion",
            xaxis_title="K-point index",
            yaxis_title="Frequency (THz)",
            yaxis=dict(range=[fmin, fmax]),
            template="plotly_white",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error plotting phonon dispersion: {str(e)}")


def _plot_manual_phonon_dos(dos_content: str) -> None:
    """Plot phonon DOS from manually uploaded data."""
    try:
        lines = dos_content.strip().split("\n")
        
        frequencies = []
        dos_values = []
        
        for line in lines:
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    try:
                        freq = float(parts[0].strip())
                        dos = float(parts[1].strip())
                        frequencies.append(freq)
                        dos_values.append(dos)
                    except:
                        continue
        
        if not frequencies:
            st.error("Could not parse DOS data")
            return
        
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            fmin = st.number_input("Minimum frequency (THz)", value=min(frequencies), step=0.1)
        with col_ctrl2:
            fmax = st.number_input("Maximum frequency (THz)", value=max(frequencies), step=0.1)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dos_values,
            y=frequencies,
            mode='lines',
            fill='tozeroy',
            name='Phonon DOS',
            line=dict(color='green', width=2)
        ))
        
        fig.update_layout(
            title="Phonon Density of States",
            xaxis_title="DOS (states/THz)",
            yaxis_title="Frequency (THz)",
            yaxis=dict(range=[fmin, fmax]),
            template="plotly_white",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error plotting phonon DOS: {str(e)}")
