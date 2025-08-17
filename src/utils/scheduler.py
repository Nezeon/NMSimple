from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox
from apscheduler.schedulers.background import BackgroundScheduler
from utils.logger import app_logger
from utils.database import db_manager  # Assumes a working DB manager is available

class SchedulerManager(QObject):
    """
    Manages the background job scheduler and exposes signals to safely interact with the UI thread.
    """
    trigger_ping_all = Signal()
    trigger_backup_all = Signal()

    def __init__(self):
        super().__init__()  # ✅ Crucial for QObject to properly initialize signals

        self.logger = app_logger.get_logger()
        self.scheduler = BackgroundScheduler(daemon=True)

        self._load_jobs_from_db()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.debug("Job scheduler started.")  # Changed to DEBUG level

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Job scheduler stopped.")

    def _load_jobs_from_db(self):
        self.logger.info("Loading scheduled jobs from database...")
        stored_jobs = db_manager.get_all_scheduled_jobs()

        for job_data in stored_jobs:
            job_id = job_data["job_id"]
            name = job_data["name"]
            job_type = job_data["type"]  # This matches your DB schema

            try:
                if job_type == "interval":
                    minutes = job_data["interval_minutes"]
                    self.scheduler.add_job(
                        self.trigger_ping_all.emit,
                        "interval",
                        minutes=minutes,
                        id=job_id,
                        name=name
                    )
                    self.logger.info(f"Restored interval job '{name}' (ID: {job_id})")

                elif job_type == "cron":
                    hour = job_data["cron_hour"]
                    minute = job_data["cron_minute"]
                    self.scheduler.add_job(
                        self.trigger_backup_all.emit,
                        "cron",
                        hour=hour,
                        minute=minute,
                        id=job_id,
                        name=name
                    )
                    self.logger.info(f"Restored cron job '{name}' (ID: {job_id})")

            except Exception as e:
                self.logger.error(f"Failed to restore job '{name}' (ID: {job_id}): {e}")

    def add_ping_job(self, minutes: int):
        job_id = "ping_all_devices"
        name = "Ping All Devices Status"

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        self.scheduler.add_job(
            self.trigger_ping_all.emit,
            "interval",
            minutes=minutes,
            id=job_id,
            name=name
        )
        self.logger.info(f"Scheduled ping job every {minutes} minutes.")
        success, message = db_manager.add_scheduled_job(
            job_id=job_id, 
            name=name, 
            job_type="interval",  # Changed from "type" to "job_type"
            interval_minutes=minutes
        )
        if success:
            self.logger.info(f"Job '{name}' persisted to database.")
        else:
            self.logger.error(f"Failed to persist job: {message}")

    def add_backup_job(self, hour: int, minute: int):
        job_id = "backup_all_devices"
        name = "Daily Backup All Devices"

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        self.scheduler.add_job(
            self.trigger_backup_all.emit,
            "cron",
            hour=hour,
            minute=minute,
            id=job_id,
            name=name
        )
        self.logger.info(f"Scheduled daily backup at {hour:02d}:{minute:02d}.")
        success, message = db_manager.add_scheduled_job(
            job_id=job_id,
            name=name,
            job_type="cron",  # Changed from "type" to "job_type"
            cron_hour=hour,
            cron_minute=minute
        )
        if success:
            self.logger.info(f"Job '{name}' persisted to database.")
        else:
            self.logger.error(f"Failed to persist job: {message}")

    def remove_job(self, job_id: str):
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed job from scheduler: {job_id}")

        if db_manager.delete_scheduled_job(job_id):
            self.logger.info(f"Removed job from database: {job_id}")
        else:
            self.logger.warning(f"Tried to delete non-existent job: {job_id}")

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def add_job(self, job_data):
        """Add job based on dialog data"""
        if job_data["type"] == "ping":
            self.add_ping_job(job_data["interval"])
        elif job_data["type"] == "backup":
            self.add_backup_job(job_data["hour"], job_data["minute"])


# ✅ Global singleton instance
scheduler_manager = SchedulerManager()
