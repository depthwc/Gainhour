from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QGridLayout, QScrollArea, QPushButton, QSizePolicy, QDialog, QLineEdit, QFileDialog)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon
from PySide6.QtWidgets import QMessageBox, QComboBox
import os

from src.ui.add_activity_dialog import AddActivityDialog
from src.ui.log_viewer_dialog import LogViewerDialog
from src.ui.flow_layout import FlowLayout

from src.utils.text_utils import format_app_name

class ActivityCard(QFrame):
    def __init__(self, activity, db, icon_manager, parent=None):
        super().__init__(parent)
        self.activity = activity
        self.formatted_name = format_app_name(activity.name)
        self.db = db
        self.icon_manager = icon_manager
        

        self.setFixedSize(280, 160) 
        self.setObjectName("ActivityCard")
        
    
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(8)
        

        header = QHBoxLayout()
        header.setSpacing(12)
        

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(40, 40)
        

        icon_path = activity.icon_path
        if icon_path and not os.path.isabs(icon_path):
             base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             icon_path = os.path.join(base_path, icon_path)

        if icon_path and os.path.exists(icon_path):
             pixmap = QPixmap(icon_path)
             if not pixmap.isNull():
                 pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                 self.icon_lbl.setPixmap(pixmap)
                 self.icon_lbl.setStyleSheet("background: transparent; border: none;")
             else:
                 self.set_fallback_icon()
        else:
             self.set_fallback_icon()
             
        header.addWidget(self.icon_lbl)
        

        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.setContentsMargins(0, 0, 0, 0) 


        name_lbl = QLabel(self.formatted_name)
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        titles.addWidget(name_lbl)
        

        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(0)
        badge_layout.setContentsMargins(0,0,0,0)
        
        type_lbl = QLabel(activity.type.upper())
        type_lbl.setFont(QFont("Segoe UI", 8, QFont.Bold))
        type_lbl.setObjectName("IrlTag")
        badge_layout.addWidget(type_lbl)
        badge_layout.addStretch()
        
        titles.addLayout(badge_layout)
        
        header.addLayout(titles)
        header.addStretch()
        self.layout.addLayout(header)
        

        stats = QHBoxLayout()
        stats.setSpacing(15)
        

        today_box = QVBoxLayout()
        today_box.setSpacing(0)
        lbl_t = QLabel("TODAY")
        lbl_t.setObjectName("HelperLabel")
        lbl_t.setStyleSheet("font-size: 9px; font-weight: bold;")
        today_box.addWidget(lbl_t)
        
        self.today_lbl = QLabel("0h 0m")
        self.today_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold)) 
        self.today_lbl.setObjectName("SectionHeader")
        today_box.addWidget(self.today_lbl)
        stats.addLayout(today_box)
        

        total_box = QVBoxLayout()
        total_box.setSpacing(0)
        lbl_tot = QLabel("TOTAL")
        lbl_tot.setObjectName("HelperLabel")
        lbl_tot.setStyleSheet("font-size: 9px; font-weight: bold;")
        total_box.addWidget(lbl_tot)
        
        self.total_lbl = QLabel("0h 0m")
        self.total_lbl.setFont(QFont("Segoe UI", 11))
        self.total_lbl.setObjectName("HelperLabel")
        total_box.addWidget(self.total_lbl)
        stats.addLayout(total_box)
        
        stats.addStretch()
        self.layout.addLayout(stats)
        
        self.layout.addStretch()
        

        footer = QHBoxLayout()
        footer.setSpacing(8)
        
        self.edit_btn = QPushButton("Edit✎")
        self.edit_btn.setFixedSize(65, 26)
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setToolTip("Edit Info")
        self.edit_btn.setObjectName("SecondaryCardButton")
        footer.addWidget(self.edit_btn)
        
        self.del_btn = QPushButton("Del🗑")
        self.del_btn.setFixedSize(65, 26) 
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setToolTip("Delete Activity")
        self.del_btn.setObjectName("DangerCardButton")
        footer.addWidget(self.del_btn)
        
        footer.addStretch()

        self.logs_btn = QPushButton("Logs")
        self.logs_btn.setFixedSize(70, 26)
        self.logs_btn.setCursor(Qt.PointingHandCursor)
        self.logs_btn.setObjectName("SecondaryCardButton")
        footer.addWidget(self.logs_btn)
        
        self.layout.addLayout(footer)
        
        self.update_stats()

    def set_fallback_icon(self):
        self.icon_lbl.setText(self.activity.name[:2].upper())
        self.icon_lbl.setStyleSheet("""
            background-color: #3e3e3e; 
            color: white; 
            border-radius: 8px; 
            qproperty-alignment: AlignCenter;
            font-weight: bold;
            font-size: 13px;
        """)

    def update_stats(self):
        today = self.db.get_today_duration(self.activity.name, self.activity.type)
        total = self.db.get_activity_duration(self.activity.name, self.activity.type)
        
        h, r = divmod(today, 3600)
        m, _ = divmod(r, 60)
        self.today_lbl.setText(f"{int(h)}h {int(m)}m")
        
        h, r = divmod(total, 3600)
        m, _ = divmod(r, 60)
        self.total_lbl.setText(f"{int(h)}h {int(m)}m")

    def set_running(self, is_running):
        pass 



