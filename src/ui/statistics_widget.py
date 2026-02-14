from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
matplotlib.use('QtAgg')

from src.utils.text_utils import format_app_name

class StatisticsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # Title
        title = QLabel("Daily Statistics")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: white;")
        self.layout.addWidget(title)
        
        # Content Split (Chart on top, List below, or side-by-side on wide screens? keep vertical for simplicity)
        
        # Chart Area
        self.chart_frame = QFrame()
        self.chart_frame.setStyleSheet("""
            background-color: #252526; 
            border-radius: 10px; 
            border: 1px solid #3e3e3e;
        """)
        self.chart_layout = QVBoxLayout(self.chart_frame)
        self.layout.addWidget(self.chart_frame)
        
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor('#252526') # Match card bg
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent; border-radius: 10px;")
        self.chart_layout.addWidget(self.canvas)
        
        # Breakdown Title
        lbl = QLabel("Activity Breakdown")
        lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl.setStyleSheet("color: white; margin-top: 10px;")
        self.layout.addWidget(lbl)
        
        # List Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(5)
        
        self.scroll.setWidget(self.list_container)
        self.layout.addWidget(self.scroll)
        
        self.refresh()
        
    def refresh(self):
        self.ax.clear()
        self.ax.set_facecolor('#252526')
        self.figure.patch.set_facecolor('#252526')
        
        stats = self.db.get_today_stats()
        # Filter small
        valid_stats = [s for s in stats if s['total_seconds'] > 60]
        # Keep top 8 for chart to avoid clutter
        chart_stats = valid_stats[:8]
        
        if not chart_stats:
            self.ax.text(0.5, 0.5, "No Data for Today", 
                         horizontalalignment='center', verticalalignment='center',
                         color='#aaaaaa', fontsize=12)
            self.canvas.draw()
            self.update_list([])
            return

        names = [format_app_name(s['name']) for s in chart_stats]
        seconds = [s['total_seconds'] for s in chart_stats]
        
        # Styled Pie Chart
        wedges, texts, autotexts = self.ax.pie(seconds, labels=names, autopct='%1.1f%%',
                                               startangle=90, 
                                               textprops=dict(color="white"),
                                               wedgeprops=dict(width=0.5, edgecolor='#252526'))
        
        # Donut Text
        total_sec = sum(seconds)
        h, m = divmod(total_sec // 60, 60)
        total_str = f"{int(h)}h {int(m)}m"
        
        self.ax.text(0, 0, total_str, ha='center', va='center', fontsize=20, color='white', fontweight='bold')
        
        self.ax.axis('equal')  
        self.canvas.draw()
        
        # Update Full List
        self.update_list(valid_stats)

    def update_list(self, stats):
        # Clear
        for i in reversed(range(self.list_layout.count())): 
            item = self.list_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        for s in stats:
             row = QFrame()
             row.setStyleSheet("""
                QFrame {
                    background-color: #2b2b2b;
                    border-radius: 6px;
                }
                QFrame:hover {
                    background-color: #333333;
                }
             """)
             row.setFixedHeight(45)
             
             row_layout = QHBoxLayout(row)
             row_layout.setContentsMargins(15, 5, 15, 5)
             
             name_lbl = QLabel(s['name'])
             name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
             name_lbl.setStyleSheet("color: white; background: transparent;")
             row_layout.addWidget(name_lbl)
             
             row_layout.addStretch()
             
             m, sec = divmod(s['total_seconds'], 60)
             h, m = divmod(m, 60)
             time_str = f"{int(h)}h {int(m)}m"
             
             time_lbl = QLabel(time_str)
             time_lbl.setStyleSheet("color: #aaaaaa; background: transparent;")
             row_layout.addWidget(time_lbl)
             
             self.list_layout.addWidget(row)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
matplotlib.use('QtAgg')

class StatisticsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        
        self.layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Statistics")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.layout.addWidget(title)
        
        # Chart Area
        self.chart_frame = QFrame()
        self.chart_layout = QVBoxLayout(self.chart_frame)
        self.layout.addWidget(self.chart_frame)
        
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor('#2b2b2b')
        self.canvas = FigureCanvas(self.figure)
        self.chart_layout.addWidget(self.canvas)
        
        self.refresh()
        
    def refresh(self):
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        self.figure.patch.set_facecolor('#2b2b2b')
        
        stats = self.db.get_today_stats()
        # Filter small
        valid_stats = [s for s in stats if s['total_seconds'] > 60]
        valid_stats.sort(key=lambda x: x['total_seconds'], reverse=True)
        top_5 = valid_stats[:5]
        
        if not top_5:
            self.ax.text(0.5, 0.5, "No Data for Today", 
                         horizontalalignment='center', verticalalignment='center',
                         color='white')
            self.canvas.draw()
            # Clear list
            self.update_list([])
            return

        names = [s['name'] for s in top_5]
        seconds = [s['total_seconds'] for s in top_5]
        
        # Pie Chart
        wedges, texts, autotexts = self.ax.pie(seconds, labels=names, autopct='%1.1f%%',
                                               startangle=90, textprops=dict(color="white"))
        
        # Donut
        centre_circle = plt.Circle((0,0),0.70,fc='#2b2b2b')
        self.figure.gca().add_artist(centre_circle)
        
        self.ax.axis('equal')  
        self.canvas.draw()
        
        # Update List
        self.update_list(valid_stats)

    def update_list(self, stats):
        # Clear existing list items (except ScrollArea if we have one)
        # We need to create a list area if it doesn't exist
        if not hasattr(self, 'list_container'):
             from PySide6.QtWidgets import QScrollArea
             self.scroll = QScrollArea()
             self.scroll.setWidgetResizable(True)
             self.list_container = QWidget()
             self.list_layout = QVBoxLayout(self.list_container)
             self.list_layout.setAlignment(Qt.AlignTop)
             self.scroll.setWidget(self.list_container)
             self.layout.addWidget(self.scroll)
        
        # Clear
        for i in reversed(range(self.list_layout.count())): 
            self.list_layout.itemAt(i).widget().setParent(None)
            
            
            for s in stats:
                 row = QFrame()
                 row.setStyleSheet("""
                    QFrame {
                        background-color: #2b2b2b;
                        border-radius: 6px;
                        border: 1px solid #3e3e3e;
                    }
                    QFrame:hover {
                        background-color: #333333;
                        border-color: #555;
                    }
                 """)
                 row.setFixedHeight(45)
                 
                 row_layout = QHBoxLayout(row)
                 row_layout.setContentsMargins(15, 0, 15, 0)
                 row_layout.setSpacing(10)
                 
                 # Rank/Index ? No, just Name
                 name_lbl = QLabel(s['name'])
                 name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
                 name_lbl.setStyleSheet("color: white; border: none; background: transparent;")
                 row_layout.addWidget(name_lbl)
                 
                 row_layout.addStretch()
                 
                 m, sec = divmod(s['total_seconds'], 60)
                 h, m = divmod(m, 60)
                 
                 # Colorize duration based on length?
                 color = "#aaaaaa"
                 if h > 2: color = "#ff9966" # Highlight long sessions
                 
                 time_str = f"{int(h)}h {int(m)}m"
                 
                 time_lbl = QLabel(time_str)
                 time_lbl.setFont(QFont("Roboto Medium", 11))
                 time_lbl.setStyleSheet(f"color: {color}; border: none; background: transparent;")
                 row_layout.addWidget(time_lbl)
                 
                 self.list_layout.addWidget(row)

