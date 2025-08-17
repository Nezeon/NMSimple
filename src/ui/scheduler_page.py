# ui/scheduler_page.py
# Description: A redesigned page for managing scheduled jobs using a modern card layout.
# Changes:
# - FIXED: Moved 'QGraphicsDropShadowEffect' from the QtGui import to the QtWidgets import.
# - NEW: Integration with database for persisting scheduled jobs.
# - The refresh_jobs_list now correctly reflects jobs managed by scheduler_manager (which loads from DB).
# - FIX: Added robust handling for job.next_run_time to prevent AttributeError.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QDialog, QSpinBox, QDialogButtonBox, QMessageBox, QComboBox,
    QStackedWidget, QTimeEdit, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QColor

from utils.scheduler import scheduler_manager
from utils.logger import app_logger
from ui.icon_manager import IconManager

class AddJobDialog(QDialog):
    """A functional dialog for creating different types of scheduled jobs."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Scheduled Job")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        form_layout = QGridLayout(); form_layout.setSpacing(15)
        form_layout.addWidget(QLabel("Task Type:"), 0, 0)
        self.task_combo = QComboBox(); self.task_combo.addItems(["Ping All Devices Status", "Daily Backup All Devices"])
        form_layout.addWidget(self.task_combo, 0, 1)
        self.options_stack = QStackedWidget()
        ping_widget = QWidget(); ping_layout = QHBoxLayout(ping_widget); ping_layout.setContentsMargins(0,0,0,0)
        ping_layout.addWidget(QLabel("Run every (minutes):")); self.interval_input = QSpinBox(); self.interval_input.setRange(1, 1440); self.interval_input.setValue(5)
        ping_layout.addWidget(self.interval_input)
        backup_widget = QWidget(); backup_layout = QHBoxLayout(backup_widget); backup_layout.setContentsMargins(0,0,0,0)
        backup_layout.addWidget(QLabel("Run daily at (HH:MM):")); self.time_input = QTimeEdit(); self.time_input.setDisplayFormat("HH:mm"); self.time_input.setTime(QTime(2, 0))
        backup_layout.addWidget(self.time_input)
        self.options_stack.addWidget(ping_widget); self.options_stack.addWidget(backup_widget)
        form_layout.addWidget(self.options_stack, 1, 0, 1, 2); layout.addLayout(form_layout)
        self.task_combo.currentIndexChanged.connect(self.options_stack.setCurrentIndex)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        job_type_text = self.task_combo.currentText()
        if job_type_text == "Ping All Devices Status": return {"type": "ping", "interval": self.interval_input.value()}
        elif job_type_text == "Daily Backup All Devices":
            time = self.time_input.time()
            return {"type": "backup", "hour": time.hour(), "minute": time.minute()}
        return None

class SchedulerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("schedulerPage")
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setSpacing(25)
        
        header_layout = self._create_header(); main_layout.addLayout(header_layout)
        
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setObjectName("scrollArea")
        scroll_content = QWidget()
        self.jobs_layout = QVBoxLayout(scroll_content)
        self.jobs_layout.setSpacing(20)
        scroll_area.setWidget(scroll_content)
        
        main_layout.addWidget(scroll_area)
        self.refresh_jobs_list()

    def _create_header(self):
        header_layout = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title_label = QLabel("Job Scheduler"); title_label.setObjectName("pageTitle")
        subtitle_label = QLabel("Automate recurring tasks like status checks and backups."); subtitle_label.setObjectName("pageSubtext")
        title_vbox.addWidget(title_label); title_vbox.addWidget(subtitle_label)
        add_job_button = QPushButton("Add Job"); add_job_button.setIcon(IconManager.get_icon("add"))
        add_job_button.clicked.connect(self._open_add_job_dialog)
        header_layout.addLayout(title_vbox); header_layout.addStretch(); header_layout.addWidget(add_job_button)
        return header_layout

    def refresh_jobs_list(self):
        """Clears the layout and rebuilds the job cards from the scheduler."""
        while self.jobs_layout.count():
            child = self.jobs_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get jobs directly from the scheduler manager, which now loads from DB
        jobs = scheduler_manager.get_jobs()
        if not jobs:
            no_jobs_label = QLabel("No scheduled jobs. Click 'Add Job' to create one.")
            no_jobs_label.setAlignment(Qt.AlignCenter)
            no_jobs_label.setObjectName("noJobsLabel")
            self.jobs_layout.addWidget(no_jobs_label)
        else:
            for job in jobs:
                job_card = self._create_job_card(job)
                self.jobs_layout.addWidget(job_card)
        
        self.jobs_layout.addStretch()

    def _open_add_job_dialog(self):
        dialog = AddJobDialog(self)
        if dialog.exec() == QDialog.Accepted:
            job_data = dialog.get_data()
            if job_data:
                try:
                    scheduler_manager.add_job(job_data)
                    self.refresh_jobs_list()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to add job:\n{str(e)}")

    def _remove_job(self, job_id):
        """Remove a job and refresh the list"""
        try:
            scheduler_manager.remove_job(job_id)
            self.refresh_jobs_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove job:\n{str(e)}")
            
    def _create_job_card(self, job):
        """Creates a styled QFrame card for a single job."""
        card = QFrame(); card.setObjectName("JobCard")
        
        main_layout = QHBoxLayout(card); main_layout.setSpacing(20)

        icon = QLabel(); icon.setPixmap(IconManager.get_icon("scheduler").pixmap(32,32))
        
        text_layout = QVBoxLayout(); text_layout.setSpacing(5)
        job_name = QLabel(job.name); job_name.setObjectName("jobName")
        job_schedule = QLabel(f"<b>Schedule:</b> {str(job.trigger)}"); job_schedule.setObjectName("jobSchedule")
        
        # --- FIX: Robustly get next_run_time and format it ---
        next_run_str = "N/A" # Default value if no run time or attribute is missing
        if hasattr(job, 'next_run_time') and job.next_run_time is not None:
            try:
                next_run_str = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            except AttributeError:
                # This catches if next_run_time exists but isn't a datetime object
                next_run_str = "Error formatting time"
        elif hasattr(job, 'next_run_time') and job.next_run_time is None:
            next_run_str = "Paused"
        # --- END FIX ---

        job_next_run = QLabel(f"<b>Next Run:</b> {next_run_str}"); job_next_run.setObjectName("jobNextRun")
        text_layout.addWidget(job_name); text_layout.addWidget(job_schedule); text_layout.addWidget(job_next_run)

        delete_button = QPushButton(); delete_button.setIcon(IconManager.get_icon("delete")); delete_button.setObjectName("iconButton"); delete_button.setToolTip("Remove Job")
        # Connect to the scheduler_manager's remove_job method
        delete_button.clicked.connect(lambda: self._remove_job(job.id))

        main_layout.addWidget(icon); main_layout.addLayout(text_layout); main_layout.addStretch(); main_layout.addWidget(delete_button)
        
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(25); shadow.setColor(QColor(0, 0, 0, 80)); shadow.setOffset(0, 3); card.setGraphicsEffect(shadow)
        return card

