# ui/switch.py
# Description: Page to manage devices.
# Changes:
# - Added 'run_status_check_silent' and 'run_backup_all_silent' methods for the scheduler.
# - These silent methods log results instead of showing UI notifications.
# - FIX: Adjusted logging levels for routine operations to DEBUG.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QHeaderView, QAbstractItemView,
    QTableWidgetItem, QGraphicsDropShadowEffect, QMessageBox, QAbstractScrollArea
)
from PySide6.QtCore import Qt, QSize, Signal, QThread
from datetime import datetime
from PySide6.QtGui import QColor

from utils.database import db_manager
from utils.logger import app_logger
from network.ssh_worker import SSHWorker
from network.ping_worker import PingWorker
from ui.add_device_dialog import AddDeviceDialog
from ui.icon_manager import IconManager
from ui.styles import Style

class DevicesPage(QWidget):
    device_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("devicesPage")
        self.threads = {}; self.ping_threads = {}
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setSpacing(25)
        header_layout = self._create_header(); main_layout.addLayout(header_layout)
        table_panel = self._create_table_panel(); main_layout.addWidget(table_panel)
        self.refresh_table()

    # --- NEW: Silent methods for the scheduler ---
    def run_status_check_silent(self):
        """Initiates a ping check for all devices without user feedback."""
        # FIX: Change this log to debug level
        app_logger.get_logger().debug("[Scheduler] Starting network-wide status check (silent)...")
        devices = db_manager.get_all_devices()
        if not devices:
            app_logger.get_logger().debug("[Scheduler] No devices to ping.") # FIX: Change to debug
            return
            
        for device_data in devices:
            # Note: This runs pings sequentially from the scheduler's signal.
            # For large networks, this should also be threaded, but is fine for now.
            db_manager.update_device_status(device_data['id'], self._ping_device_sync(device_data['ip']))
        app_logger.get_logger().debug("[Scheduler] Status check finished (silent).") # FIX: Change to debug
        self.refresh_table()

    def run_backup_all_silent(self):
        """Initiates a backup for all devices without user feedback."""
        app_logger.get_logger().info("[Scheduler] Starting daily backup for all devices...") # Keep as INFO
        devices = db_manager.get_all_devices()
        for device_data in devices:
            self._run_backup(device_data, silent=True)

    def _ping_device_sync(self, ip):
        """A synchronous ping for the silent checker."""
        import subprocess, platform
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', '-w', '2', ip]
        return "Online" if subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0 else "Offline"

    # --- Modified methods to handle 'silent' mode ---
    def _run_backup(self, device_data: dict, silent=False):
        device_id = device_data['id']
        if device_id in self.threads and self.threads[device_id].isRunning():
            if not silent: self.window().show_toast(f"Backup for {device_data['name']} is already in progress.", "info")
            return
        if not silent: self.window().show_toast(f"Backup initiated for {device_data['name']}...", "info")
        
        thread = QThread(); worker = SSHWorker(device_data); worker.moveToThread(thread)
        # Use different slots for silent mode
        if silent:
            worker.success.connect(self._on_backup_success_silent)
            worker.error.connect(self._on_backup_error_silent)
        else:
            worker.success.connect(self._on_backup_success)
            worker.error.connect(self._on_backup_error)

        worker.finished.connect(thread.quit); worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater); thread.finished.connect(lambda: self.threads.pop(device_id, None))
        thread.started.connect(worker.run_backup); thread.start(); self.threads[device_id] = (thread, worker)

    def _on_backup_success(self, device_id, config_output):
        db_manager.update_last_backup(device_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")); self.refresh_table()
        device = next((d for d in self.devices_data if d['id'] == device_id), None)
        self.window().show_toast(f"Backup successful for {device['name'] if device else 'device'}.", "success")
        app_logger.get_logger().info(f"Backup successful for device ID: {device_id}") # Keep as INFO

    def _on_backup_error(self, device_id, error_message):
        device = next((d for d in self.devices_data if d['id'] == device_id), None)
        self.window().show_toast(f"Backup failed for {device['name'] if device else 'device'}.", "error")
        app_logger.get_logger().error(f"Backup failed for device ID {device_id}: {error_message}") # Keep as ERROR

    def _on_backup_success_silent(self, device_id, config_output):
        app_logger.get_logger().info(f"[Scheduler] Backup successful for device ID: {device_id}") # Keep as INFO
        db_manager.update_last_backup(device_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.refresh_table()

    def _on_backup_error_silent(self, device_id, error_message):
        app_logger.get_logger().error(f"[Scheduler] Backup failed for device ID {device_id}: {error_message}") # Keep as ERROR

    # (The rest of the file remains the same...)
    def _create_header(self):
        header_layout = QHBoxLayout(); title_label = QLabel("Device Management"); title_label.setObjectName("pageTitle")
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Search..."); self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self._filter_table)
        self.refresh_status_button = QPushButton("Refresh Status"); self.refresh_status_button.setIcon(IconManager.get_icon("refresh")); self.refresh_status_button.setObjectName("outlineButton")
        self.refresh_status_button.clicked.connect(self._run_status_check)
        add_device_button = QPushButton("Add Device"); add_device_button.setIcon(IconManager.get_icon("add"))
        add_device_button.clicked.connect(self._open_add_device_dialog)
        header_layout.addWidget(title_label); header_layout.addStretch(); header_layout.addWidget(self.search_input); header_layout.addWidget(self.refresh_status_button); header_layout.addWidget(add_device_button)
        return header_layout
    def _run_status_check(self):
        if not self.devices_data:
            return
        self.window().show_toast(f"Pinging {len(self.devices_data)} devices...", "info")
        self.refresh_status_button.setEnabled(False)
        self.refresh_status_button.setText("Pinging...")
        app_logger.get_logger().info("Starting ping in main thread.")
        self.active_ping_threads = len(self.devices_data)
        for device_data in self.devices_data:
            thread = QThread()
            worker = PingWorker(device_data)
            worker.moveToThread(thread)
            worker.result_ready.connect(self._on_ping_result)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(self._on_ping_thread_finished)
            thread.started.connect(worker.run_ping)
            # Strong reference to both
            self.ping_threads[device_data['id']] = (thread, worker)
            thread.start()

    def _on_ping_result(self, device_id, status):
        db_manager.update_device_status(device_id, status)
        for row in range(self.table.rowCount()):
            if self.devices_data[row]['id'] == device_id:
                self.table.setCellWidget(row, 1, self._create_status_widget(status)); self.devices_data[row]['status'] = status; break
        app_logger.get_logger().info(f"Device ID {device_id} status updated to: {status}") # Keep as INFO
    def _on_ping_thread_finished(self):
        self.active_ping_threads -= 1
        if self.active_ping_threads <= 0:
            app_logger.get_logger().info("Network-wide status check finished (manual).") # Keep as INFO
            self.window().show_toast("Status check complete.", "success")
            self.refresh_status_button.setEnabled(True); self.refresh_status_button.setText("Refresh Status")
    def _create_table_panel(self):
        panel = QFrame(); panel.setObjectName("PanelWidget"); panel_layout = QVBoxLayout(panel); panel_layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(); self.table.setObjectName("devicesTable"); self.table.setColumnCount(8); self.table.setHorizontalHeaderLabels(["DEVICE INFO", "STATUS", "MODEL", "LAST BACKUP", "USERNAME", "PASSWORD", "SNMP COMMUNITY", "ACTIONS"])
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.horizontalHeader().setStretchLastSection(False); self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus); self.table.setMouseTracking(True); self.table.cellDoubleClicked.connect(self._on_device_selected)
        panel_layout.addWidget(self.table); shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(30); shadow.setColor(QColor(0, 0, 0, 80)); shadow.setOffset(0, 4); panel.setGraphicsEffect(shadow)
        return panel
    def refresh_table(self):
        try:
            self.devices_data = db_manager.get_all_devices()
            self.table.setRowCount(len(self.devices_data))
            for row, device in enumerate(self.devices_data):
                self.table.setCellWidget(row, 0, self._create_device_info_widget(device["name"], device["ip"]))
                self.table.setCellWidget(row, 1, self._create_status_widget(device["status"]))
                self.table.setCellWidget(row, 2, self._create_text_widget(device["model"]))
                self.table.setCellWidget(row, 3, self._create_text_widget(device["last_backup"], "subtext"))
                self.table.setCellWidget(row, 4, self._create_text_widget(device.get("username", "")))
                self.table.setCellWidget(row, 5, self._create_text_widget("●●●●●" if device.get("password") else ""))
                self.table.setCellWidget(row, 6, self._create_text_widget(device.get("snmp_community", ""))) # <-- ADD THIS LINE
                self.table.setCellWidget(row, 7, self._create_actions_widget(device))
                self.table.setRowHeight(row, 70)
            app_logger.get_logger().debug("Device table refreshed.") # FIX: Change to debug
        except Exception as e: app_logger.get_logger().error(f"Failed to refresh device table: {e}")
    def _open_add_device_dialog(self):
        dialog = AddDeviceDialog(self)
        if dialog.exec():
            device_data = dialog.get_data()
            success, message = db_manager.add_device(device_data)
            if success: app_logger.get_logger().info(f"Successfully added device: {device_data['name']}"); self.refresh_table()
            else: app_logger.get_logger().error(f"Failed to add device: {message}"); QMessageBox.critical(self, "Database Error", message)
    def _open_edit_device_dialog(self, device_data: dict):
        dialog = AddDeviceDialog(self, device_data=device_data)
        if dialog.exec():
            updated_data = dialog.get_data()
            success, message = db_manager.update_device(device_data['id'], updated_data)
            if success: app_logger.get_logger().info(f"Successfully updated device ID: {device_data['id']}"); self.refresh_table()
            else: app_logger.get_logger().error(f"Failed to update device: {message}"); QMessageBox.critical(self, "Database Error", message)
    def _on_device_selected(self, row, column):
        self.device_selected.emit(self.devices_data[row])
        app_logger.get_logger().debug(f"Device selected: {self.devices_data[row].get('name', 'N/A')}") # FIX: Change to debug
    def _delete_device(self, device_id: int):
        device = next((d for d in self.devices_data if d['id'] == device_id), None)
        if not device: return
        reply = QMessageBox.warning(self, "Confirm Deletion", f"Delete '{device['name']}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.delete_device(device_id): app_logger.get_logger().info(f"Deleted device ID: {device_id}"); self.refresh_table()
            else: app_logger.get_logger().error(f"Failed to delete device ID: {device_id}")
    def set_filter(self, query: str):
        self.search_input.setText(query)
        app_logger.get_logger().debug(f"Filter set to: '{query}'") # FIX: Change to debug
    def _filter_table(self, text: str):
        text = text.lower()
        if text.startswith("status:"):
            status_filter = text.split(":")[1]
            for row in range(self.table.rowCount()):
                status_widget = self.table.cellWidget(row, 1)
                if status_widget and status_widget.findChild(QLabel):
                    status_text = status_widget.findChild(QLabel).text().lower()
                    if status_filter == "critical": self.table.setRowHidden(row, status_text not in ["warning", "offline"])
                    else: self.table.setRowHidden(row, status_filter not in status_text)
                else: self.table.setRowHidden(row, True)
        else:
            for row in range(self.table.rowCount()):
                name_text = self.table.cellWidget(row, 0).findChild(QLabel, "tableName").text().lower()
                ip_text = self.table.cellWidget(row, 0).findChild(QLabel, "tableSubtext").text().lower()
                model_text = self.table.cellWidget(row, 2).findChild(QLabel).text().lower()
                match = text in name_text or text in ip_text or text in model_text
                self.table.setRowHidden(row, not match)
        app_logger.get_logger().debug(f"Table filtered by text: '{text}'") # FIX: Change to debug
    def _create_device_info_widget(self, name, ip):
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setContentsMargins(5, 0, 5, 0); layout.setSpacing(2)
        name_label = QLabel(name); name_label.setObjectName("tableName"); ip_label = QLabel(ip); ip_label.setObjectName("tableSubtext")
        layout.addWidget(name_label); layout.addWidget(ip_label); layout.addStretch(); return widget
    def _create_status_widget(self, status):
        widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 0, 5, 0); layout.setSpacing(8)
        indicator = QFrame(); indicator.setObjectName("statusIndicator"); indicator.setFixedSize(10, 10)
        color = {"Online": Style.STATUS_GREEN, "Warning": Style.STATUS_YELLOW, "Offline": Style.STATUS_RED, "Unknown": "#888"}.get(status, "#888")
        indicator.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        label = QLabel(status); layout.addWidget(indicator); layout.addWidget(label); layout.addStretch(); return widget
    def _create_text_widget(self, text, object_name=None):
        widget = QWidget(); layout = QVBoxLayout(widget); layout.setContentsMargins(5,0,5,0)
        label = QLabel(text);
        if object_name: label.setObjectName(object_name)
        layout.addWidget(label); return widget
    def _create_actions_widget(self, device_data: dict):
        widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(10)
        edit_button = QPushButton(); edit_button.setIcon(IconManager.get_icon("edit")); edit_button.setObjectName("iconButton"); edit_button.setToolTip("Edit Device")
        edit_button.clicked.connect(lambda: self._open_edit_device_dialog(device_data))
        backup_button = QPushButton(); backup_button.setIcon(IconManager.get_icon("backup_ok")); backup_button.setObjectName("iconButton"); backup_button.setToolTip("Run Backup")
        backup_button.clicked.connect(lambda: self._run_backup(device_data))
        delete_button = QPushButton(); delete_button.setIcon(IconManager.get_icon("delete")); delete_button.setObjectName("iconButton"); delete_button.setToolTip("Delete Device")
        delete_button.clicked.connect(lambda: self._delete_device(device_data['id']))
        layout.addWidget(edit_button); layout.addWidget(backup_button); layout.addWidget(delete_button); layout.addStretch()
        return widget

