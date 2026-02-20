from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QScrollArea, QPushButton, QLineEdit, QComboBox, QSizePolicy, QGridLayout, QLayout, QStackedWidget, QCheckBox)
from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon, QFontMetrics, QPainter, QColor, QPen
from PySide6.QtWidgets import QMessageBox
import os
import time

from src.core.window_watcher import get_open_windows
from src.ui.add_activity_dialog import AddActivityDialog

from src.utils.text_utils import format_app_name



class ActiveSessionCard(QFrame):
    stop_clicked = Signal()
    discord_selected = Signal(bool) 
    
    def __init__(self, name, status, is_auto, activity_obj, icon_manager, tracker=None, db=None, window_title=""):
        super().__init__()
        self.name = name
        self.display_name = format_app_name(name)
        # ... (rest of init)
    
    def set_live_style(self, is_live):
        """Updates style if this is the active Discord activity."""
        if is_live:
            self.setStyleSheet("""
                QFrame#ActiveSessionCard {
                    background-color: #252526;
                    border: 1px solid #2fa51f; /* Green Border */
                    border-radius: 8px;
                }
                /* ... other styles ... */
            """ + self._get_base_styles())
            # Maybe show a "LIVE" label?
            # Status Badge Logic
            if hasattr(self, 'status_badge'):
                # If Checked -> FORCED
                # If Unchecked but Live (Auto) -> AUTO (or MANUAL if manual session)
                # If Checked -> could be Auto or Forced.
                # Check actual Pinned state
                pinned = self.tracker.discord_pinned_activity
                is_actually_pinned = False
                if pinned:
                     if hasattr(pinned, 'name') and pinned.name == self.name:
                          is_actually_pinned = True
                     elif hasattr(pinned, 'id') and hasattr(self.activity_obj, 'id') and pinned.id == self.activity_obj.id:
                          is_actually_pinned = True
                
                if is_actually_pinned:
                     self.status_badge.setText("FORCED")
                     self.status_badge.setStyleSheet("background-color: #d32f2f; color: white; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 10px;")
                else:
                     self.status_badge.setText("AUTO" if self.is_auto else "MANUAL")
                     color = "#007acc" if self.is_auto else "#a5861f"
                     self.status_badge.setStyleSheet(f"background-color: {color}; color: white; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 10px;")
        else:
             # Revert
             self.setStyleSheet("""
                QFrame#ActiveSessionCard {
                    background-color: #252526;
                    border: 1px solid #3e3e3e;
                    border-radius: 8px;
                }
             """ + self._get_base_styles())
             if hasattr(self, 'status_badge'):
                 self.status_badge.setText("AUTO" if self.is_auto else "MANUAL")
                 color = "#007acc" if self.is_auto else "#a5861f"
                 self.status_badge.setStyleSheet(f"background-color: {color}; color: white; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 10px;")

    def _get_base_styles(self):
        return """
            QPushButton#StopButton {
                background-color: transparent;
                border: 1px solid #cc4444;
                color: #ff6666;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton#StopButton:hover {
                background-color: #cc4444;
                color: white;
            }
        """

    def __init__(self, name, status, is_auto, activity_obj, icon_manager, tracker=None, db=None, window_title=""):
        super().__init__()
        self.name = name
        self.display_name = format_app_name(name)
        self.icon_manager = icon_manager
        self.tracker = tracker 
        self.db = db
        self.activity_obj = activity_obj 
        self.window_title = window_title 
        self.is_auto = is_auto
        
        self.setObjectName("ActiveSessionCard")
        # Ensure style is applied init
        self.set_live_style(False) 
        
        # ... (Rest of Init)
        # Dynamic Size - Smart Width
        # ... (Width calc seems same, maybe +30 for new button)
        
        base_elements_width = 150 # Reduced back
        fm_name = QFontMetrics(QFont("Segoe UI", 11, QFont.Bold))
        name_width = fm_name.horizontalAdvance(self.display_name)
        
        content_width = base_elements_width + name_width + 40 + 30 # +30 for Checkbox
        
        MIN_WIDTH = 375 # Increased for Checkbox
        MAX_WIDTH = MIN_WIDTH + 100 
        
        final_width = max(MIN_WIDTH, min(content_width, MAX_WIDTH))
        
        self.setFixedWidth(final_width)
        self.setFixedHeight(200)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10) 
        layout.setSpacing(12)
        
        # 0. Discord Checkbox (New)
        self.discord_chk = QCheckBox()
        self.discord_chk.setCursor(Qt.PointingHandCursor)
        self.discord_chk.setToolTip("Force Pin to Discord")
        self.discord_chk.setFixedSize(28, 28) # Ensure it has size
        self.discord_chk.setStyleSheet("""
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
                border-radius: 12px;
                subcontrol-position: center;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2f3136; /* Discord Dark */
                border: 2px solid #555;
                image: none;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #7289da;
            }
            QCheckBox::indicator:checked {
                border: none;
                background-color: transparent;
                image: url(src/icons/discord_icon.png);
            }
        """)
        # If we don't have the white icon easily, just use color. "checkbox for active activities" - standard check is fine.
        # User said "checkbox with discord icon"... I'll try to find if I can reuse styling or just keep simple check.
        # "remove the checkbox with discord icon... add checkbox" - imply standard check?
        # "when i choose it it should not change... otherwise auto"
        
        self.discord_chk.clicked.connect(self.discord_selected)
        layout.addWidget(self.discord_chk)
        
        # 1. Icon (Left)
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(40, 40)
        self.update_icon()
        layout.addWidget(self.icon_lbl)
        
        # 2. Info (Middle)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 4, 0, 4)
        
        # Name
        name_lbl = QLabel(self.display_name)
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_lbl.setStyleSheet("color: white; border: none; background: transparent;")
        info_layout.addWidget(name_lbl)
        
        # Description Logic
        if is_auto:
            # Auto: Show Window Title + Stats
            disp_title = self.window_title if self.window_title else "Application"
            
            # Container for Title + Stats
            desc_layout = QVBoxLayout()
            desc_layout.setSpacing(2)
            desc_layout.setContentsMargins(0,0,0,0)
            
            self.desc_lbl = QLabel(disp_title)
            self.desc_lbl.setFont(QFont("Segoe UI", 9))
            self.desc_lbl.setStyleSheet("color: #aaaaaa; border: none; background: transparent;")
            self.desc_lbl.setWordWrap(True) 
            self.desc_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            desc_layout.addWidget(self.desc_lbl)
            
            # Stats Label for Title
            self.desc_stats_lbl = QLabel("")
            self.desc_stats_lbl.setFont(QFont("Segoe UI", 8))
            self.desc_stats_lbl.setStyleSheet("color: #666666; margin-top: 2px;")
            desc_layout.addWidget(self.desc_stats_lbl)
            
            info_layout.addLayout(desc_layout)
        else:
            # Manual / Forced: Show Button if empty/default, else Label (clickable?)
            # Logic: If description is notably set by user, show it. If likely default ("Manual Session"), show button.
            # But user asked: "do not add description instead but little button called add description"
            
            # Check current description
            current_desc = self.window_title
            
            self.desc_stack = QStackedWidget()
            self.desc_stack.setFixedHeight(30) # Fixed height for consistency
            
            # Page 1: Button
            btn_page = QWidget()
            btn_layout = QHBoxLayout(btn_page)
            btn_layout.setContentsMargins(0,0,0,0)
            btn_layout.setAlignment(Qt.AlignLeft)
            
            self.add_desc_btn = QPushButton("+ Add Description")
            self.add_desc_btn.setCursor(Qt.PointingHandCursor)
            self.add_desc_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #007acc;
                    border: 1px dashed #007acc;
                    border-radius: 4px;
                    font-size: 10px;
                    padding: 4px 8px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: rgba(0, 122, 204, 0.1);
                }
            """)
            self.add_desc_btn.clicked.connect(self.prompt_description)
            btn_layout.addWidget(self.add_desc_btn)
            
            # Page 2: Label (User defined description)
            lbl_page = QWidget()
            lbl_layout = QHBoxLayout(lbl_page)
            lbl_layout.setContentsMargins(0,0,0,0)
            lbl_layout.setAlignment(Qt.AlignLeft)
            
            self.user_desc_lbl = QLabel(current_desc)
            self.user_desc_lbl.setFont(QFont("Segoe UI", 9))
            self.user_desc_lbl.setStyleSheet("color: #aaaaaa;")
            # Make clickable to edit again
            self.user_desc_lbl.setCursor(Qt.PointingHandCursor)
            self.user_desc_lbl.mousePressEvent = self.prompt_description 
            lbl_layout.addWidget(self.user_desc_lbl)
            
            # Edit button small
            edit_btn = QPushButton("✎")
            edit_btn.setFixedSize(20, 20)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet("color: #666; background: transparent; border: none;")
            edit_btn.clicked.connect(self.prompt_description)
            lbl_layout.addWidget(edit_btn)

            self.desc_stack.addWidget(btn_page)
            self.desc_stack.addWidget(lbl_page)
            
            info_layout.addWidget(self.desc_stack)
            
            # Determine initial state
            # If description is empty or "Manual Session" (default from code elsewhere), show button
            if not current_desc or current_desc == "Manual Session":
                self.desc_stack.setCurrentIndex(0)
            else:
                self.desc_stack.setCurrentIndex(1)
        
        # Timer
        self.timer_lbl = QLabel("00:00:00")
        self.timer_lbl.setFont(QFont("Roboto Medium", 16, QFont.Bold))
        self.timer_lbl.setStyleSheet("color: #e0e0e0; border: none; background: transparent;")
        info_layout.addWidget(self.timer_lbl)
        
        # Stats
        self.stats_lbl = QLabel("Total: 0h 0m")
        self.stats_lbl.setStyleSheet("color: #999; font-size: 10px; border: none; background: transparent;")
        info_layout.addWidget(self.stats_lbl)
        
        layout.addLayout(info_layout)
        
        # 3. Actions (Right)
        action_layout = QVBoxLayout()
        action_layout.setSpacing(0)
        # Remove alignment to allow stretch to work full height
        # action_layout.setAlignment(Qt.AlignRight) 
        
        # Status Badge (Top)
        if is_auto:
            self.status_badge = QLabel("AUTO")
            self.status_badge.setStyleSheet("""
                background-color: #007acc; 
                color: white; 
                border-radius: 4px; 
                padding: 4px 8px; 
                font-size: 10px; 
                font-weight: bold;
            """)
        else:
            self.status_badge = QLabel("FORCED")
            self.status_badge.setStyleSheet("""
                background-color: #a5861f; 
                color: white; 
                border-radius: 4px; 
                padding: 4px 8px; 
                font-size: 10px; 
                font-weight: bold;
            """)
        # self.status_badge.setFixedHeight(20) # Auto height with padding
        self.status_badge.setAlignment(Qt.AlignCenter)
        
        # Container for badge to ensure it aligns top-right
        badge_container = QHBoxLayout()
        badge_container.setContentsMargins(0,0,0,0)
        badge_container.addStretch()
        badge_container.addWidget(self.status_badge)
        
        action_layout.addLayout(badge_container)
        
        # Push everything else down
        action_layout.addStretch()
        
        # Stop Button (Bottom)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("StopButton")
        self.stop_btn.setFixedSize(70, 30)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        
        # Container for button to align right
        btn_container = QHBoxLayout()
        btn_container.setContentsMargins(0,0,0,0)
        btn_container.addStretch()
        btn_container.addWidget(self.stop_btn)
        
        action_layout.addLayout(btn_container)
        
        layout.addLayout(action_layout)
        
    def update_icon(self):
        icon_path = self.icon_manager.get_icon_path(self.name)
        if icon_path and os.path.exists(icon_path):
             pix = QPixmap(icon_path)
             if not pix.isNull():
                 self.icon_lbl.setPixmap(pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                 self.icon_lbl.setStyleSheet("background: transparent; border: none;")
                 return
        
        self.icon_lbl.setText(self.name[:2].upper())
        self.icon_lbl.setStyleSheet("background-color: #333; color: white; border-radius: 6px; qproperty-alignment: AlignCenter; font-weight: bold; font-size: 11px;")

    def update_description(self, new_title):
        self.window_title = new_title
        if self.is_auto and hasattr(self, 'desc_lbl'):
             self.desc_lbl.setText(new_title)

    def update_stats(self, current_sec, today_sec, total_sec):
        # Timer
        h, r = divmod(current_sec, 3600)
        m, s = divmod(r, 60)
        self.timer_lbl.setText(f"{h:02}:{m:02}:{s:02}")
        
        # Stats
        h1, m1 = divmod(today_sec // 60, 60)
        h2, m2 = divmod(total_sec // 60, 60)
        self.stats_lbl.setText(f"Today: {int(h1)}h {int(m1)}m  •  Total: {int(h2)}h {int(m2)}m")

        # Description Stats (Auto only)
        if self.is_auto and self.db and self.activity_obj and self.window_title:
             # Fetch detailed stats for this specific window title
             desc_stats = self.db.get_description_stats(self.activity_obj.id, self.window_title)
             
             count = desc_stats['count']
             d_total = desc_stats['total_seconds']
             dh, dr = divmod(d_total, 3600)
             dm, _ = divmod(dr, 60)
             
             self.desc_stats_lbl.setText(f"Title used {count} times • {int(dh)}h {int(dm)}m")

    def prompt_description(self, event=None):
        if not self.db or not self.activity_obj: return
        
        from PySide6.QtWidgets import QInputDialog, QLineEdit
        
        current = self.window_title
        if current == "Manual Session": current = ""
        
        text, ok = QInputDialog.getText(self, "Add Description", "Enter description:", QLineEdit.Normal, current)
        
        if ok and text:
            # Update DB (and Log)
            self.activity_obj.description = text
            self.db.update_activity(self.activity_obj.id, description=text)
            
            # Update Tracker Log if manual
            if not self.is_auto and self.tracker:
                 self.tracker.update_manual_description(self.activity_obj.id, text)
            
            # Update UI
            self.window_title = text
            self.user_desc_lbl.setText(text)
            self.desc_stack.setCurrentIndex(1)
        # If user clears it?
        elif ok and not text:
            # Reset
             self.activity_obj.description = "Manual Session" # Or None? keeping simple
             self.db.update_activity(self.activity_obj.id, description="Manual Session")
             self.window_title = "Manual Session"
             self.desc_stack.setCurrentIndex(0)

class HorizontalScrollArea(QScrollArea):
    def wheelEvent(self, event):
        if event.angleDelta().y() != 0:
            # Map vertical wheel to horizontal scroll (standard mouse wheel)
            # Adjust speed/sensitivity if needed
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - event.angleDelta().y()
            )
            event.accept()
        else:
            super().wheelEvent(event)

class HomeWidget(QWidget):
    def __init__(self, tracker, db, icon_manager):
        super().__init__()
        self.tracker = tracker
        self.db = db
        self.icon_manager = icon_manager
        self.active_cards = {}
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(20)
        self.layout.setContentsMargins(40, 40, 40, 40)
        
        # Header: Active Sessions + Total Timer
        self.create_header()
        self.layout.addWidget(self.header_frame)
        
        # Controls: Search, Filter, Add IRL
        self.create_controls()
        self.layout.addWidget(self.controls_frame)
        
        # Apps List
        self.apps_label = QLabel("All Applications")
        self.apps_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.apps_label.setStyleSheet("color: white; margin-top: 10px;")
        self.layout.addWidget(self.apps_label)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.apps_container = QWidget()
        self.apps_layout = QVBoxLayout(self.apps_container)
        self.apps_layout.setAlignment(Qt.AlignTop)
        self.apps_layout.setSpacing(8)
        self.scroll.setWidget(self.apps_container)
        
        self.layout.addWidget(self.scroll)
        
        self.last_refresh = 0
        
    def create_header(self):
        self.header_frame = QFrame()
        # Responsive height - adjusted for compacted cards (100px card + margins + scrollbar)
        # Included label height approx 30px + spacing 10px + scroll 250px = ~290px
        # Let's remove fixed height constraint to allow natural expansion or set a reasonable min
        self.header_frame.setMinimumHeight(290)
        
        # Main Vertical Layout (Label on top, content below)
        main_v_layout = QVBoxLayout(self.header_frame)
        main_v_layout.setContentsMargins(0,0,0,0)
        main_v_layout.setSpacing(10) # Spacing between label and content
        
        # 1. Label
        lbl = QLabel("Active Sessions")
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setStyleSheet("color: white;")
        
        # 1b. Reconnect Discord Button (Top Right)
        self.reconnect_btn = QPushButton("Reconnect to Discord")
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
            }
            QPushButton:hover {
                background-color: #4752C4;
            }
        """)
        self.reconnect_btn.clicked.connect(self.tracker.reconnect_discord)
        # Hide initially, updated in update_data
        self.reconnect_btn.setVisible(False)
        
        header_top_layout = QHBoxLayout()
        header_top_layout.addWidget(lbl)
        header_top_layout.addStretch()
        header_top_layout.addWidget(self.reconnect_btn)
        
        main_v_layout.addLayout(header_top_layout)
        
        # 2. Content Row (Scroll Area + Total Card)
        content_h_layout = QHBoxLayout()
        content_h_layout.setSpacing(20)
        
        # --- Active Sessions Scroll Area ---
        self.active_scroll = HorizontalScrollArea()
        self.active_scroll.setObjectName("ActivityCard") # Reuse card style for the CONTAINER BOX
        self.active_scroll.setWidgetResizable(True)
        self.active_scroll.setFrameShape(QFrame.NoFrame)
        # Fix: Scrollbar always visible as requested
        self.active_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.active_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Tweak height to remove "void" - calculated: 200 (card) + 20 (margins) + 12 (scrollbar) = 232 ~ 250 safe
        self.active_scroll.setFixedHeight(250)
        
        self.active_scroll.setStyleSheet("""
             QScrollArea#ActivityCard {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 8px;
             }
             QWidget { background: transparent; }
             QScrollBar:horizontal {
                height: 12px;
                background: #1e1e1e;
                margin: 0px 0px 0px 0px;
             }
             QScrollBar::handle:horizontal {
                background: #444;
                min-width: 20px;
                border-radius: 6px;
             }
             QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
             }
        """)
        
        # Active Sessions Container
        self.active_area = QFrame()
        self.active_area.setStyleSheet("background: transparent;")
        
        self.active_layout = QHBoxLayout(self.active_area) 
        self.active_layout.setSpacing(10)
        self.active_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) # Center vertically to avoid gaps
        self.active_layout.setContentsMargins(10, 5, 10, 5) # Tighter margins
        # Critical: Force the container to be at least the size of its content
        self.active_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        
        self.active_scroll.setWidget(self.active_area)
        
        content_h_layout.addWidget(self.active_scroll, 1) # Give stretch
        
        # --- Total Today Timer ---
        self.total_card = QFrame()
        self.total_card.setName = "ActivityCard" # Reuse style
        self.total_card.setFixedWidth(240)
        # Match height of the scroll area for symmetry
        self.total_card.setFixedHeight(250) 
        self.total_card.setStyleSheet("""
            background-color: #252526; 
            border-radius: 8px; 
            border: 1px solid #3e3e3e;
        """)
        
        t_layout = QVBoxLayout(self.total_card)
        t_layout.setAlignment(Qt.AlignCenter)
        
        lbl_total = QLabel("TOTAL TODAY")
        lbl_total.setStyleSheet("color: #a0a0a0; font-weight: bold; font-size: 12px; letter-spacing: 1px;")
        t_layout.addWidget(lbl_total)
        
        self.total_timer_lbl = QLabel("00:00:00")
        self.total_timer_lbl.setFont(QFont("Roboto Medium", 28, QFont.Bold))
        self.total_timer_lbl.setStyleSheet("color: #007acc;")
        t_layout.addWidget(self.total_timer_lbl)
        
        content_h_layout.addWidget(self.total_card)
        
        # Add content row to main layout
        main_v_layout.addLayout(content_h_layout)
        
    def create_controls(self):
        self.controls_frame = QFrame()
        layout = QHBoxLayout(self.controls_frame)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(10)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search applications...")
        self.search_input.setFixedWidth(300)
        self.search_input.setMinimumHeight(35)
        self.search_input.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search_input)
        
        # Filter
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Apps", "IRL"])
        self.filter_combo.setFixedWidth(120)
        self.filter_combo.setMinimumHeight(35)
        self.filter_combo.setCurrentIndex(0)
        self.filter_combo.currentTextChanged.connect(self.refresh_list)
        layout.addWidget(self.filter_combo)
        
        layout.addStretch()
        
        # Add IRL
        add_btn = QPushButton("+ Add IRL Activity")
        add_btn.setObjectName("PrimaryButton")
        add_btn.setMinimumHeight(35)
        add_btn.clicked.connect(self.open_add_dialog)
        layout.addWidget(add_btn)

    def update_data(self):
        # 0. Update Reconnect Button Visibility
        is_discord_enabled = self.tracker.storage.get_setting("discord_enabled", "True") == "True"
        self.reconnect_btn.setVisible(is_discord_enabled)
        
        # 1. Update Active Sessions UI
        self.update_active_sessions()
        
        # 2. Update Total Timer
        total = self.db.get_total_today_duration()
        
        # Add current running (Auto)
        if self.tracker.current_activity:
             pname = self.tracker.current_activity.name
             if pname in self.tracker.open_sessions:
                  total += int(self.tracker.open_sessions[pname]['accumulated_time'])
        
        # Add current running (Manual)
        session = self.db.get_session()
        try:
            for act_id, log_id in list(self.tracker.manual_sessions.items()):
                 from src.database.models import ActivityLog
                 log = session.query(ActivityLog).get(log_id)
                 if log: total += int(time.time() - log.start_time.timestamp())
        except:
            pass
        finally:
            session.close()

        h, r = divmod(int(total), 3600)
        m, s = divmod(r, 60)
        self.total_timer_lbl.setText(f"{h:02}:{m:02}:{s:02}")
        
        # 3. Refresh List (throttled)
        if time.time() - self.last_refresh > 2.0: # 2 seconds throttle
            self.refresh_list()
            self.last_refresh = time.time()
            
    def update_active_sessions(self):
        # Gather current active sessions
        current_active_ids = set()
        
        # 1. AUTO Session
        if self.tracker.current_activity:
             name = self.tracker.current_activity.name
             sid = f"AUTO_{name}"
             current_active_ids.add(sid)
             
             # Get current window title
             # Use last_window_title from tracker since activity.description is NULL for apps
             desc = self.tracker.last_window_title if self.tracker.last_window_title else self.tracker.current_activity.description
             
             if sid not in self.active_cards:
                 # Create
                 card = ActiveSessionCard(name, "AUTO", True, None, self.icon_manager, self.tracker, self.db, window_title=desc)
                 card.stop_clicked.connect(lambda n=name: self.tracker.set_ignore_app(n, True))
                 
                 # Connect selection
                 # We need the ACTUAL activity object to pin. For 'AUTO', it is self.tracker.current_activity usually?
                 # Warning: active_cards key is sid="AUTO_Chrome".
                 # If we pin, we want to pin the activity object.
                 # access current?
                 current_act = self.tracker.current_activity
                 if current_act and current_act.name == name:
                      card.discord_selected.connect(lambda checked, a=current_act: self.tracker.set_discord_pin(a if checked else None))
                 
                 self.active_layout.addWidget(card)
                 self.active_cards[sid] = card
             else:
                 # Update description dynamically if changed
                 if self.active_cards[sid].window_title != desc:
                     self.active_cards[sid].update_description(desc)

             # Check if App is Enabled for Discord
             # Need to fetch fresh activity object or check DB
             # current_activity might be stale regarding discord_visible?
             # tracker updates it.
             is_visible = True
             if self.tracker.current_activity:
                 # Check DB for fresh state
                 act = self.db.get_activity_by_id(self.tracker.current_activity.id)
                 if act: is_visible = act.discord_visible
             
             # Also check Global Setting
             is_global_enabled = self.tracker.storage.get_setting("discord_enabled", "True") == "True"
             
             should_show_checkbox = is_visible and is_global_enabled
             self.active_cards[sid].discord_chk.setVisible(should_show_checkbox)

             # Update Live Status & Checkbox
             # User wants Checkbox to reflect ACTIVE status
             actual_target = getattr(self.tracker, 'discord_last_target_name', None)
             is_live_now = (actual_target == name)
             
             self.active_cards[sid].discord_chk.blockSignals(True)
             self.active_cards[sid].discord_chk.setChecked(is_live_now)
             self.active_cards[sid].discord_chk.blockSignals(False)
             
             self.active_cards[sid].set_live_style(is_live_now)

             # Update Data
             duration = 0
             if name in self.tracker.open_sessions:
                  duration = int(self.tracker.open_sessions[name]['accumulated_time'])
             
             today = self.db.get_today_duration(name)
             total = self.db.get_activity_duration(name)
             
             self.active_cards[sid].update_stats(duration, today, total)

        # 2. MANUAL Sessions
        for act_id, log_id in self.tracker.manual_sessions.items():
             act = self.db.get_activity_by_id(act_id)
             if act:
                 sid = f"MANUAL_{act.id}"
                 current_active_ids.add(sid)
                 
                 desc = getattr(act, 'description', "Manual Session")
                 # Check if description is stored in DB or we need to look it up from open windows?
                 # If act is from DB, it might not have the realtime window title if description isn't a column.
                 # Fallback: "Manual Tracking"
                 
                 if sid not in self.active_cards:
                     # Force empty description for new manual cards so button shows
                     card = ActiveSessionCard(act.name, "MANUAL", False, act, self.icon_manager, self.tracker, self.db, window_title="")
                     card.stop_clicked.connect(lambda a=act: self.tracker.stop_manual_session(a))
                     
                     # Connect Discord Checkbox
                     card.discord_selected.connect(lambda checked, a=act: self.tracker.set_discord_pin(a if checked else None))
                     
                     
                     self.active_layout.addWidget(card)
                     self.active_cards[sid] = card
                 
             # Check Visibility
             is_visible = getattr(act, 'discord_visible', True)
             # Also check Global Setting
             is_global_enabled = self.tracker.storage.get_setting("discord_enabled", "True") == "True"
             
             should_show_checkbox = is_visible and is_global_enabled
             self.active_cards[sid].discord_chk.setVisible(should_show_checkbox)
                 
             # Update Live Status & Checkbox
             actual_target = getattr(self.tracker, 'discord_last_target_name', None)
             is_live_now = (actual_target == act.name)
             
             self.active_cards[sid].discord_chk.blockSignals(True)
             self.active_cards[sid].discord_chk.setChecked(is_live_now)
             self.active_cards[sid].discord_chk.blockSignals(False)
             
             self.active_cards[sid].set_live_style(is_live_now)

                     
             # Update Data
             duration = 0
             session = self.db.get_session()
             try:
                 from src.database.models import ActivityLog
                 log = session.query(ActivityLog).get(log_id)
                 if log: duration = int(time.time() - log.start_time.timestamp())
             except: pass
             finally: session.close()
                 
             today = self.db.get_today_duration(act.name, act.type)
             total = self.db.get_activity_duration(act.name, act.type)
             
             self.active_cards[sid].update_stats(duration, today, total)

        # Remove stale cards
        for sid in list(self.active_cards.keys()):
            if sid not in current_active_ids:
                card = self.active_cards.pop(sid)
                card.deleteLater()
                
        # Show "No active sessions" if empty
        if not current_active_ids:
             if not hasattr(self, 'no_active_lbl'):
                 self.no_active_lbl = QLabel("No active sessions")
                 self.no_active_lbl.setStyleSheet("color: #666; font-size: 14px;")
                 self.no_active_lbl.setAlignment(Qt.AlignCenter)
                 self.active_layout.addWidget(self.no_active_lbl)
             self.no_active_lbl.show()
        else:
             if hasattr(self, 'no_active_lbl'): self.no_active_lbl.hide()
        
    def refresh_list(self):
        current_data = {}
        # DB Activities
        all_acts = self.db.get_all_activities()
        for a in all_acts:
            current_data[a.name] = {
                'name': a.name, 'type': a.type, 'icon': a.icon_path, 'is_irl': a.type == 'irl'
            }
            
        # Open Windows
        windows = get_open_windows()
        for w in windows:
            name = w['process_name']
            if name not in current_data:
                current_data[name] = {
                    'name': name, 'type': 'app', 'icon': w.get('executable_path'), 'is_irl': False
                }
            else:
                 if not current_data[name]['icon']:
                      current_data[name]['icon'] = w.get('executable_path')

        # Filter
        filtered_items = []
        search_txt = self.search_input.text().lower()
        filter_mode = self.filter_combo.currentText()
        
        for name, info in current_data.items():
            if filter_mode == "Apps" and info['is_irl']: continue
            if filter_mode == "IRL" and not info['is_irl']: continue
            if search_txt and search_txt not in name.lower(): continue
            
            total = self.db.get_activity_duration(name, info['type'])
            today = self.db.get_today_duration(name, info['type'])
            filtered_items.append((info, total, today))
            
        filtered_items.sort(key=lambda x: x[1], reverse=True)
        
        # Render
        v_scroll = self.scroll.verticalScrollBar().value()
        
        while self.apps_layout.count():
             child = self.apps_layout.takeAt(0)
             if child.widget(): child.widget().deleteLater()
             
        # Limit to top 50 to avoid lag
        for info, total, today in filtered_items[:50]: 
             self.create_app_row(info, total, today)
             
        self.scroll.verticalScrollBar().setValue(v_scroll)

    def create_app_row(self, info, total_seconds, today_seconds):
        row = QFrame()
        # Row styling
        row.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: #333333;
            }
        """)
        row.setFixedHeight(55)
        
        layout = QHBoxLayout(row)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(15)
        
        # Icon
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(32, 32)
        
        if info['icon'] and os.path.exists(info['icon']):
             pix = QPixmap(info['icon'])
             if not pix.isNull():
                 icon_lbl.setPixmap(pix.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                 icon_lbl.setStyleSheet("background: transparent; border: none;")
        else:
             # Text fallback
             icon_lbl.setText(info['name'][:2].upper())
             icon_lbl.setStyleSheet("background-color: #444; color: white; border-radius: 4px; qproperty-alignment: AlignCenter;")
        
        layout.addWidget(icon_lbl)
        
        # Name
        formatted_name = format_app_name(info['name'])
        
        name_lbl = QLabel(formatted_name)
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_lbl.setStyleSheet("color: white; border: none; background: transparent;")
        layout.addWidget(name_lbl)
        
        layout.addStretch()
        if info['is_irl']:
             tag = QLabel("IRL")
             tag.setFont(QFont("Segoe UI", 8, QFont.Bold))
             tag.setStyleSheet("background-color: #3e3e3e; color: #aaa; padding: 2px 6px; border-radius: 4px;")
             layout.addWidget(tag)
             
        
        # Time
        h_tot, m_tot = divmod(total_seconds // 60, 60)
        h_today, m_today = divmod(today_seconds // 60, 60)
        
        # Format: Today: 0h 10m • Total: 5h 20m
        time_text = f"Today: {int(h_today)}h {int(m_today)}m  •  Total: {int(h_tot)}h {int(m_tot)}m"
        time_lbl = QLabel(time_text)
        time_lbl.setFont(QFont("Segoe UI", 10))
        time_lbl.setStyleSheet("background: transparent; color: #888;")
        layout.addWidget(time_lbl)
        
        if info['is_irl']:
             # Edit Button
             edit_btn = QPushButton("Edit✎")
             edit_btn.setFixedSize(65, 30) # Wider for text
             edit_btn.setCursor(Qt.PointingHandCursor)
             edit_btn.setToolTip("Edit Info")
             # Use a visible style
             edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #333;
                    color: #ddd;
                    border: 1px solid #555;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #444;
                    color: white;
                    border-color: #666;
                }
             """)
             # Need act for editing
             act_for_edit = self.db.get_or_create_activity(info['name'], info['type'])
             edit_btn.clicked.connect(lambda: self.open_add_dialog(act_for_edit))
             layout.addWidget(edit_btn)
        
        # Delete Button (Trash)
        del_btn = QPushButton("Del🗑")
        del_btn.setFixedSize(65, 30)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setToolTip(f"Delete {info['name']}")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888;
                border: 1px solid #444;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #440000;
                color: #ff4444;
                border-color: #aa3333;
            }
        """)
        # We need the activity object to delete
        # Note: get_or_create_activity is cheap if exists, but we are calling it multiple times.
        # It's fine for now.
        act_del = self.db.get_or_create_activity(info['name'], info['type'])
        del_btn.clicked.connect(lambda: self.delete_activity_ui(act_del))
        layout.addWidget(del_btn)

        # Button
        btn = QPushButton("Start")
        btn.setFixedSize(70, 30)
        
        act = self.db.get_or_create_activity(info['name'], info['type'])
        if self.tracker.is_manual_running(act.id):
             btn.setText("Stop")
             btn.setObjectName("StopButton")
             # Force style - Red Outline -> Red Fill
             btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent; 
                    color: #cc4444; 
                    border: 1px solid #cc4444;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { 
                    background-color: #cc4444; 
                    color: white;
                }
             """)
             btn.clicked.connect(lambda: self.tracker.stop_manual_session(act))
             # Force refresh on click
             btn.clicked.connect(lambda: QTimer.singleShot(100, self.refresh_list))
        else:
             btn.setText("Start")
             btn.setObjectName("PrimaryButton")
             # Force style - Green Outline -> Green Fill
             btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent; 
                    color: #2fa51f; 
                    border: 1px solid #2fa51f;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { 
                    background-color: #2fa51f; 
                    color: white;
                }
             """)
             btn.clicked.connect(lambda: self.tracker.start_manual_session(act))
             btn.clicked.connect(lambda: QTimer.singleShot(100, self.refresh_list))
             
        layout.addWidget(btn)
        
        self.apps_layout.addWidget(row)

    def open_add_dialog(self, activity_to_edit=None):
        dlg = AddActivityDialog(self, self.db, self.icon_manager, activity_to_edit)
        if dlg.exec():
            # Refresh list to show changes
            self.refresh_list()
            # Also update active session if it was edited
            if activity_to_edit:
                 # Logic to update active card if exists? 
                 # refresh_list only updates the list below. 
                 # Active cards update on next timer tick mostly, but name/icon might need immediate refresh.
                 # For now, list refresh is good coverage.
                 pass

    def delete_activity_ui(self, activity):
        """Confirm and delete an activity."""
        reply = QMessageBox.question(
            self, 
            "Delete Activity", 
            f"Are you sure you want to delete '{activity.name}'?\nThis will remove all logs, description logs, and the custom icon permanently.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.db.delete_activity(activity.id)
            if success:
                # Remove from tracker manually if it's there
                if self.tracker.is_manual_running(activity.id):
                    self.tracker.stop_manual_session(activity)
                
                # Check for active session card and remove?
                # Refresh list will handle the list part. 
                # If active, it might bug out if we don't handle it.
                if self.tracker.current_activity and self.tracker.current_activity.id == activity.id:
                     self.tracker.stop_auto_tracking()
                
                self.refresh_list()
                print(f"Deleted activity {activity.name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete activity.")

