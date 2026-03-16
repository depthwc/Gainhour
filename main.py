import sys
import os


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
    

    icon_path = get_resource_path("gainhour.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    

    app.setApplicationName("Gainhour")
    app.setOrganizationName("Gainhour")     
    

    db_file = get_db_path("gainhour.db")
    init_db(db_file)
    db = StorageManager(db_file)
    db.cleanup_incomplete_logs()
    

    if db.get_setting("daily_logs_only") == "True":
        db.cleanup_old_description_logs()   
    

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
