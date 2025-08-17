# config/app_config.py
import json
import os

class AppConfig:
    _config = {}
    _config_path = "config.json" # This file will be created in your root folder

    @staticmethod
    def load_config():
        """
        Loads configuration from a JSON file.
        If the file doesn't exist, it creates one with default values.
        """
        if os.path.exists(AppConfig._config_path):
            try:
                with open(AppConfig._config_path, 'r') as f:
                    AppConfig._config = json.load(f)
            except json.JSONDecodeError:
                print("Warning: config.json is corrupted. Loading defaults.")
                AppConfig._create_default_config()
        else:
            AppConfig._create_default_config()

    @staticmethod
    def _create_default_config():
        """Sets up the default configuration and saves it."""
        AppConfig._config = {
            "theme": "light",
            "backup_path": os.path.join(os.getcwd(), "backups"),
            "auto_backup": False,
            "email_notifications": True
        }
        AppConfig.save_config()

    @staticmethod
    def save_config():
        """Saves the current configuration to the JSON file."""
        with open(AppConfig._config_path, 'w') as f:
            json.dump(AppConfig._config, f, indent=4)

    @staticmethod
    def get_setting(key, default=None):
        """Gets a specific setting by key."""
        return AppConfig._config.get(key, default)

    @staticmethod
    def set_setting(key, value):
        """Sets a specific setting and saves the config."""
        AppConfig._config[key] = value
        AppConfig.save_config()
