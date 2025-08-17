# logs_page.py
# Description: A new page to display real-time application logs.
# Features:
# - A filterable table for log entries.
# - Color-coded log levels for easy identification.
# - Buttons to filter by log level and a search bar.
# - Connects to the AppLogger to receive and display logs in real-time.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QLineEdit,
    QPushButton, QTableWidget, QHeaderView, QAbstractItemView,
    QTableWidgetItem, QButtonGroup, QGraphicsDropShadowEffect, QMessageBox # Added QMessageBox for confirmation
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from datetime import datetime # Import datetime for the clear logs message

from ui.icon_manager import IconManager
from ui.styles import Style
from utils.database import db_manager
from utils.logger import app_logger # Keep this import

class LogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logsPage")

        # FIX: Store logger instance as an instance variable
        self.logger = app_logger.get_logger()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # --- FIX: Create the table panel FIRST so self.table exists ---
        table_panel = self._create_table_panel()
        
        # Now create the header, which can safely connect to self.table
        header_layout = self._create_header()
        
        main_layout.addLayout(header_layout)
        main_layout.addWidget(table_panel)

        # NEW: Load historical logs on startup
        self._load_historical_logs()

    def _create_header(self):
        """Creates the header with title, filters, and action buttons."""
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Event Logs")
        title_label.setObjectName("pageTitle")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self._filter_table)

        # Filter buttons
        self.filter_button_group = QButtonGroup(self)
        self.filter_button_group.setExclusive(True)

        btn_all = QPushButton("All"); btn_all.setObjectName("filterButton"); btn_all.setCheckable(True); btn_all.setChecked(True)
        btn_info = QPushButton("Info"); btn_info.setObjectName("filterButton"); btn_info.setCheckable(True)
        btn_warning = QPushButton("Warning"); btn_warning.setObjectName("filterButton"); btn_warning.setCheckable(True)
        btn_error = QPushButton("Error"); btn_error.setObjectName("filterButton"); btn_error.setCheckable(True)

        self.filter_button_group.addButton(btn_all, 0)
        self.filter_button_group.addButton(btn_info, 1)
        self.filter_button_group.addButton(btn_warning, 2)
        self.filter_button_group.addButton(btn_error, 3)
        self.filter_button_group.buttonClicked.connect(self._filter_table)

        clear_button = QPushButton("Clear Logs")
        clear_button.setIcon(IconManager.get_icon("delete")) # Changed icon to delete for clarity
        # NEW: Connect clear button to a new method that clears DB
        clear_button.clicked.connect(self._clear_all_logs)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.search_input)
        header_layout.addWidget(btn_all); header_layout.addWidget(btn_info)
        header_layout.addWidget(btn_warning); header_layout.addWidget(btn_error)
        header_layout.addWidget(clear_button)
        return header_layout

    def _create_table_panel(self):
        """Creates the main panel containing the logs table."""
        panel = QFrame()
        panel.setObjectName("PanelWidget")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setObjectName("logsTable")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["LEVEL", "TIMESTAMP", "MESSAGE"])
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setMouseTracking(True)

        panel_layout.addWidget(self.table)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        panel.setGraphicsEffect(shadow)
        
        return panel

    def add_log_record(self, level, timestamp, message):
        """Inserts a new row at the top of the table with the log data."""
        row_position = 0
        self.table.insertRow(row_position)
        
        self.table.setCellWidget(row_position, 0, self._create_level_widget(level))
        self.table.setItem(row_position, 1, QTableWidgetItem(timestamp))
        self.table.setItem(row_position, 2, QTableWidgetItem(message))
        
        self.table.setRowHeight(row_position, 50)
        # Re-apply filter to the new row
        self._filter_table()

    def _create_level_widget(self, level):
        """Creates a styled QLabel for the log level."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setAlignment(Qt.AlignCenter)
        
        level_label = QLabel(level)
        level_label.setObjectName(f"log{level}")
        
        layout.addWidget(level_label)
        return widget

    def _filter_table(self):
        """Filters the table based on the selected level and search text."""
        search_text = self.search_input.text().lower()
        checked_button = self.filter_button_group.checkedButton()
        level_filter = checked_button.text().lower() if checked_button else "all"

        for row in range(self.table.rowCount()):
            level_widget = self.table.cellWidget(row, 0)
            # Ensure level_widget and its child QLabel exist before accessing
            if level_widget and level_widget.findChild(QLabel):
                level_text = level_widget.findChild(QLabel).text().lower()
                message_item = self.table.item(row, 2)
                message_text = message_item.text().lower() if message_item else ""

                level_match = (level_filter == "all" or level_filter == level_text)
                text_match = (search_text == "" or search_text in message_text)

                self.table.setRowHidden(row, not (level_match and text_match))
            else:
                self.table.setRowHidden(row, True) # Hide rows with incomplete data

    # NEW: Method to load historical logs from DB
    def _load_historical_logs(self):
        """Loads all log entries from the database and populates the table."""
        logs = db_manager.get_all_log_entries()
        self.table.setRowCount(0) # Clear existing rows
        for log in logs:
            # Insert at row 0 to keep newest logs at the top
            row_position = 0
            self.table.insertRow(row_position)
            self.table.setCellWidget(row_position, 0, self._create_level_widget(log['level']))
            self.table.setItem(row_position, 1, QTableWidgetItem(log['timestamp']))
            self.table.setItem(row_position, 2, QTableWidgetItem(log['message']))
            self.table.setRowHeight(row_position, 50)
        self._filter_table() # Apply any initial filter

    # NEW: Method to clear logs from DB and UI
    def _clear_all_logs(self):
        """Clears all log entries from the database and the UI table."""
        reply = QMessageBox.warning(self, "Confirm Clear Logs",
                                    "Are you sure you want to clear ALL log entries? This action cannot be undone.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            db_manager.clear_all_log_entries()
            self.table.setRowCount(0) # Clear UI table
            self.logger.info("All application logs cleared.") # FIX: Use self.logger
            # Re-add a message if no logs are present after clearing
            if self.table.rowCount() == 0:
                self.add_log_record("INFO", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Logs have been cleared.")

