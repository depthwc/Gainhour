import sys
import os

    # Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.ui.main_window import MainWindow
from src.database.storage import init_db, StorageManager

def main():
    app = QApplication(sys.argv)
    
    from src.utils.path_utils import get_resource_path, get_db_path
    
    # Set Global Icon
    icon_path = get_resource_path("gainhour.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Set Metadata
    app.setApplicationName("Gainhour")
    app.setOrganizationName("Gainhour")     
    
    # Initialize DB & Cleanup (Crash Recovery)
    db_file = get_db_path("gainhour.db")
    init_db(db_file)
    db = StorageManager(db_file)
    db.cleanup_incomplete_logs()
    
    # Check for Daily Logs Only Setting (Cleanup on startup)
    if db.get_setting("daily_logs_only") == "True":
        db.cleanup_old_description_logs()   
    
    # Main Window (It initializes its own Tracker/Storage internally)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
