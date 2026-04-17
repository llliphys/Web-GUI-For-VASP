import paramiko
import socket
from pathlib import Path
from typing import Optional, Callable


class SSHClient:
    def __init__(
        self,
        hostname: str,
        port: int = 22,
        username: str = "",
        password: str = "",
        key_file: Optional[str] = None
    ):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.client: Optional[paramiko.SSHClient] = None
        self.sftp: Optional[paramiko.SFTPClient] = None

    def connect(self) -> tuple[bool, str]:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                "hostname": self.hostname,
                "port": self.port,
                "username": self.username,
                "look_for_keys": True,
                "timeout": 30,
            }

            if self.key_file:
                connect_kwargs["key_filename"] = self.key_file
            elif self.password:
                connect_kwargs["password"] = self.password

            self.client.connect(**connect_kwargs)
            self.sftp = self.client.open_sftp()
            return True, "Connected successfully"
        except paramiko.AuthenticationException:
            return False, "Authentication failed"
        except socket.timeout:
            return False, "Connection timed out"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def disconnect(self) -> None:
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.client:
            self.client.close()
            self.client = None

    def is_connected(self) -> bool:
        return self.client is not None and self.client.get_transport() is not None

    def execute(self, command: str, timeout: int = 300) -> tuple[int, str, str]:
        if not self.is_connected():
            return -1, "", "Not connected"
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            return exit_code, stdout.read().decode(), stderr.read().decode()
        except Exception as e:
            return -1, "", str(e)

    def upload_file(self, local_path: str, remote_path: str) -> tuple[bool, str]:
        if not self.is_connected() or not self.sftp:
            return False, "Not connected"
        try:
            self.sftp.put(local_path, remote_path)
            return True, "File uploaded successfully"
        except Exception as e:
            return False, f"Upload failed: {str(e)}"

    def download_file(self, remote_path: str, local_path: str) -> tuple[bool, str]:
        if not self.is_connected() or not self.sftp:
            return False, "Not connected"
        try:
            self.sftp.get(remote_path, local_path)
            return True, "File downloaded successfully"
        except Exception as e:
            return False, f"Download failed: {str(e)}"

    def upload_directory(self, local_dir: str, remote_dir: str) -> tuple[bool, str]:
        if not self.is_connected() or not self.sftp:
            return False, "Not connected"
        try:
            Path(local_dir)
            local_path = Path(local_dir)
            for item in local_path.rglob("*"):
                remote_item = Path(remote_dir) / item.relative_to(local_path)
                if item.is_dir():
                    self.sftp.mkdir(remote_item)
                else:
                    self.sftp.put(item, remote_item)
            return True, "Directory uploaded successfully"
        except Exception as e:
            return False, f"Upload failed: {str(e)}"

    def upload_files_list(self, local_dir: str, remote_dir: str, file_list: list) -> tuple[bool, str]:
        if not self.is_connected() or not self.sftp:
            return False, "Not connected"
        try:
            local_path = Path(local_dir)
            for filename in file_list:
                local_file = local_path / filename
                if not local_file.exists():
                    return False, f"File not found: {filename}"
                remote_file = Path(remote_dir) / filename
                self.sftp.put(str(local_file), str(remote_file))
            return True, f"Uploaded {len(file_list)} files successfully"
        except Exception as e:
            return False, f"Upload failed: {str(e)}"

    def download_files_list(self, remote_dir: str, local_dir: str, file_list: list) -> tuple[bool, str]:
        if not self.is_connected() or not self.sftp:
            return False, "Not connected"
        try:
            Path(local_dir).mkdir(parents=True, exist_ok=True)
            for filename in file_list:
                remote_file = f"{remote_dir}/{filename}"
                local_file = Path(local_dir) / filename
                self.sftp.get(str(remote_file), str(local_file))
            return True, f"Downloaded {len(file_list)} files successfully"
        except Exception as e:
            return False, f"Download failed: {str(e)}"

    def download_directory(self, remote_dir: str, local_dir: str) -> tuple[bool, str]:
        if not self.is_connected() or not self.sftp:
            return False, "Not connected"
        try:
            os.chdir(local_dir)
            import os
            Path(local_dir).mkdir(parents=True, exist_ok=True)
            items = self.sftp.listdir_attr(remote_dir)
            for item in items:
                remote_item = f"{remote_dir}/{item.filename}"
                local_item = Path(local_dir) / item.filename
                if item.st_mode & 0o40000:
                    local_item.mkdir(exist_ok=True)
                    self.download_directory(remote_item, str(local_item))
                else:
                    self.sftp.get(remote_item, local_item)
            return True, "Directory downloaded successfully"
        except Exception as e:
            return False, f"Download failed: {str(e)}"

    def get_remote_file(self, remote_path: str) -> str:
        if not self.is_connected():
            return ""
        _, stdout, _ = self.execute(f"cat {remote_path}")
        return stdout

    def file_exists(self, remote_path: str) -> bool:
        if not self.is_connected():
            return False
        exit_code, stdout, _ = self.execute(f"test -e {remote_path} && echo exists")
        return "exists" in stdout

    def get_remote_dir_size(self, remote_dir: str) -> str:
        if not self.is_connected():
            return "0"
        _, stdout, _ = self.execute(f"du -sh {remote_dir}")
        return stdout.strip()
