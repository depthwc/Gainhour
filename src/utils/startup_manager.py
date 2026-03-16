import os
import sys
import winreg

def is_frozen():
    """Check if the application is running as a compiled PyInstaller executable."""
    return getattr(sys, 'frozen', False)

def get_executable_path():
    """Get the path to the current executable."""
    if is_frozen():
        return sys.executable
    else:
        main_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'main.py'))
        return f'"{sys.executable}" "{main_script}"'

def set_run_on_startup(enable: bool, app_name: str = "Gainhour"):
    """
    Enable or disable running the application on Windows startup.
    Uses CurrentVersion\\Run registry key.
    """
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        if enable:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

            exe_path = get_executable_path()
            if not exe_path.startswith('"'):
                exe_path = f'"{exe_path}"'
                
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        else:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
            finally:
                winreg.CloseKey(key)
                
        return True
    except Exception as e:
        print(f"Failed to modify startup registry: {e}")
        return False

def check_run_on_startup(app_name: str = "Gainhour") -> bool:
    """Check if the app is currently set to run on startup."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            value, _ = winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False
