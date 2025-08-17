# ui/main_window.py
# Description: Main application window.
# Changes:
# - Corrected all local imports to be absolute (e.g., 'ui.toast') to ensure they work correctly
#   when the application is run from the root directory.
# - ADDED: Automatic status check for all devices on application startup.
# - FIX: Corrected method call for initial status check from 'run_status_check' to '_run_status_check'.

import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QListWidget, QListWidgetItem, QStackedWidget,
                               QLabel, QFrame, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QIcon

from utils.logger import app_logger
from utils.scheduler import scheduler_manager
# --- FIX: Corrected import path after moving toast.py ---
from ui.toast import Toast
from ui.logs_page import LogsPage
from ui.dashboard_page import DashboardPage
from ui.switch import DevicesPage
from ui.device_detail_page import DeviceDetailPage
from ui.scheduler_page import SchedulerPage
from ui.styles import Style
from ui.icon_manager import IconManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = app_logger.get_logger()
        self.setWindowTitle("NMSimple - Network Management Suite")
        self.setGeometry(100, 100, 1600, 960)
        self.setStyleSheet(Style.get_stylesheet("dark"))
        self.active_toasts = []
        self._create_widgets()
        self._create_layouts()
        self._connect_signals()
        self._set_initial_page()
        
        scheduler_manager.start()
        
        self.logger.info("Application successfully started.")
        self.show_toast("Welcome to NMSimple Suite!", "info")

        # --- NEW: Trigger initial status check after UI is ready ---
        # This ensures the DevicesPage is fully initialized before the check begins.
        # FIX: Changed to call the correct private method _run_status_check
        self.switch_page._run_status_check()

    def _create_widgets(self):
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.sidebar_frame = QFrame(self.central_widget); self.sidebar_frame.setObjectName("sidebar"); self.sidebar_frame.setFixedWidth(240)
        self.logo_label = QLabel("NMSimple"); self.logo_label.setObjectName("logoLabel"); self.logo_label.setAlignment(Qt.AlignCenter)
        self.nav_list = QListWidget(self.sidebar_frame); self.nav_list.setObjectName("navList"); self.nav_list.setFocusPolicy(Qt.NoFocus)
        self.nav_list.setIconSize(QSize(24, 24)); self.nav_list.setSpacing(8)
        self.nav_list.addItem(QListWidgetItem(IconManager.get_icon("dashboard"), "Dashboard"))
        self.nav_list.addItem(QListWidgetItem(IconManager.get_icon("switches"), "Switch"))
        self.nav_list.addItem(QListWidgetItem(IconManager.get_icon("scheduler"), "Scheduler"))
        self.nav_list.addItem(QListWidgetItem(IconManager.get_icon("logs"), "Logs"))
        
        self.content_area = QStackedWidget(self.central_widget); self.content_area.setObjectName("contentArea")
        self.dashboard_page = DashboardPage(); self.switch_page = DevicesPage();  self.logs_page = LogsPage()
        self.device_detail_page = DeviceDetailPage(); self.scheduler_page = SchedulerPage()
        
        
        self.dashboard_page_index = self.content_area.addWidget(self._create_scrollable_page(self.dashboard_page))
        self.switch_page_index = self.content_area.addWidget(self._create_scrollable_page(self.switch_page))
        self.scheduler_page_index = self.content_area.addWidget(self._create_scrollable_page(self.scheduler_page))
        self.logs_page_index = self.content_area.addWidget(self._create_scrollable_page(self.logs_page))
        self.device_detail_page_index = self.content_area.addWidget(self._create_scrollable_page(self.device_detail_page))

    def _connect_signals(self):
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        self.dashboard_page.card_clicked.connect(self._handle_navigation_filter)
        log_handler = app_logger.get_handler(); log_handler.new_log_record.connect(self.logs_page.add_log_record)
        self.switch_page.device_selected.connect(self._show_device_detail)
        self.device_detail_page.back_clicked.connect(self._show_device_list)
        
        scheduler_manager.trigger_ping_all.connect(self.switch_page.run_status_check_silent)
        scheduler_manager.trigger_backup_all.connect(self.switch_page.run_backup_all_silent)

    def _on_nav_changed(self, index):
        self.content_area.setCurrentIndex(index)
        if index == self.dashboard_page_index: self.dashboard_page.refresh_data()
        if index == self.scheduler_page_index: self.scheduler_page.refresh_jobs_list()

    def closeEvent(self, event):
        scheduler_manager.stop()
        event.accept()

    def _create_layouts(self):
        main_layout = QHBoxLayout(self.central_widget); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        main_layout.addWidget(self.sidebar_frame); main_layout.addWidget(self.content_area, 1)
        sidebar_layout = QVBoxLayout(self.sidebar_frame); sidebar_layout.setContentsMargins(0, 20, 0, 20); sidebar_layout.setSpacing(20)
        sidebar_layout.addWidget(self.logo_label); separator = QFrame(); separator.setFrameShape(QFrame.HLine); separator.setObjectName("separator")
        sidebar_layout.addWidget(separator); sidebar_layout.addWidget(self.nav_list); sidebar_layout.addStretch()
    def _create_scrollable_page(self, page_widget):
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setWidget(page_widget); scroll_area.setObjectName("scrollArea")
        return scroll_area
    def show_toast(self, message, toast_type='info'):
        toast = Toast(self, message, toast_type)
        y_pos = self.height() - (len(self.active_toasts) + 1) * (toast.height() + 10) - 10
        toast.move(self.width(), y_pos)
        toast.closed.connect(self._remove_toast); self.active_toasts.append(toast); toast.show_toast()
    def _remove_toast(self, toast_to_remove):
        try: self.active_toasts.remove(toast_to_remove)
        except ValueError: pass
        self._reposition_toasts()
    def _reposition_toasts(self):
        for i, toast in enumerate(self.active_toasts):
            new_y = self.height() - (i + 1) * (toast.height() + 10) - 10
            anim = QPropertyAnimation(toast, b"pos", self); anim.setEndValue(QPoint(toast.x(), new_y)); anim.setDuration(200); anim.setEasingCurve(QEasingCurve.InOutQuad); anim.start()
    def _show_device_detail(self, device_info: dict):
        self.device_detail_page.load_device_data(device_info); self.content_area.setCurrentIndex(self.device_detail_page_index)
    def _show_device_list(self): self.content_area.setCurrentIndex(self.switch_page_index)
    def _handle_navigation_filter(self, query: str):
        self.logger.info(f"Navigating to Switch page with filter: '{query}'")
        self.nav_list.blockSignals(True); self.nav_list.setCurrentRow(self.switch_page_index); self.nav_list.blockSignals(False)
        self._on_nav_changed(self.switch_page_index); self.switch_page.set_filter(query)
    def _set_initial_page(self): self.nav_list.setCurrentRow(0)