class ActivitiesWidget(QWidget):
    def __init__(self, db, tracker, icon_manager):
        super().__init__()
        self.db = db
        self.tracker = tracker
        self.icon_manager = icon_manager
        self.cards = {} 
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        

        header = QHBoxLayout()
        title = QLabel("Manage Activities")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.addWidget(title)
        
        

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search activities...")
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setFixedWidth(250)
        controls_layout.addWidget(self.search_input)
        

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Types", "App", "IRL"])
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        self.filter_combo.setFixedWidth(120)
        controls_layout.addWidget(self.filter_combo)
        
        controls_layout.addStretch()
        
        add_btn = QPushButton("+ Add IRL Activity")
        add_btn.setObjectName("PrimaryButton")
        add_btn.setMinimumHeight(34) 
        add_btn.clicked.connect(self.open_add_dialog)
        controls_layout.addWidget(add_btn)
        
        layout.addLayout(controls_layout)
        

        self.current_search_text = ""
        self.current_filter_type = "All Types"
        

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.grid_container = QWidget()

        self.flow_layout = FlowLayout(self.grid_container, margin=0, spacing=20) 
        
        
        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)
        
        self.refresh()
        
    def refresh(self):
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards.clear()
        
        
        all_activities = self.db.get_all_activities()
        activities = []
        search_text = self.current_search_text.lower()
        filter_type = self.current_filter_type
        
        for act in all_activities:
            if filter_type == "App" and act.type != "app":
                continue
            if filter_type == "IRL" and act.type != "irl": 
                 pass 


            if filter_type == "App" and act.type != "app":
                continue
            if filter_type == "IRL" and act.type == "app":
                continue 
            
            if search_text and search_text not in act.name.lower():
                continue
                
            activities.append(act)
            
        activities.sort(key=lambda x: x.name)
        

        cols = 4 
        for i, act in enumerate(activities):
            card = ActivityCard(act, self.db, self.icon_manager)
            
            card.logs_btn.clicked.connect(lambda checked, a=act: self.open_logs_dialog(a))   
            card.edit_btn.clicked.connect(lambda checked, a=act: self.open_edit_dialog(a))
            card.del_btn.clicked.connect(lambda checked, a=act: self.delete_activity_ui(a)) 
            
            self.flow_layout.addWidget(card)
            self.cards[act.id] = card
            
        self.update_states()

    def update_states(self):
        for act_id, card in self.cards.items():
            is_running = self.tracker.is_manual_running(act_id)
            card.set_running(is_running)

    def toggle_activity(self, activity):
        if self.tracker.is_manual_running(activity.id):
            self.tracker.stop_manual_session(activity)
        else:
            self.tracker.start_manual_session(activity)
        self.update_states()

        if activity.id in self.cards:
             self.cards[activity.id].update_stats()

    def open_logs_dialog(self, activity):
        dlg = LogViewerDialog(activity, self.db, self.icon_manager, parent=self)
        dlg.exec()

    def open_add_dialog(self):
        dlg = AddActivityDialog(self, self.db, self.icon_manager)
        if dlg.exec():
            self.refresh()

    def open_edit_dialog(self, activity):
        dlg = AddActivityDialog(self, self.db, self.icon_manager, activity_to_edit=activity)
        if dlg.exec():
            self.refresh()
        
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
                
                self.refresh()
                print(f"Deleted activity {activity.name}")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete activity.")
        
    def on_search_changed(self, text):
        self.current_search_text = text
        self.refresh()
        
    def on_filter_changed(self, text):
        self.current_filter_type = text
        self.refresh()

    def update_data(self):
        self.update_states()
        for card in self.cards.values():
            card.update_stats()

