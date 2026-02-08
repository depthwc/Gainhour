import customtkinter as ctk
from PIL import Image, ImageTk
import os
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
import pystray
from pystray import MenuItem as item

# Add project root to sys.path if running directly
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# Import our modules
from src.database.storage import StorageManager
from src.database.models import Activity, ActivityLog
from src.core.tracker import Tracker
from src.core.icon_manager import IconManager
from src.core.window_watcher import get_open_windows

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gainhour")
        self.geometry("1000x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Set App Icon
        # We rely on gainhour.ico existing in root now
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "gainhour.ico")
        if os.path.exists(icon_path):
             try:
                 self.iconbitmap(icon_path)
             except Exception as e:
                 print(f"Failed to load icon: {e}")

        # Initialize Managers
        self.db = StorageManager("gainhour.db")
        self.db.clean_explorer_data() # Remove tracked explorer data
        self.icon_manager = IconManager()
        self.tracker = Tracker(self.db)
        
        # Start Tracker in Automatic Mode by default
        self.tracker.start()

        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create Navigation Frame
        self.create_navigation_frame()

        # Create Frames
        # Create Frames
        self.home_frame = HomeFrame(self, self.tracker)
        self.activities_frame = ActivitiesFrame(self, self.db, self.tracker, self.icon_manager)
        self.statistics_frame = StatisticsFrame(self, self.db)
        self.settings_frame = SettingsFrame(self)

        # Select default frame
        self.select_frame("home")

        # System Tray Setup
        self.tray_icon = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.withdraw()
        if not self.tray_icon:
            self.setup_tray()
            
    def setup_tray(self):
        icon_path = "gainhour.ico"
        image = Image.open(icon_path) if os.path.exists(icon_path) else Image.new('RGB', (64, 64), color='blue')
        
        menu = (
            item('Open', self.show_window),
            item('Quit', self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("gainhour", image, "Gainhour", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.deiconify()
        self.lift()

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.tracker.stop()
        self.quit()
        self.destroy()

    def create_navigation_frame(self):
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)

        self.navigation_frame_label = ctk.CTkLabel(self.navigation_frame, text="Gainhour",
                                                             compound="left", font=ctk.CTkFont(size=15, weight="bold"))
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Home",
                                                   fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                   anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.activities_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Activities",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      anchor="w", command=self.activities_button_event)
        self.activities_button.grid(row=2, column=0, sticky="ew")
        
        self.statistics_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Statistics",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      anchor="w", command=self.statistics_button_event)
        self.statistics_button.grid(row=3, column=0, sticky="ew")

        self.settings_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Settings",
                                                      fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                                      anchor="w", command=self.settings_button_event)
        self.settings_button.grid(row=4, column=0, sticky="ew")

    def select_frame(self, name):
        # set button color for selected button
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.activities_button.configure(fg_color=("gray75", "gray25") if name == "activities" else "transparent")
        self.statistics_button.configure(fg_color=("gray75", "gray25") if name == "statistics" else "transparent")
        self.settings_button.configure(fg_color=("gray75", "gray25") if name == "settings" else "transparent")

        # show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        
        if name == "activities":
            self.activities_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.activities_frame.grid_forget()

        if name == "statistics":
            self.statistics_frame.grid(row=0, column=1, sticky="nsew")
            if hasattr(self.statistics_frame, 'refresh'):
                self.statistics_frame.refresh() 
        else:
            self.statistics_frame.grid_forget()
            
        if name == "settings":
            self.settings_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.settings_frame.grid_forget()

    def home_button_event(self):
        self.select_frame("home")

    def activities_button_event(self):
        self.select_frame("activities")

    def statistics_button_event(self):
        self.select_frame("statistics")

    def settings_button_event(self):
        self.select_frame("settings")

class HomeFrame(ctk.CTkFrame):
    def __init__(self, master, tracker):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.tracker = tracker
        self.db = master.db 
        self.icon_manager = master.icon_manager
        
        # Header: Currently Tracking (Auto)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=10)
        
        self.status_label = ctk.CTkLabel(self.header_frame, text="Active Sessions:", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(side="left", anchor="n", pady=2)
        
        # Container for dynamic session rows
        self.sessions_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.sessions_frame.pack(side="left", padx=10, fill="x", expand=True)
        
        # Global Timer (Total Today) - Styled Box
        self.timer_card = ctk.CTkFrame(self.header_frame, fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#333333")
        self.timer_card.pack(side="right", anchor="n", pady=0, padx=5)
        
        self.timer_title = ctk.CTkLabel(self.timer_card, text="TOTAL TODAY", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray70")
        self.timer_title.pack(padx=15, pady=(5, 0))
        
        self.timer_value = ctk.CTkLabel(self.timer_card, text="00:00:00", font=ctk.CTkFont(family="Roboto Medium", size=24, weight="bold"), text_color="#4cc9f0")
        self.timer_value.pack(padx=15, pady=(0, 5))


        
        # Sub-header: App List + Controls
        self.subheader = ctk.CTkFrame(self, fg_color="transparent")
        self.subheader.pack(fill="x", padx=20, pady=(10, 5))
        
        # Row 1: Label + Add IRL
        row1 = ctk.CTkFrame(self.subheader, fg_color="transparent")
        row1.pack(fill="x")
        ctk.CTkLabel(row1, text="Applications", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        self.add_irl_btn = ctk.CTkButton(row1, text="+ Add IRL Activity", command=self.add_irl_activity, height=28)
        self.add_irl_btn.pack(side="right")
        
        # Row 2: Search + Filter
        row2 = ctk.CTkFrame(self.subheader, fg_color="transparent")
        row2.pack(fill="x", pady=(5, 0))
        
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(row2, placeholder_text="Search...", width=200, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        self.filter_var = ctk.StringVar(value="All")
        self.filter_btn = ctk.CTkSegmentedButton(row2, values=["All", "Apps", "IRL"], variable=self.filter_var, command=self.on_filter_change)
        self.filter_btn.pack(side="left")
        
        self.search_var.trace_add("write", self.on_search_change)
        
        # Top Apps Section (New)
        ctk.CTkLabel(self, text="Top Used", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=20, pady=(10,0))
        self.top_apps_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_apps_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(self, text="All Applications", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x", padx=20, pady=(10,0))
        self.apps_scroll = ctk.CTkScrollableFrame(self, label_text=None)
        self.apps_scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.app_rows = {} # Map unique_row_key -> {frame, name_lbl, ...}
        self.session_cards = {} # Map log_id -> {card_frame, timer_label, ...} for smooth updates
        
        self.last_refresh = 0
        self.refresh_rate = 1 
        self.update_ui()

    def add_irl_activity(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Start IRL Activity")
        dialog.geometry("400x550")
        
        try:
            dialog.iconbitmap("gainhour.ico")
        except:
            pass
            
        dialog.grab_set()
        
        # 1. Icon Selection
        self.selected_icon_path = None
        
        icon_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        icon_frame.pack(pady=(20, 10))
        
        self.icon_btn = ctk.CTkButton(
            icon_frame, 
            text="+", 
            width=100, 
            height=100, 
            font=ctk.CTkFont(size=40),
            fg_color="gray30",
            hover_color="gray40",
            command=lambda: self.select_icon_dialog(self.icon_btn)
        )
        self.icon_btn.pack()
        ctk.CTkLabel(dialog, text="Select Icon (Optional)", text_color="gray").pack()

        # 2. Name (Single Combo)
        ctk.CTkLabel(dialog, text="Activity Name").pack(pady=(20, 5))
        existing = [a.name for a in self.db.get_all_activities() if a.type == 'irl']
        self.name_combobox = ctk.CTkComboBox(dialog, values=existing, width=250)
        self.name_combobox.pack(pady=5)
        self.name_combobox.set("")
        
        # 3. Description
        ctk.CTkLabel(dialog, text="Description").pack(pady=(10, 5))
        self.desc_text = ctk.CTkTextbox(dialog, width=250, height=100)
        self.desc_text.pack(pady=5)
        
        # 4. Start Button
        def start_irl():
            name = self.name_combobox.get()
            desc = self.desc_text.get("1.0", "end-1c")
            
            if name:
                final_icon_path = None
                if self.selected_icon_path:
                    final_icon_path = self.icon_manager.save_user_icon(self.selected_icon_path, name)
                
                activity = self.db.get_or_create_activity(name, 'irl', description=desc, icon_path=final_icon_path)
                
                # Update recent changes
                session = self.db.get_session()
                try:
                    act = session.query(Activity).get(activity.id)
                    if desc: act.description = desc
                    if final_icon_path: act.icon_path = final_icon_path
                    session.commit()
                finally:
                    session.close()
                
                self.tracker.start_manual_session(activity)
                self.refresh_apps_list()
                dialog.destroy()
        
        ctk.CTkButton(dialog, text="Start Timer", command=start_irl, width=200, height=40, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=30)

    def select_icon_dialog(self, btn_widget):
        path = ctk.filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.ico")])
        if path:
            self.selected_icon_path = path
            try:
                img = Image.open(path)
                ctk_img = ctk.CTkImage(img, size=(80, 80))
                btn_widget.configure(image=ctk_img, text="", fg_color="transparent") 
            except Exception as e:
                print(f"Error loading preview: {e}")

    # ... update_ui ...

    # ... refresh_apps_list ...

    def create_app_row(self, key, info):
        frame = ctk.CTkFrame(self.apps_scroll)
        frame.pack(fill="x", pady=2)
        
        name = info['process_name']
        is_irl = info['is_irl']
        
        # ... (Icon Logic same as before) ...
        # Copied for stability, ensuring no missing logic
        icon_image = None
        icon_path = None
        exe_path = info.get('executable_path')
        if exe_path and os.path.exists(exe_path) and exe_path.lower().endswith('.exe'):
             cached = self.icon_manager.get_icon_path(name)
             if cached: icon_path = cached
             else: icon_path = self.icon_manager.extract_icon(exe_path, name)
        if not icon_path: icon_path = self.icon_manager.get_icon_path(name)
        if not icon_path and exe_path and os.path.exists(exe_path): icon_path = exe_path
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                icon_image = ctk.CTkImage(img, size=(20, 20))
            except: pass

        icon_text = ""
        if not icon_image: icon_text = name[:2].upper() if name else "??"

        icon_label = ctk.CTkLabel(frame, text=icon_text, image=icon_image, width=30, fg_color="gray30" if not icon_image else "transparent", corner_radius=5)
        icon_label.pack(side="left", padx=5)
        
        # Name + IRL Container (Fixed Width)
        info_frame = ctk.CTkFrame(frame, fg_color="transparent", width=200, height=24)
        info_frame.pack(side="left", padx=5)
        info_frame.pack_propagate(False)
        
        name_text = name
        if len(name_text) > 20: name_text = name_text[:17] + "..."
        name_label = ctk.CTkLabel(info_frame, text=name_text, font=ctk.CTkFont(weight="bold"), anchor="w")
        name_label.pack(side="left")

        if is_irl:
             ctk.CTkLabel(info_frame, text="IRL", font=ctk.CTkFont(size=10, weight="bold"), fg_color="#333333", corner_radius=4).pack(side="left", padx=5)
        
        title_text = info.get('title', '') or ''
        display_title = title_text
        if len(display_title) > 30: display_title = display_title[:27] + "..."
        
        title_label = ctk.CTkLabel(frame, text=display_title, text_color="gray", width=200, anchor="w", cursor="hand2")
        title_label.pack(side="left", padx=10)
        title_label.bind("<Button-1>", lambda e, k=key: self.edit_description(k))
        
        time_label = ctk.CTkLabel(frame, text="0h 0m", width=80, anchor="e")
        time_label.pack(side="left", padx=10)

        # Buttons Frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)

        # Edit Button for IRL
        if is_irl:
            edit_btn = ctk.CTkButton(btn_frame, text="Edit", width=40, height=24, fg_color="gray", command=lambda: self.edit_irl_activity(key))
            edit_btn.pack(side="left", padx=2)
        
        btn = ctk.CTkButton(btn_frame, text="Start", width=60)
        btn.pack(side="left", padx=2)
        
        self.app_rows[key] = {
            'frame': frame,
            'name': name_label,
            'title': title_label,
            'time': time_label,
            'btn': btn,
            'icon': icon_label,
            'info': info,
            'parent': parent_frame
        }
        self.update_app_row(key, info)

    def edit_irl_activity(self, key):
        # Allow editing Icon, Description (and Name?)
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit {key}")
        dialog.geometry("400x550")
        try: dialog.iconbitmap("gainhour.ico")
        except: pass
        dialog.grab_set()
        
        # Get existing data
        activity = self.db.get_or_create_activity(key, 'irl') # Should exist
        
        # Icon
        self.selected_icon_path = None
        icon_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        icon_frame.pack(pady=(20, 10))
        
        btn_img = None
        if activity.icon_path and os.path.exists(activity.icon_path):
             try:
                 img = Image.open(activity.icon_path)
                 btn_img = ctk.CTkImage(img, size=(80, 80))
             except: pass
             
        self.edit_icon_btn = ctk.CTkButton(
            icon_frame, 
            text="+" if not btn_img else "", 
            image=btn_img,
            width=100, 
            height=100, 
            font=ctk.CTkFont(size=40),
            fg_color="gray30" if not btn_img else "transparent",
            hover_color="gray40",
            command=lambda: self.select_icon_dialog(self.edit_icon_btn)
        )
        self.edit_icon_btn.pack()
        ctk.CTkLabel(dialog, text="Change Icon").pack()

        # Name (Editable?) - Renaming is complex, let's allow updating description primarily
        # If we rename, we create a new activity effectively or rename the DB entry.
        # Let's just do description for now to be safe, or rename if simple.
        ctk.CTkLabel(dialog, text="Activity Name (Read Only)").pack(pady=(20, 5))
        name_entry = ctk.CTkEntry(dialog, width=250)
        name_entry.insert(0, key)
        name_entry.configure(state="disabled")
        name_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Description").pack(pady=(10, 5))
        desc_text = ctk.CTkTextbox(dialog, width=250, height=100)
        desc_text.insert("1.0", activity.description or "")
        desc_text.pack(pady=5)
        
        def save():
            new_desc = desc_text.get("1.0", "end-1c")
            
            # Save icon if changed
            final_icon_path = activity.icon_path
            if self.selected_icon_path:
                final_icon_path = self.icon_manager.save_user_icon(self.selected_icon_path, key)
            
            session = self.db.get_session()
            try:
                act = session.query(Activity).get(activity.id)
                act.description = new_desc
                if final_icon_path: act.icon_path = final_icon_path
                session.commit()
            finally:
                session.close()
            
            # Update UI
            self.refresh_apps_list()
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Save Changes", command=save, width=200, height=40).pack(pady=30)

    def edit_description(self, key):
        widgets = self.app_rows.get(key)
        if not widgets: return
        
        info = widgets['info']
        current_desc = info.get('title', '')
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit {key}")
        dialog.geometry("300x200")
        try: dialog.iconbitmap("gainhour.ico")
        except: pass
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Edit Description").pack(pady=5)
        entry = ctk.CTkTextbox(dialog, width=250, height=100)
        entry.pack(pady=5)
        entry.insert("1.0", current_desc or "")
        
        def save():
            new_desc = entry.get("1.0", "end-1c")
            
            # Update DB
            activity_type = info.get('type', 'app')
            activity = self.db.get_or_create_activity(key, activity_type)
            
            session = self.db.get_session()
            try:
                act = session.query(Activity).get(activity.id)
                act.description = new_desc
                session.commit()
            finally:
                session.close()
                
            # Update Local Info
            info['title'] = new_desc
            widgets['info']['title'] = new_desc
            
            # Force UI update
            self.update_app_row(key, info)
            
            # Also update Discord if running?
            if self.tracker.current_activity and self.tracker.current_activity.name == key:
                self.tracker.current_activity.description = new_desc
                self.tracker.discord.update(details=f"Using {key}", state=new_desc)
            
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Save", command=save, width=100).pack(pady=10)

    def edit_description(self, key):
        widgets = self.app_rows.get(key)
        if not widgets: return
        
        info = widgets['info']
        current_desc = info.get('title', '')
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit {key}")
        dialog.geometry("300x200")
        try: dialog.iconbitmap("gainhour.ico")
        except: pass
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Edit Description").pack(pady=5)
        entry = ctk.CTkTextbox(dialog, width=250, height=100)
        entry.pack(pady=5)
        entry.insert("1.0", current_desc or "")
        
        def save():
            new_desc = entry.get("1.0", "end-1c")
            
            # Update DB
            activity_type = info.get('type', 'app')
            activity = self.db.get_or_create_activity(key, activity_type)
            
            session = self.db.get_session()
            try:
                act = session.query(Activity).get(activity.id)
                act.description = new_desc
                session.commit()
            finally:
                session.close()
                
            # Update Local Info
            info['title'] = new_desc
            widgets['info']['title'] = new_desc
            widgets['title'].configure(text=new_desc)
            
            # Force UI update
            self.update_app_row(key, info)
            
            # Also update Discord if running?
            if self.tracker.current_activity and self.tracker.current_activity.name == key:
                self.tracker.current_activity.description = new_desc
                self.tracker.discord.update(details=f"Using {key}", state=new_desc)
            
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Save", command=save, width=100).pack(pady=10)

        # Update Header with ALL Active Sessions (Auto + Manual)
        # Clear previous widgets in current_activity_label (which we will repurpose as a container frame?)
        # Actually current_activity_label is a Label. We should use a frame container.
        # Let's check init: self.current_activity_label = ctk.CTkLabel... 
        # We need to change the structure in __init__ first!
        pass 

    # We need to change __init__ to use a Frame for active sessions list
    # But wait, I can just destroy children of header_frame except status label?
    # Let's do a targeted replace of update_ui AND __init__ part if possible.
    # OR, simpler: Just repack everything in header_frame.
    
    # Let's look at __init__ again.
    # self.header_frame contains: status_label, current_activity_label, timer_label.
    # We should make a 'sessions_frame' inside header_frame.

    # I'll replace update_ui to rebuild the content of a container.
    # But first I need to ensure there IS a container.
    # In __init__ (lines 159-160), 'current_activity_label' is a Label.
    # I will construct the list dynamically.
    
    def stop_session(self, log_id, is_auto):
        if is_auto:
            self.tracker.stop_auto_tracking()
            # If we want to prevent auto-restart immediately, we might need a "temporary ignore" or just rely on user focus switch.
            # But "Stop" on auto usually means "I'm done with this, stop tracking even if focused?" 
            # Or just "Stop the timer visually". 
            # Tracker refetches active window every second. If focused, it will restart.
            # To truly stop, we might need to ignore it. 
            # For now, let's just stop tracking.
        else:
            # Manual
            # We need to find the activity key for this log_id
            # But wait, stop_manual_session takes activity object.
            # We have log_id.
            # Better: stop_manual_session by Log ID?
            # Or iterate.
            session = self.db.get_session()
            try:
                log = session.query(ActivityLog).get(log_id)
                if log:
                    self.db.stop_logging(log_id)
                    # Remove from tracker.manual_sessions
                    # We need to find which activity this log belongs to
                    for act_id, lid in list(self.tracker.manual_sessions.items()):
                        if lid == log_id:
                             del self.tracker.manual_sessions[act_id]
                             break
            finally:
                session.close()
        self.update_ui()

    def update_or_create_card(self, log_id, activity, start_time=None, is_auto=True, accumulated=0.0):
        # Calculate time
        # If auto (persistent), time is accumulated. If it's currently focused, it might render slightly differently?
        # Actually Tracker updates 'accumulated_time' continuously if focused.
        # But for smooth UI, we might want to add (now - last_update) if focused.
        # Let's rely on Tracker's accumulated time for simplicity, or passed value.
        
        elapsed = int(accumulated)
        if not is_auto and start_time: # Manual sessions use start_time
             elapsed = int(time.time() - start_time)
        
        h, r = divmod(elapsed, 3600)
        m, s = divmod(r, 60)
        timer_str = f"{h:02}:{m:02}:{s:02}"
        
        # Restore Stats (Today / Total)
        total_disp = 0
        today_disp = 0
        try:
             total = self.db.get_activity_duration(activity.name, activity.type)
             today = self.db.get_today_duration(activity.name, activity.type) 
             
             # Add current elapsed to totals for display
             total_disp = total + elapsed
             today_disp = today + elapsed 
        except: pass

        def fmt_time(seconds):
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            return f"{h}h {m}m"

        stats_text = f"Today: {fmt_time(today_disp)}   |   Total: {fmt_time(total_disp)}"

        # If card exists, update it
        if log_id in self.session_cards:
            widgets = self.session_cards[log_id]
            widgets['timer_label'].configure(text=timer_str)
            if 'stats_label' in widgets:
                widgets['stats_label'].configure(text=stats_text)
            
            # Update description if it changed
            if 'desc_label' in widgets and activity.description:
                # Truncate
                dtext = activity.description
                if len(dtext) > 50: dtext = dtext[:47] + "..."
                widgets['desc_label'].configure(text=dtext)
                
            return

        # Create New Card
        card = ctk.CTkFrame(self.sessions_frame, fg_color="#2b2b2b", corner_radius=10)
        card.pack(fill="x", pady=5)
        
        # Row 1: ... (Same as before)
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=5, pady=(5, 0))
        
        # Icon logic...
        icon_image = None
        icon_path = self.icon_manager.get_icon_path(activity.name)
        if not icon_path and activity.type == 'app':
             if activity.icon_path and os.path.exists(activity.icon_path):
                 icon_path = activity.icon_path
        
        if icon_path and isinstance(icon_path, str) and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                icon_image = ctk.CTkImage(img, size=(20, 20))
            except: pass
        
        ctk.CTkLabel(row1, text="", image=icon_image, width=24).pack(side="left")
        ctk.CTkLabel(row1, text=activity.name, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=5)
        
        badge_text = "AUTO" if is_auto else "FORCED"
        badge_color = "#1f6aa5" if is_auto else "#a55a1f"
        ctk.CTkLabel(row1, text=badge_text, font=ctk.CTkFont(size=10, weight="bold"), fg_color=badge_color, corner_radius=4).pack(side="right")
        
        # Description
        desc_lbl = None
        if activity.description:
            row_desc = ctk.CTkFrame(card, fg_color="transparent")
            row_desc.pack(fill="x", padx=35, pady=(0, 0))
            dtext = activity.description
            if len(dtext) > 50: dtext = dtext[:47] + "..."
            desc_lbl = ctk.CTkLabel(row_desc, text=dtext, font=ctk.CTkFont(size=11), text_color="gray80", anchor="w")
            desc_lbl.pack(fill="x")

        # Timer
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=5, pady=0)
        timer_lbl = ctk.CTkLabel(row2, text=timer_str, font=ctk.CTkFont(size=20, weight="bold", family="Consolas"))
        timer_lbl.pack(side="left", padx=30)
        
        # Stats Row (Restored)
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=5, pady=(0, 5))
        stats_lbl = ctk.CTkLabel(row3, text=stats_text, font=ctk.CTkFont(size=11), text_color="gray")
        stats_lbl.pack(side="left", padx=30)

        # Stop Button
        row4 = ctk.CTkFrame(card, fg_color="transparent")
        row4.pack(fill="x", padx=5, pady=(0, 5))
        ctk.CTkButton(row4, text="Stop", width=60, height=24, fg_color="gray", hover_color="darkred", 
                     command=lambda: self.stop_session(log_id, is_auto)).pack(side="right")

        self.session_cards[log_id] = {
            'card': card,
            'timer_label': timer_lbl,
            'stats_label': stats_lbl,
            'desc_label': desc_lbl
        }

    def update_ui(self):
        try:
            if not self.winfo_exists(): return
        except: return

        active_log_ids = set()
        session = self.db.get_session()
        try:
            # 1. Active Auto Session (Single Focused Window, Persistent Timer)
            if self.tracker.current_activity:
                pname = self.tracker.current_activity.name
                if pname in self.tracker.open_sessions:
                    data = self.tracker.open_sessions[pname]
                    card_id = f"auto_{pname}"
                    active_log_ids.add(card_id)
                    acc = data['accumulated_time']
                    self.update_or_create_card(card_id, data['activity'], is_auto=True, accumulated=acc)

            # 2. Manual Sessions
            for act_id, log_id in list(self.tracker.manual_sessions.items()):
                activity = session.query(Activity).get(act_id)
                log = session.query(ActivityLog).get(log_id)
                if log and activity:
                    active_log_ids.add(log_id) 
                    self.update_or_create_card(log_id, activity, start_time=log.start_time.timestamp(), is_auto=False)
            
            # 3. Update Global Timer (Total Today)
            # 3. Update Global Timer (Total Today)
            total_today = self.db.get_total_today_duration()
            
            # Add current running sessions
            # Auto
            if self.tracker.current_activity:
                 pname = self.tracker.current_activity.name
                 if pname in self.tracker.open_sessions:
                      total_today += int(self.tracker.open_sessions[pname]['accumulated_time'])

            # Manual (Add elapsed since start)
            for act_id, log_id in list(self.tracker.manual_sessions.items()):
                 log = session.query(ActivityLog).get(log_id)
                 if log:
                      total_today += int(time.time() - log.start_time.timestamp())

            h, r = divmod(int(total_today), 3600)
            m, s = divmod(r, 60)
            self.timer_value.configure(text=f"{h:02}:{m:02}:{s:02}")
                    
        except Exception as e:
            print(f"UI Update Error: {e}")
        finally:
            session.close()

        # Remove stale cards
        for log_id in list(self.session_cards.keys()):
            if log_id not in active_log_ids:
                widgets = self.session_cards.pop(log_id)
                try: widgets['card'].destroy()
                except: pass

        # Refresh List
        if time.time() - self.last_refresh > self.refresh_rate:
            self.refresh_apps_list()
            self.last_refresh = time.time()
        
        self.after(1000, self.update_ui)



    


    # SPLIT: The replacement content above ends at update_ui. 
    # I will perform THIS edit for update_ui first.

    


    def on_filter_change(self, value):
        self.refresh_apps_list()

    def on_search_change(self, *args):
        # Debounce could be added here if needed, but for local list direct call is fine usually
        self.refresh_apps_list()
    
    def refresh_apps_list(self):
        current_data = {}
        
        # 1. Get ALL known activities from DB (Persistent List)
        all_activities = self.db.get_all_activities() 
        
        for activity in all_activities:
            if not activity.name: continue
            
            # Map DB activity to info dict
            current_data[activity.name] = {
                'process_name': activity.name,
                'title': activity.description,
                'executable_path': activity.icon_path,
                'type': activity.type,
                'is_irl': (activity.type == 'irl')
            }

        # 2. Get Open Windows (to update status/title and add new ones not in DB yet)
        windows = get_open_windows()
        for w in windows:
            proc_name = w['process_name']
            
            # Update or Add
            if proc_name in current_data:
                # Update title and path if available
                current_data[proc_name]['title'] = w['title']
                if not current_data[proc_name]['executable_path']:
                    current_data[proc_name]['executable_path'] = w.get('executable_path')
            else:
                # Add new discovered app
                current_data[proc_name] = {
                    'process_name': proc_name,
                    'title': w['title'],
                    'executable_path': w.get('executable_path'),
                    'type': 'app', 
                    'is_irl': False
                }

        # 3. Calculate Global Top 5 (Before Filter)
        durations = {}
        for key, info in current_data.items():
            durations[key] = self.db.get_activity_duration(key, info['type'])
            
        def sort_key_global(k):
            return (-durations.get(k, 0), k.lower())
            
        all_sorted = sorted(current_data.keys(), key=sort_key_global)
        top_keys = all_sorted[:5]
        top_set = set(top_keys)

        # 4. Filtering & Sorting for Main List
        search_text = self.search_var.get().lower()
        filter_mode = self.filter_var.get() # All, Apps, IRL
        
        filtered_keys = []
        for key, info in current_data.items():
            # Duplicates allowed now (user request)
            # if key in top_set: continue  <-- Removed strict exclusion
            
            # Apply Type Filter
            is_irl = info['is_irl']
            if filter_mode == "Apps" and is_irl: continue
            if filter_mode == "IRL" and not is_irl: continue
            
            # Apply Search Filter
            name = info['process_name'].lower()
            title = (info.get('title') or "").lower()
            if search_text and (search_text not in name and search_text not in title):
                continue
                
            filtered_keys.append(key)

        sorted_rest_keys = sorted(filtered_keys, key=sort_key_global)
        
        # 5. Update/Create Rows & Enforce Order
        
        # We need unique IDs for rows because keys can now appear in both lists
        # Format: "TOP:{key}" and "MAIN:{key}"
        
        active_row_keys = set()
        
        # Helper to manage rows
        def process_list(keys, parent_frame, prefix):
             for key in keys:
                 info = current_data[key]
                 row_key = f"{prefix}:{key}"
                 active_row_keys.add(row_key)
                 
                 if row_key in self.app_rows:
                     self.update_app_row(row_key, key, info)
                 else:
                     self.create_app_row(row_key, key, info, parent_frame)
                     
                 # Enforce Order (Pack)
                 self.app_rows[row_key]['frame'].pack(fill="x", pady=2)
                 
        # Process Top Apps (Always Visible)
        process_list(top_keys, self.top_apps_frame, "TOP")
        
        # Process Rest
        process_list(sorted_rest_keys, self.apps_scroll, "MAIN")
             
        # 6. Remove stale rows (Hidden by filter or deleted)
        for row_key in list(self.app_rows.keys()):
            if row_key not in active_row_keys:
                self.app_rows[row_key]['frame'].destroy()
                del self.app_rows[row_key]

    def create_app_row(self, row_key, real_key, info, parent_frame):
        # Style difference for Top Apps
        is_top = (parent_frame == self.top_apps_frame)
        bg_color = "gray10" if is_top else None 
        border_width = 2 if is_top else 0
        border_color = "#3B8ED0" if is_top else None
        corner_radius = 10 if is_top else 0
        
        frame = ctk.CTkFrame(parent_frame, fg_color=bg_color, border_width=border_width, border_color=border_color, corner_radius=corner_radius)
        frame.pack(fill="x", pady=4 if is_top else 2, padx=2 if is_top else 0, ipady=5 if is_top else 0)
        
        name = info['process_name']
        is_irl = info['is_irl']
        
        # Icon Logic
        icon_image = None
        icon_path = None
        
        # 1. Check if we have an executable path to extract from
        exe_path = info.get('executable_path')
        if exe_path and os.path.exists(exe_path) and exe_path.lower().endswith('.exe'):
             cached = self.icon_manager.get_icon_path(name)
             if cached: icon_path = cached
             else: icon_path = self.icon_manager.extract_icon(exe_path, name)
        
        if not icon_path: icon_path = self.icon_manager.get_icon_path(name)
        if not icon_path and exe_path and os.path.exists(exe_path): icon_path = exe_path

        icon_size = (20, 20)
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path)
                icon_image = ctk.CTkImage(img, size=icon_size)
            except: pass

        icon_text = ""
        if not icon_image: icon_text = name[:2].upper() if name else "??"

        icon_label = ctk.CTkLabel(frame, text=icon_text, image=icon_image, width=30, fg_color="gray30" if not icon_image else "transparent", corner_radius=5)
        icon_label.pack(side="left", padx=5)
        
        # Name + IRL Container (Fixed Width - REDUCED to fix overflow)
        info_frame = ctk.CTkFrame(frame, fg_color="transparent", width=180, height=24) 
        info_frame.pack(side="left", padx=5)
        info_frame.pack_propagate(False)
        
        name_text = name
        if len(name_text) > 22: name_text = name_text[:19] + "..." 
        
        name_font = ctk.CTkFont(weight="bold")
        name_label = ctk.CTkLabel(info_frame, text=name_text, font=name_font, anchor="w")
        name_label.pack(side="left")

        if is_irl:
             ctk.CTkLabel(info_frame, text="IRL", font=ctk.CTkFont(size=10, weight="bold"), fg_color="#333333", corner_radius=4).pack(side="left", padx=5)
        
        # Title/Description Hidden in Main List as requested
        # title_label = ctk.CTkLabel(frame, text=display_title, ...)
        # We keep the key for update logic but don't show it
        
        time_label = ctk.CTkLabel(frame, text="0h 0m", width=70, anchor="e") 
        time_label.pack(side="left", padx=5)

        # Buttons Frame
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=5) 

        # Edit Button for IRL
        if is_irl:
            edit_btn = ctk.CTkButton(btn_frame, text="Edit", width=40, height=24, fg_color="gray", command=lambda: self.edit_irl_activity(real_key))
            edit_btn.pack(side="left", padx=2)
        
        btn = ctk.CTkButton(btn_frame, text="Start", width=60)
        btn.pack(side="left", padx=2)
        
        self.app_rows[row_key] = {
            'frame': frame,
            'name': name_label,
            # 'title': title_label, # Removed
            'time': time_label,
            'btn': btn,
            'icon': icon_label,
            'info': info
        }
        self.update_app_row(row_key, real_key, info)


    def update_app_row(self, row_key, bg_key, info):
        widgets = self.app_rows[row_key]
        key = bg_key
        
        # Get Activity ID
        activity = self.db.get_or_create_activity(
            name=key, 
            activity_type='irl' if info['is_irl'] else 'app'
        )
        
        # Update Time (Today | Total)
        total_seconds = self.db.get_activity_duration(key, activity.type)
        today_seconds = self.db.get_today_duration(key, activity.type)
        
        def fmt(seconds):
            if seconds <= 0: return "0m"
            m, _ = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return f"{h}h {m}m"

        time_str = f"Today: {fmt(today_seconds)} | Total: {fmt(total_seconds)}"
        
        # Adjust width if needed or anchor
        widgets['time'].configure(text=time_str, width=200) # Increased width for dual stats
        
        # Determine Status & Button State
        is_manual = self.tracker.is_manual_running(activity.id)
        
        is_auto = (self.tracker.current_activity and self.tracker.current_activity.id == activity.id)
        # Also check open_sessions for "paused" auto
        if not is_auto and key in self.tracker.open_sessions:
             is_auto = True # It's technically an auto session, just not focused.
             # But button behavior: "Stop" signals "Suppress"? 
             # If it's just open in background, user might want to "Block" it?
             # For now, let's keep is_auto logic simple: active tracking.

        if is_manual:
             widgets['btn'].configure(text="Stop", fg_color="red", command=lambda: self.stop_manual(activity))
        elif is_auto:
             widgets['btn'].configure(text="Stop", fg_color="#FF9900", command=lambda: self.suppress_app(activity))
        else:
             widgets['btn'].configure(text="Start", fg_color="#3B8ED0", command=lambda: self.start_manual(activity))

    def start_manual(self, activity):
        self.tracker.start_manual_session(activity)
        self.refresh_apps_list()

    def stop_manual(self, activity):
        self.tracker.stop_manual_session(activity)
        self.refresh_apps_list()

    def suppress_app(self, activity):
        self.tracker.set_ignore_app(activity.name, True)
        self.refresh_apps_list()

class ActivitiesFrame(ctk.CTkFrame):
    def __init__(self, master, db, tracker, icon_manager):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.db = db
        self.tracker = tracker
        self.icon_manager = icon_manager
        
        self.label = ctk.CTkLabel(self, text="Manage Activities", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        self.add_button = ctk.CTkButton(self, text="Add IRL Activity", command=self.add_activity_dialog)
        self.add_button.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Your Activities")
        self.scrollable_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.load_activities()

    def load_activities(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        activities = self.db.get_all_activities()
        # Sort so enabled ones are top? Or just alphabetical.
        activities.sort(key=lambda x: x.name)
        
        for i, activity in enumerate(activities):
            self.create_activity_row(i, activity)

    def create_activity_row(self, row, activity):
        frame = ctk.CTkFrame(self.scrollable_frame)
        frame.pack(fill="x", pady=5)
        
        # Icon
        icon_image = None
        if activity.icon_path and os.path.exists(activity.icon_path):
             try:
                img = Image.open(activity.icon_path)
                icon_image = ctk.CTkImage(img, size=(30, 30))
             except:
                pass
        
        icon_label = ctk.CTkLabel(frame, text="", image=icon_image, width=40)
        icon_label.pack(side="left", padx=5)

        name_label = ctk.CTkLabel(frame, text=activity.name, font=ctk.CTkFont(weight="bold"))
        name_label.pack(side="left", padx=10)
        
        type_desc = "App" if activity.type == 'app' else "IRL"
        type_label = ctk.CTkLabel(frame, text=type_desc, text_color="gray")
        type_label.pack(side="left", padx=10)

        # Privacy toggle
        switch_var = ctk.BooleanVar(value=activity.discord_visible)
        
        def toggle_privacy():
            self.db.update_activity_visibility(activity.id, switch_var.get())
            
        switch = ctk.CTkSwitch(frame, text="Discord", variable=switch_var, command=toggle_privacy)
        switch.pack(side="right", padx=10)
        
        if activity.type == 'irl':
            start_btn = ctk.CTkButton(frame, text="Start", width=60, command=lambda a=activity: self.start_manual(a))
            start_btn.pack(side="right", padx=10)

    def start_manual(self, activity):
        self.tracker.set_manual_activity(activity)
        self.master.select_frame("home") # Switch to home to show timer

    def add_activity_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Activity")
        dialog.geometry("400x400")
        dialog.grab_set() # Modal
        
        ctk.CTkLabel(dialog, text="Activity Name").pack(pady=5)
        name_entry = ctk.CTkEntry(dialog)
        name_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Description").pack(pady=5)
        desc_entry = ctk.CTkEntry(dialog)
        desc_entry.pack(pady=5)
        
        # Icon Upload (Simulated for now, just text entry or file picker)
        # For simplicity, we can let them type a path or just use default
        ctk.CTkLabel(dialog, text="Icon Path (Optional)").pack(pady=5)
        icon_entry = ctk.CTkEntry(dialog)
        icon_entry.pack(pady=5)

        def save():
            name = name_entry.get()
            desc = desc_entry.get()
            icon_p = icon_entry.get()
            if name:
                # If icon path provided, try to copy it using manager
                final_icon_path = None
                if icon_p and os.path.exists(icon_p):
                     # Copy logic could be in App/Manager, but for now direct
                     final_icon_path = self.icon_manager.save_user_icon(icon_p, name)
                
                self.db.get_or_create_activity(name, 'irl', description=desc, icon_path=final_icon_path)
                self.load_activities()
                dialog.destroy()
        
        ctk.CTkButton(dialog, text="Save", command=save).pack(pady=20)


class StatisticsFrame(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.db = db
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.label = ctk.CTkLabel(self, text="Statistics", font=ctk.CTkFont(size=20, weight="bold"))
        self.label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # Container for Charts
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1) # Chart
        self.content_frame.grid_rowconfigure(1, weight=1) # List
    
    def refresh(self):
        # Clear previous
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        stats = self.db.get_activity_stats()
        if not stats:
            ctk.CTkLabel(self.content_frame, text="No data available yet.").pack(pady=20)
            return

        # Prepare data
        names = [s['name'] for s in stats[:5]] # Top 5
        seconds = [s['total_seconds'] for s in stats[:5]]
        
        # 1. Matplotlib Chart
        fig, ax = plt.subplots(figsize=(6, 4))
        # Dark theme check
        plt.style.use('dark_background')
        fig.patch.set_facecolor('#2b2b2b') # Match CTk dark theme roughly
        ax.set_facecolor('#2b2b2b')
        
        wedges, texts, autotexts = ax.pie(seconds, labels=names, autopct='%1.1f%%', startangle=90)
        ax.axis('equal') 
        plt.setp(texts, color="white")
        plt.setp(autotexts, size=8, weight="bold", color="white")
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.content_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", pady=10)
        
        # 2. Detailed List
        list_frame = ctk.CTkScrollableFrame(self.content_frame, label_text="Activity Breakdown")
        list_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        
        for s in stats:
            row = ctk.CTkFrame(list_frame)
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=s['name'], font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            
            # Format time
            m, s_remain = divmod(s['total_seconds'], 60)
            h, m = divmod(m, 60)
            time_str = f"{h}h {m}m {s_remain}s"
            
            ctk.CTkLabel(row, text=time_str).pack(side="right", padx=10)


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self, text="Settings (Coming Soon)", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

if __name__ == "__main__":
    app = App()
    app.mainloop()
