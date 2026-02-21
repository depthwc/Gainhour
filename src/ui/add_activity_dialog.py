from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QFileDialog, QFrame)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont
import os

from src.ui.styles import get_stylesheet

class AddActivityDialog(QDialog):
    def __init__(self, parent, db, icon_manager, activity_to_edit=None):
        super().__init__(parent)
        self.db = db
        self.icon_manager = icon_manager
        self.activity_to_edit = activity_to_edit
        self.selected_icon_path = None
        
        self.setWindowTitle("Edit Activity" if activity_to_edit else "Add IRL Activity")
        self.setFixedSize(350, 450) # Taller, narrower for modern look
        
        # Apply Global Theme directly to Dialog
        self.setStyleSheet(get_stylesheet("theme") + """
            QPushButton#SaveBtn {
                padding: 10px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#CancelBtn {
                padding: 10px;
                background-color: transparent;
                border-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 40, 30, 30)
        
        # 1. Icon Selection Area (Top Center)
        icon_layout = QVBoxLayout()
        icon_layout.setAlignment(Qt.AlignCenter)
        
        self.icon_btn = QPushButton()
        self.icon_btn.setFixedSize(120, 120)
        self.icon_btn.setCursor(Qt.PointingHandCursor)
        self.icon_btn.clicked.connect(self.browse_icon)
        self.icon_btn.setObjectName("SecondaryButton")
        self.icon_btn.setStyleSheet("""
            QPushButton {
                border: 2px dashed #555;
                border-radius: 12px;
            }
        """)
        icon_layout.addWidget(self.icon_btn)
        
        icon_hint = QLabel("Select Icon")
        icon_hint.setObjectName("SectionHeader")
        icon_hint.setStyleSheet("font-size: 11px; font-weight: normal; margin-top: 5px;")
        icon_layout.addWidget(icon_hint, 0, Qt.AlignCenter)
        
        layout.addLayout(icon_layout)
        
        # 2. Inputs
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Name
        name_container = QVBoxLayout()
        name_container.setSpacing(5)
        name_lbl = QLabel("ACTIVITY NAME")
        name_lbl.setObjectName("SectionHeader")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Reading, Workout")
        name_container.addWidget(name_lbl)
        name_container.addWidget(self.name_input)
        form_layout.addLayout(name_container)
        
        # Description
        desc_container = QVBoxLayout()
        desc_container.setSpacing(5)
        desc_lbl = QLabel("DESCRIPTION (OPTIONAL)")
        desc_lbl.setObjectName("SectionHeader")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Brief description...")
        desc_container.addWidget(desc_lbl)
        desc_container.addWidget(self.desc_input)
        form_layout.addLayout(desc_container)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # 3. Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("SecondaryButton")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Create Activity" if not activity_to_edit else "Save Changes")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self.save)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Initialize Values
        if activity_to_edit:
            self.name_input.setText(activity_to_edit.name)
            # self.name_input.setReadOnly(True) # Optional: Allow renaming? Usually risky if ID based.
            self.desc_input.setText(activity_to_edit.description or "")
            if activity_to_edit.icon_path:
                self.selected_icon_path = activity_to_edit.icon_path
                self.update_icon_preview()
        
        if not self.selected_icon_path:
            self.set_default_icon_state()

    def set_default_icon_state(self):
        self.icon_btn.setText("+")
        self.icon_btn.setIcon(QIcon())
        self.icon_btn.setObjectName("SecondaryButton")
        self.icon_btn.setStyleSheet("""
            QPushButton {
                border: 2px dashed #555;
                border-radius: 12px;
                font-size: 40px;
                font-weight: bold;
            }
        """)

    def update_icon_preview(self):
        if self.selected_icon_path and os.path.exists(self.selected_icon_path):
            pix = QPixmap(self.selected_icon_path)
            if not pix.isNull():
                self.icon_btn.setText("")
                icon = QIcon(pix)
                self.icon_btn.setIcon(icon)
                self.icon_btn.setIconSize(QSize(80, 80))
                # Solid border for selected
                self.icon_btn.setObjectName("SecondaryButton")
                self.icon_btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: 2px solid #555;
                        border-radius: 12px;
                    }
                """)

    def browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Image Files (*.png *.jpg *.ico)")
        if path:
            self.selected_icon_path = path
            self.update_icon_preview()

    def save(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        
        if not name:
            return # TODO: Show error
            
        final_icon_path = None
        if self.selected_icon_path and os.path.exists(self.selected_icon_path):
             # Save to internal user_icons folder if it's new
             if self.activity_to_edit and self.activity_to_edit.icon_path == self.selected_icon_path:
                 final_icon_path = self.selected_icon_path
             else:
                 final_icon_path = self.icon_manager.save_user_icon(self.selected_icon_path, name)
              
        if self.activity_to_edit:
            # Update
            self.db.update_activity(self.activity_to_edit.id, description=desc, icon_path=final_icon_path)
        else:
            # Create
            self.db.get_or_create_activity(name, 'irl', description=desc, icon_path=final_icon_path)
            
        self.accept()
