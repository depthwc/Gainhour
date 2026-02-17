from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                                 QScrollArea, QPushButton, QStackedWidget)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QColor, QIcon
from datetime import date, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
from src.utils.text_utils import format_app_name

matplotlib.use('QtAgg')

class ScrollableCanvas(FigureCanvas):
    def wheelEvent(self, event):
        event.ignore()

class StatsPanel(QFrame):
    """Reusable panel for displaying a Chart + List."""
    def __init__(self, title=""):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        # --- Chart Area (Scrollable) ---
        self.chart_scroll = QScrollArea()
        self.chart_scroll.setWidgetResizable(True) 
        self.chart_scroll.setFrameShape(QFrame.NoFrame)
        self.chart_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chart_scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:horizontal {
                height: 8px;
                background: #2b2b2b;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #444;
                border-radius: 4px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                background: none;
            }
        """)
        # Reduced height to allow top box to be smaller
        self.chart_scroll.setFixedHeight(230) 

        self.chart_container = QWidget()
        self.chart_container.setStyleSheet("background: transparent;")
        self.chart_layout = QHBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_layout.setAlignment(Qt.AlignLeft) 
        
        self.figure, self.ax = plt.subplots(figsize=(5, 2.8), dpi=90) 
        self.figure.patch.set_facecolor('#252526')
        self.canvas = ScrollableCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        self.chart_layout.addWidget(self.canvas)
        self.chart_scroll.setWidget(self.chart_container)
        
        self.layout.addWidget(self.chart_scroll)
        
        # List Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(5)
        self.list_layout.setContentsMargins(0,0,0,0)
        
        self.scroll.setWidget(self.list_container)
        self.layout.addWidget(self.scroll)

    def update_data(self, stats):
        self.ax.clear()
        self.ax.set_facecolor('#252526')
        self.figure.patch.set_facecolor('#252526')
        
        self.figure.subplots_adjust(bottom=0.1, top=0.95, left=0.1, right=0.95)
        
        valid_stats = [s for s in stats if s['total_seconds'] > 60]
        chart_stats = valid_stats[:50] 

        if not chart_stats:
            self.ax.text(0.5, 0.5, "No Data", 
                         horizontalalignment='center', verticalalignment='center',
                         color='#666666', fontsize=12)
            self.canvas.draw()
            self._fill_list([], [])
            return

        names = [format_app_name(s['name']) for s in chart_stats]
        
        max_sec = max(s['total_seconds'] for s in chart_stats)
        if max_sec > 3600:
             values = [s['total_seconds'] / 3600 for s in chart_stats]
             unit = "Hours"
        elif max_sec > 60:
             values = [s['total_seconds'] / 60 for s in chart_stats]
             unit = "Minutes"
        else:
             values = [s['total_seconds'] for s in chart_stats]
             unit = "Seconds"

        colors = ['#5865F2', '#EB459E', '#F7B731', '#20BF6B', '#A55EEA', '#45AAF2', '#778CA3']
        bar_colors = [colors[i % len(colors)] for i in range(len(values))]
        
        bars = self.ax.bar(range(len(values)), values, color=bar_colors, width=0.7)
        
        self.ax.set_xticks([]) 
        self.ax.tick_params(axis='y', colors='#aaaaaa', labelsize=7)
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#444')
        self.ax.spines['bottom'].set_color('#444')
        
        self.ax.grid(axis='y', linestyle='--', alpha=0.3, color='#444')
        self.ax.set_ylabel(unit, color='#aaaaaa', fontsize=8)
        
        num_bars = len(values)
        # Increased width per bar to prevent squeezing and enable scrolling
        width_inch = max(5, num_bars * 0.6) 
        height_inch = 2.8 
        
        self.figure.set_size_inches(width_inch, height_inch)
        self.canvas.setFixedWidth(int(width_inch * 90)) 
        
        self.canvas.draw()
        
        self._fill_list(chart_stats, bar_colors)

    def _fill_list(self, stats, colors):
        for i in reversed(range(self.list_layout.count())): 
            item = self.list_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        for i, s in enumerate(stats):
             color = colors[i] if i < len(colors) else '#cccccc'
             
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
             row.setFixedHeight(35) 
             
             row_layout = QHBoxLayout(row)
             row_layout.setContentsMargins(10, 0, 10, 0)
             
             color_box = QFrame()
             color_box.setFixedSize(10, 10)
             color_box.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
             row_layout.addWidget(color_box)
             
             name_lbl = QLabel(format_app_name(s['name']))
             name_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold)) 
             name_lbl.setStyleSheet("color: white; background: transparent; border: none;")
             row_layout.addWidget(name_lbl)
             
             row_layout.addStretch()
             
             m, sec = divmod(s['total_seconds'], 60)
             h, m = divmod(m, 60)
             time_str = f"{int(h)}h {int(m)}m"
             
             time_lbl = QLabel(time_str)
             time_lbl.setFont(QFont("Segoe UI", 9))
             time_lbl.setStyleSheet("color: #cccccc; background: transparent; border: none;")
             row_layout.addWidget(time_lbl)
             
             self.list_layout.addWidget(row)


class StatisticsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_date = date.today()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # === 1. TOP ROW (Left + Right Columns) ===
        self.top_row_widget = QWidget()
        self.top_row_layout = QHBoxLayout(self.top_row_widget)
        self.top_row_layout.setContentsMargins(0, 0, 0, 0)
        self.top_row_layout.setSpacing(20)
        
        # --- A. Left Column (Stats) ---
        self.left_col = QWidget()
        self.left_layout = QVBoxLayout(self.left_col)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(10)
        
        # Tab Header
        self.tab_layout = QHBoxLayout()
        self.tab_layout.setSpacing(10)
        self.btn_daily = self._create_tab_btn("Daily", True)
        self.btn_total = self._create_tab_btn("Total", False)
        self.btn_daily.clicked.connect(lambda: self.switch_tab(0))
        self.btn_total.clicked.connect(lambda: self.switch_tab(1))
        self.tab_layout.addWidget(self.btn_daily)
        self.tab_layout.addWidget(self.btn_total)
        self.tab_layout.addStretch()
        self.left_layout.addLayout(self.tab_layout)

        # Main Box (Stacked Content)
        self.main_box = QFrame()
        self.main_box.setStyleSheet("""
            QFrame#MainBox {
                background-color: #252526; 
                border-radius: 10px; 
                border: 1px solid #3e3e3e;
            }
        """)
        self.main_box.setObjectName("MainBox")
        self.main_box_layout = QVBoxLayout(self.main_box)
        self.main_box_layout.setContentsMargins(15, 15, 15, 15)
        
        self.stack = QStackedWidget()
        
        # Daily Page
        self.page_daily = QWidget()
        self.page_daily_layout = QVBoxLayout(self.page_daily)
        self.page_daily_layout.setContentsMargins(0,0,0,0)
        
        self.daily_header = QHBoxLayout()
        self.btn_prev = self._create_nav_btn("src/icons/prev.png", self.prev_day)
        self.btn_next = self._create_nav_btn("src/icons/next.png", self.next_day)
        self.date_lbl = QLabel("Today")
        self.date_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.date_lbl.setStyleSheet("color: white;")
        
        self.daily_total_lbl = QLabel("Total: 0h 0m")
        self.daily_total_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.daily_total_lbl.setStyleSheet("color: #cccccc;")
        
        self.daily_header.addWidget(self.btn_prev)
        self.daily_header.addWidget(self.date_lbl)
        self.daily_header.addWidget(self.btn_next)
        self.daily_header.addStretch()
        self.daily_header.addWidget(self.daily_total_lbl)
        
        self.page_daily_layout.addLayout(self.daily_header)
        self.page_daily_layout.addWidget(StatsPanel()) 
        self.daily_panel = self.page_daily_layout.itemAt(1).widget()
        
        # Total Page
        self.page_total = QWidget()
        self.page_total_layout = QVBoxLayout(self.page_total)
        self.page_total_layout.setContentsMargins(0,0,0,0)
        
        total_header = QHBoxLayout()
        total_lbl = QLabel("Lifetime Statistics")
        total_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        total_lbl.setStyleSheet("color: white;")
        
        self.lifetime_total_lbl = QLabel("Total: 0h 0m")
        self.lifetime_total_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lifetime_total_lbl.setStyleSheet("color: #cccccc;")
        
        total_header.addWidget(total_lbl)
        total_header.addStretch()
        total_header.addWidget(self.lifetime_total_lbl)
        
        self.page_total_layout.addLayout(total_header)
        self.page_total_layout.addWidget(StatsPanel()) 
        self.total_panel = self.page_total_layout.itemAt(1).widget()

        self.stack.addWidget(self.page_daily)
        self.stack.addWidget(self.page_total)
        self.main_box_layout.addWidget(self.stack)
        
        self.left_layout.addWidget(self.main_box)
        
        # --- B. Right Column (Placeholder) ---
        self.right_col = QWidget()
        self.right_layout = QVBoxLayout(self.right_col)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(10)
        
        header_spacer = QWidget()
        header_spacer.setFixedSize(10, 35) 
        self.right_layout.addWidget(header_spacer)

        self.right_box = QFrame()
        self.right_box.setStyleSheet("""
            background-color: #252526; 
            border-radius: 10px; 
            border: 1px solid #3e3e3e;
        """)
        self.right_layout.addWidget(self.right_box)
        
        self.top_row_layout.addWidget(self.left_col, stretch=1)
        self.top_row_layout.addWidget(self.right_col, stretch=1) 
        
        self.layout.addWidget(self.top_row_widget)
        
        # === 2. BOTTOM ROW (Full Width) ===
        self.bottom_box = QFrame()
        self.bottom_box.setStyleSheet("""
            background-color: #252526; 
            border-radius: 10px; 
            border: 1px solid #3e3e3e;
        """)
        self.bottom_box.setFixedHeight(400) 
        self.layout.addWidget(self.bottom_box)
        
        # Auto-refresh timer (every 1 minute)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(60000) 

        self.refresh()
        
    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_daily.setStyleSheet(self._get_tab_style(index == 0))
        self.btn_total.setStyleSheet(self._get_tab_style(index == 1))
        
    def _create_tab_btn(self, text, active):
        btn = QPushButton(text)
        btn.setFixedSize(100, 35)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        btn.setStyleSheet(self._get_tab_style(active))
        return btn
        
    def _get_tab_style(self, active):
        if active:
            return """
                QPushButton {
                    background-color: #5865F2; 
                    color: white; 
                    border: none; 
                    border-radius: 6px;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #2b2b2b; 
                    color: #aaaaaa; 
                    border: 1px solid #3e3e3e; 
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #333333;
                    color: white;
                }
            """

    def _create_nav_btn(self, icon_path, callback):
        btn = QPushButton()
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(20, 20))
        btn.setFixedSize(30, 30)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #444;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #666;
            }
        """)
        return btn

    def prev_day(self):
        self.current_date -= timedelta(days=1)
        self.refresh_daily() 
        
    def next_day(self):
        if self.current_date < date.today():
            self.current_date += timedelta(days=1)
            self.refresh_daily()
            
    def refresh(self):
        self.refresh_daily()
        self.refresh_total()
        
    def _calculate_total_str(self, stats):
        total_sec = sum(s['total_seconds'] for s in stats)
        h, m = divmod(total_sec // 60, 60)
        return f"Total: {int(h)}h {int(m)}m"

    def refresh_daily(self):
        if self.current_date == date.today():
             self.date_lbl.setText("Today")
             self.btn_next.setEnabled(False)
        elif self.current_date == date.today() - timedelta(days=1):
             self.date_lbl.setText("Yesterday")
             self.btn_next.setEnabled(True)
        else:
             self.date_lbl.setText(self.current_date.strftime("%b %d"))
             self.btn_next.setEnabled(True)
             
        if self.current_date == date.today():
             stats = self.db.get_today_stats()
        else:
             stats = self.db.get_daily_stats(self.current_date)
        
        self.daily_total_lbl.setText(self._calculate_total_str(stats))
        self.daily_panel.update_data(stats)

    def refresh_total(self):
        stats = self.db.get_activity_stats()
        self.lifetime_total_lbl.setText(self._calculate_total_str(stats))
        self.total_panel.update_data(stats)
