# add_device_dialog.py
# Description: A dialog window for adding or editing a device.
# Changes:
# - The constructor now accepts optional 'device_data' to pre-fill the form for editing.
# - The window title changes dynamically to "Add New Device" or "Edit Device".

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QDialogButtonBox, QMessageBox
)
from PySide6.QtWidgets import QScrollArea, QWidget


class AddDeviceDialog(QDialog):
    def __init__(self, parent=None, device_data=None):
        super().__init__(parent)

        self.is_edit_mode = device_data is not None
        title = "Edit Device" if self.is_edit_mode else "Add New Device"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        # --- Form Widgets ---
        self.name_input = QLineEdit()
        self.ip_input = QLineEdit()
        self.model_input = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Online", "Offline", "Warning", "Unknown"])
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.snmp_input = QLineEdit()

        # --- Content Widget inside Scroll Area ---
        content_widget = QWidget()
        form_layout = QVBoxLayout(content_widget)
        form_layout.setSpacing(15)
        form_layout.addWidget(QLabel("Device Name:"))
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(QLabel("IP Address:"))
        form_layout.addWidget(self.ip_input)
        form_layout.addWidget(QLabel("Model:"))
        form_layout.addWidget(self.model_input)
        form_layout.addWidget(QLabel("Status:"))
        form_layout.addWidget(self.status_combo)
        form_layout.addWidget(QLabel("SSH Username:"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("SSH Password:"))
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(QLabel("SNMP Community:"))
        form_layout.addWidget(self.snmp_input)

        # --- Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        form_layout.addWidget(button_box)

        # --- Scroll Area ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        # --- Pre-fill data if in edit mode ---
        if self.is_edit_mode:
            self.name_input.setText(device_data.get("name", ""))
            self.ip_input.setText(device_data.get("ip", ""))
            self.model_input.setText(device_data.get("model", ""))
            self.status_combo.setCurrentText(device_data.get("status", "Unknown"))
            self.username_input.setText(device_data.get("username", ""))
            self.password_input.setText(device_data.get("password", ""))
            self.snmp_input.setText(device_data.get("snmp_community", ""))

    def accept(self):
        if not self.name_input.text() or not self.ip_input.text():
            QMessageBox.warning(self, "Missing Information", "Device Name and IP Address are required.")
            return
        super().accept()

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "ip": self.ip_input.text(),
            "model": self.model_input.text(),
            "status": self.status_combo.currentText(),
            "username": self.username_input.text(),
            "password": self.password_input.text(),
            "snmp_community": self.snmp_input.text(),
        }
