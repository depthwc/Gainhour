import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.ui.main_window import MainWindow
from src.database.storage import init_db, StorageManager

def main():
    app = QApplication(sys.argv)
    
    # Set Global Icon
    if os.path.exists("gainhour.ico"):
        app.setWindowIcon(QIcon("gainhour.ico"))
    
    # Set Metadata
    app.setApplicationName("Gainhour")
    app.setOrganizationName("Gainhour")     
    
    # Initialize DB & Cleanup (Crash Recovery)
    init_db("gainhour.db")
    db = StorageManager("gainhour.db")
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
