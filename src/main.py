# main.py
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from ui.main_window import MainWindow

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Updated font loading for PyInstaller compatibility
    font_path = resource_path("resources/fonts/Roboto-Regular.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)
    
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        print(f"Successfully loaded font: {font_family}")
    else:
        print(f"Warning: Could not load font from {font_path}. Using system default.")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
