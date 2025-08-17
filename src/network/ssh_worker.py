# network/ssh_worker.py
# Description: Handles SSH connections and command execution in a background thread.

import paramiko
import json
import os
from PySide6.QtCore import QObject, Signal
from datetime import datetime

from utils.logger import app_logger
from utils.database import db_manager

class SSHWorker(QObject):
    finished = Signal()
    success = Signal(int, str)
    error = Signal(int, str)

    def __init__(self, device_info: dict):
        super().__init__()
        self.device_info = device_info
        self.logger = app_logger.get_logger()

    def run_backup(self):
        device_id = self.device_info['id']
        ip = self.device_info['ip']
        self.logger.info(f"Starting backup task for {self.device_info['name']} ({ip})...")

        try:
            username = self.device_info.get("username")
            password = self.device_info.get("password")

            if not username or not password:
                raise ValueError("Missing SSH username or password for device.")

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ip, username=username, password=password, timeout=10)

            self.logger.info(f"SSH connection established for device ID: {device_id}")
            
            stdin, stdout, stderr = client.exec_command('show running-config')
            config_output = stdout.read().decode('utf-8')
            error_output = stderr.read().decode('utf-8')
            client.close()

            if error_output:
                raise IOError(error_output)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db_manager.add_backup(device_id, timestamp, config_output)

            self.logger.info(f"Configuration for device ID {device_id} saved to database.")
            self.success.emit(device_id, config_output)

        except Exception as e:
            err_msg = f"An error occurred: {e}"
            self.logger.error(f"Failed backup for device ID {device_id}. {err_msg}")
            self.error.emit(device_id, err_msg)

        finally:
            self.finished.emit()