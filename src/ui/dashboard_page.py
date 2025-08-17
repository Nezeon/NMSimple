# ui/dashboard_page.py
# Description: The main dashboard view, now with live data.
# Changes:
# - Imports the database manager.
# - Adds a `refresh_data` method to query the database and update UI elements.
# - Stat cards and the donut chart are now instance variables to be updated dynamically.
# - The DonutChartWidget has a new `set_values` method to accept live data.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QPushButton, QGridLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, Property, QEasingCurve, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QConicalGradient

# --- NEW: Import the database manager ---
from utils.database import db_manager
from utils.logger import app_logger
from ui.icon_manager import IconManager

class DonutChartWidget(QWidget):
    """A custom, animated donut chart widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(250)
        self.values = []
        self._animation_progress = 0
        self.animation = QPropertyAnimation(self, b"animationProgress", self)
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

    def set_values(self, values: list):
        """Sets the data for the chart and restarts the animation."""
        self.values = values
        self.animation.stop()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        self.update()

    @Property(float)
    def animationProgress(self):
        return self._animation_progress

    @animationProgress.setter
    def animationProgress(self, value):
        self._animation_progress = value
        self.update()

    def paintEvent(self, event):
        if not self.values:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height())
        rect = self.rect().adjusted(side / 4, side / 4, -side / 4, -side / 4)
        pen_width = 25
        painter.setPen(Qt.NoPen)
        total_value = sum(item['value'] for item in self.values)
        if total_value == 0: return # Avoid division by zero
        start_angle = 90 * 16
        for item in self.values:
            angle = (item['value'] / total_value) * 360
            span_angle = -angle * 16 * self._animation_progress
            gradient = QConicalGradient(rect.center(), start_angle / 16)
            gradient.setColorAt(0, item["color"].lighter(120))
            gradient.setColorAt(1, item["color"])
            pen = QPen(gradient, pen_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(rect, int(start_angle), int(span_angle))
            start_angle += span_angle
        
        # Draw inner text for the largest segment (usually "Online")
        online_value = next((item['value'] for item in self.values if item['label'] == 'Online'), 0)
        percentage = (online_value / total_value) * 100 if total_value > 0 else 0
        font = QFont("Roboto", 24, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect, Qt.AlignCenter, f"{percentage:.0f}%")
        font.setPointSize(12); font.setWeight(QFont.Normal)
        painter.setFont(font)
        painter.setPen(QColor("#9EB0C8"))
        painter.drawText(rect.translated(0, 40), Qt.AlignCenter, "Online")

class CardWidget(QFrame):
    clicked = Signal()
    def __init__(self, title, value, subtext=None, icon_name=None, parent=None):
        super().__init__(parent)
        self.setObjectName("CardWidget"); self.setContentsMargins(20, 20, 20, 20)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred); self.setCursor(Qt.PointingHandCursor)
        layout = QHBoxLayout(self); layout.setSpacing(15)
        if icon_name:
            self.icon_label = QLabel(); self.icon_label.setPixmap(IconManager.get_icon(icon_name).pixmap(36, 36)); layout.addWidget(self.icon_label)
        text_layout = QVBoxLayout(); text_layout.setSpacing(5)
        self.value_label = QLabel(str(value)); self.value_label.setObjectName("cardValue")
        self.title_label = QLabel(title); self.title_label.setObjectName("cardTitle")
        text_layout.addWidget(self.value_label); text_layout.addWidget(self.title_label)
        if subtext:
            self.subtext_label = QLabel(subtext); self.subtext_label.setObjectName("cardSubtext"); text_layout.addWidget(self.subtext_label)
        layout.addLayout(text_layout); layout.addStretch()
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(30); shadow.setColor(QColor(0, 0, 0, 80)); shadow.setOffset(0, 4); self.setGraphicsEffect(shadow)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit()
        super().mousePressEvent(event)
    def set_value(self, value): self.value_label.setText(str(value))
    def set_subtext(self, text):
        if hasattr(self, 'subtext_label'): self.subtext_label.setText(text)

class DashboardPage(QWidget):
    card_clicked = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dashboardPage")
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setSpacing(25)
        self._create_widgets()
        header_layout = QHBoxLayout()
        title_label = QLabel("Dashboard Overview"); title_label.setObjectName("pageTitle")
        refresh_button = QPushButton("Refresh"); refresh_button.setIcon(IconManager.get_icon("refresh")); refresh_button.setObjectName("outlineButton")
        refresh_button.clicked.connect(self.refresh_data) # Connect refresh button
        header_layout.addWidget(title_label); header_layout.addStretch(); header_layout.addWidget(refresh_button)
        main_layout.addLayout(header_layout)
        cards_layout = QGridLayout(); cards_layout.setSpacing(25)
        cards_layout.addWidget(self.card_total_devices, 0, 0); cards_layout.addWidget(self.card_online, 0, 1)
        cards_layout.addWidget(self.card_alerts, 0, 2); cards_layout.addWidget(self.card_backups, 0, 3)
        main_layout.addLayout(cards_layout)
        bottom_layout = QHBoxLayout(); bottom_layout.setSpacing(25)
        bottom_layout.addWidget(self._create_activity_panel(), 5)
        bottom_layout.addWidget(self._create_summary_panel(), 4)
        main_layout.addLayout(bottom_layout); main_layout.addStretch()
        self.refresh_data() # Initial data load

    def _create_widgets(self):
        """Creates the main widgets and stores them as instance variables."""
        self.card_total_devices = CardWidget("Total Devices", "0", icon_name="total_devices")
        self.card_total_devices.clicked.connect(lambda: self.card_clicked.emit(""))
        self.card_online = CardWidget("Devices Online", "0", " ", "online")
        self.card_online.clicked.connect(lambda: self.card_clicked.emit("status:Online"))
        self.card_alerts = CardWidget("Critical Alerts", "0", " ", "alert")
        self.card_alerts.clicked.connect(lambda: self.card_clicked.emit("status:Critical"))
        self.card_backups = CardWidget("Backups OK", "0", " ", "backup_ok")
        self.card_backups.clicked.connect(lambda: self.card_clicked.emit(""))
        self.donut_chart = DonutChartWidget()

    def refresh_data(self):
        """Fetches data from the database and updates the dashboard widgets."""
        app_logger.get_logger().info("Refreshing dashboard data...")
        try:
            devices = db_manager.get_all_devices()
            total_devices = len(devices)
            online_count = len([d for d in devices if d['status'] == 'Online'])
            warning_count = len([d for d in devices if d['status'] == 'Warning'])
            offline_count = len([d for d in devices if d['status'] == 'Offline'])
            critical_count = warning_count + offline_count
            backups_ok_count = len([d for d in devices if 'Never' not in d['last_backup']])

            # Update stat cards
            self.card_total_devices.set_value(total_devices)
            self.card_online.set_value(f"{online_count} / {total_devices}")
            self.card_alerts.set_value(critical_count)
            self.card_backups.set_value(backups_ok_count)

            # Update donut chart
            chart_values = [
                {"label": "Online", "value": online_count, "color": QColor("#00E5FF")},
                {"label": "Warning", "value": warning_count, "color": QColor("#FFC107")},
                {"label": "Offline", "value": offline_count, "color": QColor("#F44336")}
            ]
            self.donut_chart.set_values(chart_values)

        except Exception as e:
            app_logger.get_logger().error(f"Failed to refresh dashboard data: {e}")

    def _create_summary_panel(self):
        panel, layout = self._create_panel("Device Status Summary")
        layout.addWidget(self.donut_chart) # Add the instance variable
        legend_layout = QHBoxLayout(); legend_layout.setSpacing(20); legend_layout.addStretch()
        legend_layout.addWidget(self._create_legend_item("#00E5FF", "Online"))
        legend_layout.addWidget(self._create_legend_item("#FFC107", "Warning"))
        legend_layout.addWidget(self._create_legend_item("#F44336", "Offline"))
        legend_layout.addStretch(); layout.addLayout(legend_layout)
        return panel

    # --- Helper methods (no changes) ---
    def _create_panel(self, title):
        panel = QFrame(); panel.setObjectName("PanelWidget"); layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 20, 25, 25); layout.setSpacing(15); header = QLabel(title); header.setObjectName("panelTitle")
        layout.addWidget(header); shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(30); shadow.setColor(QColor(0, 0, 0, 80)); shadow.setOffset(0, 4); panel.setGraphicsEffect(shadow)
        return panel, layout
    def _create_activity_panel(self):
        panel, layout = self._create_panel("Recent Activity")
        self._add_activity_item(layout, "config", "Config Updated", "Core Switch 192.168.1.24", "Today, 18:42")
        self._add_activity_item(layout, "backup_ok", "Backup Success", "All devices - Scheduled", "Today, 14:30")
        self._add_activity_item(layout, "warning", "High CPU Usage", "Access Switch 192.168.1.12", "Today, 11:15")
        self._add_activity_item(layout, "offline", "Device Offline", "Access Switch Floor 3", "Today, 09:22")
        self._add_activity_item(layout, "add", "New Device Added", "Access Switch Floor 5", "Yesterday, 18:47")
        layout.addStretch(); return panel
    def _add_activity_item(self, layout, icon_name, title, subtitle, time):
        item_layout = QHBoxLayout(); item_layout.setSpacing(15); icon_label = QLabel(); icon_label.setPixmap(IconManager.get_icon(icon_name).pixmap(24, 24)); icon_label.setObjectName("activityIcon")
        text_layout = QVBoxLayout(); text_layout.setSpacing(2); title_label = QLabel(title); title_label.setObjectName("activityTitle"); subtitle_label = QLabel(subtitle); subtitle_label.setObjectName("activitySubtext")
        text_layout.addWidget(title_label); text_layout.addWidget(subtitle_label); time_label = QLabel(time); time_label.setObjectName("activityTime"); time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        item_layout.addWidget(icon_label); item_layout.addLayout(text_layout); item_layout.addStretch(); item_layout.addWidget(time_label); layout.addLayout(item_layout)
    def _create_legend_item(self, color, text):
        item_layout = QHBoxLayout(); item_layout.setSpacing(8); color_box = QFrame(); color_box.setFixedSize(12, 12); color_box.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
        label = QLabel(text); label.setObjectName("legendLabel"); item_layout.addWidget(color_box); item_layout.addWidget(label); widget = QWidget(); widget.setLayout(item_layout); return widget
