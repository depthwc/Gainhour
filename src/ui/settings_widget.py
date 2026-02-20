from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QCheckBox, QComboBox, 
                               QPushButton, QHBoxLayout, QFrame, QDialog, QScrollArea, QSizePolicy, QLineEdit)
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QPixmap
from PySide6.QtCore import Qt, QTimer, Property, QSize, QEasingCurve, QPropertyAnimation

from src.utils.startup_manager import set_run_on_startup, check_run_on_startup

class ToggleSwitch(QWidget):
    def __init__(self, parent=None, track_radius=10, thumb_radius=8):
        super().__init__(parent)
        self.setFixedSize(50, 24)
        self.setCursor(Qt.PointingHandCursor)

        self._track_radius = track_radius
        self._thumb_radius = thumb_radius
        
        self._margin = 3
        self._base_offset = self._margin
        self._end_offset = self.width() - 2 * self._thumb_radius - self._margin 
        
        self._thumb_pos = self._base_offset
        
        self._checked = False
        
        # Animations
        self._anim = QPropertyAnimation(self, b"thumbPos", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            target = self._end_offset if checked else self._base_offset
            self._thumb_pos = target # No animation for programmatic set (optional)
            self.update()
            # self.toggled.emit(checked) # Usually don't emit on programmatic change unless desired

    # Signal
    from PySide6.QtCore import Signal
    toggled = Signal(bool)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._animate()
            self.toggled.emit(self._checked)
        super().mouseReleaseEvent(event)

    def getThumbPos(self):
        return self._thumb_pos

    def setThumbPos(self, pos):
        self._thumb_pos = pos
        self.update()

    thumbPos = Property(float, getThumbPos, setThumbPos)

    def _animate(self):
        target = self._end_offset if self._checked else self._base_offset
        self._anim.setStartValue(self._thumb_pos)
        self._anim.setEndValue(target)
        self._anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Draw Track
        track_color = QColor("#5865F2") if self._checked else QColor("#444")
        p.setBrush(track_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)
        
        # Draw Thumb
        p.setBrush(QColor("white"))
        # thumb_pos acts as x coordinate
        # y is centered
        thumb_y = (self.height() - 2 * self._thumb_radius) / 2
        
        # Fix thumb pos logic: _end_offset needs to be calculated such that circle fits
        # Circle size = thumb_radius * 2
        
        d = self._thumb_radius * 2
        x = self._thumb_pos
        y = (self.height() - d) / 2
        
        p.drawEllipse(x, y, d, d)
        
    def resizeEvent(self, event):
        self._end_offset = self.width() - 2 * self._thumb_radius - self._margin
        super().resizeEvent(event)


class SavedDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Saved")
        self.setFixedSize(300, 150)
        self.setStyleSheet("background-color: #2b2b2b; color: white; border: 1px solid #444;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 14px;")
        layout.addWidget(lbl)
        
        btn = QPushButton("OK")
        btn.setStyleSheet("background-color: #007acc; padding: 8px; border-radius: 4px; font-weight: bold;")
        btn.clicked.connect(self.accept)
        
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)


