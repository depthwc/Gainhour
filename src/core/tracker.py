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
        
        self.current_activity = None 
        self.current_log_id = None
        self.current_desc_log_id = None
        self.last_process_name = None
        self.last_window_title = None
        self.start_time = None 
        self.session_start_time = time.time() 
        self.last_heartbeat = 0
        
        self.open_sessions = {}
        
        self.manual_sessions = {} 
        self.manual_activities = {} 
        self.manual_desc_sessions = {}
        self.manual_start_times = {}
 
        # Default ignored apps (can be modified)
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

    def reconnect_discord(self):
        """Manually reconnect to Discord RPC if connection was lost."""
        if self.discord.connected:
            self.discord.clear()
            self.discord.close()
        
        self.discord.connected = False
        self.discord.connect()
        self._update_discord()

    def _resolve_icon_path(self, process_name, executable_path):
        if not self.icon_manager or not executable_path:
            return executable_path
            
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
        if self.current_log_id:
            self.storage.stop_logging(self.current_log_id)
        
        for log_id in self.manual_sessions.values():
            self.storage.stop_logging(log_id)
        self.manual_sessions.clear()
        self.manual_start_times.clear()
        self.manual_activities.clear()
        
        if self.discord.connected:
            self.discord.clear()
            self.discord.close()

    def start_manual_session(self, activity):
        """Starts a concurrent manual timer for an activity."""
        if activity.name in self.ignored_apps:
            self.ignored_apps.remove(activity.name)

        if activity.id in self.manual_sessions:
            return 
            
        if self.current_activity and self.current_activity.id == activity.id:
            self.stop_auto_tracking()
            
        log_id = self.storage.start_logging(activity.id)
        self.manual_sessions[activity.id] = log_id
        self.manual_start_times[activity.id] = time.time()
        self.manual_activities[activity.id] = activity
        
        desc = activity.description if activity.description else "Manual Session"
        desc_id = self.storage.start_description_log(activity.id, desc)
        self.manual_desc_sessions[activity.id] = desc_id
        
    def stop_manual_session(self, activity):
        """Stops a manual timer."""
        if activity.id in self.manual_sessions:
            log_id = self.manual_sessions.pop(activity.id)
            self.storage.stop_logging(log_id)
            
            if activity.id in self.manual_start_times:
                self.manual_start_times.pop(activity.id)
            
            if activity.id in self.manual_activities:
                self.manual_activities.pop(activity.id)
            
            if activity.id in self.manual_desc_sessions:
                desc_id = self.manual_desc_sessions.pop(activity.id)
                self.storage.stop_description_log(desc_id)

    def is_manual_running(self, activity_id):
        return activity_id in self.manual_sessions
        
    def update_manual_description(self, activity_id, new_description):
        """Switches description log for a running manual session."""
        if activity_id in self.manual_sessions:
            if activity_id in self.manual_desc_sessions:
                old_desc_id = self.manual_desc_sessions.pop(activity_id)
                self.storage.stop_description_log(old_desc_id)
            
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
        
        if self.discord.connected:
            self.discord.clear()

    def set_discord_pin(self, activity):
        """Manually pins an activity for Discord status."""
        
        self.discord_pinned_activity = activity
        print(f"DEBUG: Pinning Activity: {activity.name if activity else 'None'}")
        self._update_discord()
        

        
    def _update_discord(self):
        if not self.discord.connected:
            return

        is_enabled = self.storage.get_setting("discord_enabled", "True") == "True"
        if not is_enabled:
            self.discord.clear()
            self.discord_last_target_name = None 
            return


        target = self.discord_pinned_activity
        
        is_pinned_valid = False
        if target:
            if self.current_activity and self.current_activity.id == target.id:
                 is_pinned_valid = True
            elif target.id in self.manual_sessions:
                 is_pinned_valid = True
            elif target.type == 'app' and target.name in self.open_sessions:
                 is_pinned_valid = True
            
            if not is_pinned_valid:
                target = None 
        
        

        if not target:
            if self.current_activity:
                 target = self.current_activity
            elif self.open_sessions:
                 try:
                     best_sess = max(self.open_sessions.values(), key=lambda x: x.get('last_focus_time', 0))
                     target = best_sess['activity']
                 except Exception as e:
                     print(f"Error in background fallback: {e}")
            elif self.manual_sessions:
                 first_mid = next(iter(self.manual_sessions))
                 target = self.storage.get_activity_by_id(first_mid)

        if target:
            fresh_act = self.storage.get_activity_by_id(target.id)
            if fresh_act:
                target.discord_visible = fresh_act.discord_visible
            
            if not target.discord_visible:
                self.discord.update(
                    details="Idling",
                    state="Waiting for activity...",
                    start=self.session_start_time
                )
                self.discord_last_target_name = "Idling"
                return
                
            state = target.description
            
            if target.type == 'app':
                if self.current_activity and self.current_activity.id == target.id and self.last_window_title:
                     state = self.last_window_title
                else:
                     state = "Active"
            
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
            self.discord.update(
                details="Idling",
                state="Waiting for activity...",
                start=self.session_start_time
            )
            self.discord_last_target_name = "Idling"

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
                self._update_discord()
            except Exception as e:
                print(f"Error in tracker loop: {e}")
            time.sleep(1) 

    def _check_window(self):
        try:
            open_windows = get_open_windows() 
        except:
            open_windows = []

        active_info = get_active_window_info()
        
        if active_info:
             if "Gainhour" in active_info['title'] or "Settings Saved" == active_info['title']:
                 active_info = None
                 
        focused_name = active_info['process_name'] if active_info else None
        
        current_pnames = set()
        for win in open_windows:
            pname = win['process_name']
            if pname in self.ignored_apps or "Gainhour" in win['title'] or "Settings Saved" == win['title']:
                continue
            
            current_pnames.add(pname)
            
            if pname not in self.open_sessions:
                icon_path = self._resolve_icon_path(pname, win.get('executable_path'))

                act = self.storage.get_or_create_activity(
                    name=pname,
                    activity_type='app',
                    description=win['title'],
                    icon_path=icon_path
                )
                self.open_sessions[pname] = {
                    'activity': act,
                    'executable_path': win.get('executable_path'), 
                    'accumulated_time': 0.0,
                    'last_update': time.time(),
                    'last_focus_time': time.time(), 
                    'is_focused': False
                }
        
        for pname in list(self.open_sessions.keys()):
            if pname not in current_pnames:
                del self.open_sessions[pname]


        if self.current_activity and self.current_activity.name not in current_pnames:

             self.stop_auto_tracking()


        now = time.time()
        for pname, sess in self.open_sessions.items():
            if sess['is_focused']:
                dt = now - sess['last_update']
                sess['accumulated_time'] += dt
            
            is_detected_focused = (pname == focused_name)
            sess['is_focused'] = is_detected_focused
            sess['last_update'] = now
            
            if is_detected_focused:
                 sess['last_focus_time'] = now

            if is_detected_focused and active_info:
                 sess['activity'].description = active_info['title']
                 
                 act = sess['activity']
                 if (not act.icon_path or not act.icon_path.endswith('.png')) and sess.get('executable_path'):
                      new_icon = self._resolve_icon_path(pname, sess['executable_path'])
                      if new_icon and new_icon.endswith('.png') and new_icon != act.icon_path:
                           print(f"Auto-fetched missing icon for {pname}")
                           act.icon_path = new_icon
                           self.storage.get_session().commit()
                           self.storage.update_activity(act.id, icon_path=new_icon)
                           
            else:
                 pass
                 pass

        if not active_info: return
        title = active_info['title']
        if "Gainhour" in title or title == "Add IRL Activity" or title == "Edit Activity" or title == "Add Description" or title == "Select Icon" or title == "Delete Activity" or title.startswith("Activity Logs - ") or title == "Explorer": 
            return
        
        process_name = active_info['process_name']
        if process_name == "explorer.exe":
             pass 

        if process_name in self.ignored_apps or process_name.lower() in [i.lower() for i in self.ignored_apps]:
             if self.current_activity and self.current_activity.name == process_name:
                 self.stop_auto_tracking()
             return
        activity = self.storage.get_or_create_activity(
            name=process_name, 
            activity_type='app',
            description=active_info['title'],
            icon_path=self._resolve_icon_path(process_name, active_info.get('executable_path'))
        )
        
        if activity.id in self.manual_sessions:
            if self.current_log_id:
                self.stop_auto_tracking()
            return

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
             
             self.current_desc_log_id = self.storage.start_description_log(activity.id, active_info['title'])
             self.last_window_title = active_info['title']
             
        else:
            if time.time() - self.last_heartbeat > 30:
                if self.current_log_id:
                    self.storage.update_log_heartbeat(self.current_log_id)
                if self.current_desc_log_id:
                    self.storage.update_desc_heartbeat(self.current_desc_log_id)
                
                for mid in list(self.manual_sessions.values()):
                     self.storage.update_log_heartbeat(mid)
                for did in list(self.manual_desc_sessions.values()):
                     self.storage.update_desc_heartbeat(did)
                     
                self.last_heartbeat = time.time()

            if self.last_window_title != active_info['title']:
                  self.last_window_title = active_info['title']
                  
                  if self.current_desc_log_id:
                      self.storage.stop_description_log(self.current_desc_log_id)
                  
                  self.current_desc_log_id = self.storage.start_description_log(self.current_activity.id, active_info['title'])
                  
                  if self.current_activity.type != 'app':
                      self.current_activity.description = active_info['title']


