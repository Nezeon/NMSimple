# ui/icon_manager.py

import os
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPainterPath, QFont
from PySide6.QtCore import Qt, QDir, QPointF, QRectF

from ui.styles import Style

class IconManager:
    _icons = {}
    _icon_path = ""
    _color = QColor("#00E5FF")

    @staticmethod
    def _initialize_path():
        if not IconManager._icon_path:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            IconManager._icon_path = os.path.join(project_root, "resources", "icons")

    @staticmethod
    def get_icon(name: str, color: QColor = None) -> QIcon:
        cache_key = f"{name}_{color.name()}" if color else name
        if cache_key in IconManager._icons:
            return IconManager._icons[cache_key]
        IconManager._initialize_path()
        icon_path = os.path.join(IconManager._icon_path, f"{name}.svg")
        if os.path.exists(icon_path) and not color:
            icon = QIcon(icon_path)
            IconManager._icons[name] = icon
            return icon
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(color if color else IconManager._color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        draw_func = getattr(IconManager, f"_draw_{name}_icon", IconManager._draw_default_icon)
        draw_func(painter)
        painter.end()
        placeholder_icon = QIcon(pixmap)
        IconManager._icons[cache_key] = placeholder_icon
        return placeholder_icon

    # --- Icon Drawing Methods ---
    @staticmethod
    def _draw_default_icon(p: QPainter): p.drawRect(8, 8, 16, 16)
    @staticmethod
    def _draw_dashboard_icon(p: QPainter): p.drawRect(7, 7, 8, 8); p.drawRect(17, 7, 8, 8); p.drawRect(7, 17, 8, 8); p.drawRect(17, 17, 8, 8)
    @staticmethod
    def _draw_switches_icon(p: QPainter): p.drawLine(6, 16, 26, 16); p.drawLine(10, 12, 10, 20); p.drawLine(16, 12, 16, 20); p.drawLine(22, 12, 22, 20)
    @staticmethod
    def _draw_settings_icon(p: QPainter): p.drawEllipse(QRectF(8, 8, 16, 16)); p.drawLine(16, 6, 16, 10); p.drawLine(16, 22, 16, 26); p.drawLine(6, 16, 10, 16); p.drawLine(22, 16, 26, 16)
    @staticmethod
    def _draw_logs_icon(p: QPainter): p.drawRect(8, 6, 16, 20); p.drawLine(12, 12, 20, 12); p.drawLine(12, 18, 20, 18); p.drawLine(12, 24, 16, 24)
    @staticmethod
    def _draw_help_icon(p: QPainter): p.drawEllipse(QRectF(6, 6, 20, 20)); p.setFont(QFont("Roboto", 14, QFont.Bold)); p.drawText(QRectF(6, 6, 20, 20), Qt.AlignCenter, "?")
    @staticmethod
    def _draw_refresh_icon(p: QPainter): path = QPainterPath(); path.arcTo(QRectF(7, 7, 18, 18), 90, -270); p.drawPath(path); p.drawLine(7, 16, 11, 20); p.drawLine(7, 16, 3, 12)
    @staticmethod
    def _draw_total_devices_icon(p: QPainter): p.drawRect(7, 13, 18, 10); p.drawRect(10, 9, 12, 4)
    @staticmethod
    def _draw_online_icon(p: QPainter): pen = p.pen(); pen.setColor(QColor(Style.STATUS_GREEN)); p.setPen(pen); p.drawPolyline([QPointF(9, 16), QPointF(14, 21), QPointF(23, 12)])
    @staticmethod
    def _draw_alert_icon(p: QPainter): pen = p.pen(); pen.setColor(QColor(Style.STATUS_RED)); p.setPen(pen); p.drawLine(16, 8, 16, 18); p.drawPoint(16, 22)
    @staticmethod
    def _draw_backup_ok_icon(p: QPainter): IconManager._draw_online_icon(p)
    @staticmethod
    def _draw_config_icon(p: QPainter): IconManager._draw_settings_icon(p)
    @staticmethod
    def _draw_warning_icon(p: QPainter): pen = p.pen(); pen.setColor(QColor(Style.STATUS_YELLOW)); p.setPen(pen); p.drawLine(8, 24, 16, 8); p.drawLine(16, 8, 24, 24); p.drawLine(8, 24, 24, 24); p.drawPoint(16, 20)
    @staticmethod
    def _draw_offline_icon(p: QPainter): pen = p.pen(); pen.setColor(QColor(Style.STATUS_RED)); p.setPen(pen); p.drawLine(10, 10, 22, 22); p.drawLine(10, 22, 22, 10)
    @staticmethod
    def _draw_add_icon(p: QPainter): p.drawLine(16, 9, 16, 23); p.drawLine(9, 16, 23, 16)
    @staticmethod
    def _draw_save_icon(p: QPainter): p.drawRect(8, 8, 16, 16); p.drawRect(12, 8, 8, 8); p.drawLine(14, 20, 18, 20)
    @staticmethod
    def _draw_api_icon(p: QPainter): p.drawLine(10, 13, 15, 8); p.drawLine(10, 19, 15, 24); p.drawLine(17, 8, 22, 13); p.drawLine(17, 24, 22, 19)
    @staticmethod
    def _draw_notification_icon(p: QPainter): p.drawRect(8, 10, 16, 12); path = QPainterPath(); path.moveTo(8, 10); path.arcTo(QRectF(8, 6, 16, 8), 180, -180); p.drawPath(path); p.drawEllipse(15, 5, 2, 2)
    @staticmethod
    def _draw_ui_icon(p: QPainter): p.drawRect(7, 9, 18, 14); p.drawLine(7, 14, 25, 14)
    @staticmethod
    def _draw_back_arrow_icon(p: QPainter): p.drawLine(20, 16, 8, 16); p.drawLine(13, 11, 8, 16); p.drawLine(13, 21, 8, 16)
    @staticmethod
    def _draw_delete_icon(p: QPainter): pen = p.pen(); pen.setColor(QColor(Style.STATUS_RED)); p.setPen(pen); p.drawLine(10, 10, 22, 22); p.drawLine(10, 22, 22, 10)
    # --- NEW: Edit Icon ---
    @staticmethod
    def _draw_edit_icon(p: QPainter):
        path = QPainterPath()
        path.moveTo(22, 8)
        path.lineTo(14, 24)
        path.lineTo(8, 18)
        path.lineTo(16, 2)
        path.closeSubpath()
        p.drawPath(path)
        p.drawLine(12, 20, 10, 22)

    @staticmethod
    def _draw_info_icon(p: QPainter):
        p.drawEllipse(QRectF(7, 7, 18, 18))
        p.setFont(QFont("Roboto", 12, QFont.Bold))
        p.drawText(QRectF(7, 7, 18, 18), Qt.AlignCenter, "i")

    @staticmethod
    def _draw_scheduler_icon(p: QPainter):
        p.drawEllipse(QRectF(7, 7, 18, 18))
        p.drawLine(16, 16, 16, 8)
        p.drawLine(16, 16, 20, 20)
    
    # Add these methods inside the IconManager class in ui/icon_manager.py
    @staticmethod
    def _draw_ip_address_icon(p: QPainter):
        p.drawLine(8, 16, 24, 16)
        p.drawLine(12, 12, 12, 20)
        p.drawLine(20, 12, 20, 20)
    @staticmethod
    def _draw_chip_icon(p: QPainter):
        p.drawRect(8, 8, 16, 16)
        p.drawLine(8, 12, 4, 12)
        p.drawLine(8, 20, 4, 20)
        p.drawLine(24, 12, 28, 12)
        p.drawLine(24, 20, 28, 20)
    @staticmethod
    def _draw_status_icon(p: QPainter):
        p.drawEllipse(QRectF(8, 12, 16, 16))
        p.drawLine(16, 12, 16, 4)
    @staticmethod
    def _draw_reboot_icon(p: QPainter):
        path = QPainterPath()
        path.arcTo(QRectF(7, 7, 18, 18), 45, 270)
        p.drawPath(path)
        p.drawLine(21, 10, 25, 6)
        p.drawLine(21, 10, 17, 6)

    @staticmethod
    def _draw_view_icon(p: QPainter):
        path = QPainterPath()
        path.moveTo(6, 16)
        path.cubicTo(6, 16, 16, 8, 26, 16)
        path.cubicTo(26, 16, 16, 24, 6, 16)
        p.drawPath(path)
        p.drawEllipse(QRectF(12, 12, 8, 8))

    # --- NEW: Icon for the Interfaces Tab ---
    @staticmethod
    def _draw_interfaces_icon(p: QPainter):
        """Draws an icon representing network interfaces/ports."""
        p.drawRect(6, 14, 20, 4) # Main switch body
        p.drawLine(10, 14, 10, 10) # Port 1
        p.drawLine(16, 14, 16, 10) # Port 2
        p.drawLine(22, 14, 22, 10) # Port 3

