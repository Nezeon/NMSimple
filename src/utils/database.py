# utils/database.py
# Description: Manages all database operations for the application.

import os
import sys
import sqlite3


class DatabaseManager:
    _instance = None
    _connection = None

    # ------------------------------------------------------------------
    # Static helper: find a writable DB path (works in dev or PyInstaller)
    # ------------------------------------------------------------------
    @staticmethod
    def get_database_path() -> str:
        """
        Return path to SQLite DB.
        • In a PyInstaller bundle:  %USERPROFILE%/.nmsimple/nexus_control.db
        • In dev/source run:        <project-root>/nexus_control.db
        """
        if getattr(sys, "frozen", False):          # Running from EXE
            app_data = os.path.expanduser("~/.nmsimple")
            os.makedirs(app_data, exist_ok=True)
            return os.path.join(app_data, "nexus_control.db")
        else:                                      # Running from source
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            return os.path.join(project_root, "nexus_control.db")

    # ------------------------------------------------------------------
    # Singleton pattern: only one DB connection for entire application
    # ------------------------------------------------------------------
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            db_path = cls.get_database_path()      # << fixed call
            cls._connection = sqlite3.connect(db_path, check_same_thread=False)
            cls._connection.row_factory = sqlite3.Row
            cls._instance._create_tables()
        return cls._instance

    # ------------------------------------------------------------------
    # TABLE CREATION (runs only once, on first instantiation)
    # ------------------------------------------------------------------
    def _create_tables(self):
        cur = self._connection.cursor()

        # Devices
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL UNIQUE,
                ip            TEXT    NOT NULL UNIQUE,
                model         TEXT,
                status        TEXT    DEFAULT 'Unknown',
                last_backup   TEXT    DEFAULT 'Never',
                username      TEXT,
                password      TEXT,
                snmp_community TEXT   DEFAULT 'public'
            )
            """
        )

        # Backups
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS backups (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id    INTEGER NOT NULL,
                timestamp    TEXT    NOT NULL,
                configuration TEXT    NOT NULL,
                FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
            )
            """
        )

        # Scheduled jobs
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                db_id            INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id           TEXT NOT NULL UNIQUE,
                name             TEXT NOT NULL,
                type             TEXT NOT NULL,
                interval_minutes INTEGER,
                cron_hour        INTEGER,
                cron_minute      INTEGER
            )
            """
        )

        # Application logs
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS application_logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                level     TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                message   TEXT NOT NULL
            )
            """
        )

        self._connection.commit()

    # ------------------------------------------------------------------
    #  DEVICE CRUD
    # ------------------------------------------------------------------
    def get_all_devices(self):
        cur = self._connection.cursor()
        cur.execute("SELECT * FROM devices ORDER BY name ASC")
        return [dict(r) for r in cur.fetchall()]

    def add_device(self, data: dict):
        cur = self._connection.cursor()
        try:
            cur.execute(
                """
                INSERT INTO devices
                (name, ip, model, status, username, password, snmp_community)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["name"],
                    data["ip"],
                    data["model"],
                    data["status"],
                    data["username"],
                    data["password"],
                    data.get("snmp_community", "public"),
                ),
            )
            self._connection.commit()
            return True, "Device added successfully."
        except sqlite3.IntegrityError as e:
            return False, f"Error: Device name or IP already exists ({e})."

    def update_device(self, device_id: int, data: dict):
        cur = self._connection.cursor()
        try:
            cur.execute(
                """
                UPDATE devices
                SET name=?, ip=?, model=?, status=?, username=?,
                    password=?, snmp_community=?
                WHERE id=?
                """,
                (
                    data["name"],
                    data["ip"],
                    data["model"],
                    data["status"],
                    data["username"],
                    data["password"],
                    data.get("snmp_community", "public"),
                    device_id,
                ),
            )
            self._connection.commit()
            return True, "Device updated successfully."
        except sqlite3.IntegrityError as e:
            return False, f"Error: Device name or IP already exists ({e})."

    def delete_device(self, device_id: int):
        cur = self._connection.cursor()
        cur.execute("DELETE FROM devices WHERE id=?", (device_id,))
        self._connection.commit()
        return cur.rowcount > 0

    def update_last_backup(self, device_id: int, timestamp: str):
        cur = self._connection.cursor()
        cur.execute("UPDATE devices SET last_backup=? WHERE id=?", (timestamp, device_id))
        self._connection.commit()
        return cur.rowcount > 0

    def update_device_status(self, device_id: int, status: str):
        cur = self._connection.cursor()
        cur.execute("UPDATE devices SET status=? WHERE id=?", (status, device_id))
        self._connection.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    #  BACKUP METHODS
    # ------------------------------------------------------------------
    def add_backup(self, device_id: int, timestamp: str, configuration: str):
        cur = self._connection.cursor()
        cur.execute(
            "INSERT INTO backups (device_id, timestamp, configuration) VALUES (?, ?, ?)",
            (device_id, timestamp, configuration),
        )
        self._connection.commit()

    def get_backups_for_device(self, device_id: int):
        cur = self._connection.cursor()
        cur.execute("SELECT * FROM backups WHERE device_id=? ORDER BY timestamp DESC", (device_id,))
        return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    #  SCHEDULED JOBS
    # ------------------------------------------------------------------
    def add_scheduled_job(
        self,
        job_id: str,
        name: str,
        job_type: str,
        interval_minutes: int | None = None,
        cron_hour: int | None = None,
        cron_minute: int | None = None,
    ):
        cur = self._connection.cursor()
        try:
            cur.execute(
                """
                INSERT INTO scheduled_jobs
                (job_id, name, type, interval_minutes, cron_hour, cron_minute)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job_id, name, job_type, interval_minutes, cron_hour, cron_minute),
            )
            self._connection.commit()
            return True, "Job added successfully."
        except sqlite3.IntegrityError as e:
            return False, f"Error: Job ID already exists ({e})."

    def get_all_scheduled_jobs(self):
        cur = self._connection.cursor()
        cur.execute("SELECT * FROM scheduled_jobs")
        return [dict(r) for r in cur.fetchall()]

    def delete_scheduled_job(self, job_id: str):
        cur = self._connection.cursor()
        cur.execute("DELETE FROM scheduled_jobs WHERE job_id=?", (job_id,))
        self._connection.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    #  APPLICATION LOGS
    # ------------------------------------------------------------------
    def add_log_entry(self, level: str, timestamp: str, message: str):
        cur = self._connection.cursor()
        cur.execute(
            "INSERT INTO application_logs (level, timestamp, message) VALUES (?, ?, ?)",
            (level, timestamp, message),
        )
        self._connection.commit()

    def get_all_log_entries(self):
        cur = self._connection.cursor()
        cur.execute("SELECT * FROM application_logs ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]

    def clear_all_log_entries(self):
        cur = self._connection.cursor()
        cur.execute("DELETE FROM application_logs")
        self._connection.commit()
        return cur.rowcount > 0


# Singleton instance for use across the application
db_manager = DatabaseManager()
