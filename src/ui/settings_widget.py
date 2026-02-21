from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QCheckBox, QComboBox, 
                               QPushButton, QHBoxLayout, QFrame, QDialog, QScrollArea, QSizePolicy, QLineEdit, QColorDialog, QGridLayout)
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QPixmap
from PySide6.QtCore import Qt, QTimer, Property, QSize, QEasingCurve, QPropertyAnimation

from src.utils.startup_manager import set_run_on_startup, check_run_on_startup
from src.ui.styles import THEMES

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
        # Fetch dynamic primary color
        primary_color = "#5865F2"
        try:
            from src.ui.styles import themes_dir, FALLBACK_THEME
            import os, json
            main_theme_path = os.path.join(themes_dir, "theme.json")
            if os.path.exists(main_theme_path):
                with open(main_theme_path, 'r', encoding='utf-8') as f:
                    t = json.load(f)
                    primary_color = t.get('primary', FALLBACK_THEME['primary'])
        except: pass
        
        track_color = QColor(primary_color) if self._checked else QColor("#444")
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
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        
        btn = QPushButton("OK")
        btn.setObjectName("PrimaryButton")
        btn.clicked.connect(self.accept)
        
        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addWidget(btn)
        h_layout.addStretch()
        layout.addLayout(h_layout)


class ResetDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reset All Data")
        self.setFixedSize(400, 250)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Warning label
        warning_lbl = QLabel("⚠ DANGER: This will delete ALL your tracked data, apps, and settings. This action CANNOT be undone.")
        warning_lbl.setWordWrap(True)
        warning_lbl.setAlignment(Qt.AlignCenter)
        warning_lbl.setObjectName("WarningLabel")
        layout.addWidget(warning_lbl)
        
        # Checkbox
        self.confirm_check = QCheckBox("I understand this cannot be undone.")
        layout.addWidget(self.confirm_check)
        
        # Instructions and Input
        inst_lbl = QLabel("Type 'i am sure' below to confirm:")
        inst_lbl.setObjectName("HelperLabel")
        layout.addWidget(inst_lbl)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("i am sure")
        layout.addWidget(self.confirm_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        self.ok_btn = QPushButton("Delete Everything")
        self.ok_btn.setObjectName("DangerButton")
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
        
        # Connect validation
        self.confirm_check.toggled.connect(self.validate)
        self.confirm_input.textChanged.connect(self.validate)

    def validate(self):
        is_checked = self.confirm_check.isChecked()
        is_text_matching = self.confirm_input.text().strip() == "i am sure"
        self.ok_btn.setEnabled(is_checked and is_text_matching)

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
        title.setObjectName("SectionHeader")
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
        general_lbl.setObjectName("SectionHeader")
        left_col.addWidget(general_lbl)
        
        self.general_box = QFrame()
        self.general_box.setObjectName("SettingsCard")
        g_layout = QVBoxLayout(self.general_box)
        g_layout.setSpacing(10)
        g_layout.setContentsMargins(15, 15, 15, 15)
        
        self.startup_check = QCheckBox("Run on Startup")
        
        # We will read from DB, but also verify with the registry.
        # DB will override at load.
        is_startup = check_run_on_startup()
        self.startup_check.setChecked(is_startup)
        
        g_layout.addWidget(self.startup_check)
        
        left_col.addWidget(self.general_box)

        # 2. Data Management Section
        data_lbl = QLabel("Data Management")
        data_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        data_lbl.setObjectName("SectionHeader")
        left_col.addWidget(data_lbl)
        
        self.logs_box = QFrame()
        self.logs_box.setObjectName("SettingsCard")
        
        logs_layout = QVBoxLayout(self.logs_box)
        logs_layout.setSpacing(10)
        logs_layout.setContentsMargins(15, 15, 15, 15)
        
        daily_container = QHBoxLayout()
        daily_container.setAlignment(Qt.AlignLeft)
        daily_lbl = QLabel("Keep Only Daily Logs?")
        daily_container.addWidget(daily_lbl)
        self.daily_logs_combo = QComboBox()
        self.daily_logs_combo.addItems(["No", "Yes"])
        self.daily_logs_combo.setFixedWidth(80)
        daily_container.addWidget(self.daily_logs_combo)
        logs_layout.addLayout(daily_container)
        
        self.warning_lbl = QLabel("⚠ 'Yes' will delete all history except today on save.")
        self.warning_lbl.setObjectName("WarningLabel")
        self.warning_lbl.setVisible(False)
        logs_layout.addWidget(self.warning_lbl)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.setFixedSize(80, 30)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setObjectName("PrimaryButton")
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
        from src.utils.path_utils import get_resource_path
        d_pix = QPixmap(get_resource_path("src/icons/discord_icon.png"))
        if not d_pix.isNull():
            d_icon.setPixmap(d_pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            discord_header.addWidget(d_icon)
            
        discord_lbl = QLabel("Discord Integration")
        discord_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        discord_lbl.setObjectName("SectionHeader")
        discord_header.addWidget(discord_lbl)
        
        left_col.addLayout(discord_header)

        self.discord_box = QFrame()
        self.discord_box.setObjectName("SettingsCard")
        self.discord_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 
        
        d_layout = QVBoxLayout(self.discord_box)
        d_layout.setSpacing(15)
        d_layout.setContentsMargins(15, 15, 15, 15)

        # Master Toggle ROW
        master_row = QHBoxLayout()
        master_lbl = QLabel("Enable Discord Rich Presence")
        master_lbl.setObjectName("SectionHeader")
        master_row.addWidget(master_lbl)
        master_row.addStretch()
        
        self.discord_enabled_switch = ToggleSwitch()
        self.discord_enabled_switch.toggled.connect(self.on_discord_toggled_auto)
        
        self.reconnect_btn = QPushButton("Reconnect")
        self.reconnect_btn.setCursor(Qt.PointingHandCursor)
        self.reconnect_btn.setObjectName("DiscordButton")
        if hasattr(self, 'tracker') and self.tracker:
            self.reconnect_btn.clicked.connect(self.tracker.reconnect_discord)
            
        master_row.addWidget(self.discord_enabled_switch)
        master_row.addWidget(self.reconnect_btn)
        d_layout.addLayout(master_row)
        
        # Search Bar
        search_layout = QHBoxLayout()
        search_icon = QLabel("🔍")
        search_layout.addWidget(search_icon)
        
        self.status_search = QLineEdit()
        self.status_search.setPlaceholderText("Search apps...")
        self.status_search.textChanged.connect(self.filter_apps)
        search_layout.addWidget(self.status_search)
        d_layout.addLayout(search_layout)
        
        helper_lbl = QLabel("Select apps to share on Discord (Auto-Saved):")
        helper_lbl.setObjectName("HelperLabel")
        d_layout.addWidget(helper_lbl)

        self.app_scroll = QScrollArea()
        self.app_scroll.setWidgetResizable(True)
        self.app_scroll.setFixedHeight(300) 
        self.app_scroll.setStyleSheet("""
            QScrollArea { border-radius: 4px; }
            QScrollBar:vertical { width: 10px; }
            QScrollBar::handle:vertical { border-radius: 5px; }
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
        custom_lbl.setObjectName("SectionHeader")
        right_col.addWidget(custom_lbl)
        
        self.custom_box = QFrame()
        self.custom_box.setObjectName("SettingsCard")
        
        c_layout = QVBoxLayout(self.custom_box)
        c_layout.setSpacing(10)
        c_layout.setContentsMargins(15, 15, 15, 15)
        
        c_lbl = QLabel("Select Theme:")
        c_layout.addWidget(c_lbl)
        
        # Theme Buttons Layout
        theme_btn_layout = QHBoxLayout()
        theme_btn_layout.setSpacing(10)
        
        def create_theme_btn(name, bg_color, text_color, theme_id):
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            
            # Keep basic colors inline since they represent that specific theme's preview,
            # but don't hardcode other styling that might clash.
            theme_primary = THEMES.get(theme_id, {}).get("primary", "#5865F2")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    border: 1px solid {theme_primary};
                }}
            """)
            btn.clicked.connect(lambda: self.on_theme_changed(theme_id))
            return btn
            
        for theme_id, theme_data in THEMES.items():
            t_name = theme_data.get("theme_name", theme_id.title())
            bg = theme_data.get("bg_main", "#1e1e1e")
            txt = theme_data.get("text_main", "#e0e0e0")
            btn = create_theme_btn(t_name, bg, txt, theme_id)
            theme_btn_layout.addWidget(btn)
        
        c_layout.addLayout(theme_btn_layout)
        
        # --- Advanced Colors ---
        adv_lbl = QLabel("Advanced Colors:")
        adv_lbl.setStyleSheet("margin-top: 10px; font-weight: bold;")
        c_layout.addWidget(adv_lbl)
        
        adv_grid = QGridLayout()
        adv_grid.setSpacing(10)
        
        self.color_buttons = {} # key -> QPushButton
        
        color_props = [
            ("Background", "bg_main"),
            ("Cards", "card_bg"),
            ("Text", "text_main"),
            ("Accent", "primary"),
            ("Sidebar", "bg_nav")
        ]
        
        for i, (name, key) in enumerate(color_props):
            lbl = QLabel(name)
            lbl.setObjectName("SectionHeader")
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.PointingHandCursor)
            
            # Connect using closure
            btn.clicked.connect(lambda checked=False, k=key: self.pick_custom_color(k))
            
            row = i // 2
            col = (i % 2) * 2
            adv_grid.addWidget(lbl, row, col)
            adv_grid.addWidget(btn, row, col + 1)
            
            self.color_buttons[key] = btn
            
        c_layout.addLayout(adv_grid)
        
        right_col.addWidget(self.custom_box)
        
        # --- Danger Zone ---
        danger_lbl = QLabel("Delete All Data")
        danger_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        danger_lbl.setObjectName("DangerHeader")
        right_col.addWidget(danger_lbl)
        
        self.danger_box = QFrame()
        self.danger_box.setObjectName("DangerBox")
        
        danger_layout = QVBoxLayout(self.danger_box)
        danger_layout.setSpacing(10)
        danger_layout.setContentsMargins(15, 15, 15, 15)
        
        danger_desc = QLabel("Permanently delete all tracked data, settings, and apps. This cannot be undone.")
        danger_desc.setWordWrap(True)
        danger_layout.addWidget(danger_desc)
        
        self.reset_data_btn = QPushButton("Reset All Data")
        self.reset_data_btn.setCursor(Qt.PointingHandCursor)
        self.reset_data_btn.setObjectName("DangerButton")
        self.reset_data_btn.clicked.connect(self.on_reset_data_clicked)
        
        reset_btn_layout = QHBoxLayout()
        reset_btn_layout.addStretch()
        reset_btn_layout.addWidget(self.reset_data_btn)
        danger_layout.addLayout(reset_btn_layout)
        
        right_col.addWidget(self.danger_box)
        
        content_layout.addLayout(right_col, 1) # Equal Width
        
        self.layout.addLayout(content_layout)

        # Load State
        self.load_settings()
        self.update_color_buttons()
        
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
                 icon_lbl.setStyleSheet("font-size: 14px;")

            row_layout.addWidget(icon_lbl)
            
            # Clean Name logic: Remove .exe, Title Case
            clean_name = app.name
            if clean_name.lower().endswith(".exe"):
                clean_name = clean_name[:-4]
            clean_name = clean_name.replace("_", " ").title()
            
            lbl = QLabel(clean_name)
            lbl.setStyleSheet("font-size: 13px; margin-left: 5px; background: transparent; border: none;")
            row_layout.addWidget(lbl)
            
            # Add IRL Tag
            if app.type == 'irl':
                 tag = QLabel("IRL")
                 tag.setFont(QFont("Segoe UI", 8, QFont.Bold))
                 tag.setObjectName("IRLTag")
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

    def set_theme_callback(self, callback):
        self.apply_theme_callback = callback

    def update_color_buttons(self):
        from src.ui.styles import themes_dir
        import os, json
        
        main_theme_path = os.path.join(themes_dir, "theme.json")
        t = {}
        if os.path.exists(main_theme_path):
            with open(main_theme_path, 'r', encoding='utf-8') as f:
                try:
                    t = json.load(f)
                except: pass
                
        for key, btn in self.color_buttons.items():
            color = t.get(key, "#ffffff")
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid #555; border-radius: 4px;")

    def pick_custom_color(self, key):
        from src.ui.styles import themes_dir
        import os, json
        
        main_theme_path = os.path.join(themes_dir, "theme.json")
        t = {}
        if os.path.exists(main_theme_path):
            with open(main_theme_path, 'r', encoding='utf-8') as f:
                try:
                    t = json.load(f)
                except: pass
                
        current_color = t.get(key, "#ffffff")
        
        color = QColorDialog.getColor(QColor(current_color), self, f"Select Color")
        if color.isValid():
            new_hex = color.name()
            t[key] = new_hex
            
            # Sync related text/accent variables if the master color was chosen
            if key == "text_main":
                r, g, b = color.red(), color.green(), color.blue()
                # Qt Stylesheets heavily favor #AARRGGBB or solid #RRGGBB.
                # 65% of 255 is ~165 (0xA5)
                secondary_hex = f"#a5{r:02x}{g:02x}{b:02x}"
                t["text_secondary"] = secondary_hex
                t["nav_text"] = secondary_hex
                
            if key == "primary":
                r, g, b = color.red(), color.green(), color.blue()
                r = max(0, int(r * 0.8))
                g = max(0, int(g * 0.8))
                b = max(0, int(b * 0.8))
                t["primary_hover"] = f"#{r:02x}{g:02x}{b:02x}"
                
            if key == "bg_main":
                r, g, b = color.red(), color.green(), color.blue()
                # Determine if it's a light or dark theme based on perceived brightness
                brightness = (r * 0.299 + g * 0.587 + b * 0.114)
                if brightness > 128:
                    # Light theme -> bg slightly darker for inputs (e.g. from f0f0f0 -> e0e0e0)
                    r_i = max(0, int(r * 0.95))
                    g_i = max(0, int(g * 0.95))
                    b_i = max(0, int(b * 0.95))
                else:
                    # Dark theme -> bg slightly lighter for inputs (e.g. from 1e1e1e -> 2d2d2d)
                    r_i = min(255, int(r * 1.5) if r > 0 else 30)
                    g_i = min(255, int(g * 1.5) if g > 0 else 30)
                    b_i = min(255, int(b * 1.5) if b > 0 else 30)
                
                t["input_bg"] = f"#{r_i:02x}{g_i:02x}{b_i:02x}"
                t["card_bg"] = f"#{r_i:02x}{g_i:02x}{b_i:02x}"
                
            if key == "bg_nav":
                r, g, b = color.red(), color.green(), color.blue()
                brightness = (r * 0.299 + g * 0.587 + b * 0.114)
                if brightness > 128:
                    # Light nav -> hover slightly darker
                    r_h = max(0, int(r * 0.95))
                    g_h = max(0, int(g * 0.95))
                    b_h = max(0, int(b * 0.95))
                else:
                    # Dark nav -> hover slightly lighter
                    r_h = min(255, int(r * 1.5) if r > 0 else 30)
                    g_h = min(255, int(g * 1.5) if g > 0 else 30)
                    b_h = min(255, int(b * 1.5) if b > 0 else 30)
                
                t["nav_hover"] = f"#{r_h:02x}{g_h:02x}{b_h:02x}"
            
            try:
                with open(main_theme_path, 'w', encoding='utf-8') as f:
                    json.dump(t, f, indent=4)
            except Exception as e:
                print(f"Failed to save color: {e}")
                
            self.update_color_buttons()
            
            # Apply instantly
            if hasattr(self, 'apply_theme_callback') and self.apply_theme_callback:
                self.apply_theme_callback("theme")

    def on_theme_changed(self, theme_name):
        # Write to main theme.json
        from src.ui.styles import THEMES, themes_dir
        import json
        import os
        
        target_theme_data = THEMES.get(theme_name)
        if target_theme_data:
            main_theme_path = os.path.join(themes_dir, "theme.json")
            try:
                with open(main_theme_path, 'w', encoding='utf-8') as f:
                    json.dump(target_theme_data, f, indent=4)
            except Exception as e:
                print(f"Failed to write to theme.json: {e}")

        # Save to DB (optional now that theme.json drives it, but good for record)
        self.db.set_setting("theme", theme_name)
        
        self.update_color_buttons()
        
        # Apply instantly
        if hasattr(self, 'apply_theme_callback') and self.apply_theme_callback:
            self.apply_theme_callback("theme")

    def refresh(self):
        self.load_settings()

    def on_reset_data_clicked(self):
        from PySide6.QtWidgets import QMessageBox, QApplication
        import shutil
        import os

        dialog = ResetDataDialog(self)
        if dialog.exec():
            # User confirmed
            
            # 1. Stop Tracker safely
            if self.tracker:
                self.tracker.stop()

            # 2. Wipe DB
            success = self.db.wipe_data()

            # 3. Wipe Icons
            icons_dir = os.path.join("assets", "icons")
            if os.path.exists(icons_dir):
                try:
                    shutil.rmtree(icons_dir)
                    os.makedirs(icons_dir)
                except Exception as e:
                    print(f"Error clearing icons: {e}")

            if success:
                QMessageBox.information(
                    self, 
                    "Reset Complete", 
                    "All data has been deleted. Gainhour will now close.\n\nPlease restart the application for a fresh start."
                )
                QApplication.quit()
            else:
                QMessageBox.critical(
                    self,
                    "Reset Failed",
                    "An error occurred while wiping the database. Please check the logs."
                )
