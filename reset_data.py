import os
import shutil
import sys

def reset_data():
    print("Resetting Gainhour Data...")
    
    # 1. Delete Database
    db_path = "gainhour.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Deleted {db_path}")
        except Exception as e:
            print(f"Error deleting {db_path}: {e}")
    else:
        print(f"{db_path} not found.")
        
    # 2. Delete Icons
    # Assuming standard path relative to this script or project root
    # This script will be run from project root ideally
    icons_dir = os.path.join("assets", "icons")
    if os.path.exists(icons_dir):
        try:
            shutil.rmtree(icons_dir)
            os.makedirs(icons_dir) # Recreate empty dir
            print(f"Cleared {icons_dir}")
        except Exception as e:
            print(f"Error clearing {icons_dir}: {e}")
    else:
        print(f"{icons_dir} not found. Creating it.")
        os.makedirs(icons_dir, exist_ok=True)
        
    print("Reset Complete. Please restart the application.")

if __name__ == "__main__":
    reset_data()
