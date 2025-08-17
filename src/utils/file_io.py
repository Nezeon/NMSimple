# utils/file_io.py
import os
from datetime import datetime

class FileIO:
    @staticmethod
    def save_text_to_file(directory, filename, content):
        """Saves string content to a file."""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"File saved: {filepath}"
        except Exception as e:
            return False, f"Error saving file {filepath}: {e}"

    @staticmethod
    def load_text_from_file(filepath):
        """Loads string content from a file."""
        if not os.path.exists(filepath):
            return None, "File not found."
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, "File loaded successfully."
        except Exception as e:
            return None, f"Error loading file {filepath}: {e}"

    @staticmethod
    def create_timestamped_folder(base_path):
        """Creates a timestamped subfolder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_path = os.path.join(base_path, timestamp)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path