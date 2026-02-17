import time
import threading
from datetime import datetime
from .window_watcher import get_open_windows, get_active_window_info
from .discord_rpc import DiscordRPC

class Tracker:
    def __init__(self, storage_manager, icon_manager=None):
        self.storage = storage_manager
        self.icon_manager = icon_manager
        self.is_running = False
        
        # Logging State (Database)
        self.current_activity = None 
        self.current_log_id = None
        self.current_desc_log_id = None
        self.last_process_name = None
        self.last_window_title = None # Track title changes without using Activity.description
        self.start_time = None 
        self.session_start_time = time.time() # Global session start for Discord
        self.last_heartbeat = 0
        
        # Open Window Persistence State (UI Only)
        # Map: process_name -> { 'activity': Obj, 'accumulated_time': float, 'last_focus_time': timestamp, 'is_focused': bool }
        self.open_sessions = {}
        
        # Manual/Concurrent Tracking State
        self.manual_sessions = {} 
        self.manual_desc_sessions = {}
 
        
        # Suppression State
        self.ignored_apps = {"explorer.exe", "SearchApp.exe", "ShellExperienceHost.exe"}
        
        
        self.discord = DiscordRPC(client_id="1469935146579918868")
        self.discord_pinned_activity = None
        self.discord_last_target_name = None

        
    def start(self):
        self.is_running = True
        self.discord.connect()
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()

    def _resolve_icon_path(self, process_name, executable_path):
        if not self.icon_manager or not executable_path:
            return executable_path # Fallback to exe path if no manager (though storage expects png)
            
        extracted = self.icon_manager.extract_icon(executable_path, process_name)
        return extracted if extracted else executable_path

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
        if self.discord.connected:
            self.discord.clear()
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
        
        # Start description logging for manual session
        desc = activity.description if activity.description else "Manual Session"
        desc_id = self.storage.start_description_log(activity.id, desc)
        self.manual_desc_sessions[activity.id] = desc_id
        
    def stop_manual_session(self, activity):
        """Stops a manual timer."""
        if activity.id in self.manual_sessions:
            log_id = self.manual_sessions.pop(activity.id)
            self.storage.stop_logging(log_id)
            
            if activity.id in self.manual_desc_sessions:
                desc_id = self.manual_desc_sessions.pop(activity.id)
                self.storage.stop_description_log(desc_id)

    def is_manual_running(self, activity_id):
        return activity_id in self.manual_sessions
        
    def update_manual_description(self, activity_id, new_description):
        """Switches description log for a running manual session."""
        if activity_id in self.manual_sessions:
            # Stop old desc log
            if activity_id in self.manual_desc_sessions:
                old_desc_id = self.manual_desc_sessions.pop(activity_id)
                self.storage.stop_description_log(old_desc_id)
            
            # Start new desc log
            new_desc_id = self.storage.start_description_log(activity_id, new_description)
            self.manual_desc_sessions[activity_id] = new_desc_id
        
    def stop_auto_tracking(self):
        if self.current_log_id:
            self.storage.stop_logging(self.current_log_id)
            self.current_log_id = None
            
        if self.current_desc_log_id:
            self.storage.stop_description_log(self.current_desc_log_id)
            self.current_desc_log_id = None

        self.current_activity = None
        self.last_process_name = None
        self.last_window_title = None
        
        # Ensure cleared on stop
        if self.discord.connected:
            self.discord.clear()

    def set_discord_pin(self, activity):
        """Manually pins an activity for Discord status."""
        # If toggling off (passing likely same activity but logic handles external toggle state?)
        # UI will pass activity to pin. If we want to unpin, UI should pass None?
        # Or UI handles toggle.
        # Let's assume UI passes activity to PIN. To UNPIN, pass None.
        
        self.discord_pinned_activity = activity
        print(f"DEBUG: Pinning Activity: {activity.name if activity else 'None'}")
        self._update_discord() # Force immediate update
        

        
    def _update_discord(self):
        if not self.discord.connected:
            return

        # 1. Check Global Setting
        is_enabled = self.storage.get_setting("discord_enabled", "True") == "True"
        if not is_enabled:
            self.discord.clear()
            self.discord_last_target_name = None # Ensure nothing is checked
            return

        # RESOLVE TARGET ACTIVITY
        target = self.discord_pinned_activity
        
        # Verify if pinned target is still valid/running
        is_pinned_valid = False
        if target:
            if self.current_activity and self.current_activity.id == target.id:
                 is_pinned_valid = True
            elif target.id in self.manual_sessions:
                 is_pinned_valid = True
            elif target.type == 'app' and target.name in self.open_sessions:
                 is_pinned_valid = True
            
            if not is_pinned_valid:
                target = None # Pin lost - Fallback to Auto
        
        
        # If no valid pin, use current activity
        if not target:
            if self.current_activity:
                 target = self.current_activity
            elif self.open_sessions:
                 # Fallback to Background Auto (Most recent)
                 # Find session with max last_focus_time (MRU)
                 try:
                     # Use last_focus_time, defaulting to 0 if missing (backward compatibility key)
                     best_sess = max(self.open_sessions.values(), key=lambda x: x.get('last_focus_time', 0))
                     target = best_sess['activity']
                 except Exception as e:
                     print(f"Error in background fallback: {e}")
            elif self.manual_sessions:
                 # Fallback to Manual
                 first_mid = next(iter(self.manual_sessions))
                 target = self.storage.get_activity_by_id(first_mid)

        if target:
            # 2. Check Per-Activity Setting (Fresh)
            fresh_act = self.storage.get_activity_by_id(target.id)
            if fresh_act:
                target.discord_visible = fresh_act.discord_visible
            
            if not target.discord_visible:
                self.discord.update(
                    details="Idling",
                    state="Waiting for activity...",
                    start=self.session_start_time
                )
                self.discord_last_target_name = "Idling" # Hidden activity isn't "Live" as itself
                return
                
            # Determine State/Description
            state = target.description
            
            if target.type == 'app':
                if self.current_activity and self.current_activity.id == target.id and self.last_window_title:
                     state = self.last_window_title
                else:
                     state = "Active"
            
            # Formatting
            details = f"Using {target.name}"
            if target.type == 'irl':
                details = f"{target.name}"
            
            if not state: state = target.description or "Active"

            self.discord.update(
                details=details,
                state=state,
                start=self.session_start_time
            )
            self.discord_last_target_name = target.name
        else:
            # Final Fallback: Allow "Idling"
            self.discord.update(
                details="Idling",
                state="Waiting for activity...",
                start=self.session_start_time
            )
            self.discord_last_target_name = "Idling"

    # Legacy aliases
    def set_manual_activity(self, activity):
        self.start_manual_session(activity)

    def force_start_app(self, app_info):
        """Used by UI to start manual tracking from window info dict"""
        icon_path = self._resolve_icon_path(app_info['process_name'], app_info.get('executable_path'))
        activity = self.storage.get_or_create_activity(
            name=app_info['process_name'], 
            activity_type='app',
            description=app_info['title'],
            icon_path=icon_path
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
                self._update_discord() # Keep Discord status updated
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
        
        # Filter active window if it's one of ours
        if active_info:
             if "Gainhour" in active_info['title'] or "Settings Saved" == active_info['title']:
                 active_info = None
                 
        focused_name = active_info['process_name'] if active_info else None
        
        # --- Persistence Logic ---
        current_pnames = set()
        for win in open_windows:
            pname = win['process_name']
            if pname in self.ignored_apps or "Gainhour" in win['title'] or "Settings Saved" == win['title']:
                continue
            
            current_pnames.add(pname)
            
            # Add to open_sessions if new
            if pname not in self.open_sessions:
                # Extract icon if needed
                icon_path = self._resolve_icon_path(pname, win.get('executable_path'))

                # Get activity for UI
                act = self.storage.get_or_create_activity(
                    name=pname,
                    activity_type='app',
                    description=win['title'],
                    icon_path=icon_path
                )
                self.open_sessions[pname] = {
                    'activity': act,
                    'executable_path': win.get('executable_path'), # Store for icon retry
                    'accumulated_time': 0.0,
                    'last_update': time.time(),
                    'last_focus_time': time.time(), # Initialize with current time (assumption: just opened/discovered)
                    'is_focused': False
                }
        
        # Remove closed apps
        for pname in list(self.open_sessions.keys()):
            if pname not in current_pnames:
                del self.open_sessions[pname]

        # CRITICAL FIX: Ensure we stop tracking if the current activity is closed
        # (Even if we are currently focused on an ignored app like Explorer)
        if self.current_activity and self.current_activity.name not in current_pnames:
             # Only stop if it's really gone (not just temporarily missing due to some glitch, but current_pnames is robust)
             # Also active_windows check implies it's closed.
             self.stop_auto_tracking()

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
            
            if is_detected_focused:
                 sess['last_focus_time'] = now

            # Update Description if changed (Find matching window title)
            # We need to find the window again? optimize?
            # active_info has title if focused.
            # Update Description if changed (Find matching window title)
            if is_detected_focused and active_info:
                 sess['activity'].description = active_info['title']
                 
                 # --- Auto-Icon Retry Logic ---
                 # If icon is missing or not a PNG (extracted), try to fetch it again
                 act = sess['activity']
                 if (not act.icon_path or not act.icon_path.endswith('.png')) and sess.get('executable_path'):
                      # Try to extract
                      new_icon = self._resolve_icon_path(pname, sess['executable_path'])
                      if new_icon and new_icon.endswith('.png') and new_icon != act.icon_path:
                           print(f"Auto-fetched missing icon for {pname}")
                           act.icon_path = new_icon
                           self.storage.get_session().commit() # Commit changes to this object? 
                           # Note: sess['activity'] is attached to a session? 
                           # Tracker holds `storage` but `get_or_create_activity` closes its session. 
                           # The activity object in `open_sessions` might be detached.
                           # Safer to use update_activity via storage.
                           self.storage.update_activity(act.id, icon_path=new_icon)
                           
            else:
                 # Search in open_windows (slower but needed for background updates if titles change?)
                 pass# For now, let's just update if focused, or if we iterate open_windows again properly.
                 # Actually we iterated open_windows above. passing title would be better.
                 pass

        # Better approach: Update description during the open_windows loop
        # Reworking the loop above would be cleaner but this diff targets this block.
        # Let's trust focused update for now, or re-iterate if crucial.


        # --- Normal Auto-Tracking (DB Logging) Logic ---
        if not active_info: return
        # Ignore App windows
        title = active_info['title']
        if "Gainhour" in title or title == "Add IRL Activity" or title == "Edit Activity" or title == "Add Description" or title == "Select Icon" or title == "Delete Activity" or title.startswith("Activity Logs - ") or title == "Explorer": 
            return
        
        process_name = active_info['process_name']
        if process_name == "explorer.exe":
             pass # Removed debug print

        # Check ignore list (case-insensitive for safety)
        if process_name in self.ignored_apps or process_name.lower() in [i.lower() for i in self.ignored_apps]:
             if self.current_activity and self.current_activity.name == process_name:
                 self.stop_auto_tracking()
             return

        # Check Manual
        activity = self.storage.get_or_create_activity(
            name=process_name, 
            activity_type='app',
            description=active_info['title'],
            icon_path=self._resolve_icon_path(process_name, active_info.get('executable_path'))
        )
        
        if activity.id in self.manual_sessions:
            if self.current_log_id:
                self.stop_auto_tracking()
            # Removed redundant discord update
            return

        # Normal Auto-Tracking Logic
        if self.last_process_name != process_name:
             self.stop_auto_tracking()
             
             activity = self.storage.get_or_create_activity(
                name=process_name, 
                activity_type='app',
                description=active_info['title'],
                icon_path=self._resolve_icon_path(process_name, active_info.get('executable_path'))
            )
             
             self.current_log_id = self.storage.start_logging(activity.id)
             self.current_activity = activity
             self.last_process_name = process_name
             self.start_time = time.time()
             
             # Start description log (New table tracking)
             self.current_desc_log_id = self.storage.start_description_log(activity.id, active_info['title'])
             self.last_window_title = active_info['title']
             
             # Removed redundant discord update
        else:
            # -------------------------------------------------------------------------
            # HEARTBEAT: Update end_time in DB periodically to prevent data loss on crash
            # -------------------------------------------------------------------------
            if time.time() - self.last_heartbeat > 30: # Every 30 seconds
                if self.current_log_id:
                    self.storage.update_log_heartbeat(self.current_log_id)
                if self.current_desc_log_id:
                    self.storage.update_desc_heartbeat(self.current_desc_log_id)
                
                # Heartbeat for manual sessions
                for mid in list(self.manual_sessions.values()):
                     self.storage.update_log_heartbeat(mid)
                for did in list(self.manual_desc_sessions.values()):
                     self.storage.update_desc_heartbeat(did)
                     
                self.last_heartbeat = time.time()

            if self.last_window_title != active_info['title']:
                  self.last_window_title = active_info['title']
                  
                  # Stop old desc log
                  if self.current_desc_log_id:
                      self.storage.stop_description_log(self.current_desc_log_id)
                  
                  # Start new desc log
                  self.current_desc_log_id = self.storage.start_description_log(self.current_activity.id, active_info['title'])
                  
                  # Update Activity.description ONLY if NOT an app (for IRL stuff)
                  if self.current_activity.type != 'app':
                      self.current_activity.description = active_info['title']


