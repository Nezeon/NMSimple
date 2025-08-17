# ui/components/toast.py
# Description: A custom widget for displaying non-blocking toast notifications.
# Location: This file should be in the 'ui/components' folder.

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, Signal
from PySide6.QtGui import QFont

from ui.icon_manager import IconManager

class Toast(QFrame):
    """
    A custom toast notification widget.
    """
    closed = Signal(object) # Signal emits itself when closed

    def __init__(self, parent, message, toast_type='info', duration=4000):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumWidth(320)
        self.setObjectName("ToastFrame")
        self.setProperty("toast_type", toast_type)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        icon_name = {
            'success': 'online', # Reusing the checkmark icon
            'error': 'offline', # Reusing the cross icon
            'info': 'info'
        }.get(toast_type, 'info')
        
        icon_label = QLabel()
        icon_label.setPixmap(IconManager.get_icon(icon_name).pixmap(22, 22))
        
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setObjectName("toastMessage")

        layout.addWidget(icon_label)
        layout.addWidget(message_label, 1)

        self.animation = QPropertyAnimation(self, b"pos", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(300)

        QTimer.singleShot(duration, self.hide_toast)

    def show_toast(self):
        start_pos = QPoint(self.parent.width(), self.y())
        end_pos = QPoint(self.parent.width() - self.width() - 15, self.y())
        self.move(start_pos)
        self.show()
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()

    def hide_toast(self):
        start_pos = self.pos()
        end_pos = QPoint(self.parent.width(), self.y())
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.finished.connect(self.close)
        self.animation.start()
    
    def closeEvent(self, event):
        self.closed.emit(self)
        super().closeEvent(event)
