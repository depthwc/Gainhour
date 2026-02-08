import sys
import os

# Ensure the project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.ui.app import App

def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
