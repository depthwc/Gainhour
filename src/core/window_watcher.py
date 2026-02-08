import pywintypes
import win32gui
import win32process
import psutil
import os

def get_active_window_info():
    """
    Returns a dictionary with window title and process name.
    """
    try:
        window_handle = win32gui.GetForegroundWindow()
        pid = win32process.GetWindowThreadProcessId(window_handle)[1]
        process = psutil.Process(pid)
        process_name = process.name()
        window_title = win32gui.GetWindowText(window_handle)
        
        # Filter out some common system/empty windows if needed
        if not window_title.strip():
            window_title = process_name

        try:
            executable_path = process.exe()
        except (psutil.AccessDenied, psutil.ZombieProcess):
            executable_path = None

        return {
            "title": window_title,
            "process_name": process_name,
            "executable_path": executable_path
        }
    except Exception as e:
        # Fallback or error handling
        return None
def get_open_windows():
    """
    Returns a list of dictionaries with window info for all visible windows.
    """
    windows = []
    
    def enum_window_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                process_name = process.name()
                window_title = win32gui.GetWindowText(hwnd)
                try:
                    executable_path = process.exe()
                except (psutil.AccessDenied, psutil.ZombieProcess):
                    executable_path = None
                
                # Filter out some common system stuff or empty titles just in case
                if not window_title.strip():
                    return

                windows.append({
                    "hwnd": hwnd,
                    "title": window_title,
                    "process_name": process_name,
                    "executable_path": executable_path
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            except Exception:
                pass

    win32gui.EnumWindows(enum_window_callback, None)
    return windows
