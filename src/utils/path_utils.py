import os
import sys

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, works for both development 
    and PyInstaller built executable.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)

def get_db_path(db_name="gainhour.db"):
    """
    Get the absolute path for the database file. 
    It should sit next to the executable when frozen.
    """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # project root
    return os.path.join(base_path, db_name)