class SettingsWidget(QWidget):
    def __init__(self, db, tracker=None):
        super().__init__()
        self.db = db
        self.tracker = tracker
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(40, 20, 40, 20)
        
        # Title
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: white; margin-bottom: 20px;")
        self.layout.addWidget(title)

        # Main Content Layout (Columns)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setAlignment(Qt.AlignTop)
        
        # --- Left Column (All Current Settings) ---
        left_col = QVBoxLayout()
        left_col.setSpacing(20)
        left_col.setAlignment(Qt.AlignTop)
        
        # 1. General Section
        general_lbl = QLabel("General")
        general_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        general_lbl.setStyleSheet("color: #aaaaaa;")
        left_col.addWidget(general_lbl)
        
        self.general_box = QFrame()
        self.general_box.setObjectName("GeneralBox")
        self.general_box.setStyleSheet("""
            QFrame#GeneralBox {
                background-color: #2b2b2b;
                border: 1px solid #3e3e3e;
                border-radius: 8px;
            }
        """)
        g_layout = QVBoxLayout(self.general_box)
        g_layout.setSpacing(10)
        g_layout.setContentsMargins(15, 15, 15, 15)
        
        self.startup_check = QCheckBox("Run on Startup")
        
        # We will read from DB, but also verify with the registry.
        # DB will override at load.
        is_startup = check_run_on_startup()
        self.startup_check.setChecked(is_startup)
        self.startup_check.setStyleSheet("font-size: 14px; color: #ddd;")
        
        g_layout.addWidget(self.startup_check)
        
        left_col.addWidget(self.general_box)

        # 2. Data Management Section
        data_lbl = QLabel("Data Management")
        data_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        data_lbl.setStyleSheet("color: #aaaaaa;")
        left_col.addWidget(data_lbl)
        
        self.logs_box = QFrame()
        self.logs_box.setObjectName("LogsBox")
        self.logs_box.setStyleSheet("""
            QFrame#LogsBox {
                background-color: #2b2b2b;
                border: 1px solid #3e3e3e;
                border-radius: 8px;
            }
        """)
        
        logs_layout = QVBoxLayout(self.logs_box)
        logs_layout.setSpacing(10)
        logs_layout.setContentsMargins(15, 15, 15, 15)
        
        daily_container = QHBoxLayout()
        daily_container.setAlignment(Qt.AlignLeft)
        daily_lbl = QLabel("Keep Only Daily Logs?")
        daily_lbl.setStyleSheet("font-size: 14px; color: #ddd; margin-right: 15px; border: none; background: transparent;")
        daily_container.addWidget(daily_lbl)
        self.daily_logs_combo = QComboBox()
        self.daily_logs_combo.addItems(["No", "Yes"])
        self.daily_logs_combo.setFixedWidth(80)
        self.daily_logs_combo.setStyleSheet("QComboBox { padding: 5px; border: 1px solid #555; border-radius: 4px; background-color: #333; color: white; } QComboBox::drop-down { border: none; }")
        daily_container.addWidget(self.daily_logs_combo)
        logs_layout.addLayout(daily_container)
        
        self.warning_lbl = QLabel("⚠ 'Yes' will delete all history except today on save.")
        self.warning_lbl.setStyleSheet("color: #aa6666; font-size: 12px; font-style: italic; border: none; background: transparent;")
        self.warning_lbl.setVisible(False)
        logs_layout.addWidget(self.warning_lbl)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedSize(80, 30)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("QPushButton { background-color: #007acc; color: white; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #0062a3; }")
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        logs_layout.addLayout(btn_layout)
        
        left_col.addWidget(self.logs_box)
        
        # 3. Discord Integration
        discord_header = QHBoxLayout()
        discord_header.setAlignment(Qt.AlignLeft)
        discord_header.setSpacing(10)
        
        # Icon
        d_icon = QLabel()
        d_pix = QPixmap("src/icons/discord_icon.png")
        if not d_pix.isNull():
            d_icon.setPixmap(d_pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            discord_header.addWidget(d_icon)
            
        discord_lbl = QLabel("Discord Integration")
        discord_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        discord_lbl.setStyleSheet("color: #aaaaaa;")
        discord_header.addWidget(discord_lbl)
        
        left_col.addLayout(discord_header)

        self.discord_box = QFrame()
        self.discord_box.setObjectName("DiscordBox")
        self.discord_box.setStyleSheet("""
            QFrame#DiscordBox {
                background-color: #2b2b2b;
                border: 1px solid #3e3e3e;
                border-radius: 8px;
            }
        """)
        self.discord_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        
        d_layout = QVBoxLayout(self.discord_box)
        d_layout.setSpacing(15)
        d_layout.setContentsMargins(15, 15, 15, 15)

        # Master Toggle ROW
        master_row = QHBoxLayout()
        master_lbl = QLabel("Enable Discord Rich Presence")
        master_lbl.setStyleSheet("font-size: 14px; color: #ddd; font-weight: bold;")
        master_row.addWidget(master_lbl)
        master_row.addStretch()
        
        self.discord_enabled_switch = ToggleSwitch()
        self.discord_enabled_switch.toggled.connect(self.on_discord_toggled_auto)
        
        self.reconnect_btn = QPushButton("Reconnect")
        self.reconnect_btn.setCursor(Qt.PointingHandCursor)
        self.reconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #5865F2; /* Discord Color */
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
                margin-left: 10px;
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
        """)
        if hasattr(self, 'tracker') and self.tracker:
            self.reconnect_btn.clicked.connect(self.tracker.reconnect_discord)
            
        master_row.addWidget(self.discord_enabled_switch)
        master_row.addWidget(self.reconnect_btn)
        d_layout.addLayout(master_row)
        
        # Search Bar
        search_layout = QHBoxLayout()
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #888; border: none; font-size: 14px;")
        search_layout.addWidget(search_icon)
        
        self.status_search = QLineEdit()
        self.status_search.setPlaceholderText("Search apps...")
        self.status_search.setStyleSheet("""
            QLineEdit {
                background-color: #222;
                color: #ddd;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #555;
            }
        """)
        self.status_search.textChanged.connect(self.filter_apps)
        search_layout.addWidget(self.status_search)
        d_layout.addLayout(search_layout)
        
        helper_lbl = QLabel("Select apps to share on Discord (Auto-Saved):")
        helper_lbl.setStyleSheet("color: #888; font-size: 12px;")
        d_layout.addWidget(helper_lbl)

        self.app_scroll = QScrollArea()
        self.app_scroll.setWidgetResizable(True)
        self.app_scroll.setFixedHeight(300) 
        self.app_scroll.setStyleSheet("""
            QScrollArea { border: 1px solid #444; border-radius: 4px; background-color: #222; }
            QScrollBar:vertical { width: 10px; background: #222; }
            QScrollBar::handle:vertical { background: #444; border-radius: 5px; }
        """)
        
        self.app_list_widget = QWidget()
        self.app_list_layout = QVBoxLayout(self.app_list_widget)
        self.app_list_layout.setSpacing(10) # More spacing for list items
        self.app_list_layout.setContentsMargins(15, 15, 15, 15)
        self.app_scroll.setWidget(self.app_list_widget)
        
        d_layout.addWidget(self.app_scroll)
        
        self.app_switches = {} # { activity_id: ToggleSwitch }
        self.app_rows = [] # Store (name, widget) tuples for filtering
        
        left_col.addWidget(self.discord_box)
        content_layout.addLayout(left_col, 1) 
        
        # --- Right Column (Customization Placeholder) ---
        right_col = QVBoxLayout()
        right_col.setSpacing(20)
        right_col.setAlignment(Qt.AlignTop)
        
        custom_lbl = QLabel("Customization")
        custom_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        custom_lbl.setStyleSheet("color: #aaaaaa;")
        right_col.addWidget(custom_lbl)
        
        self.custom_box = QFrame()
        self.custom_box.setObjectName("CustomBox")
        self.custom_box.setStyleSheet("""
            QFrame#CustomBox {
                background-color: #222;
                border: 2px dashed #444;
                border-radius: 8px;
            }
        """)
        self.custom_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        c_layout = QVBoxLayout(self.custom_box)
        c_layout.setAlignment(Qt.AlignCenter)
        
        c_lbl = QLabel("Design & Coloring Settings\n(Coming Soon)")
        c_lbl.setAlignment(Qt.AlignCenter)
        c_lbl.setStyleSheet("color: #666; font-size: 14px; font-style: italic;")
        c_layout.addWidget(c_lbl)
        
        right_col.addWidget(self.custom_box)
        
        content_layout.addLayout(right_col, 1) # Equal Width
        
        self.layout.addLayout(content_layout)

        # Load State
        self.load_settings()
        
        # Connect combo change
        self.daily_logs_combo.currentIndexChanged.connect(self.on_combo_changed)

    def load_settings(self):
        # Daily Logs
        val = self.db.get_setting("daily_logs_only", "False")
        idx = 1 if val == "True" else 0
        self.daily_logs_combo.setCurrentIndex(idx)
        self.warning_lbl.setVisible(idx == 1)

        # Startup Setting
        startup_val = self.db.get_setting("run_on_startup", "False")
        # Ensure registry matches this database state
        set_run_on_startup(startup_val == "True")
        self.startup_check.setChecked(startup_val == "True")

        # Discord Globals
        discord_val = self.db.get_setting("discord_enabled", "True")
        is_enabled = (discord_val == "True")
        self.discord_enabled_switch.setChecked(is_enabled)
        self.app_scroll.setEnabled(is_enabled)
        self.reconnect_btn.setVisible(is_enabled)
        
        # Populate App List
        for i in reversed(range(self.app_list_layout.count())): 
            widget = self.app_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.app_switches.clear()
        
        activities = self.db.get_all_activities()
        # Include both apps and IRL activities
        apps = sorted([a for a in activities if a.type in ('app', 'irl')], key=lambda x: x.name.lower())
        
        self.app_rows = []
        
        for app in apps:
            # Row Layout for App + Switch
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0,0,0,0)
            
            # Icon
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(24, 24)
            icon_lbl.setAlignment(Qt.AlignCenter)
            
            # Use app.icon_path if available
            has_icon = False
            if app.icon_path:
                 px = QPixmap(app.icon_path)
                 if not px.isNull():
                     icon_lbl.setPixmap(px.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                     has_icon = True
            
            if not has_icon:
                 if app.type == 'irl':
                     icon_lbl.setText("🌲") # Distinct icon for IRL
                 else:
                     icon_lbl.setText("🔹")
                 icon_lbl.setStyleSheet("color: #5865F2; font-size: 14px;")

            row_layout.addWidget(icon_lbl)
            
            # Clean Name logic: Remove .exe, Title Case
            clean_name = app.name
            if clean_name.lower().endswith(".exe"):
                clean_name = clean_name[:-4]
            clean_name = clean_name.replace("_", " ").title()
            
            lbl = QLabel(clean_name)
            lbl.setStyleSheet("color: #ddd; font-size: 13px; margin-left: 5px;")
            row_layout.addWidget(lbl)
            
            # Add IRL Tag
            if app.type == 'irl':
                 tag = QLabel("IRL")
                 tag.setFont(QFont("Segoe UI", 8, QFont.Bold))
                 tag.setStyleSheet("background-color: #3e3e3e; color: #aaa; padding: 2px 4px; border-radius: 3px; margin-left: 5px;")
                 row_layout.addWidget(tag)
            
            row_layout.addStretch()
            
            switch = ToggleSwitch()
            switch.setChecked(app.discord_visible)
            # Store ID in switch or use closure
            switch.toggled.connect(lambda checked, aid=app.id: self.on_app_toggled_auto(aid, checked))
            
            row_layout.addWidget(switch)
            
            self.app_list_layout.addWidget(row)
            self.app_switches[app.id] = switch
            
            # Store for filtering (search matches against clean_name or original name)
            self.app_rows.append((clean_name.lower(), row))

    def on_combo_changed(self, index):
        self.warning_lbl.setVisible(index == 1)

    def on_discord_toggled_auto(self, checked):
        # 1. Update UI state
        self.app_scroll.setEnabled(checked)
        self.reconnect_btn.setVisible(checked)
        # 2. Auto-save to DB
        self.db.set_setting("discord_enabled", "True" if checked else "False")

    def on_app_toggled_auto(self, activity_id, checked):
        # Auto-save app visibility
        self.db.update_activity_visibility(activity_id, checked)

    def save_settings(self):
        # 1. Update Startup
        is_startup = self.startup_check.isChecked()
        self.db.set_setting("run_on_startup", "True" if is_startup else "False")
        
        # Apply Registry Change immediately
        success = set_run_on_startup(is_startup)
        
        # 2. Daily Logs
        daily_logs_val = "True" if self.daily_logs_combo.currentIndex() == 1 else "False"
        self.db.set_setting("daily_logs_only", daily_logs_val)
        
        if daily_logs_val == "True":
            deleted = self.db.cleanup_old_description_logs()
            msg = f"Settings Saved.\n\nCleanup complete: {deleted} old description logs deleted."
        else:
            msg = "Settings Saved."
            
        if is_startup and not success:
            msg += "\n\nWarning: Could not set Windows Registry to run on startup. Try running as Administrator."
            
        dlg = SavedDialog(msg, self)
        dlg.exec()

    def filter_apps(self, text):
        text = text.lower()
        for name, widget in self.app_rows:
            if text in name:
                widget.setVisible(True)
            else:
                widget.setVisible(False)

    def refresh(self):
        self.load_settings()
