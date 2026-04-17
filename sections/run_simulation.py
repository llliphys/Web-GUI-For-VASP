"""
sections/run_simulation.py — Run Simulation page.

Provides two modes:
  1. Local runner  – execute VASP via bash script on the local machine.
  2. Remote runner – submit Slurm jobs on a remote cluster via SSH.
"""

import os
import time
import subprocess
import threading

import streamlit as st
from dotenv import load_dotenv

from styles import COMMON_STYLES
from sections.my_projects import render_file_preview

# Load environment variables from .env file
load_dotenv()


# ===========================================================================
# Session-state initialisation
# ===========================================================================

def _init_run_simulation_state() -> None:
    """Ensure all Run Simulation session-state keys exist."""
    defaults = {
        "run_mode":      "Local",
        "local_runner":  None,
        "slurm_ssh":     None,
        "slurm_runner":  None,
        "job_output":    "",
        "job_status":    "idle",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ===========================================================================
# Public entry point
# ===========================================================================

def render_run_simulation() -> None:
    """Render the Run Simulation page (local or remote mode selector)."""
    _init_run_simulation_state()
    st.markdown(COMMON_STYLES, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">▶️ Run Simulation</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Run VASP calculations locally or on a remote cluster</p>',
                unsafe_allow_html=True)
    st.markdown("---")

    # ── Mode selector ───────────────────────────────────────────────
    run_mode = st.radio(
        "Select Run Mode",
        ["Local", "Remote (Slurm)"],
        horizontal=True,
        index=0 if st.session_state.run_mode == "Local" else 1,
        key="run_mode_radio",
    )
    st.session_state.run_mode = run_mode
    st.markdown("---")

    if run_mode == "Local":
        _render_local_runner()
    else:
        _render_remote_runner()


# ===========================================================================
# Local runner
# ===========================================================================

def _render_local_runner() -> None:
    """Render the local job runner UI (environment, script, controls)."""
    st.markdown("### 🖥️ Local Job Runner")

    # ── Default session-state values ────────────────────────────────
    if "local_work_dir" not in st.session_state:
        st.session_state.local_work_dir = os.getcwd()
    if "vasp_bin_dir" not in st.session_state:
        st.session_state.vasp_bin_dir = ""
    if "intel_dir" not in st.session_state:
        st.session_state.intel_dir = ""

    # ── Environment settings ────────────────────────────────────────
    with st.expander("⚙️ Environment Settings", expanded=True):
        vasp_bin_dir = st.text_input(
            "VASP Binary Directory",
            value=os.environ.get("LOCAL_VASP_BIN_DIR", ""),
            key="vasp_bin_dir_input",
            placeholder="/path/to/vasp/bin",
        )
        st.session_state.vasp_bin_dir = vasp_bin_dir

        intel_dir = st.text_input(
            "Intel OneAPI Directory",
            value=os.environ.get("LOCAL_INTEL_ONEAPI_DIR", ""),
            key="intel_dir_input",
            placeholder="/path/to/intel/oneapi",
        )
        st.session_state.intel_dir = intel_dir

    # ── Working directory ───────────────────────────────────────────
    # work_dir = st.text_input(
    #     "Working Directory",
    #     value=st.session_state.local_work_dir,
    #     key="local_work_dir_input",
    # )
    # st.session_state.local_work_dir = work_dir

    # if "local_work_dir" not in st.session_state:
    #     st.session_state.local_work_dir = ""

    col_work_dir, col_work_test = st.columns([4, 1])
    with col_work_dir:
        work_dir = st.text_input(
            "Working Directory",
            value=st.session_state.local_work_dir,
            key="local_work_dir_input",
            help="Path to working directory",
        )
        # st.session_state.local_work_dir = work_dir
    with col_work_test:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Test Path", key="test_work_path_local"):
            if os.path.exists(work_dir):
                st.success("Working directory exists")
            else:
                os.makedirs(work_dir,  exist_ok=True)
                st.success("Working directory created")
            # st.session_state.local_work_dir = work_dir
    st.session_state.local_work_dir = work_dir


    # ── Previous directory ───────────────────────────────────────────
    use_prev_local = st.checkbox("Use Previous Directory", value=False, key="if_use_prev_dir_local")
    if use_prev_local:

        col_prev_dir, col_prev_test = st.columns([4, 1])
        with col_prev_dir:
            prev_dir_local = st.text_input(
                "Previous calculation directory",
                value=os.getcwd(),
                key="local_prev_dir",
                help="Path to previous calculation directory",
            )
        with col_prev_test:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Test Path", key="test_prev_path_local"):
                if os.path.exists(prev_dir_local):
                    st.success("Previous calculation directory exists")
                else:
                    st.error("No previous calculation directory found")

        # prev_dir_local = st.text_input(
        # "Previous Directory",
        # value=os.getcwd(),
        # key="local_prev_dir_input")
    
    if use_prev_local:
        use_prev_local_chgcar = st.checkbox("Use the CHGCAR file from Previous Calculation Directory",
                                            value = False,
                                            key = "if_use_prev_local_chgcar")
        use_prev_local_wavecar = st.checkbox("Use the WAVRCAR file from Previous Calculation Directory",
                                            value = False,
                                            key = "if_use_prev_local_wavecar")
    soft_link = ""
    if use_prev_local and use_prev_local_chgcar and os.path.exists(prev_dir_local):
        soft_link += f"ln -s {prev_dir_local}/CHGCAR {work_dir}/CHGCAR \n"
    if use_prev_local and use_prev_local_wavecar and os.path.exists(prev_dir_local):
        soft_link += f"ln -s {prev_dir_local}/WAVECAR {work_dir}/WAVECAR \n"

    # ── VASP binary and process count ───────────────────────────────
    col_vasp, col_procs = st.columns([2, 2])
    with col_vasp:
        default_local_vasp_exec = os.environ.get("LOCAL_VASP_EXECUTABLE", "vasp_std")
        local_vasp_options = ["vasp_std", "vasp_gam", "vasp_ncl"]
        default_local_idx = local_vasp_options.index(default_local_vasp_exec) if default_local_vasp_exec in local_vasp_options else 0
        vasp_bin = st.selectbox("VASP Binary", local_vasp_options, index=default_local_idx)
    with col_procs:
        nprocs = st.number_input("Number of Processes", value=4, min_value=1, max_value=16,
                                 key="nprocs_input")

    # ── Persistent job state ────────────────────────────────────────
    if "job_state" not in st.session_state:
        st.session_state.job_state = {
            "status":  "idle",
            "output":  "",
            "process": None,
        }
    job_state = st.session_state.job_state

    # ── Script preview ──────────────────────────────────────────────
    vasp_script = _generate_local_script(work_dir, soft_link, vasp_bin_dir, intel_dir, vasp_bin, nprocs)
    with st.expander("📜 Preview Job Script", expanded=True):
        st.code(vasp_script, language="bash")

    if st.button("Generate Job Script"):
        script_path = os.path.join(work_dir, "run_vasp.sh")
        with open(script_path, "w") as f:
            f.write(vasp_script)
        os.chmod(script_path, 0o755)

    # ── Required-file check ─────────────────────────────────────────
    required_files = ["INCAR", "POSCAR", "POTCAR", "KPOINTS"]
    existing_files = []
    with st.expander("📋 Check Required Files"):
        for fname in required_files:
            file_exists = os.path.exists(os.path.join(work_dir, fname))
            status = "✅" if file_exists else "❌"
            st.markdown(f"{status} {fname}")
            if file_exists:
                existing_files.append(fname)

        if vasp_bin_dir:
            vasp_path = os.path.join(vasp_bin_dir, vasp_bin)
            has_vasp = os.path.exists(vasp_path)
            st.markdown(f"{'✅' if has_vasp else '❌'} {vasp_path}")
        else:
            st.markdown("⚠️ Please specify VASP binary directory above")

    # Preview each existing input file
    for item in existing_files:
        item_path = os.path.join(work_dir, item)
        with st.expander(f"📄 {item}"):
            render_file_preview(item_path)

    st.markdown("")

    # ── Job runner (runs in a background thread – no st.* calls) ───
    script_path = os.path.join(work_dir, "run_vasp.sh")

    def _run_job_local():
        try:
            job_state["status"] = "running"
            job_state["output"] = ""
            process = subprocess.Popen(
                ["bash", script_path],
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            job_state["process"] = process
            for line in process.stdout:
                job_state["output"] += line
            process.wait()
            job_state["status"] = "completed" if process.returncode == 0 else "failed"
        except Exception as e:
            job_state["status"] = "failed"
            job_state["output"] += f"\nERROR: {e}"

    def _stop_job_local():
        process = job_state.get("process")
        if process:
            process.terminate()
            job_state["status"] = "failed"

    # ── Start / Stop / Status controls ──────────────────────────────
    col_run, col_stop, col_status = st.columns([1, 1, 2])

    with col_run:
        run_disabled = (job_state["status"] == "running")
        if st.button("▶️ Start Job", key="start_local_job", disabled=run_disabled):
            thread = threading.Thread(target=_run_job_local, daemon=True)
            thread.start()

    with col_stop:
        stop_disabled = (job_state["status"] != "running")
        if st.button("⏹️ Stop Job", key="stop_local_job", disabled=stop_disabled):
            _stop_job_local()

    with col_status:
        status = job_state["status"]
        if status == "running":
            st.success("🟢 Job is running")
        elif status == "completed":
            st.success("✅ Job completed successfully")
        elif status == "failed":
            st.error("❌ Job failed")
        else:
            st.info("⚪ Idle")

    # ── Job output ──────────────────────────────────────────────────
    if job_state["output"]:
        st.code(job_state["output"], language="bash")

    # ── Auto-refresh while running ──────────────────────────────────
    if job_state["status"] == "running":
        time.sleep(1)
        st.rerun()


def _generate_local_script(work_dir: str, soft_link: str, vasp_bin_dir: str, intel_dir: str,
                           vasp_bin: str, nprocs: int) -> str:
    """Generate the bash script content for running VASP locally."""
    lines = [
        "#!/bin/bash",
        "",
        f"# Working directory",
        f"cd {work_dir}",
        "",
    ]

    if intel_dir:
        lines.append(f"# Source Intel OneAPI environment")
        lines.append(f"source {intel_dir}/setvars.sh > /dev/null 2>&1")
        lines.append("")

    if vasp_bin_dir:
        lines.append(f"# Export VASP binary directory")
        lines.append(f"export VASP_DIR={vasp_bin_dir}")
        lines.append(f"export PATH=$VASP_DIR:$PATH")
        lines.append("")

    if soft_link:
        lines.append(f"{soft_link}")
        
    lines.append("# Run VASP")
    if nprocs > 1:
        lines.append(f"mpirun -n {nprocs} {vasp_bin}")
    else:
        lines.append(vasp_bin)

    return "\n".join(lines)


# ===========================================================================
# Remote (Slurm) runner
# ===========================================================================

def _render_remote_runner() -> None:
    """Render the remote Slurm job runner UI."""
    st.markdown("### 🖧 Remote Job Runner (Slurm)")

    ssh_connected = (st.session_state.get("slurm_ssh")
                     and st.session_state.slurm_ssh.is_connected())

    # ── SSH connection settings ─────────────────────────────────────
    with st.expander("🔐 SSH Connection Settings", expanded=not ssh_connected):
        col_host, col_port = st.columns([3, 1])
        with col_host:
            hostname = st.text_input("Hostname",
                                     value=os.environ.get("SSH_HOSTNAME", ""),
                                     key="ssh_hostname",
                                     placeholder="e.g., login.cluster.de")
        with col_port:
            port = st.number_input("Port", value=int(os.environ.get("SSH_PORT", "22")),
                                   min_value=1, max_value=65535,
                                   key="ssh_port")

        username = st.text_input("Username", value=os.environ.get("SSH_USERNAME", ""), key="ssh_username")

        auth_method = st.radio("Authentication", ["Password", "SSH Key"],
                               horizontal=True, key="ssh_auth_method")
        if auth_method == "Password":
            password = st.text_input("Password", type="password",
                                     value=os.environ.get("SSH_PASSWORD", ""),
                                     key="ssh_password")
        else:
            password = ""

        if auth_method == "SSH Key":
            ssh_key = st.text_input("SSH Key Path",
                                    value=os.environ.get("SSH_KEY_PATH", ""),
                                    key="ssh_key_path")
        else:
            ssh_key = ""

        col_connect, col_disconnect = st.columns(2)
        with col_connect:
            if st.button("🔗 Connect", key="ssh_connect"):
                _connect_ssh(hostname, port, username, password, ssh_key)
        with col_disconnect:
            if ssh_connected:
                if st.button("🔌 Disconnect", key="ssh_disconnect"):
                    _disconnect_ssh()

    if ssh_connected:
        _render_remote_job_ui()


# ---------------------------------------------------------------------------
# SSH helpers
# ---------------------------------------------------------------------------

def _connect_ssh(hostname: str, port: int, username: str,
                 password: str, key_file: str) -> None:
    """Establish an SSH connection to the remote server."""
    if not hostname or not username:
        st.error("Hostname and username are required")
        return
    try:
        from utils.ssh_client import SSHClient

        ssh = SSHClient(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            key_file=key_file if key_file else None,
        )
        success, message = ssh.connect()
        if success:
            st.session_state.slurm_ssh = ssh
            st.success(f"Connected to {hostname}")
            st.rerun()
        else:
            st.error(f"Connection failed: {message}")
    except ImportError:
        st.error("Please install paramiko: pip install paramiko")


def _disconnect_ssh() -> None:
    """Disconnect the current SSH session."""
    ssh = st.session_state.get("slurm_ssh")
    if ssh:
        ssh.disconnect()
        st.session_state.slurm_ssh = None
        st.session_state.slurm_runner = None
        st.success("Disconnected")
        st.rerun()


# ---------------------------------------------------------------------------
# Remote job UI (file sync + job settings + submission)
# ---------------------------------------------------------------------------

def _render_remote_job_ui() -> None:
    """Render the full remote-job interface (sync, settings, script, submit)."""
    ssh = st.session_state.slurm_ssh

    st.markdown("#### 📁 Working Directory on Remote Server")

    # ── Remote working directory ────────────────────────────────────
    col_remote_dir, col_test = st.columns([4, 1])
    with col_remote_dir:
        remote_work_dir = st.text_input(
            "Remote Path",
            value="/scratch/hpc-prf-meop/Test",
            key="remote_work_dir",
        )
    with col_test:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Test Path", key="test_remote_path"):
            if ssh.file_exists(remote_work_dir):
                st.success("Working directory exists")
            else:
                exit_code, stdout, stderr = ssh.execute(f'mkdir -p "{remote_work_dir}"')
                if exit_code == 0 and ssh.file_exists(remote_work_dir):
                    st.success("Working directory created successfully")
                else:
                    st.error(f"Failed to create working directory: {stderr}")


    st.markdown("---")
    # ── File synchronisation (upload / download) ────────────────────
    col_sync_local, col_sync_remote = st.columns(2)

    with col_sync_local:
        st.markdown("##### 📤 Sync Local → Remote")
        local_sync_dir = st.text_input(
            "Local Directory",
            value=st.session_state.get("local_work_dir", os.getcwd()),
            key="local_sync_dir",
        )
        vasp_files = ["INCAR", "POSCAR", "POTCAR", "KPOINTS"]
        with st.expander("📋 Select Files to Upload"):
            selected_upload = st.multiselect(
                "Select files to upload", vasp_files,
                default=vasp_files, key="select_files_upload",
            )
            for item in selected_upload:
                item_path = os.path.join(local_sync_dir, item)
                with st.expander(f"📄 {item}"):
                    render_file_preview(item_path)

        if st.button("Upload Files", key="upload_files"):
            _upload_to_remote(local_sync_dir, remote_work_dir, selected_upload)

    with col_sync_remote:
        st.markdown("##### 📥 Sync Remote → Local")
        local_download_dir = st.text_input("Download to", value=os.getcwd(),
                                           key="download_dir")
        vasp_input_files = ["INCAR", "POSCAR", "POTCAR", "KPOINTS"]
        vasp_output_files = ["CONTCAR", "OSZICAR", "OUTCAR", "EIGENVAL",
                             "DOSCAR", "PROCAR", "vasprun.xml"]
        with st.expander("📥 Select Files to Download"):
            selected_download = st.multiselect(
                "Select files to download", vasp_input_files+vasp_output_files,
                default=vasp_input_files+vasp_output_files, key="select_files_download",
            )
        if st.button("Download Files", key="download_results"):
            _download_from_remote(remote_work_dir, local_download_dir, selected_download)

        for item in selected_download:
            item_path = os.path.join(local_download_dir, item)
            if os.path.exists(item_path):
                with st.expander(f"📄 {item}"):
                    render_file_preview(item_path)

    
    st.markdown("---")
   # ── previous calculation directory ────────────────────────────────────
    use_prev_remote = st.checkbox("Use Previous Calculation Directory on Remote Server", value=False, key="if_use_prev_dir")
    if use_prev_remote:
        col_prev_dir, col_prev_test = st.columns([4, 1])
        with col_prev_dir:
            prev_dir_remote = st.text_input(
                "Previous calculation directory",
                value="/scratch/hpc-prf-meop/Test", 
                key="remote_prev_dir",
                help="Path to previous calculation directory on remote server",
            )
        with col_prev_test:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Test Path", key="test_prev_path"):
                if ssh.file_exists(prev_dir_remote):
                    st.success("Previous calculation directory exists on remote server")
                else:
                    st.error("No previous calculation directory found on remote server")

    if use_prev_remote:
        use_prev_remote_chgcar = st.checkbox("Use the CHGCAR file from Previous Directory on Remote Server", 
                                             value=False, 
                                             key="if_use_chgcar_from_prev_dir")
        use_prev_remote_wavecar = st.checkbox("Use the WAVECAR file from Previous Directory on Remote Server", 
                                              value=False, 
                                              key="if_use_wavecar_from_prev_dir")

    # ── Job settings ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### ⚙️ Job Settings")

    col_name, col_partition, col_time = st.columns(3)
    with col_name:
        job_name = st.text_input("Job Name", value="VASP_Job", key="job_name")
    with col_partition:
        available_partitions = _get_available_partitions()
        partition = st.selectbox("Partition", available_partitions,
                                 index=available_partitions.index("normal"),
                                 key="job_partition")
    with col_time:
        time_limit = st.selectbox(
            "Time Limit",
            ["00:10:00", "01:00:00", "02:00:00", "04:00:00", "06:00:00",
             "08:00:00", "10:00:00", "12:00:00", "24:00:00", "36:00:00",
             "48:00:00", "60:00:00", "72:00:00", "96:00:00"],
            index=1, key="job_time",
        )

    col_nodes, col_tasks, col_cpus = st.columns(3)
    with col_nodes:
        nodes = st.number_input("Nodes", value=1, min_value=1, key="job_nodes")
    with col_tasks:
        ntasks = st.number_input("Tasks per Node", value=64, min_value=1,
                                 key="job_ntasks")
    with col_cpus:
        cpus_per_task = st.number_input("CPUs per Task", value=2, min_value=1,
                                        key="job_ncpus")

    # ── Modules ─────────────────────────────────────────────────────
    st.markdown("##### 🧩 Modules to Load")
    modules_input = st.text_input(
        "Modules To Load (comma-separated)",
        value=os.environ.get("REMOTE_MODULES_TO_LOAD", ""),
        key="job_modules",
        help="Enter module names to load on the remote server",
    )
    modules = [m.strip() for m in modules_input.split(",") if m.strip()]

    vasp_path_input = st.text_input(
        "Custom VASP Binary Path (optional)",
        value=os.environ.get("REMOTE_VASP_BIN_PATH", ""),
        key="job_vasp_path",
        help="Path to directory containing VASP executable",
    )
    vasp_path = vasp_path_input.strip() if vasp_path_input.strip() else None

    default_remote_vasp_exec = os.environ.get("REMOTE_VASP_EXECUTABLE", "vasp_std")
    remote_vasp_options = ["vasp_std", "vasp_gam", "vasp_ncl"]
    default_remote_idx = remote_vasp_options.index(default_remote_vasp_exec) if default_remote_vasp_exec in remote_vasp_options else 0
    vasp_cmd = st.selectbox("VASP Executable", remote_vasp_options,
                            index=default_remote_idx,
                            key="remote_vasp_cmd")

    # ── Script preview ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📜 Script Preview")

    soft_link = ""
    if use_prev_remote and use_prev_remote_chgcar and ssh.file_exists(prev_dir_remote):
        soft_link += f"ln -s {prev_dir_remote}/CHGCAR {remote_work_dir}/CHGCAR \n"
    if use_prev_remote and use_prev_remote_wavecar and ssh.file_exists(prev_dir_remote):
        soft_link += f"ln -s {prev_dir_remote}/WAVECAR {remote_work_dir}/WAVECAR \n"

    run_script = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --partition={partition}
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-node={ntasks}
#SBATCH --cpus-per-task={cpus_per_task}
#SBATCH --time={time_limit}
#SBATCH --output=./%J.out
#SBATCH --error=./%J.err

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

module reset
"""
    for mod in modules:
        run_script += f"module load {mod}\n"
    if vasp_path:
        run_script += f"export PATH={vasp_path}:$PATH\n"
    if soft_link:
        run_script += f"\n{soft_link}"
    run_script += f"\nsrun {vasp_cmd}"

    st.code(run_script, language="bash")
    st.markdown("---")

    # ── Submit / Cancel / Status ────────────────────────────────────
    col_submit, col_cancel, col_status = st.columns([1, 1, 2])
    with col_submit:
        if st.button("📤 Submit Job", key="submit_slurm_job"):
            _submit_slurm_job(remote_work_dir, job_name, partition, nodes,
                              ntasks, cpus_per_task, time_limit, modules,
                              soft_link, vasp_cmd, vasp_path)
            
    with col_cancel:
        if st.button("🗑️ Cancel Job", key="cancel_slurm_job"):
            _cancel_slurm_job()
    with col_status:
        job_is_active = _render_slurm_status()

    if "slurm_output" in st.session_state and st.session_state.slurm_output:
        st.markdown("---")
        st.markdown("#### 📜 Submission Output")
        st.code(st.session_state.slurm_output, language="bash")

    # ── Auto-refresh while job is active (PENDING / RUNNING) ────────
    if job_is_active:
        time.sleep(5)
        st.rerun()


# ---------------------------------------------------------------------------
# Remote file-transfer helpers
# ---------------------------------------------------------------------------

def _upload_to_remote(local_dir: str, remote_dir: str,
                      selected_files: list = None) -> None:
    """Upload selected local files to the remote server."""
    ssh = st.session_state.get("slurm_ssh")
    if not ssh or not ssh.is_connected():
        st.error("Not connected to remote server")
        return
    if not selected_files:
        st.warning("No files selected for upload")
        return
    with st.spinner("Uploading files..."):
        success, message = ssh.upload_files_list(local_dir, remote_dir, selected_files)
        if success:
            st.success(f"Files uploaded to {remote_dir}")
        else:
            st.error(f"Upload failed: {message}")


def _download_from_remote(remote_dir: str, local_dir: str,
                          selected_files: list = None) -> None:
    """Download selected files from the remote server."""
    ssh = st.session_state.get("slurm_ssh")
    if not ssh or not ssh.is_connected():
        st.error("Not connected to remote server")
        return
    if not selected_files:
        st.warning("No files selected for download")
        return
    with st.spinner("Downloading results..."):
        success, message = ssh.download_files_list(remote_dir, local_dir, selected_files)
        if success:
            st.success(f"Results downloaded to {local_dir}")
            for item in selected_files:
                item_path = os.path.join(local_dir, item)
                if os.path.exists(item_path):
                    with st.expander(f"📄 {item}"):
                        render_file_preview(item_path)
        else:
            st.error(f"{message}")


# ---------------------------------------------------------------------------
# Slurm job helpers
# ---------------------------------------------------------------------------

def _get_available_partitions() -> list:
    """Return the list of available Slurm partitions."""
    return ["normal", "largeem", "hugeem", "gpu", "dgx", "fpga"]


def _submit_slurm_job(work_dir: str, job_name: str, partition: str,
                      nodes: int, ntasks: int, cpus_per_task: int,
                      time_limit: str, modules: list, soft_link: str, vasp_cmd: str,
                      vasp_path: str = None) -> None:
    """Submit a Slurm batch job on the remote server."""
    from utils.run_job_slurm import SlurmJobRunner

    ssh = st.session_state.get("slurm_ssh")
    if not ssh or not ssh.is_connected():
        st.error("Not connected to remote server")
        return

    runner = SlurmJobRunner(ssh, work_dir)
    st.session_state.slurm_runner = runner

    success, message = runner.submit_job(
        job_name=job_name,
        partition=partition,
        nodes=nodes,
        ntasks_per_node=ntasks,
        cpus_per_task=cpus_per_task,
        time_limit=time_limit,
        modules=modules,
        soft_link=soft_link,
        vasp_cmd=vasp_cmd,
        vasp_path=vasp_path,
    )

    st.session_state.slurm_output = message
    if success:
        st.success(message)
        st.rerun()
    else:
        st.error(message)


def _cancel_slurm_job() -> None:
    """Cancel the active Slurm job."""
    runner = st.session_state.get("slurm_runner")
    if runner and runner.job_id:
        success, message = runner.cancel_job()
        if success:
            st.success(message)
            st.session_state.slurm_runner = None
            st.rerun()
        else:
            st.error(message)
    else:
        st.warning("No active job to cancel")


def _render_slurm_status() -> bool:
    """Display the current Slurm job status.

    Returns True if the job is still active (PENDING or RUNNING) and the
    UI should keep polling, False otherwise.
    """
    runner = st.session_state.get("slurm_runner")
    if not runner or not runner.job_id:
        st.info("⚪ No active job")
        return False

    job = runner.get_job_status()
    if job:
        status_map = {
            "PENDING":   ("⏳", "Pending"),
            "RUNNING":   ("🟢", "Running"),
            "COMPLETED": ("✅", "Completed"),
            "FAILED":    ("❌", "Failed"),
            "CANCELLED": ("🗑️", "Cancelled"),
            "TIMEOUT":   ("⏰", "Timed out"),
        }
        icon, status_text = status_map.get(job.status, ("⚪", job.status))
        st.markdown(f"**{icon} Job ID:** `{job.job_id}` | **{status_text}** | **Runtime:** `{job.run_time}`")

        # Job is still active if PENDING or RUNNING
        return job.status in ("PENDING", "RUNNING")
    else:
        st.info("⚪ Job not found in queue (may have finished)")
        return False
