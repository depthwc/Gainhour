from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QScrollArea, QPushButton, QLineEdit, QComboBox, QSizePolicy, QGridLayout, QLayout, QStackedWidget, QCheckBox)
from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon, QFontMetrics, QPainter, QColor, QPen
from PySide6.QtWidgets import QMessageBox
import os
import time

from PySide6.QtCore import Qt, QTimer, QSize, Signal
from src.ui.add_activity_dialog import AddActivityDialog

from src.utils.text_utils import format_app_name



class ActiveSessionCard(QFrame):
    stop_clicked = Signal()
    discord_selected = Signal(bool) 
    
    def __init__(self, name, status, is_auto, activity_obj, icon_manager, tracker=None, db=None, window_title=""):
        super().__init__()
        self.name = name
        self.display_name = format_app_name(name)
    
    def set_live_style(self, is_live):
        """Updates style if this is the active Discord activity."""
        if is_live:
            self.setStyleSheet("""
                QFrame#ActiveSessionCard {
                    border: 1px solid #2fa51f; /* Green Border */
                    border-radius: 8px;
                }
            """ + self._get_base_styles())
            if hasattr(self, 'status_badge'):
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
                     color = "#43697d" if self.is_auto else "#a5861f"
                     self.status_badge.setStyleSheet(f"background-color: {color}; color: white; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 10px;")
        else:
             self.setStyleSheet("""
                QFrame#ActiveSessionCard {
                    border-radius: 8px;
                }
             """ + self._get_base_styles())
             if hasattr(self, 'status_badge'):
                 self.status_badge.setText("AUTO" if self.is_auto else "MANUAL")
                 color = "#43697d" if self.is_auto else "#a5861f"
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
        self.set_live_style(False) 
        
        
        base_elements_width = 150 
        fm_name = QFontMetrics(QFont("Segoe UI", 11, QFont.Bold))
        name_width = fm_name.horizontalAdvance(self.display_name)
        
        content_width = base_elements_width + name_width + 40 + 30 
        
        MIN_WIDTH = 375
        MAX_WIDTH = MIN_WIDTH + 100 
        
        final_width = max(MIN_WIDTH, min(content_width, MAX_WIDTH))
        
        self.setFixedWidth(final_width)
        self.setFixedHeight(200)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10) 
        layout.setSpacing(12)
        
        self.discord_chk = QCheckBox()
        self.discord_chk.setCursor(Qt.PointingHandCursor)
        self.discord_chk.setToolTip("Force Pin to Discord")
        self.discord_chk.setFixedSize(28, 28) 
        from src.utils.path_utils import get_resource_path
        discord_icon_path = get_resource_path("src/icons/discord_icon.png").replace('\\', '/')
        self.discord_chk.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 24px;
                height: 24px;
                border-radius: 12px;
                subcontrol-position: center;
            }}
            QCheckBox::indicator:unchecked {{
                background-color: #2f3136; /* Discord Dark */
                border: 2px solid #555;
                image: none;
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: #7289da;
            }}
            QCheckBox::indicator:checked {{
                border: none;
                background-color: transparent;
                image: url({discord_icon_path});
            }}
        """)
        
        self.discord_chk.clicked.connect(self.discord_selected)
        layout.addWidget(self.discord_chk)
        
        #Left
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(40, 40)
        self.update_icon()
        layout.addWidget(self.icon_lbl)
        
        #Middle
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 4, 0, 4)
        
        #Name
        name_lbl = QLabel(self.display_name)
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_lbl.setStyleSheet("border: none; background: transparent;")
        info_layout.addWidget(name_lbl)
        
        if is_auto:
            disp_title = self.window_title if self.window_title else "Application"
            
            desc_layout = QVBoxLayout()
            desc_layout.setSpacing(2)
            desc_layout.setContentsMargins(0,0,0,0)
            
            self.desc_lbl = QLabel(disp_title)
            self.desc_lbl.setFont(QFont("Segoe UI", 9))
            self.desc_lbl.setObjectName("HelperLabel")
            self.desc_lbl.setStyleSheet("border: none; background: transparent;")
            self.desc_lbl.setWordWrap(True) 
            self.desc_lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            desc_layout.addWidget(self.desc_lbl)
            
            self.desc_stats_lbl = QLabel("")
            self.desc_stats_lbl.setFont(QFont("Segoe UI", 8))
            self.desc_stats_lbl.setObjectName("HelperLabel")
            self.desc_stats_lbl.setStyleSheet("margin-top: 2px;")
            desc_layout.addWidget(self.desc_stats_lbl)
            
            info_layout.addLayout(desc_layout)
        else:
            current_desc = self.window_title
            
            self.desc_stack = QStackedWidget()
            self.desc_stack.setFixedHeight(30) 
            
            btn_page = QWidget()
            btn_layout = QHBoxLayout(btn_page)
            btn_layout.setContentsMargins(0,0,0,0)
            btn_layout.setAlignment(Qt.AlignLeft)
            
            self.add_desc_btn = QPushButton("+ Add Description")
            self.add_desc_btn.setCursor(Qt.PointingHandCursor)
            self.add_desc_btn.setObjectName("AccentButton")
            self.add_desc_btn.clicked.connect(self.prompt_description)
            btn_layout.addWidget(self.add_desc_btn)
            

            lbl_page = QWidget()
            lbl_layout = QHBoxLayout(lbl_page)
            lbl_layout.setContentsMargins(0,0,0,0)
            lbl_layout.setAlignment(Qt.AlignLeft)
            
            self.user_desc_lbl = QLabel(current_desc)
            self.user_desc_lbl.setFont(QFont("Segoe UI", 9))
            self.user_desc_lbl.setObjectName("HelperLabel")

            self.user_desc_lbl.setCursor(Qt.PointingHandCursor)
            self.user_desc_lbl.mousePressEvent = self.prompt_description 
            lbl_layout.addWidget(self.user_desc_lbl)
            

            edit_btn = QPushButton("✎")
            edit_btn.setFixedSize(20, 20)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setObjectName("HelperLabel") # So the text logic is somewhat inherited, though it's a button. Wait, a button with "HelperLabel" won't work perfectly. Let's make it inherit border:none.
            edit_btn.setStyleSheet("background: transparent; border: none;")
            edit_btn.clicked.connect(self.prompt_description)
            lbl_layout.addWidget(edit_btn)

            self.desc_stack.addWidget(btn_page)
            self.desc_stack.addWidget(lbl_page)
            
            info_layout.addWidget(self.desc_stack)
            

            if not current_desc or current_desc == "Manual Session":
                self.desc_stack.setCurrentIndex(0)
            else:
                self.desc_stack.setCurrentIndex(1)
        

        self.timer_lbl = QLabel("00:00:00")
        self.timer_lbl.setFont(QFont("Roboto Medium", 16, QFont.Bold))
        self.timer_lbl.setObjectName("AccentText")
        self.timer_lbl.setStyleSheet("border: none; background: transparent;")
        info_layout.addWidget(self.timer_lbl)
        

        self.stats_lbl = QLabel("Total: 0h 0m")
        self.stats_lbl.setObjectName("AccentText")
        self.stats_lbl.setStyleSheet("font-size: 10px; border: none; background: transparent;")
        info_layout.addWidget(self.stats_lbl)
        
        layout.addLayout(info_layout)
        

        action_layout = QVBoxLayout()
        action_layout.setSpacing(0)

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

        self.status_badge.setAlignment(Qt.AlignCenter)
        

        badge_container = QHBoxLayout()
        badge_container.setContentsMargins(0,0,0,0)
        badge_container.addStretch()
        badge_container.addWidget(self.status_badge)
        
        action_layout.addLayout(badge_container)
        

        action_layout.addStretch()
        

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("StopButton")
        self.stop_btn.setFixedSize(70, 30)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        

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
        h, r = divmod(current_sec, 3600)
        m, s = divmod(r, 60)
        self.timer_lbl.setText(f"{h:02}:{m:02}:{s:02}")
        

        h1, m1 = divmod(today_sec // 60, 60)
        h2, m2 = divmod(total_sec // 60, 60)
        self.stats_lbl.setText(f"Today: {int(h1)}h {int(m1)}m  •  Total: {int(h2)}h {int(m2)}m")


        if self.is_auto and self.db and self.activity_obj and self.window_title:
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
            self.activity_obj.description = text
            self.db.update_activity(self.activity_obj.id, description=text)
            

            if not self.is_auto and self.tracker:
                 self.tracker.update_manual_description(self.activity_obj.id, text)
            

            self.window_title = text
            self.user_desc_lbl.setText(text)
            self.desc_stack.setCurrentIndex(1)
        elif ok and not text:
             self.activity_obj.description = "Manual Session" # Or None? keeping simple
             self.db.update_activity(self.activity_obj.id, description="Manual Session")
             self.window_title = "Manual Session"
             self.desc_stack.setCurrentIndex(0)

class HorizontalScrollArea(QScrollArea):
    def wheelEvent(self, event):
        if event.angleDelta().y() != 0:
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
        

        self.create_header()
        self.layout.addWidget(self.header_frame)
        

        self.create_controls()
        self.layout.addWidget(self.controls_frame)
        

        self.apps_label = QLabel("All Applications")
        self.apps_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.apps_label.setStyleSheet("margin-top: 10px;")
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
        self.header_frame.setMinimumHeight(290)
        

        main_v_layout = QVBoxLayout(self.header_frame)
        main_v_layout.setContentsMargins(0,0,0,0)
        main_v_layout.setSpacing(10)
        
        lbl = QLabel("Active Sessions")
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setStyleSheet("")
        

        self.reconnect_btn = QPushButton("Reconnect to Discord")
        self.reconnect_btn.setCursor(Qt.PointingHandCursor)
        self.reconnect_btn.setObjectName("DiscordButton")
        self.reconnect_btn.clicked.connect(self.tracker.reconnect_discord)

        self.reconnect_btn.setVisible(False)
        
        header_top_layout = QHBoxLayout()
        header_top_layout.addWidget(lbl)
        header_top_layout.addStretch()
        header_top_layout.addWidget(self.reconnect_btn)
        
        main_v_layout.addLayout(header_top_layout)
        

        content_h_layout = QHBoxLayout()
        content_h_layout.setSpacing(20)

        self.active_scroll = HorizontalScrollArea()
        self.active_scroll.setObjectName("ActivityCard") 
        self.active_scroll.setWidgetResizable(True)
        self.active_scroll.setFrameShape(QFrame.NoFrame)
        self.active_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.active_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.active_scroll.setFixedHeight(250)
        
        self.active_scroll.setStyleSheet("""
             QScrollArea#ActivityCard {
                border-radius: 8px;
                background-color: transparent;
             }
             QWidget { background: transparent; }
             QScrollBar:horizontal {
                height: 12px;
                background: transparent;
                margin: 0px 0px 0px 0px;
             }
             QScrollBar::handle:horizontal {
                background: rgba(128, 128, 128, 0.5);
                min-width: 20px;
                border-radius: 6px;
             }
             QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
             }
        """)
        

        self.active_area = QFrame()
        self.active_area.setStyleSheet("background: transparent;")
        
        self.active_layout = QHBoxLayout(self.active_area) 
        self.active_layout.setSpacing(10)
        self.active_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) 
        self.active_layout.setContentsMargins(10, 5, 10, 5) 
        self.active_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)
        
        self.active_scroll.setWidget(self.active_area)
        
        content_h_layout.addWidget(self.active_scroll, 1)
        

        self.total_card = QFrame()
        self.total_card.setObjectName("ActivityCard")
        self.total_card.setFixedWidth(240)
        self.total_card.setFixedHeight(250) 
        
        t_layout = QVBoxLayout(self.total_card)
        t_layout.setAlignment(Qt.AlignCenter)
        
        lbl_total = QLabel("TOTAL TODAY")
        lbl_total.setObjectName("SectionHeader")
        lbl_total.setStyleSheet("font-weight: bold; font-size: 12px; letter-spacing: 1px;")
        t_layout.addWidget(lbl_total)
        
        self.total_timer_lbl = QLabel("00:00:00")
        self.total_timer_lbl.setFont(QFont("Roboto Medium", 28, QFont.Bold))
        self.total_timer_lbl.setObjectName("AccentText")
        t_layout.addWidget(self.total_timer_lbl)
        
        content_h_layout.addWidget(self.total_card)
        
        main_v_layout.addLayout(content_h_layout)
        
    def create_controls(self):
        self.controls_frame = QFrame()
        layout = QHBoxLayout(self.controls_frame)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(10)
        

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search applications...")
        self.search_input.setFixedWidth(300)
        self.search_input.setMinimumHeight(35)
        self.search_input.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search_input)
        

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Apps", "IRL"])
        self.filter_combo.setFixedWidth(120)
        self.filter_combo.setMinimumHeight(35)
        self.filter_combo.setCurrentIndex(0)
        self.filter_combo.currentTextChanged.connect(self.refresh_list)
        layout.addWidget(self.filter_combo)
        
        layout.addStretch()
        

        add_btn = QPushButton("+ Add IRL Activity")
        add_btn.setObjectName("PrimaryButton")
        add_btn.setMinimumHeight(35)
        add_btn.clicked.connect(self.open_add_dialog)
        layout.addWidget(add_btn)

    def update_data(self):
        is_discord_enabled = self.tracker.storage.get_setting("discord_enabled", "True") == "True"
        self.reconnect_btn.setVisible(is_discord_enabled)
        
        self.update_active_sessions()
        
        total = self.db.get_total_today_duration()
        
        if self.tracker.current_activity:
             pname = self.tracker.current_activity.name
             if pname in self.tracker.open_sessions:
                  total += int(self.tracker.open_sessions[pname]['accumulated_time'])
        
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
        
        if time.time() - self.last_refresh > 2.0: 
            self.refresh_list()
            self.last_refresh = time.time()
            
    def update_active_sessions(self):
        current_active_ids = set()
        

        if self.tracker.current_activity:
             name = self.tracker.current_activity.name
             sid = f"AUTO_{name}"
             current_active_ids.add(sid)
             

             desc = self.tracker.last_window_title if self.tracker.last_window_title else self.tracker.current_activity.description
             
             if sid not in self.active_cards:
                 card = ActiveSessionCard(name, "AUTO", True, None, self.icon_manager, self.tracker, self.db, window_title=desc)
                 card.stop_clicked.connect(lambda n=name: self.tracker.set_ignore_app(n, True))

                 current_act = self.tracker.current_activity
                 if current_act and current_act.name == name:
                      card.discord_selected.connect(lambda checked, a=current_act: self.tracker.set_discord_pin(a if checked else None))
                 
                 self.active_layout.addWidget(card)
                 self.active_cards[sid] = card
             else:
                 if self.active_cards[sid].window_title != desc:
                     self.active_cards[sid].update_description(desc)


             is_visible = True
             if self.tracker.current_activity:
                 act = self.db.get_activity_by_id(self.tracker.current_activity.id)
                 if act: is_visible = act.discord_visible
             
             is_global_enabled = self.tracker.storage.get_setting("discord_enabled", "True") == "True"
             
             should_show_checkbox = is_visible and is_global_enabled
             self.active_cards[sid].discord_chk.setVisible(should_show_checkbox)

             actual_target = getattr(self.tracker, 'discord_last_target_name', None)
             is_live_now = (actual_target == name)
             
             self.active_cards[sid].discord_chk.blockSignals(True)
             self.active_cards[sid].discord_chk.setChecked(is_live_now)
             self.active_cards[sid].discord_chk.blockSignals(False)
             
             self.active_cards[sid].set_live_style(is_live_now)

             duration = 0
             if name in self.tracker.open_sessions:
                  duration = int(self.tracker.open_sessions[name]['accumulated_time'])
             
             today = self.db.get_today_duration(name)
             total = self.db.get_activity_duration(name)
             
             self.active_cards[sid].update_stats(duration, today, total)

        for act_id, log_id in self.tracker.manual_sessions.items():
             act = self.db.get_activity_by_id(act_id)
             if act:
                 sid = f"MANUAL_{act.id}"
                 current_active_ids.add(sid)
                 
                 desc = getattr(act, 'description', "Manual Session")
                 
                 if sid not in self.active_cards:
                     card = ActiveSessionCard(act.name, "MANUAL", False, act, self.icon_manager, self.tracker, self.db, window_title="")
                     card.stop_clicked.connect(lambda a=act: self.tracker.stop_manual_session(a))
                     
                     card.discord_selected.connect(lambda checked, a=act: self.tracker.set_discord_pin(a if checked else None))
                     
                     
                     self.active_layout.addWidget(card)
                     self.active_cards[sid] = card
                 
             is_visible = getattr(act, 'discord_visible', True)
             is_global_enabled = self.tracker.storage.get_setting("discord_enabled", "True") == "True"
             
             should_show_checkbox = is_visible and is_global_enabled
             self.active_cards[sid].discord_chk.setVisible(should_show_checkbox)
                 
             actual_target = getattr(self.tracker, 'discord_last_target_name', None)
             is_live_now = (actual_target == act.name)
             
             self.active_cards[sid].discord_chk.blockSignals(True)
             self.active_cards[sid].discord_chk.setChecked(is_live_now)
             self.active_cards[sid].discord_chk.blockSignals(False)
             
             self.active_cards[sid].set_live_style(is_live_now)

                     
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


        for sid in list(self.active_cards.keys()):
            if sid not in current_active_ids:
                card = self.active_cards.pop(sid)
                card.deleteLater()
                
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

        all_acts = self.db.get_all_activities()
        for a in all_acts:
            current_data[a.name] = {
                'name': a.name, 'type': a.type, 'icon': a.icon_path, 'is_irl': a.type == 'irl'
            }
            
        for name, info in self.tracker.open_sessions.items():
            if name not in current_data:
                current_data[name] = {
                    'name': name, 'type': 'app', 'icon': info.get('executable_path'), 'is_irl': False
                }
            else:
                 if not current_data[name]['icon']:
                      current_data[name]['icon'] = info.get('executable_path')

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
        
        v_scroll = self.scroll.verticalScrollBar().value()
        
        while self.apps_layout.count():
             child = self.apps_layout.takeAt(0)
             if child.widget(): child.widget().deleteLater()
             
        for info, total, today in filtered_items[:50]: 
             self.create_app_row(info, total, today)
             
        self.scroll.verticalScrollBar().setValue(v_scroll)

    def create_app_row(self, info, total_seconds, today_seconds):
        row = QFrame()
        row.setObjectName("ActivityCard")
        row.setFixedHeight(55)
        
        layout = QHBoxLayout(row)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(15)
        

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(32, 32)
        
        if info['icon'] and os.path.exists(info['icon']):
             pix = QPixmap(info['icon'])
             if not pix.isNull():
                 icon_lbl.setPixmap(pix.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                 icon_lbl.setStyleSheet("background: transparent; border: none;")
        else:
             icon_lbl.setText(info['name'][:2].upper())
             icon_lbl.setObjectName("AppIcon")
        
        layout.addWidget(icon_lbl)
        

        formatted_name = format_app_name(info['name'])
        
        name_lbl = QLabel(formatted_name)
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_lbl.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(name_lbl)
        
        layout.addStretch()
        if info['is_irl']:
             tag = QLabel("IRL")
             tag.setFont(QFont("Segoe UI", 8, QFont.Bold))
             tag.setObjectName("IrlTag")
             layout.addWidget(tag)
             
        

        h_tot, m_tot = divmod(total_seconds // 60, 60)
        h_today, m_today = divmod(today_seconds // 60, 60)
        
        time_text = f"Today: {int(h_today)}h {int(m_today)}m  •  Total: {int(h_tot)}h {int(m_tot)}m"
        time_lbl = QLabel(time_text)
        time_lbl.setFont(QFont("Segoe UI", 10))
        time_lbl.setObjectName("HelperLabel")
        layout.addWidget(time_lbl)
        
        if info['is_irl']:
             edit_btn = QPushButton("Edit✎")
             edit_btn.setFixedSize(65, 30)
             edit_btn.setCursor(Qt.PointingHandCursor)
             edit_btn.setToolTip("Edit Info")
             edit_btn.setObjectName("SecondaryCardButton")
             act_for_edit = self.db.get_or_create_activity(info['name'], info['type'])
             edit_btn.clicked.connect(lambda: self.open_add_dialog(act_for_edit))
             layout.addWidget(edit_btn)
        
        del_btn = QPushButton("Del🗑")
        del_btn.setFixedSize(65, 30)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setToolTip(f"Delete {info['name']}")
        del_btn.setObjectName("DangerCardButton")
        act_del = self.db.get_or_create_activity(info['name'], info['type'])
        del_btn.clicked.connect(lambda: self.delete_activity_ui(act_del))
        layout.addWidget(del_btn)


        btn = QPushButton("Start")
        btn.setFixedSize(70, 30)
        
        act = self.db.get_or_create_activity(info['name'], info['type'])
        if self.tracker.is_manual_running(act.id):
             btn.setText("Stop")
             btn.setObjectName("StopCardButton")
             btn.clicked.connect(lambda: self.tracker.stop_manual_session(act))

             btn.clicked.connect(lambda: QTimer.singleShot(100, self.refresh_list))
        else:
             btn.setText("Start")
             btn.setObjectName("StartCardButton")
             btn.clicked.connect(lambda: self.tracker.start_manual_session(act))
             btn.clicked.connect(lambda: QTimer.singleShot(100, self.refresh_list))
             
        layout.addWidget(btn)
        
        self.apps_layout.addWidget(row)

    def open_add_dialog(self, activity_to_edit=None):
        dlg = AddActivityDialog(self, self.db, self.icon_manager, activity_to_edit)
        if dlg.exec():
            self.refresh_list()
            if activity_to_edit:
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
                if self.tracker.is_manual_running(activity.id):
                    self.tracker.stop_manual_session(activity)

                if self.tracker.current_activity and self.tracker.current_activity.id == activity.id:
                     self.tracker.stop_auto_tracking()
                
                self.refresh_list()
                print(f"Deleted activity {activity.name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete activity.")

