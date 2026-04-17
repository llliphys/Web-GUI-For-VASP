import re
import threading
from pathlib import Path
from typing import Optional, Callable

from utils.ssh_client import SSHClient


class SlurmJob:
    def __init__(
        self,
        job_id: str,
        job_name: str = "VASP Job",
        status: str = "PENDING",
        submit_time: str = "",
        run_time: str = "",
        nodes: int = 1,
        cores: int = 1,
        partition: str = "",
        nodelist: str = ""
    ):
        self.job_id = job_id
        self.job_name = job_name
        self.status = status
        self.submit_time = submit_time
        self.run_time = run_time
        self.nodes = nodes
        self.cores = cores
        self.partition = partition
        self.nodelist = nodelist

    def __repr__(self):
        return f"SlurmJob(id={self.job_id}, name={self.job_name}, status={self.status})"


class SlurmJobRunner:
    def __init__(self, ssh_client: SSHClient, work_dir: str):
        self.ssh = ssh_client
        self.work_dir = work_dir
        self.job_id: Optional[str] = None
        self.is_running: bool = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.output_callback: Optional[Callable] = None

    def submit_job(
        self,
        job_name: str = "VASP_Job",
        partition: str = "default",
        nodes: int = 1,
        ntasks_per_node: int = 1,
        cpus_per_task: int = 1,
        time_limit: str = "01:00:00",
        modules: Optional[list] = None,
        soft_link: Optional[str] = None,
        vasp_cmd: str = "vasp_std",
        vasp_path: Optional[str] = None,
        extra_srun_opts: str = "",
        extra_sbatch_opts: str = ""
    ) -> tuple[bool, str]:
        if self.is_running:
            return False, "A job is already running"

        modules_str = "module reset\n"
        if modules:
            for mod in modules:
                modules_str += f"module load {mod}\n"
        
        export_vasp_str = ""
        if vasp_path:
            # modules_str += f"\nexport PATH={vasp_path}:$PATH\n"
            export_vasp_str += f"\nexport PATH={vasp_path}:$PATH\n"

        soft_link_str = ""
        if soft_link:
            soft_link_str += f"\n{soft_link}\n"
        
        all_str_combined = modules_str + export_vasp_str + soft_link_str

        required_files = ["INCAR", "POSCAR", "POTCAR", "KPOINTS"]
        missing = []
        for f in required_files:
            _, stdout, _ = self.ssh.execute(f"test -f {self.work_dir}/{f} && echo exists")
            if "exists" not in stdout:
                missing.append(f)

        if missing:
            return False, f"Missing required files on remote: {', '.join(missing)}"

        run_script = f"""#!/bin/bash
#SBATCH --chdir={self.work_dir}
#SBATCH --job-name={job_name}
#SBATCH --partition={partition}
#SBATCH --nodes={nodes}
#SBATCH --ntasks-per-node={ntasks_per_node}
#SBATCH --cpus-per-task={cpus_per_task}
#SBATCH --time={time_limit}
#SBATCH --output=./%J.out
#SBATCH --error=./%J.err
{extra_sbatch_opts}

# cd {self.work_dir}

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

{all_str_combined}

srun {extra_srun_opts} {vasp_cmd}
"""
        script_path = f"{self.work_dir}/run_vasp.sh"
        exit_code, stdout, stderr = self.ssh.execute(f"cat > {script_path} << 'EOF'\n{run_script}\nEOF")
        if exit_code != 0:
            return False, f"Failed to create script: {stderr}"

        exit_code, stdout, stderr = self.ssh.execute(f"sbatch {script_path}")

        if exit_code == 0:
            match = re.search(r"Submitted batch job (\d+)", stdout)
            if match:
                self.job_id = match.group(1)
                self.is_running = True
                return True, f"Job submitted successfully. Job ID: {self.job_id}"
        return False, f"Failed to submit job: {stderr or stdout}"

    def cancel_job(self) -> tuple[bool, str]:
        if not self.job_id:
            return False, "No job to cancel"
        exit_code, stdout, stderr = self.ssh.execute(f"scancel {self.job_id}")
        if exit_code == 0:
            self.job_id = None
            self.is_running = False
            return True, "Job cancelled successfully"
        return False, f"Failed to cancel job: {stderr}"

    def get_job_status(self) -> Optional[SlurmJob]:
        if not self.job_id:
            return None

        # 1. Try squeue first – works for PENDING / RUNNING jobs
        exit_code, stdout, stderr = self.ssh.execute(
            f"squeue -j {self.job_id} -o '%i|%j|%T|%M|%S|%l|%D|%C|%R|%V' --noheader"
        )
        if exit_code == 0 and stdout.strip():
            parts = stdout.strip().split("|")
            if len(parts) >= 9:
                return SlurmJob(
                    job_id=parts[0].strip(),
                    job_name=parts[1].strip(),
                    status=parts[2].strip(),
                    run_time=parts[3].strip(),
                    submit_time=parts[8].strip() if len(parts) > 8 else "",
                    nodes=int(parts[6]) if parts[6].strip().isdigit() else 1,
                    cores=int(parts[7]) if parts[7].strip().isdigit() else 1,
                )

        # 2. Job no longer in squeue – query sacct for the final state
        #    sacct retains info for COMPLETED / FAILED / CANCELLED / TIMEOUT jobs.
        exit_code, stdout, stderr = self.ssh.execute(
            f"sacct -j {self.job_id} --format=JobID,JobName%30,State,Elapsed,Submit,NNodes,NCPUs "
            f"--parsable2 --noheader"
        )
        if exit_code == 0 and stdout.strip():
            # sacct may return multiple lines (job + job.batch + job.extern).
            # Use the first line which represents the overall job entry.
            for line in stdout.strip().splitlines():
                parts = line.split("|")
                if len(parts) >= 7:
                    sacct_job_id = parts[0].strip()
                    # Skip sub-steps like "12345.batch" or "12345.extern"
                    if "." in sacct_job_id:
                        continue
                    status = parts[2].strip()
                    # sacct may append modifiers like "CANCELLED by 12345"
                    if " " in status:
                        status = status.split()[0]
                    self.is_running = status in ("PENDING", "RUNNING")
                    return SlurmJob(
                        job_id=sacct_job_id,
                        job_name=parts[1].strip(),
                        status=status,
                        run_time=parts[3].strip(),
                        submit_time=parts[4].strip(),
                        nodes=int(parts[5]) if parts[5].strip().isdigit() else 1,
                        cores=int(parts[6]) if parts[6].strip().isdigit() else 1,
                    )

        return None

    def get_job_info(self) -> Optional[str]:
        if not self.job_id:
            return None
        exit_code, stdout, stderr = self.ssh.execute(f"scontrol show job {self.job_id}")
        return stdout if exit_code == 0 else None

    def monitor_job(self, callback: Optional[Callable] = None, interval: int = 30) -> None:
        self.output_callback = callback

        def monitor():
            while self.is_running:
                job = self.get_job_status()
                if job:
                    if callback:
                        callback(f"[{job.status}] {job.job_name} - Runtime: {job.run_time}")
                    if job.status in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]:
                        self.is_running = False
                        if callback:
                            callback(f"Job {self.job_id} has finished with status: {job.status}")
                        break
                else:
                    self.is_running = False
                    if callback:
                        callback("Job no longer found in queue")
                    break
                import time
                time.sleep(interval)

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def get_output_files(self, local_dir: str) -> tuple[bool, str]:
        if not self.job_id:
            return False, "No job ID"
        files = ["OUTCAR", "CONTCAR", "vasp.out", f"VASP_Job_{self.job_id}.out", f"VASP_Job_{self.job_id}.err"]
        success_files = []
        for f in files:
            remote_path = f"{self.work_dir}/{f}"
            if self.ssh.file_exists(remote_path):
                _, local_name = self.ssh.download_file(remote_path, f"{local_dir}/{f}")
                success_files.append(f)
        if success_files:
            return True, f"Downloaded: {', '.join(success_files)}"
        return False, "No output files found"

    def sync_local_to_remote(self, local_dir: str) -> tuple[bool, str]:
        return self.ssh.upload_directory(local_dir, self.work_dir)

    def check_convergence(self) -> bool:
        content = self.ssh.get_remote_file(f"{self.work_dir}/OUTCAR")
        return "free  energy   MOM" in content or "EDIFF" in content

    def get_remote_dir_size(self) -> str:
        return self.ssh.get_remote_dir_size(self.work_dir)
