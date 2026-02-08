import time
import threading
from datetime import datetime
from .window_watcher import get_open_windows, get_active_window_info
from .discord_rpc import DiscordRPC

class Tracker:
    def __init__(self, storage_manager):
        self.storage = storage_manager
        self.is_running = False
        
        # Logging State (Database)
        self.current_activity = None 
        self.current_log_id = None   
        self.last_process_name = None
        self.start_time = None 
        
        # Open Window Persistence State (UI Only)
        # Map: process_name -> { 'activity': Obj, 'accumulated_time': float, 'last_focus_time': timestamp, 'is_focused': bool }
        self.open_sessions = {}
        
        # Manual/Concurrent Tracking State
        self.manual_sessions = {} 
        
        # Suppression State
        self.ignored_apps = {"explorer.exe", "SearchApp.exe", "ShellExperienceHost.exe"}
        
        self.discord = DiscordRPC(client_id="1469935146579918868")
        
    def start(self):
        self.is_running = True
        self.discord.connect()
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()

    def set_ignore_app(self, app_name, ignore=True):
        if ignore:
            self.ignored_apps.add(app_name)
            if self.current_activity and self.current_activity.name == app_name:
                self.stop_auto_tracking()
        else:
            if app_name in self.ignored_apps:
                self.ignored_apps.remove(app_name)

    def is_ignored(self, app_name):
        return app_name in self.ignored_apps

    def stop(self):
        self.is_running = False
        # Stop auto
        if self.current_log_id:
            self.storage.stop_logging(self.current_log_id)
        
        # Stop all manuals
        for log_id in self.manual_sessions.values():
            self.storage.stop_logging(log_id)
        self.discord.close()

    def start_manual_session(self, activity):
        """Starts a concurrent manual timer for an activity."""
        # Un-suppress if manual start
        if activity.name in self.ignored_apps:
            self.ignored_apps.remove(activity.name)

        if activity.id in self.manual_sessions:
            return 
            
        # If auto-tracking matches this, stop auto-tracking
        if self.current_activity and self.current_activity.id == activity.id:
            self.stop_auto_tracking()
            
        log_id = self.storage.start_logging(activity.id)
        self.manual_sessions[activity.id] = log_id
        
    def stop_manual_session(self, activity):
        """Stops a manual timer."""
        if activity.id in self.manual_sessions:
            log_id = self.manual_sessions.pop(activity.id)
            self.storage.stop_logging(log_id)

    def is_manual_running(self, activity_id):
        return activity_id in self.manual_sessions
        
    def stop_auto_tracking(self):
        if self.current_log_id:
            self.storage.stop_logging(self.current_log_id)
            self.current_log_id = None
        self.current_activity = None
        self.last_process_name = None
        self.discord.clear()

    # Legacy aliases
    def set_manual_activity(self, activity):
        self.start_manual_session(activity)

    def force_start_app(self, app_info):
        """Used by UI to start manual tracking from window info dict"""
        activity = self.storage.get_or_create_activity(
            name=app_info['process_name'], 
            activity_type='app',
            description=app_info['title'],
            icon_path=app_info.get('executable_path')
        )
        self.start_manual_session(activity)

    def set_automatic_mode(self):
        for act_id in list(self.manual_sessions.keys()):
            log_id = self.manual_sessions.pop(act_id)
            self.storage.stop_logging(log_id)

    def _loop(self):
        while self.is_running:
            try:
                self._check_window()
            except Exception as e:
                print(f"Error in tracker loop: {e}")
            time.sleep(1) 

    def _check_window(self):
        # 1. Get Open Windows (for persistence)
        try:
            open_windows = get_open_windows() 
        except:
            open_windows = []

        active_info = get_active_window_info()
        focused_name = active_info['process_name'] if active_info else None
        
        # --- Persistence Logic ---
        current_pnames = set()
        for win in open_windows:
            pname = win['process_name']
            if pname in self.ignored_apps or "Gainhour" in win['title']:
                continue
            
            current_pnames.add(pname)
            
            # Add to open_sessions if new
            if pname not in self.open_sessions:
                # Get activity for UI
                act = self.storage.get_or_create_activity(
                    name=pname,
                    activity_type='app',
                    description=win['title'],
                    icon_path=win.get('executable_path')
                )
                self.open_sessions[pname] = {
                    'activity': act,
                    'accumulated_time': 0.0,
                    'last_update': time.time(),
                    'is_focused': False
                }
        
        # Remove closed apps
        for pname in list(self.open_sessions.keys()):
            if pname not in current_pnames:
                del self.open_sessions[pname]

        # Update timings & Description
        now = time.time()
        for pname, sess in self.open_sessions.items():
            if sess['is_focused']:
                # Add elapsed time since last check
                dt = now - sess['last_update']
                sess['accumulated_time'] += dt
            
            # Update focus state
            is_detected_focused = (pname == focused_name)
            sess['is_focused'] = is_detected_focused
            sess['last_update'] = now

            # Update Description if changed (Find matching window title)
            # We need to find the window again? optimize?
            # active_info has title if focused.
            if is_detected_focused and active_info:
                 sess['activity'].description = active_info['title']
            else:
                 # Search in open_windows (slower but needed for background updates if titles change?)
                 # For now, let's just update if focused, or if we iterate open_windows again properly.
                 # Actually we iterated open_windows above. passing title would be better.
                 pass

        # Better approach: Update description during the open_windows loop
        # Reworking the loop above would be cleaner but this diff targets this block.
        # Let's trust focused update for now, or re-iterate if crucial.
        # User wants description "back".

            
        # --- Normal Auto-Tracking (DB Logging) Logic ---
        if not active_info: return
        if "Gainhour" in active_info['title']: return
        
        process_name = active_info['process_name']
        if process_name in self.ignored_apps:
             if self.current_activity and self.current_activity.name == process_name:
                 self.stop_auto_tracking()
             return

        # Check Manual
        activity = self.storage.get_or_create_activity(
            name=process_name, 
            activity_type='app',
            description=active_info['title'],
            icon_path=active_info.get('executable_path')
        )
        
        if activity.id in self.manual_sessions:
            if self.current_log_id:
                self.stop_auto_tracking()
            if activity.discord_visible:
                 self.discord.update(details=f"Using {activity.name}", state=activity.description)
            return

        # Normal Auto-Tracking Logic
        if self.last_process_name != process_name:
             self.stop_auto_tracking()
             
             activity = self.storage.get_or_create_activity(
                name=process_name, 
                activity_type='app',
                description=active_info['title'],
                icon_path=active_info.get('executable_path')
            )
             
             self.current_log_id = self.storage.start_logging(activity.id)
             self.current_activity = activity
             self.last_process_name = process_name
             self.start_time = time.time()
             
             if activity.discord_visible:
                self.discord.update(details=f"Using {process_name}", state=active_info['title'])
        else:
             if self.current_activity and self.current_activity.description != active_info['title']:
                 self.current_activity.description = active_info['title']
                 if self.current_activity.discord_visible:
                     self.discord.update(details=f"Using {process_name}", state=active_info['title'])
