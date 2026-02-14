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
import ctypes
from ctypes import windll, c_int, byref

# DWM constants
DWMWA_CLOAKED = 13

def is_cloaked(hwnd):
    """Check if window is cloaked (Windows 8+)"""
    cloaked = c_int(0)
    try:
        windll.dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, byref(cloaked), ctypes.sizeof(cloaked))
        return cloaked.value != 0
    except:
        return False

def get_open_windows():
    """
    Returns a list of dictionaries with window info for all visible windows.
    Filters out cloaked windows and tool windows.
    """
    windows = []
    
    def enum_window_callback(hwnd, _):
        # Basic visibility check
        if not win32gui.IsWindowVisible(hwnd):
            return

        # Title check
        window_title = win32gui.GetWindowText(hwnd)
        if not window_title or not window_title.strip():
            return
            
        # Cloaked check
        if is_cloaked(hwnd):
            # print(f"DEBUG: Rejected Cloaked: {window_title}")
            # return
            pass

        # Tool window check (avoids background processes/helpers)
        # GWL_EXSTYLE = -20
        # WS_EX_TOOLWINDOW = 0x00000080
        # WS_EX_APPWINDOW = 0x00040000
        try:
            ex_style = win32gui.GetWindowLong(hwnd, -20)
            if (ex_style & 0x00000080) and not (ex_style & 0x00040000):
                # print(f"DEBUG: Rejected ToolWindow: {window_title}")
                # return
                pass
        except:
             pass

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()
            try:
                executable_path = process.exe()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                executable_path = None
            
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
