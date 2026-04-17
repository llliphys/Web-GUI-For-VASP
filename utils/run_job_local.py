import os
import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable


class LocalJobRunner:
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.process: Optional[subprocess.Popen] = None
        self.output: str = ""
        self.is_running: bool = False

    def run(
        self,
        vasp_bin_dir: str = "",
        intel_dir: str = "",
        vasp_bin: str = "vasp_std",
        nprocs: int = 1,
        callback: Optional[Callable] = None
    ) -> tuple[bool, str]:
        if self.is_running:
            return False, "A job is already running"

        required_files = ["INCAR", "POSCAR", "POTCAR", "KPOINTS"]
        missing = [f for f in required_files if not (self.work_dir / f).exists()]
        if missing:
            return False, f"Missing required files: {', '.join(missing)}"

        if not vasp_bin_dir:
            return False, "VASP binary directory is not specified"

        os.chdir(self.work_dir)

        setup_cmd = ""
        if intel_dir:
            setup_cmd += f"source {intel_dir}/setvars.sh > /dev/null 2>&1 && "
        
        vasp_path = os.path.join(vasp_bin_dir, f"{vasp_bin}")

        # if not os.path.exists(vasp_path):
        #     vasp_path = os.path.join(vasp_bin_dir, "vasp_gam")
        # if not os.path.exists(vasp_path):
        #     vasp_path = os.path.join(vasp_bin_dir, "vasp_ncl")

        if not os.path.exists(vasp_path):
            return False, f"No VASP executable found in {vasp_bin_dir}"

        setup_cmd += f"export PATH={vasp_bin_dir}:$PATH && "
        cmd = setup_cmd + (f"mpirun -n {nprocs} {vasp_path}" if nprocs > 1 else f"{vasp_path}")

        try:
            self.process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                executable="/bin/bash"
            )
            self.is_running = True
            self.output = ""

            while self.is_running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    self.output += line
                    if callback:
                        callback(line)

            self.is_running = False
            returncode = self.process.wait()
            self.process = None

            if returncode == 0:
                return True, self.output
            return False, self.output
        except Exception as e:
            self.is_running = False
            return False, str(e)

    def stop(self) -> bool:
        if not self.is_running or self.process is None:
            return False
        self.process.terminate()
        self.process.wait()
        self.is_running = False
        self.process = None
        return True

    def get_status(self) -> str:
        if not self.is_running:
            return "idle"
        if self.process and self.process.poll() is None:
            return "running"
        return "idle"

    def check_convergence(self) -> bool:
        outcar = self.work_dir / "OUTCAR"
        if not outcar.exists():
            return False
        with open(outcar, "r") as f:
            content = f.read()
            return "free  energy   MOM" in content or "EDIFF" in content

    def get_job_info(self) -> dict:
        return {
            "status": self.get_status(),
            "work_dir": str(self.work_dir),
            "is_running": self.is_running,
        }
