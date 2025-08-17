# ui/working_dynamic_cpu_graph.py
# Fixed CPUDataWorker and connection

import random
import math
from collections import deque
from typing import Dict, Any
from datetime import datetime, timedelta

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QLinearGradient, QPainterPath

from ui.styles import Style
from utils.logger import app_logger


class CPUDataWorker(QObject):
    """Worker for generating CPU data (simulated for now)."""
    
    data_received = Signal(float)
    error_occurred = Signal(str)
    finished = Signal()  # Add finished signal
    
    def __init__(self, device_info: Dict[str, Any]):
        super().__init__()
        self.device_info = device_info
        self.logger = app_logger.get_logger()
        
    def run(self):  # Changed from run_fetch to run
        """Generate simulated CPU data with realistic patterns."""
        try:
            device_status = self.device_info.get("status", "Unknown")
            
            if device_status == "Online":
                # Simulate network delay
                import time
                time.sleep(0.1)
                
                # Generate more realistic CPU patterns
                base_cpu = getattr(self, '_last_cpu', random.uniform(25, 45))
                
                # Create different patterns based on time or device type
                current_time = datetime.now()
                time_factor = (current_time.minute % 10) / 10.0  # 10-minute cycles
                
                # Different behavior patterns
                device_model = self.device_info.get("model", "").lower()
                if "cisco" in device_model:
                    # Cisco devices tend to have more stable CPU
                    variation = random.uniform(-3, 8)
                    trend_factor = 0.5
                else:
                    # Other devices might be more variable
                    variation = random.uniform(-8, 12)
                    trend_factor = 1.0
                
                # Add some cyclical behavior
                cyclical = 5 * math.sin(time_factor * 2 * math.pi) * trend_factor
                
                # Occasional load spikes (simulating real network activity)
                spike_probability = 0.08  # 8% chance
                if random.random() < spike_probability:
                    spike = random.uniform(20, 40)
                    self.logger.debug(f"CPU spike generated: +{spike:.1f}%")
                else:
                    spike = 0
                
                # Calculate new CPU value
                new_cpu = base_cpu + variation + cyclical + spike
                
                # Keep within realistic bounds
                new_cpu = max(5.0, min(95.0, new_cpu))
                self._last_cpu = new_cpu
                
                self.data_received.emit(new_cpu)
                self.logger.debug(f"Generated CPU data: {new_cpu:.1f}% for {self.device_info.get('name', 'Unknown')}")
            else:
                self.error_occurred.emit("Device not online")
                
        except Exception as e:
            self.logger.error(f"Error generating CPU data: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()


class WorkingDynamicCPUGraph(QWidget):
    """A working CPU graph widget with proper visualization."""
    
    def __init__(self, device_info: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.device_info = device_info or {}
        
        # Set minimum size to ensure graph is visible
        self.setMinimumHeight(300)
        self.setMinimumWidth(400)
        
        # Data storage
        self.max_data_points = 30  # Show last 30 data points
        self.cpu_data = deque(maxlen=self.max_data_points)
        self.time_labels = deque(maxlen=self.max_data_points)
        
        # Setup UI FIRST (before initializing data)
        self._setup_ui()
        
        # Initialize with some data AFTER UI is setup
        self._initialize_data()
        
        # Thread management
        self.worker_thread = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._fetch_new_data)
        
        self.logger = app_logger.get_logger()
        
        # Force initial paint
        self.update()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with current CPU value
        header_layout = QHBoxLayout()
        
        self.cpu_label = QLabel("CPU Utilization")
        self.cpu_label.setObjectName("graphTitle")
        font = self.cpu_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.cpu_label.setFont(font)
        
        self.current_cpu_label = QLabel("---%")
        self.current_cpu_label.setObjectName("graphValue")
        self.current_cpu_label.setAlignment(Qt.AlignRight)
        font = self.current_cpu_label.font()
        font.setPointSize(18)
        font.setBold(True)
        self.current_cpu_label.setFont(font)
        
        header_layout.addWidget(self.cpu_label)
        header_layout.addStretch()
        header_layout.addWidget(self.current_cpu_label)
        
        layout.addLayout(header_layout)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("graphStatus")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add spacer to push graph area
        layout.addStretch()
        
    def _initialize_data(self):
        """Initialize with realistic placeholder data."""
        current_time = datetime.now()
        
        # Generate a realistic CPU pattern
        base_cpu = 30.0
        for i in range(self.max_data_points):
            # Create some variation
            variation = random.uniform(-5, 15)
            cpu_value = base_cpu + variation + (10 * (i / self.max_data_points))  # Slight upward trend
            cpu_value = max(5.0, min(90.0, cpu_value))
            
            self.cpu_data.append(cpu_value)
            
            time_point = current_time - timedelta(seconds=(self.max_data_points - i) * 5)
            self.time_labels.append(time_point.strftime("%H:%M:%S"))
        
        # Set initial display value
        if self.cpu_data:
            self.current_cpu_label.setText(f"{self.cpu_data[-1]:.1f}%")
    
    def start_monitoring(self, device_info: Dict[str, Any]):
        """Start CPU monitoring with real-time updates."""
        try:
            self.device_info = device_info
            
            # Update status based on device
            if device_info.get("status") != "Online":
                self.status_label.setText("Device offline - showing last known data")
                self.status_label.setStyleSheet(f"color: {Style.STATUS_RED};")
                return
            
            self.status_label.setText("Live monitoring active")
            self.status_label.setStyleSheet(f"color: {Style.STATUS_GREEN};")
            
            # Start the timer with faster updates (every 2 seconds for more responsive feel)
            self.update_timer.start(2000)  # Changed from 3000 to 2000ms
            
            # Start first fetch immediately
            self._fetch_new_data()
            
            self.logger.debug(f"Started CPU monitoring for {device_info.get('name', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to start CPU monitoring: {e}")
            self.status_label.setText("Failed to start monitoring")
            self.status_label.setStyleSheet(f"color: {Style.STATUS_RED};")
    
    def stop_monitoring(self):
        """Stop CPU monitoring."""
        try:
            if self.update_timer.isActive():
                self.update_timer.stop()
            
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait(1000)
            
            self.status_label.setText("Monitoring stopped")
            self.status_label.setStyleSheet(f"color: {Style.DARK_TEXT_SECONDARY};")
            
        except Exception as e:
            self.logger.error(f"Error stopping CPU monitoring: {e}")
    
    def _fetch_new_data(self):
        """Fetch new CPU data."""
        try:
            if self.worker_thread and self.worker_thread.isRunning():
                return
            
            self.worker_thread = QThread()
            self.worker = CPUDataWorker(self.device_info)
            self.worker.moveToThread(self.worker_thread)
            
            # Connect signals
            self.worker.data_received.connect(self._on_data_received)
            self.worker.error_occurred.connect(self._on_error_occurred)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            
            # Cleanup
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.finished.connect(lambda: setattr(self, 'worker_thread', None))
            
            # Start worker - FIXED: Connect to 'run' instead of 'run_fetch'
            self.worker_thread.started.connect(self.worker.run)
            self.worker_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error starting CPU fetch: {e}")
    
    def _on_data_received(self, cpu_value: float):
        """Handle new CPU data with improved real-time updates."""
        try:
            # Add new data point
            self.cpu_data.append(cpu_value)
            
            # Add timestamp
            current_time = datetime.now()
            self.time_labels.append(current_time.strftime("%H:%M:%S"))
            
            # Update display with more dynamic formatting
            self.current_cpu_label.setText(f"{cpu_value:.1f}%")
            
            # Update color based on CPU usage
            if cpu_value > 90:
                self.current_cpu_label.setStyleSheet(f"color: {Style.STATUS_RED};")
                self.status_label.setText("⚠️ High CPU Usage")
                self.status_label.setStyleSheet(f"color: {Style.STATUS_RED};")
            elif cpu_value > 70:
                self.current_cpu_label.setStyleSheet(f"color: {Style.STATUS_YELLOW};")
                self.status_label.setText("🔶 Moderate CPU Usage") 
                self.status_label.setStyleSheet(f"color: {Style.STATUS_YELLOW};")
            else:
                self.current_cpu_label.setStyleSheet(f"color: {Style.STATUS_GREEN};")
                self.status_label.setText("✅ Normal CPU Usage")
                self.status_label.setStyleSheet(f"color: {Style.STATUS_GREEN};")
            
            # Force immediate repaint for smooth updates
            self.repaint()  # Use repaint() instead of update() for immediate drawing
            
            self.logger.debug(f"CPU updated: {cpu_value:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error handling CPU data: {e}")
    
    def _on_error_occurred(self, error_message: str):
        """Handle errors."""
        self.status_label.setText("CPU data unavailable")
        self.status_label.setStyleSheet(f"color: {Style.STATUS_RED};")
        self.logger.warning(f"CPU graph error: {error_message}")
    
    def paintEvent(self, event):
        """Paint the CPU graph."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get dimensions for graph area (leave space for header and status)
        widget_width = self.width()
        widget_height = self.height()
        
        # Define graph area (leave space for header/status)
        margin = 20
        graph_top = 80  # Space for header
        graph_bottom = widget_height - 40  # Space for status
        graph_left = margin + 40  # Space for Y-axis labels
        graph_right = widget_width - margin
        
        graph_width = graph_right - graph_left
        graph_height = graph_bottom - graph_top
        
        if graph_width <= 0 or graph_height <= 0:
            return
        
        # Draw graph background
        painter.fillRect(graph_left, graph_top, graph_width, graph_height, 
                        QColor(Style.DARK_BG_SECONDARY))
        
        # Draw border
        border_pen = QPen(QColor(Style.DARK_BORDER))
        border_pen.setWidth(1)
        painter.setPen(border_pen)
        painter.drawRect(graph_left, graph_top, graph_width, graph_height)
        
        # Draw horizontal grid lines and Y-axis labels
        grid_pen = QPen(QColor(Style.DARK_BORDER))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        
        # Draw horizontal lines for CPU percentages
        for i in range(6):  # 0%, 20%, 40%, 60%, 80%, 100%
            percentage = i * 20
            y = graph_bottom - (percentage / 100.0 * graph_height)
            
            # Draw grid line
            painter.drawLine(graph_left, y, graph_right, y)
            
            # Draw percentage label
            painter.drawText(graph_left - 35, y + 5, f"{percentage}%")
        
        # Draw the CPU data line
        if len(self.cpu_data) >= 2:
            # Create points for the line
            points = []
            for i, cpu_value in enumerate(self.cpu_data):
                x = graph_left + (graph_width * i / (len(self.cpu_data) - 1))
                y = graph_bottom - (cpu_value / 100.0 * graph_height)
                points.append(QPointF(x, y))
            
            # Draw the main line
            line_pen = QPen(QColor(Style.DARK_ACCENT_PRIMARY))
            line_pen.setWidth(2)
            painter.setPen(line_pen)
            
            for i in range(1, len(points)):
                painter.drawLine(points[i-1], points[i])
            
            # Draw fill area under the line
            if points:
                gradient = QLinearGradient(0, graph_top, 0, graph_bottom)
                gradient.setColorAt(0.0, QColor(Style.DARK_ACCENT_PRIMARY).lighter(150))
                gradient.setColorAt(1.0, QColor(Style.DARK_BG_SECONDARY))
                painter.setBrush(gradient)
                painter.setPen(Qt.NoPen)
                
                # Create fill path
                fill_path = QPainterPath()
                fill_path.moveTo(points[0].x(), graph_bottom)
                for point in points:
                    fill_path.lineTo(point)
                fill_path.lineTo(points[-1].x(), graph_bottom)
                fill_path.closeSubpath()
                
                painter.drawPath(fill_path)
            
            # Draw data points
            point_pen = QPen(QColor(Style.DARK_ACCENT_PRIMARY))
            point_pen.setWidth(3)
            painter.setPen(point_pen)
            painter.setBrush(QColor(Style.DARK_ACCENT_PRIMARY))
            
            for point in points:
                painter.drawEllipse(point, 3, 3)
        
        # Draw time labels on X-axis
        if len(self.time_labels) > 1:
            painter.setPen(QColor(Style.DARK_TEXT_SECONDARY))
            
            # Show every 5th time label to avoid crowding
            step = max(1, len(self.time_labels) // 6)
            for i in range(0, len(self.time_labels), step):
                if i < len(self.time_labels):
                    x = graph_left + (graph_width * i / (len(self.time_labels) - 1))
                    painter.drawText(x - 20, graph_bottom + 15, self.time_labels[i])
    
    def closeEvent(self, event):
        """Clean up when closing."""
        try:
            self.stop_monitoring()
            super().closeEvent(event)
        except Exception as e:
            self.logger.error(f"Error in close event: {e}")
            super().closeEvent(event)