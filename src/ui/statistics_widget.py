from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                                 QScrollArea, QPushButton, QStackedWidget)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QColor, QIcon
from datetime import date, timedelta
from typing import Dict, List, Tuple
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
from src.utils.text_utils import format_app_name
from src.ui.checkable_combobox import CheckableComboBox

matplotlib.use('QtAgg')

class ScrollableCanvas(FigureCanvas):
    def __init__(self, figure, scroll_area=None):
        super().__init__(figure)
        self.scroll_area = scroll_area

    def wheelEvent(self, event):
        if self.scroll_area:
            delta_y = event.angleDelta().y()
            delta_x = event.angleDelta().x()
            
            scrollbar = self.scroll_area.horizontalScrollBar()
            if abs(delta_x) > abs(delta_y):
                scrollbar.setValue(scrollbar.value() - delta_x)
                event.accept()
                return
            elif delta_y != 0:
                scrollbar.setValue(scrollbar.value() - delta_y)
                event.accept()
                return
        super().wheelEvent(event)

class LifetimeStackedChart(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
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
        self.chart_scroll.setFixedHeight(300)
        
        self.chart_container = QWidget()
        self.chart_container.setStyleSheet("background: transparent;")
        self.chart_layout = QHBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0,0,0,0)
        self.chart_layout.setAlignment(Qt.AlignLeft)
        
        self.figure, self.ax = plt.subplots(figsize=(5, 3.5), dpi=90)
        self.figure.patch.set_facecolor('#252526')
        self.canvas = ScrollableCanvas(self.figure, self.chart_scroll)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        self.chart_layout.addWidget(self.canvas)
        self.chart_scroll.setWidget(self.chart_container)
        self.chart_layout.addWidget(self.canvas)
        self.chart_scroll.setWidget(self.chart_container)
        self.layout.addWidget(self.chart_scroll)
        
        # List Area
        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setFrameShape(QFrame.NoFrame)
        self.list_scroll.setStyleSheet("background: transparent; border: none;")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(5)
        self.list_layout.setContentsMargins(0,0,0,0)
        
        self.list_scroll.setWidget(self.list_container)
        self.layout.addWidget(self.list_scroll)

    def update_data(self, daily_breakdown):
        self.ax.clear()
        self.ax.set_facecolor('#252526')
        
        if not daily_breakdown:
            self.ax.text(0.5, 0.5, "No Data", color='#666', ha='center', va='center')
            self.canvas.draw()
            return
            
        # Sort dates
        sorted_dates = sorted(daily_breakdown.keys())
        date_labels = [d.strftime("%b %d, %Y") for d in sorted_dates]
        
        # Get all unique activities
        all_activities = set()
        for d in daily_breakdown:
            all_activities.update(daily_breakdown[d].keys())
        sorted_activities = sorted(list(all_activities))
        
        # Prepare data for stacking
        # x = indices
        x = range(len(sorted_dates))
        bottoms = [0] * len(sorted_dates)
        
        colors = [
            '#5865F2', '#EB459E', '#F7B731', '#20BF6B', '#A55EEA', '#45AAF2', '#778CA3', 
            '#FF6B6B', '#48DBFB', '#1DD1A1', '#FF9F43', '#54A0FF', '#5F27CD', '#C8D6E5', 
            '#576574', '#0ABDE3', '#EE5253', '#10AC84', '#2E86DE', '#341F97', '#8395A7', '#FFC312'
        ]
        
        # Calculate total duration for each activity to sort them
        activity_totals = {}
        for act in sorted_activities:
             total = sum(daily_breakdown[d].get(act, 0) for d in sorted_dates)
             activity_totals[act] = total
             
        # Sort activities by total duration (descending) so biggest stacks are consistently colored/ordered
        sorted_activities.sort(key=lambda a: activity_totals[a], reverse=True)

        # We will only put the top 10 in the legend to avoid clutter
        top_activities = set(sorted_activities[:10])
        
        handles = []
        labels = []
        
        for i, activity in enumerate(sorted_activities):
            color = colors[i % len(colors)]
            values = []
            for d in sorted_dates:
                # Convert to hours
                seconds = daily_breakdown[d].get(activity, 0)
                values.append(seconds / 3600)
            
            bar = self.ax.bar(x, values, bottom=bottoms, color=color, width=0.6, linewidth=0)
            
            # Record handle for legend if in top 10
            if activity in top_activities:
                handles.append(bar)
                labels.append(format_app_name(activity))
            
            # Update bottoms
            for j in range(len(bottoms)):
                bottoms[j] += values[j]
        
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(date_labels, rotation=45, ha='right', color='#aaaaaa', fontsize=8)
        # Horizontal labels, centered
        self.ax.set_xticklabels(date_labels, rotation=0, ha='center', color='#aaaaaa', fontsize=8)
        self.ax.tick_params(axis='y', colors='#aaaaaa', labelsize=8)
        self.ax.set_ylabel("Hours", color='#aaaaaa', fontsize=9)
        
        # Styling
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#444')
        self.ax.spines['bottom'].set_color('#444')
        self.ax.grid(axis='y', linestyle='--', alpha=0.3, color='#444')
        
        # Dynamic Width
        # Increase width significantly to fit "Feb 17, 2026" horizontally without overlap
        # Estimate ~80-100px per label?
        width_inch = max(6, len(sorted_dates) * 1.2) 
        self.figure.set_size_inches(width_inch, 3.5)
        self.canvas.setFixedWidth(int(width_inch * 90))
        
        self.figure.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.15)
        
        self.canvas.draw()
        
        # Update List
        self._fill_list(sorted_activities, activity_totals, colors)

    def _fill_list(self, sorted_activities, activity_totals, colors):
        for i in reversed(range(self.list_layout.count())): 
            item = self.list_layout.itemAt(i)
            if item.widget(): item.widget().setParent(None)
            
        for i, activity in enumerate(sorted_activities):
             color = colors[i % len(colors)]
             total_seconds = activity_totals[activity]
             
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
             
             name_lbl = QLabel(format_app_name(activity))
             name_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold)) 
             name_lbl.setStyleSheet("color: white; background: transparent; border: none;")
             row_layout.addWidget(name_lbl)
             
             row_layout.addStretch()
             
             m, sec = divmod(total_seconds, 60)
             h, m = divmod(m, 60)
             time_str = f"{int(h)}h {int(m)}m"
             
             time_lbl = QLabel(time_str)
             time_lbl.setFont(QFont("Segoe UI", 9))
             time_lbl.setStyleSheet("color: #cccccc; background: transparent; border: none;")
             row_layout.addWidget(time_lbl)
             
             self.list_layout.addWidget(row)

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
        self.canvas = ScrollableCanvas(self.figure, self.chart_scroll)
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

        colors = [
            '#5865F2', '#EB459E', '#F7B731', '#20BF6B', '#A55EEA', '#45AAF2', '#778CA3', 
            '#FF6B6B', '#48DBFB', '#1DD1A1', '#FF9F43', '#54A0FF', '#5F27CD', '#C8D6E5', 
            '#576574', '#0ABDE3', '#EE5253', '#10AC84', '#2E86DE', '#341F97', '#8395A7', '#FFC312'
        ]
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


