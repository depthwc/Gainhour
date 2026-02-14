from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QTabWidget, QWidget, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
import os
from datetime import datetime

from src.utils.text_utils import format_app_name

class LogViewerDialog(QDialog):
    def __init__(self, activity, db, icon_manager, parent=None):
        super().__init__(parent)
        self.activity = activity
        self.db = db
        self.icon_manager = icon_manager
        
        formatted_name = format_app_name(activity.name)
        
        self.setWindowTitle(f"Activity Logs - {formatted_name}")
        self.setFixedSize(900, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #3e3e3e;
                background-color: #252526;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 8px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3e3e3e;
                color: #ffffff;
                font-weight: bold;
            }
            QTableWidget {
                background-color: #252526;
                color: #dddddd;
                gridline-color: #3e3e3e;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #3e3e3e;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # Icon
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(64, 64)
        icon_path = activity.icon_path
        if icon_path and not os.path.isabs(icon_path):
             base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             icon_path = os.path.join(base_path, icon_path)

        if icon_path and os.path.exists(icon_path):
             pixmap = QPixmap(icon_path)
             if not pixmap.isNull():
                 pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                 icon_lbl.setPixmap(pixmap)
        
        header_layout.addWidget(icon_lbl)

        # Info
        info_layout = QVBoxLayout()
        name_lbl = QLabel(formatted_name)
        name_lbl.setStyleSheet("font-size: 24px; font-weight: bold;")
        info_layout.addWidget(name_lbl)

        # Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        # Total Duration
        total_duration = self.db.get_activity_duration(activity.name, activity.type)
        h, r = divmod(total_duration, 3600)
        m, _ = divmod(r, 60)
        total_lbl = QLabel(f"Total: {int(h)}h {int(m)}m")
        total_lbl.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        stats_layout.addWidget(total_lbl)
        
        # Today Duration
        today_duration = self.db.get_today_duration(activity.name, activity.type)
        th, tr = divmod(today_duration, 3600)
        tm, _ = divmod(tr, 60)
        today_lbl = QLabel(f"Today: {int(th)}h {int(tm)}m")
        today_lbl.setStyleSheet("font-size: 14px; color: #e0e0e0; font-weight: bold;")
        stats_layout.addWidget(today_lbl)
        
        stats_layout.addStretch()
        info_layout.addLayout(stats_layout)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- Tabs ---
        self.tabs = QTabWidget()
        
        # Tab 1: All Time
        if not self.db.get_setting("daily_logs_only") == "True":
            self.tab_all = QWidget()
            self.setup_tab(self.tab_all, today_only=False)
            self.tabs.addTab(self.tab_all, "All Time")

        # Tab 2: Today
        self.tab_today = QWidget()
        self.setup_tab(self.tab_today, today_only=True)
        self.tabs.addTab(self.tab_today, "Today")

        layout.addWidget(self.tabs)

        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 35)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3e3e3e;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def setup_tab(self, tab_widget, today_only):
        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Description", "Start Time", "End Time", "Duration", "Times Used", "Total Usage"
        ])
        
        # Table Settings
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)       # Description
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Start
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # End
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Duration
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Count
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Total Usage
        
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Fetch Data
        logs = self.db.get_activity_description_logs(self.activity.id, today_only=today_only)
        table.setRowCount(len(logs))
        
        for i, log in enumerate(logs):
            # Description
            table.setItem(i, 0, QTableWidgetItem(log['description']))
            
            # Start/End
            t_start = log['start_time'].strftime("%Y-%m-%d %H:%M:%S")
            t_end = log['end_time'].strftime("%Y-%m-%d %H:%M:%S") if log['end_time'] else "Running..."
            table.setItem(i, 1, QTableWidgetItem(t_start))
            table.setItem(i, 2, QTableWidgetItem(t_end))
            
            # Duration
            dur_str = self.format_duration(log['duration'])
            table.setItem(i, 3, QTableWidgetItem(dur_str))
            
            # Stats (Count / Total)
            table.setItem(i, 4, QTableWidgetItem(str(log['count'])))
            
            total_str = self.format_duration(log['total_usage'])
            table.setItem(i, 5, QTableWidgetItem(total_str))
            
        layout.addWidget(table)

    def format_duration(self, seconds):
        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02}:{int(m):02}:{int(s):02}"
