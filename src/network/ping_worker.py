# File: network/ping_worker.py

import platform
import subprocess
import logging

from PySide6.QtCore import QObject, Signal

# Set up logging
logger = logging.getLogger(__name__)


class PingWorker(QObject):
    """
    A Qt-compatible worker class used to ping a device in a separate thread.
    This structure allows integration with PySide6 for GUI applications.
    """

    # Qt signals
    finished = Signal()
    result_ready = Signal(int, str)  # device_id, status ("Online"/"Offline")

    def __init__(self, device_info):
        super().__init__()
        self.device_info = device_info

    def run_ping(self):
        """
        Called when thread starts. Pings the device and emits the result.
        """
        ip = self.device_info.get('ip')
        device_id = self.device_info.get('id', -1)

        try:
            system_platform = platform.system().lower()

            if 'windows' in system_platform:
                param = '-n'
                timeout_flag = '-w'  # milliseconds
                timeout_value = '5000'
            else:
                param = '-c'
                timeout_flag = '-W'  # seconds
                timeout_value = '5'

            command = ['ping', param, '1', timeout_flag, timeout_value, ip]
            logger.debug(f"Pinging {ip} with command: {' '.join(command)}")

            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=7  # overall timeout
            )

            logger.debug(f"Ping result for {ip}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

            if result.returncode == 0:
                logger.info(f"Ping to {ip} successful.")
                self.result_ready.emit(device_id, "Online")
            else:
                logger.warning(f"Ping to {ip} failed.")
                self.result_ready.emit(device_id, "Offline")

        except subprocess.TimeoutExpired:
            logger.warning(f"Ping to {ip} timed out.")
            self.result_ready.emit(device_id, "Offline")

        except Exception as e:
            logger.error(f"Error pinging {ip}: {e}")
            self.result_ready.emit(device_id, "Offline")

        finally:
            self.finished.emit()


# OPTIONAL: Add a static/class method if you want to test outside of GUI
def ping_ip(ip):
    """
    Standalone ping that returns True/False — can be used for testing.
    """
    try:
        system_platform = platform.system().lower()
        if 'windows' in system_platform:
            param = '-n'
            timeout_flag = '-w'
            timeout_value = '5000'
        else:
            param = '-c'
            timeout_flag = '-W'
            timeout_value = '5'

        command = ['ping', param, '1', timeout_flag, timeout_value, ip]
        logger.debug(f"(Static) Pinging {ip} with command: {' '.join(command)}")

        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=7)

        logger.debug(f"(Static) Ping result:\n{result.stdout.strip()}")
        return result.returncode == 0

    except Exception as e:
        logger.error(f"(Static) Error pinging {ip}: {e}")
        return False
