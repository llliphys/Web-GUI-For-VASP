# WGUI4VASP

A web-based GUI (WGUI) tool for VASP (Vienna Ab initio Simulation Package) simulation workflows, built using Python framework Streamlit.

## Overview

WGUI4VASP provides an end-to-end graphical interface for density-functional theory (DFT) simulation workflows using VASP. It runs in your web browser and covers the full simulation pipeline: generating input files, managing project directories, executing simulations locally or on remote HPC clusters, and visualizing output data including crystal structures, electronic band structures, density of states, and phonon properties.

## Features

### Input File Generation

- **INCAR** — 15 preset templates across 7 categories (Standard DFT, Phonon, Magnetic, DFT+U, Hybrid Functional, GW/BSE, AIMD) plus a full custom builder with 60+ configurable parameters organized into 10 tabs
- **POSCAR** — 6 methods for crystal structure generation:
  - Upload existing POSCAR/CONTCAR files
  - ASE preset materials (elements, binary compounds, common structures)
  - Materials Project database search (by formula or Material ID)
  - Custom builder with manual lattice vectors and atomic coordinates
- **POTCAR** — Element selection from the full periodic table with automatic concatenation from a local pseudopotential library (PBE/LDA/GGA)
- **KPOINTS** — Monkhorst-Pack or Gamma-centered k-mesh generation and line-mode band structure paths with labeled high-symmetry points

### Project Management

- File-system browser for organizing VASP calculation directories
- Create, navigate, and manage project folders
- In-app text file preview for all VASP input/output files

### Simulation Execution

- **Local execution** — Run VASP via mpirun with Intel OneAPI environment sourcing, configurable binary selection (vasp_std/vasp_gam/vasp_ncl), process count, and live output streaming
- **Remote execution** — Submit jobs to Slurm-managed HPC clusters via SSH (password or key-file authentication), with automatic batch script generation, file upload/download synchronization, and job monitoring (submit/cancel/status)

### Structure Visualization

- Interactive 3D crystal structure viewer powered by Py3Dmol
- Unit cell wireframe with color-coded lattice vector arrows (a=red, b=green, c=blue)
- CPK-colored atoms for the full periodic table
- 2D view mode (along c-axis) and standard 3D rotatable view
- Lattice parameter display (a, b, c, α, β, γ) and element count summary

### Electronic Properties Plotting

- **Band Structure** — Line-mode with high-symmetry k-point labels, spin-polarized support, Fermi level shifting
- **Total DOS** — Spin-resolved density of states with configurable energy range
- **Projected DOS (PDOS)** — Element- and orbital-resolved (s, p, d, f) partial density of states
- **Projected Band Structure (Fat Bands)** — Orbital-weighted band structure with marker size proportional to projection weight
- Dual plotting backends: Matplotlib (static, publication-quality) and Plotly (interactive)

### Phonon Properties Plotting

- Phonon dispersion and phonon DOS visualization from pre-processed data files
- Interactive Plotly plots with configurable axes

## Installation

### Prerequisites

- Python 3.8 or higher
- A working VASP installation (for running simulations)

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/GUI4VASP.git
   cd GUI4VASP
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Dependency Notes

All dependencies are listed in `requirements.txt`. The core application requires `streamlit`, `numpy`, and `plotly`. Other packages enable specific features:

| Package | Feature |
|---------|---------|
| `pymatgen` | Electronic band structure and DOS plotting (parses `vasprun.xml`) |
| `matplotlib` | Static/publication-quality plot rendering |
| `ase` | Crystal structure building, file I/O, preset materials |
| `py3Dmol` | Interactive 3D crystal structure visualization |
| `mp-api` | Fetching structures from the Materials Project database |
| `pandas` | Tabular display of Materials Project search results |
| `paramiko` | SSH/SFTP connectivity for remote Slurm job submission |

The application degrades gracefully when optional packages are missing — unavailable features display an installation prompt instead of crashing.

