import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QSystemTrayIcon, QMenu, QApplication)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon, QFont, QAction, QPixmap
from src.ui.styles import STYLESHEET

from src.database.storage import StorageManager
from src.core.tracker import Tracker
from src.core.icon_manager import IconManager
from src.ui.home_widget import HomeWidget
from src.ui.activities_widget import ActivitiesWidget
from src.ui.statistics_widget import StatisticsWidget
from src.ui.settings_widget import SettingsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gainhour")
        # Start maximized or large
        self.resize(1400, 900)
        
        # Setup Core
        self.db = StorageManager("gainhour.db")
        self.db.clean_explorer_data()
        self.icon_manager = IconManager()
        self.tracker = Tracker(self.db, self.icon_manager)
        self.tracker.start()

        # Apply Unified Theme
        self.setStyleSheet(STYLESHEET)

        # Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation Bar
        self.create_nav_bar()
        main_layout.addWidget(self.nav_frame)

        # Content Area (Stacked Widget)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Initialize Widgets
        self.home_widget = HomeWidget(self.tracker, self.db, self.icon_manager)
        self.activities_widget = ActivitiesWidget(self.db, self.tracker, self.icon_manager)
        self.statistics_widget = StatisticsWidget(self.db, self.tracker)
        self.settings_widget = SettingsWidget(self.db)
        
        self.stack.addWidget(self.home_widget)
        self.stack.addWidget(self.activities_widget)
        self.stack.addWidget(self.statistics_widget)
        self.stack.addWidget(self.settings_widget)
        
        # Timer for updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000) # 1 second
        
        # Tray Icon
        self.create_tray_icon()

    def create_nav_bar(self):
        self.nav_frame = QWidget()
        self.nav_frame.setObjectName("NavFrame")
        self.nav_frame.setFixedWidth(220) # Slightly wider
        
        layout = QVBoxLayout(self.nav_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # App Title
        title = QLabel("GAINHOUR")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(80)
        title.setStyleSheet("color: white; letter-spacing: 2px;")
        layout.addWidget(title)
        
        # Buttons
        self.nav_btns = []
        
        def add_btn(text, index):
            btn = QPushButton(text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda: self.switch_tab(index))
            layout.addWidget(btn)
            self.nav_btns.append(btn)
            
        add_btn("  Home", 0)
        add_btn("  Activities", 1)
        add_btn("  Statistics", 2)
        add_btn("  Settings", 3)
        
        layout.addStretch()
        
        self.nav_btns[0].setChecked(True)


    def switch_tab(self, index):
        if index < self.stack.count():
            self.stack.setCurrentIndex(index)
            
            # Update Button State
            self.nav_btns[index].setChecked(True)
                
            # Refresh if needed
            widget = self.stack.currentWidget()
            if hasattr(widget, 'refresh'):
                widget.refresh()

    def update_ui(self):
        # Propagate updates to active widget
        current = self.stack.currentWidget()
        if hasattr(current, 'update_data'):
            current.update_data()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Icon
        if os.path.exists("gainhour.ico"):
            self.tray_icon.setIcon(QIcon("gainhour.ico"))
        else:
             # Fallback 
             pass
            
        # Menu
        menu = QMenu()
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show_normal)
        menu.addAction(open_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_normal()

    def show_normal(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()

    def quit_app(self):
        self.tracker.stop()
        QApplication.instance().quit()

    def closeEvent(self, event):
        # Check settings? Or default to tray
        if self.tray_icon.isVisible():
            self.hide()
            # Notification removed as per user request
            # self.tray_icon.showMessage(
            #     "Gainhour",
            #     "Running in background",
            #     QSystemTrayIcon.Information,
            #     2000
            # )
            event.ignore()
        else:
            self.tracker.stop()
            event.accept()
