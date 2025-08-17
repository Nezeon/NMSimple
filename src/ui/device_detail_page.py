# ui/device_detail_page.py
# Description: A redesigned page with a more attractive and data-rich UI.
# UPDATED: Changed Uptime column to VLAN column for interface data

import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QGridLayout, QTableWidget, QTextEdit, QTabWidget, QHeaderView,
    QTableWidgetItem, QGraphicsDropShadowEffect, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPointF, QThread
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QLinearGradient, QPainterPath
from PySide6.QtWidgets import QFileDialog
from ui.icon_manager import IconManager
from ui.styles import Style
from utils.database import db_manager
from utils.logger import app_logger
from network.snmp_worker import SNMPWorker
from network.ssh_worker import SSHWorker
from ui.working_dynamic_cpu_graph import WorkingDynamicCPUGraph

class GraphPlaceholder(QWidget):
    """A widget that draws a visually appealing, simulated line graph."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.data_points = [0.2, 0.3, 0.25, 0.4, 0.5, 0.45, 0.6, 0.75, 0.7, 0.8, 0.6, 0.65]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        grid_pen = QPen(QColor(Style.DARK_BORDER)); grid_pen.setWidth(1); painter.setPen(grid_pen)
        num_h_lines = 5
        for i in range(1, num_h_lines + 1):
            y = self.height() * i / (num_h_lines + 1)
            painter.drawLine(0, y, self.width(), y)
        graph_pen = QPen(QColor(Style.DARK_ACCENT_PRIMARY)); graph_pen.setWidth(2); painter.setPen(graph_pen)
        points = [QPointF(self.width() * i / (len(self.data_points) - 1), self.height() - (val * self.height() * 0.8) - (self.height() * 0.1)) for i, val in enumerate(self.data_points)]
        painter.drawPolyline(points)
        gradient = QLinearGradient(0, 0, 0, self.height()); gradient.setColorAt(0.0, QColor(Style.DARK_ACCENT_PRIMARY).lighter(150)); gradient.setColorAt(1.0, QColor(Style.DARK_BG_PRIMARY)); painter.setBrush(gradient); painter.setPen(Qt.NoPen)
        fill_path = QPainterPath(); fill_path.moveTo(points[0].x(), self.height())
        for p in points: fill_path.lineTo(p)
        fill_path.lineTo(points[-1].x(), self.height()); painter.drawPath(fill_path)

import paramiko
from PySide6.QtCore import QObject, Signal

class DeviceDetailPage(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("deviceDetailPage")
        self.current_device_id = None
        self.current_device_info = {} # Store full device info
        self.backups = []
        self.snmp_thread = None # To manage the SNMP worker thread
        self._backup_thread = None
        self._backup_worker = None
        self._reboot_thread = None
        self._reboot_worker = None

        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setSpacing(25)
        header_layout = self._create_header(); main_layout.addLayout(header_layout)
        
        content_layout = QHBoxLayout(); content_layout.setSpacing(25)
        left_vbox = QVBoxLayout(); left_vbox.setSpacing(25)
        left_vbox.addWidget(self._create_info_panel())
        left_vbox.addStretch()
        
        right_tabs = self._create_details_tabs()
        content_layout.addLayout(left_vbox, 1); content_layout.addWidget(right_tabs, 3) # Give more space to tabs
        main_layout.addLayout(content_layout)

    def load_device_data(self, device_info: dict):
        self.current_device_id = device_info.get("id")
        self.current_device_info = device_info
        
        self.device_name_label.setText(device_info.get("name", "N/A"))
        self.status_card_val.setText(device_info.get("status", "N/A"))
        self.ip_card_val.setText(device_info.get("ip", "N/A"))
        self.model_card_val.setText(device_info.get("model", "N/A"))
        self.snmp_card_val.setText(device_info.get("snmp_community", "N/A"))

        status_color = {
            "Online": Style.STATUS_GREEN,
            "Warning": Style.STATUS_YELLOW,
            "Offline": Style.STATUS_RED,
        }.get(device_info.get("status"), Style.DARK_TEXT_SECONDARY)
        self.status_card_val.setStyleSheet(f"color: {status_color};")
        
        # Handle CPU graph safely and START monitoring
        if hasattr(self, 'cpu_graph'):
            try:
                # Stop any existing monitoring first
                self.cpu_graph.stop_monitoring()
                
                # Start monitoring with new device info
                self.cpu_graph.start_monitoring(device_info)
                
                app_logger.get_logger().debug(f"CPU graph monitoring started for device: {device_info.get('name', 'N/A')}")
                
            except Exception as e:
                app_logger.get_logger().error(f"Failed to start CPU graph monitoring: {e}")

        self._load_backup_history()
        self._load_interface_data()
        app_logger.get_logger().debug(f"Loaded details for device: {device_info.get('name', 'N/A')}")

    def _create_header(self):
        header_layout = QHBoxLayout()
        back_button = QPushButton("Back to Devices"); back_button.setIcon(IconManager.get_icon("back_arrow")); back_button.setObjectName("outlineButton")
        back_button.clicked.connect(self.back_clicked.emit)
        self.device_name_label = QLabel("Device Details"); self.device_name_label.setObjectName("pageTitle")
        header_layout.addWidget(back_button); header_layout.addWidget(self.device_name_label); header_layout.addStretch()
        return header_layout

    def _create_info_panel(self):
        panel = QFrame()
        panel.setObjectName("PanelWidget")
        layout = QVBoxLayout(panel)

        title = QLabel("Key Information")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self.status_card_val = self._create_info_card(layout, "status", "Status", "...")
        self.ip_card_val = self._create_info_card(layout, "ip_address", "IP Address", "...")
        self.model_card_val = self._create_info_card(layout, "chip", "Device Model", "...")
        self.snmp_card_val = self._create_info_card(layout, "settings", "SNMP Community", "...")

        return panel
        
    def _create_info_card(self, parent_layout, icon_name, label_text, value_text):
        card = QFrame(); card.setObjectName("InfoCard"); layout = QHBoxLayout(card); layout.setSpacing(15)
        icon = QLabel(); icon.setPixmap(IconManager.get_icon(icon_name).pixmap(24,24))
        text_layout = QVBoxLayout(); text_layout.setSpacing(2)
        label = QLabel(label_text); label.setObjectName("infoCardLabel")
        value = QLabel(value_text); value.setObjectName("infoCardValue")
        text_layout.addWidget(label); text_layout.addWidget(value)
        layout.addWidget(icon); layout.addLayout(text_layout)
        parent_layout.addWidget(card)
        return value

    def _create_details_tabs(self):
        tabs = QTabWidget()
        tabs.setObjectName("detailsTabs")

        # Live Performance Tab
        performance_tab = QWidget()
        perf_layout = QVBoxLayout(performance_tab)
        perf_layout.setContentsMargins(15, 15, 15, 15)
        perf_layout.setSpacing(15)

        self.cpu_graph = WorkingDynamicCPUGraph()
        self.cpu_graph.setMinimumHeight(300)  # Ensure it's visible
        perf_layout.addWidget(self.cpu_graph)
    
        perf_layout.addStretch()

        # Interfaces Tab - UPDATED to show VLAN instead of Uptime
        interfaces_tab = QWidget()
        if_layout = QVBoxLayout(interfaces_tab)
        if_layout.setContentsMargins(0, 10, 0, 0)
        self.interface_table = QTableWidget()
        self.interface_table.setObjectName("devicesTable")
        self.interface_table.setColumnCount(6)
        # UPDATED: Changed "UPTIME" to "VLAN"
        self.interface_table.setHorizontalHeaderLabels(["INTERFACE", "OPER STATUS", "ADMIN STATUS", "VLAN", "TRAFFIC (IN / OUT)", "POWER"])

        # Set column resize modes for interfaces table
        header = self.interface_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # INTERFACE - takes available space
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # OPER STATUS - fits content
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # ADMIN STATUS - fits content
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # VLAN - fits content
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # TRAFFIC (IN / OUT) - fits content
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # POWER - fits content

        self.interface_table.verticalHeader().setDefaultSectionSize(40)

        # Set minimum widths if needed to prevent squishing for specific columns
        header.setMinimumSectionSize(80)  # General minimum to prevent columns from becoming too small
        self.interface_table.setColumnWidth(1, 100)  # Give OPER STATUS a bit more room
        self.interface_table.setColumnWidth(2, 100)  # Give ADMIN STATUS a bit more room
        self.interface_table.setColumnWidth(3, 120)  # Give VLAN enough room for "100 (Sales)"
        self.interface_table.setColumnWidth(4, 150)  # Give TRAFFIC enough room for values like "1.23 GB / 4.56 GB"
        self.interface_table.setColumnWidth(5, 80)   # Give POWER enough room for "15.4W"

        if_layout.addWidget(self.interface_table)

        # Backup History Tab - ENHANCED UI
        backup_history_tab = QWidget()  # Create a container widget for the backup history
        backup_layout = QVBoxLayout(backup_history_tab)
        backup_layout.setContentsMargins(0, 10, 0, 0)  # Adjust margins for the tab content

        self.backup_table = QTableWidget()
        self.backup_table.setObjectName("backupTable")  # Set object name for styling
        self.backup_table.setColumnCount(3)
        self.backup_table.setHorizontalHeaderLabels(["TIMESTAMP", "STATUS", "ACTIONS"])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # TIMESTAMP
        self.backup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # STATUS
        self.backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # ACTIONS

        # Set column resize modes for better distribution
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # Set resize modes and widths for optimal layout
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # TIMESTAMP stretches
        self.backup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # STATUS fits text
        self.backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)  # ACTIONS fixed

        # Adjusted column width for ACTIONS to accommodate the hyperlink
        self.backup_table.setColumnWidth(1, 120)  # Give STATUS enough room for pill + text
        self.backup_table.setColumnWidth(2, 100)  # ACTIONS column width for the hyperlink (reduced from 200)

        # Set default row height for better button visibility
        self.backup_table.verticalHeader().setDefaultSectionSize(40)  # Increased row height

        self.backup_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.backup_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.backup_table.setAlternatingRowColors(True)  # Enable alternating row colors

        # Ensure scrollbars are enabled if content exceeds visible area
        self.backup_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.backup_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        backup_layout.addWidget(self.backup_table)

        # View Configuration Tab
        self.config_text_edit = QTextEdit()
        self.config_text_edit.setReadOnly(True)
        self.config_text_edit.setObjectName("configText")

        tabs.addTab(performance_tab, IconManager.get_icon("chip"), "Live Performance")
        tabs.addTab(interfaces_tab, IconManager.get_icon("interfaces"), "Interfaces")
        tabs.addTab(backup_history_tab, IconManager.get_icon("backup_ok"), "Backup History")
        tabs.addTab(self.config_text_edit, IconManager.get_icon("view"), "View Configuration")
        return tabs

    def _load_backup_history(self):
        self.backup_table.setRowCount(0); self.config_text_edit.clear()
        if self.current_device_id is None: return
        self.backups = db_manager.get_backups_for_device(self.current_device_id)
        if not self.backups: self.config_text_edit.setPlaceholderText("No backups found for this device."); return
        
        self.backup_table.setRowCount(len(self.backups))
        for row, backup in enumerate(self.backups):
            # Column 0: Timestamp
            timestamp_item = QTableWidgetItem(backup['timestamp'])
            timestamp_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.backup_table.setItem(row, 0, timestamp_item)
            
            # Column 1: Status (using custom widget with indicator)
            status_text = backup.get("status", "Success") # Default to Success if not specified
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.backup_table.setItem(row, 1, status_item)
            
            # Column 2: Actions (using a hyperlink)
            export_link = QLabel('<a href="#">Export</a>')
            export_link.setOpenExternalLinks(False)
            export_link.setTextInteractionFlags(Qt.TextBrowserInteraction)
            export_link.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            export_link.linkActivated.connect(lambda _, r=row: self._export_backup_config(r))
            self.backup_table.setCellWidget(row, 2, export_link)

        # Automatically show the latest backup config if available
        if self.backups: self._show_backup_config(0)
        app_logger.get_logger().debug(f"Loaded backup history for device ID: {self.current_device_id}")

    def _load_interface_data(self):
        """Initiates the background SNMP query for interface data."""
        app_logger.get_logger().info(f"_load_interface_data called for device: {self.current_device_info}")
        
        if getattr(self, "snmp_thread", None) and self.snmp_thread.isRunning():
            return # A query is already in progress
        
        app_logger.get_logger().info(f"Device info keys: {list(self.current_device_info.keys())}")
        
        # Show a loading message
        self.interface_table.setRowCount(1)
        loading_item = QTableWidgetItem("Fetching interface data via SNMP...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.interface_table.setItem(0, 0, loading_item)
        self.interface_table.setSpan(0, 0, 1, self.interface_table.columnCount())
        app_logger.get_logger().debug(f"Initiating SNMP data load for device: {self.current_device_info.get('ip', 'N/A')}")

        app_logger.get_logger().info(f"Creating SNMP worker with device info: {self.current_device_info}")
        
        self.snmp_thread = QThread()
        worker = SNMPWorker(self.current_device_info)
        worker.moveToThread(self.snmp_thread)

        worker.success.connect(self._on_snmp_success)
        worker.error.connect(self._on_snmp_error)
        worker.finished.connect(self.snmp_thread.quit)
        worker.finished.connect(worker.deleteLater)
        self.snmp_thread.finished.connect(self.snmp_thread.deleteLater)
        self.snmp_thread.finished.connect(lambda: setattr(self, "snmp_thread", None))
        
        self.snmp_thread.started.connect(worker.run)
        self.snmp_thread.start()
        
        app_logger.get_logger().info("SNMP thread started successfully")

    def _on_snmp_success(self, interfaces: list):
        """Populates the interface table upon successful SNMP query."""
        self.interface_table.setRowCount(0) # Clear loading message
        if not interfaces:
            self._on_snmp_error("No interfaces found or device did not respond.")
            app_logger.get_logger().warning(f"No SNMP interfaces found for device {self.current_device_info.get('ip', 'N/A')}.")
            return

        self.interface_table.setRowCount(len(interfaces))
        for row, iface in enumerate(interfaces):
            # Column 0: Interface Name
            self.interface_table.setItem(row, 0, QTableWidgetItem(iface['Description']))
            # Column 1: Operational Status
            self.interface_table.setCellWidget(row, 1, self._create_status_widget(iface['OpStatus']))
            # Column 2: Admin Status
            self.interface_table.setCellWidget(row, 2, self._create_status_widget(iface['AdminStatus'], admin=True))
            # Column 3: VLAN (UPDATED: Changed from Uptime to VLAN)
            vlan_info = iface.get("VLAN", "N/A")
            vlan_item = QTableWidgetItem(str(vlan_info))
            vlan_item.setTextAlignment(Qt.AlignCenter)
            # Color code VLAN cells for better visibility
            if vlan_info != "N/A" and str(vlan_info).isdigit():
                # Give VLAN cells a subtle background color
                vlan_item.setBackground(QColor(Style.DARK_ACCENT_PRIMARY).lighter(170))
            self.interface_table.setItem(row, 3, vlan_item)
            # Column 4: Traffic
            traffic_text = f"{self._format_bytes(iface['InOctets'])} / {self._format_bytes(iface['OutOctets'])}"
            self.interface_table.setItem(row, 4, QTableWidgetItem(traffic_text))
            # Column 5: Power
            power_status = iface.get("Power", "N/A")
            self.interface_table.setItem(row, 5, QTableWidgetItem(str(power_status)))

        app_logger.get_logger().debug(f"Successfully loaded {len(interfaces)} interfaces for device {self.current_device_info.get('ip', 'N/A')}")

    def _on_snmp_error(self, message: str):
        """Displays an error message in the interface table."""
        self.interface_table.setRowCount(1)
        error_item = QTableWidgetItem(f"Error: {message}")
        error_item.setTextAlignment(Qt.AlignCenter)
        error_item.setForeground(QColor(Style.STATUS_RED))
        self.interface_table.setItem(0, 0, error_item)
        self.interface_table.setSpan(0, 0, 1, self.interface_table.columnCount())
        QMessageBox.critical(self, "SNMP Error", message)
        app_logger.get_logger().error(
            f"SNMP interface data load failed for device {self.current_device_info.get('ip', 'N/A')}: {message}"
        )

    def _create_status_widget(self, status_code: int, admin=False):
        """Creates a colored status indicator widget for the interface table."""
        status_map = {1: "Up", 2: "Down", 3: "Testing"}
        color_map = {1: Style.STATUS_GREEN, 2: Style.STATUS_RED, 3: Style.STATUS_YELLOW}
        
        text = status_map.get(status_code, "Unknown")
        color = color_map.get(status_code, Style.DARK_TEXT_DISABLED)

        widget = QWidget(); layout = QHBoxLayout(widget); layout.setContentsMargins(5, 0, 5, 0); layout.setSpacing(8)
        indicator = QFrame(); indicator.setFixedSize(10, 10)
        indicator.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        label = QLabel(text)
        
        layout.addWidget(indicator); layout.addWidget(label); layout.addStretch()
        return widget

    def _create_backup_status_widget(self, status_text: str):
        """Creates a colored status indicator widget for the backup history table."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Align content to left and center vertically
        layout.setSpacing(8)

        indicator = QFrame()
        indicator.setObjectName("status-indicator") # Object name for styling
        
        # Map status text to a CSS class property for dynamic styling
        if status_text.lower() == "success":
            indicator.setProperty("status", "success")
        elif status_text.lower() == "failed" or status_text.lower() == "error":
            indicator.setProperty("status", "failure")
        else:
            indicator.setProperty("status", "pending") # Or 'info' for other statuses

        indicator.setFixedSize(10, 10) # Small circular indicator

        label = QLabel(status_text)
        label.setMinimumWidth(70) 
        label.setStyleSheet(f"color: {Style.DARK_TEXT_PRIMARY};") # Ensure text color is primary

        layout.addWidget(indicator)
        layout.addWidget(label)
        layout.addStretch() # Push content to the left

        return widget

    def _create_backup_action_button(self, button_text: str, icon_name: str, row_index: int, action_function):
        """
        Creates a styled action button for the backup history table.
        Args:
            button_text (str): The text to display on the button.
            icon_name (str): The name of the icon to use from IconManager.
            row_index (int): The row index associated with this button's action.
            action_function (callable): The function to connect to the button's clicked signal.
        """
        button = QPushButton(button_text)
        button.setObjectName("backupActionButton") # Object name for styling
        button.setIcon(IconManager.get_icon(icon_name)) # Add an icon
        button.setMinimumWidth(70)
        button.setMaximumWidth(90)  # Prevent oversized buttons when localized
        button.clicked.connect(lambda checked=False, r=row_index: action_function(r))
        return button

    def _format_bytes(self, num_bytes):
        """Format bytes into human readable format with safety checks."""
        try:
            # Ensure we have a numeric value
            if isinstance(num_bytes, str):
                try:
                    num_bytes = int(num_bytes)
                except (ValueError, TypeError):
                    return "0 B"
            
            # Handle None or other non-numeric types
            if num_bytes is None or not isinstance(num_bytes, (int, float)):
                return "0 B"
            
            # Convert to int if it's a float
            num_bytes = int(num_bytes)
            
            # Format the bytes
            if num_bytes < 1024:
                return f"{num_bytes} B"
            elif num_bytes < 1024**2:
                return f"{num_bytes/1024:.1f} KB"
            elif num_bytes < 1024**3:
                return f"{num_bytes/(1024**2):.1f} MB"
            elif num_bytes < 1024**4:
                return f"{num_bytes/(1024**3):.1f} GB"
            else:
                return f"{num_bytes/(1024**4):.1f} TB"
                
        except Exception as e:
            app_logger.get_logger().warning(f"Error formatting bytes value '{num_bytes}': {e}")
            return "0 B"
    
    def _show_backup_config(self, index: int):
        """Display the configuration text from the selected backup in the text viewer."""
        if not self.backups or index >= len(self.backups):
            self.config_text_edit.setPlainText("Backup data not found.")
            return

        backup = self.backups[index]
        config_text = backup.get("configuration", "No configuration available.")
        self.config_text_edit.setPlainText(config_text)

    def _export_backup_config(self, index: int):
        """Allows the user to save the selected backup config to a text file."""
        if not self.backups or index >= len(self.backups):
            QMessageBox.warning(self, "Export Failed", "Backup data not found.")
            return

        backup = self.backups[index]
        config_text = backup.get("configuration", "")
        default_name = f"{self.current_device_info.get('name', 'backup')}_{backup['timestamp'].replace(':','-').replace(' ', '_')}.txt"

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Configuration", default_name, "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(config_text)
                QMessageBox.information(self, "Export Successful", "Backup configuration exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to save file: {e}")

    def _format_ticks(self, ticks_raw: str) -> str:
        """Converts SNMP ticks (1/100ths of seconds) into readable uptime."""
        try:
            ticks = int(ticks_raw)
            seconds = ticks // 100
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        except:
            return "N/A"