class ClusteredColumnChart(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.chart_scroll = QScrollArea()
        self.chart_scroll.setWidgetResizable(True)
        self.chart_scroll.setFrameShape(QFrame.NoFrame)
        self.chart_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chart_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chart_scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:horizontal { height: 8px; background: #2b2b2b; border-radius: 4px; }
            QScrollBar::handle:horizontal { background: #444; border-radius: 4px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { background: none; }
        """)
        self.chart_scroll.setFixedHeight(300)
        
        self.chart_container = QWidget()
        self.chart_container.setStyleSheet("background: transparent;")
        self.chart_layout = QHBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0,0,0,0)
        self.chart_layout.setAlignment(Qt.AlignLeft)
        
        self.figure, self.ax = plt.subplots(figsize=(5, 3.5), dpi=90)
        self.figure.patch.set_facecolor('#252526')
        self.canvas = ScrollableCanvas(self.figure, self.chart_scroll)
        self.canvas.setStyleSheet("background-color: transparent;")
        
        self.chart_layout.addWidget(self.canvas)
        self.chart_scroll.setWidget(self.chart_container)
        self.layout.addWidget(self.chart_scroll)

    def update_data(self, daily_breakdown, groups, group_colors):
        self.ax.clear()
        self.ax.set_facecolor('#252526')
        
        if not daily_breakdown or not any(groups):
            self.ax.text(0.5, 0.5, "No Data or Groups Selected", color='#666', ha='center', va='center')
            self.canvas.draw()
            return
            
        sorted_dates = sorted(daily_breakdown.keys())
        date_labels = [d.strftime("%b %d") for d in sorted_dates]
        
        x = range(len(sorted_dates))
        n_groups = len(groups)
        bar_width = 0.8 / n_groups if n_groups > 0 else 0.8
        
        max_val = 0
        # Calculate total max in seconds to determine unit
        for i, group in enumerate(groups):
            if group:
                for d in sorted_dates:
                    day_data = daily_breakdown.get(d, {})
                    day_sum = sum(day_data.get(app, 0) for app in group)
                    max_val = max(max_val, day_sum)
                    
        if max_val > 3600:
            unit_div = 3600
            unit_label = "Hours"
        elif max_val > 60:
            unit_div = 60
            unit_label = "Minutes"
        else:
            unit_div = 1
            unit_label = "Seconds"

        max_plot_val = 0
        
        for i, group in enumerate(groups):
            if not group:
                values = [0] * len(sorted_dates)
            else:
                values = []
                for d in sorted_dates:
                    day_data = daily_breakdown.get(d, {})
                    day_sum = sum(day_data.get(app, 0) for app in group)
                    values.append(day_sum / unit_div) 
            
            if values:
                max_plot_val = max(max_plot_val, max(values))
            
            offset = (i - n_groups / 2.0 + 0.5) * bar_width if n_groups > 0 else 0
            x_pos = [pos + offset for pos in x]
            
            self.ax.bar(x_pos, values, width=bar_width, color=group_colors[i], linewidth=0)
            
        self.ax.set_xticks(list(x))
        self.ax.set_xticklabels(date_labels, rotation=0, ha='center', color='#aaaaaa', fontsize=8)
        self.ax.tick_params(axis='y', colors='#aaaaaa', labelsize=8)
        self.ax.set_ylabel(unit_label, color='#aaaaaa', fontsize=9)
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#444')
        self.ax.spines['bottom'].set_color('#444')
        self.ax.grid(axis='y', linestyle='--', alpha=0.3, color='#444')
        
        width_inch = max(6, len(sorted_dates) * max(1.2, bar_width * n_groups * 1.5))
        pixel_width = int(width_inch * 90)
        self.figure.set_size_inches(width_inch, 3.5)
        self.canvas.setFixedWidth(pixel_width)
        self.chart_container.setMinimumWidth(pixel_width)
        
        max_y = max_plot_val * 1.1 if max_plot_val > 0 else 1
        self.ax.set_ylim(0, max_y)
        
        # Save horizontal scrollbar position
        scrollbar = self.chart_scroll.horizontalScrollBar()
        scroll_val = scrollbar.value()
        
        self.figure.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.15)
        self.canvas.draw()
        
        # Restore scrollbar position after drawing
        # Use QTimer to ensure layout has updated before setting scroll
        QTimer.singleShot(0, lambda: scrollbar.setValue(scroll_val))

class StatisticsWidget(QWidget):
    def __init__(self, db, tracker=None):
        super().__init__()
        self.db = db
        self.tracker = tracker
        self.current_date = date.today()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # ... (Layout setup remains same until timer) ... Since I can't easily skip lines in replace_file_content without context matching, 
        # I will target the __init__ signature and the Timer block separately if possible, or just the whole file if I have to.
        # But here I am replacing the whole class or large chunks.
        # Let's try to do it in chunks.
        
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
        
        # --- B. Right Column (Lifetime Stacked) ---
        self.right_col = QWidget()
        self.right_layout = QVBoxLayout(self.right_col)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(10)
        
        self.stacked_header = QLabel("Daily Breakdown (Lifetime)")
        self.stacked_header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.stacked_header.setStyleSheet("color: white;")
        self.right_layout.addWidget(self.stacked_header)

        self.right_box = QFrame()
        self.right_box.setStyleSheet("""
            background-color: #252526; 
            border-radius: 10px; 
            border: 1px solid #3e3e3e;
        """)
        self.right_box_layout = QVBoxLayout(self.right_box)
        self.right_box_layout.setContentsMargins(10,10,10,10)
        
        self.lifetime_chart = LifetimeStackedChart()
        self.right_box_layout.addWidget(self.lifetime_chart)
        
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
        # We let it expand naturally instead of fixing height
        self.bottom_box_layout = QVBoxLayout(self.bottom_box)
        self.bottom_box_layout.setContentsMargins(15, 15, 15, 15)
        self.bottom_box_layout.setSpacing(10)
        
        bottom_header_label = QLabel("Compare Apps")
        bottom_header_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        bottom_header_label.setStyleSheet("color: white;")
        self.bottom_box_layout.addWidget(bottom_header_label)

        self.groups_layout = QHBoxLayout()
        self.groups_layout.setSpacing(20)
        self.groups_layout.setAlignment(Qt.AlignLeft)
        self.group_combos = []
        self.group_colors = ['#FF6B6B', '#1DD1A1', '#54A0FF'] # Red, Green, Blue
        
        # Load cached selections
        self.cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'chart_cache.json')
        self.cached_selections = [[], [], []]
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cached_selections = json.load(f)
        except Exception as e:
            print(f"Failed to load chart cache: {e}")
        
        for i in range(3):
            bg_layout = QHBoxLayout()
            color_box = QFrame()
            color_box.setFixedSize(12, 12)
            color_box.setStyleSheet(f"background-color: {self.group_colors[i]}; border-radius: 6px;")
            combo = CheckableComboBox()
            combo.setFixedWidth(200)
            
            # Identify the combo logic to save to cache when selection changes
            combo.setProperty("group_index", i)
            combo.selectionChanged.connect(self._on_combo_selection_changed)
            
            bg_layout.addWidget(color_box)
            bg_layout.addWidget(combo)
            self.groups_layout.addLayout(bg_layout)
            self.group_combos.append(combo)
            
        self.groups_layout.addStretch()
        self.bottom_box_layout.addLayout(self.groups_layout)
        
        self.clustered_chart = ClusteredColumnChart()
        self.bottom_box_layout.addWidget(self.clustered_chart)
        
        self.layout.addWidget(self.bottom_box)
        
        # Auto-refresh timer (every 1 second for live stats)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000) 

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
             
             # MERGE LIVE DATA FROM TRACKER
             if self.tracker:
                 import time
                 current_time = time.time()
                 
                 # Helper to add/update stats list
                 def add_to_stats(name, duration):
                     for s in stats:
                         if s['name'] == name:
                             s['total_seconds'] += duration
                             return
                     stats.append({'name': name, 'total_seconds': duration})

                 # 1. Auto-Tracker
                 if self.tracker.current_activity and self.tracker.start_time:
                     duration = current_time - self.tracker.start_time
                     if duration > 0:
                         add_to_stats(self.tracker.current_activity.name, duration)
                         
                 # 2. Manual Sessions
                 # Use manual_activities if available, else skip to avoid crash
                 if hasattr(self.tracker, 'manual_activities') and hasattr(self.tracker, 'manual_start_times'):
                     for aid, activity in self.tracker.manual_activities.items():
                         start_t = self.tracker.manual_start_times.get(aid)
                         if start_t:
                             duration = current_time - start_t
                             if duration > 0:
                                 add_to_stats(activity.name, duration)
             
             # Re-sort after merging
             stats.sort(key=lambda x: x['total_seconds'], reverse=True)
             
        else:
             stats = self.db.get_daily_stats(self.current_date)
        
        self.daily_total_lbl.setText(self._calculate_total_str(stats))
        self.daily_panel.update_data(stats)

    def refresh_total(self):
        stats = self.db.get_activity_stats()
        # For total, we could also merge live data, but 'today' is most important for "Live" feel.
        # Let's merge it for consistency if we are looking at total.
        
        if self.tracker:
             import time
             current_time = time.time()
             
             def add_to_stats(name, duration):
                 for s in stats:
                     if s['name'] == name:
                         s['total_seconds'] += duration
                         return
                 stats.append({'name': name, 'total_seconds': duration})

             if self.tracker.current_activity and self.tracker.start_time:
                 duration = current_time - self.tracker.start_time
                 if duration > 0:
                     add_to_stats(self.tracker.current_activity.name, duration)
                     
             if hasattr(self.tracker, 'manual_activities') and hasattr(self.tracker, 'manual_start_times'):
                 for aid, activity in self.tracker.manual_activities.items():
                     start_t = self.tracker.manual_start_times.get(aid)
                     if start_t:
                         duration = current_time - start_t
                         if duration > 0:
                             add_to_stats(activity.name, duration)
                             
             stats.sort(key=lambda x: x['total_seconds'], reverse=True)

        self.lifetime_total_lbl.setText(self._calculate_total_str(stats))
        self.total_panel.update_data(stats)
        
        # Update Stacked Chart
        daily_breakdown = self.db.get_daily_activity_breakdown()
        # We can optionally merge live data here too if we want "Today" column to be live in the stacked chart
        # But let's keep it simple for now, or just add it to today's entry
        
        if self.tracker:
            import time
            from datetime import date
            today = date.today()
            current_time = time.time()
            
            if today not in daily_breakdown:
                daily_breakdown[today] = {}
            
            def add_to_breakdown(name, duration):
                if name in daily_breakdown[today]:
                    daily_breakdown[today][name] += duration
                else:
                    daily_breakdown[today][name] = duration

            if self.tracker.current_activity and self.tracker.start_time:
                 duration = current_time - self.tracker.start_time
                 if duration > 0:
                     add_to_breakdown(self.tracker.current_activity.name, duration)
            
            if hasattr(self.tracker, 'manual_activities') and hasattr(self.tracker, 'manual_start_times'):
                 for aid, activity in self.tracker.manual_activities.items():
                     start_t = self.tracker.manual_start_times.get(aid)
                     if start_t:
                         duration = current_time - start_t
                         if duration > 0:
                             add_to_breakdown(activity.name, duration)

        self.lifetime_chart.update_data(daily_breakdown)

        # Build comprehensive list of all activities for comboboxes
        all_activities = set()
        for d in daily_breakdown:
            all_activities.update(daily_breakdown[d].keys())
        all_act_list = sorted(list(all_activities))
        
        for i, combo in enumerate(self.group_combos):
            # Pass cached selections if applicable
            combo.set_items(all_act_list, initial_checked=self.cached_selections[i])
            
        self.refresh_clustered_chart(daily_breakdown)

    def _on_combo_selection_changed(self):
        # Save to cache
        try:
            selections = [c.get_checked_items() for c in self.group_combos]
            with open(self.cache_file, 'w') as f:
                json.dump(selections, f)
            self.cached_selections = selections
        except Exception as e:
            print(f"Failed to save chart cache: {e}")
            
        self.refresh_clustered_chart()

    def refresh_clustered_chart(self, daily_breakdown=None):
        if not hasattr(self, 'group_combos') or not hasattr(self, 'clustered_chart'):
            return
            
        # Re-fetch if called directly from CheckableComboBox signal
        if not isinstance(daily_breakdown, dict):
            daily_breakdown = self.db.get_daily_activity_breakdown()
            
            if self.tracker:
                import time
                from datetime import date
                today = date.today()
                current_time = time.time()
                
                if today not in daily_breakdown:
                    daily_breakdown[today] = {}
                
                def add_to_breakdown(name, duration):
                    if name in daily_breakdown[today]:
                        daily_breakdown[today][name] += duration
                    else:
                        daily_breakdown[today][name] = duration

                if self.tracker.current_activity and self.tracker.start_time:
                     duration = current_time - self.tracker.start_time
                     if duration > 0:
                         add_to_breakdown(self.tracker.current_activity.name, duration)
                
                if hasattr(self.tracker, 'manual_activities') and hasattr(self.tracker, 'manual_start_times'):
                     for aid, activity in self.tracker.manual_activities.items():
                         start_t = self.tracker.manual_start_times.get(aid)
                         if start_t:
                             duration = current_time - start_t
                             if duration > 0:
                                 add_to_breakdown(activity.name, duration)
                                 
        groups = [combo.get_checked_items() for combo in self.group_combos]
        self.clustered_chart.update_data(daily_breakdown, groups, self.group_colors)