## Usage

### Quick Start

```bash
streamlit run app.py
```

The application opens in your default web browser. Use the sidebar to navigate between pages.

### Typical Workflow

1. **Home** — Read about features and get started
2. **Input Generator** — Generate INCAR, POSCAR, POTCAR, and KPOINTS files; save each to a named project folder
3. **My Projects** — Navigate to the project folder and verify all 4 input files are present
4. **Run Simulation** — Point to the project folder, configure the VASP environment, and start the calculation (locally or remotely)
5. **Structural Plotter** — Visualize input/output structures (POSCAR/CONTCAR) in 3D
6. **Electronic Plotter** — Load `vasprun.xml` to plot band structure, DOS, PDOS, or projected bands
7. **Phononic Plotter** — Visualize phonon dispersion and DOS from processed data

### Configuration

- **Materials Project API**: To use the Materials Project structure search, you need an API key from [materialsproject.org](https://materialsproject.org). Enter it in the POSCAR generator's Materials Project tab.
- **POTCAR library**: The POTCAR generator requires a local directory containing VASP pseudopotential files organized as `<root>/<functional>/<element>/POTCAR`.
- **Local VASP execution**: Configure paths to your VASP binaries and Intel OneAPI installation in the Run Simulation page.
- **Remote Slurm execution**: Configure SSH connection details (hostname, port, credentials) and Slurm settings (partition, nodes, time limit) in the Run Simulation page.

## Project Structure

```
GUI4VASP/
├── app.py                        # Main entry point — page config, routing, sidebar
├── styles.py                     # Global CSS styles
├── requirements.txt              # Python dependencies
├── sections/                     # Page-level UI modules
│   ├── home.py                   # Home/welcome page
│   ├── my_projects.py            # File/folder browser & project manager
│   ├── input_generator.py        # Tabbed INCAR/POSCAR/POTCAR/KPOINTS hub
│   ├── run_simulation.py         # Local & remote (Slurm) job runner
│   └── placeholder.py           # Stub for pages under construction
├── generators/                   # VASP input file generators
│   ├── incar.py                  # INCAR parameter generator (presets + custom)
│   ├── poscar.py                 # POSCAR structure generator (6 methods)
│   ├── potcar.py                 # POTCAR pseudopotential assembler
│   └── kpoints.py                # KPOINTS mesh/path generator
├── plotters/                     # Output visualization modules
│   ├── structural_plotter.py     # 3D crystal structure viewer
│   ├── electronic_plotter.py     # Band structure, DOS, PDOS, fat bands
│   └── phononic_plotter.py       # Phonon dispersion & phonon DOS
└── utils/                        # Backend utilities
    ├── ssh_client.py             # Paramiko-based SSH/SFTP client
    ├── run_job_local.py          # Local VASP job runner (subprocess)
    └── run_job_slurm.py          # Remote Slurm job runner
```

## Known Limitations

- **Phononic Plotter**: Cannot parse phonon data directly from `vasprun.xml` yet. Currently requires pre-processed data files (e.g., from Phonopy) in .dat/txt format.
- **Projected DOS (Plotly)**: The Plotly backend for PDOS plotting is not yet implemented; only the Matplotlib backend is functional.
- **Projected Band Structure**: The function signature has a minor mismatch with its call site regarding the `kpoints_file` parameter.
- **Hardcoded paths**: The Run Simulation page contains default paths specific to the developer's environment. Users will need to update these to match their own setup.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [VASP](https://www.vasp.at/) — Vienna Ab initio Simulation Package
- [Streamlit](https://streamlit.io/) — Web application framework
- [pymatgen](https://pymatgen.org/) — Materials science analysis library
- [ASE](https://wiki.fysik.dtu.dk/ase/) — Atomic Simulation Environment
- [Materials Project](https://materialsproject.org/) — Open materials database
- [Py3Dmol](https://3dmol.csb.pitt.edu/) — 3D molecular visualization
