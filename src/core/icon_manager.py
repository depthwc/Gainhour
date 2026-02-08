import os
import shutil
from PIL import Image
import win32ui
import win32gui
import win32con
import win32api

class IconManager:
    def __init__(self, icons_dir="assets/icons"):
        self.icons_dir = icons_dir
        if not os.path.exists(self.icons_dir):
            os.makedirs(self.icons_dir)
    
    def get_icon_path(self, name):
        """Returns the path to the icon for the given activity name."""
        # Sanitize name for filename
        safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filename = f"{safe_name}.png"
        path = os.path.join(self.icons_dir, filename)
        if os.path.exists(path):
            return path
        return None

    def extract_icon(self, exe_path, name):
        """Extracts the icon from the exe using ExtractIconEx."""
        if not exe_path or not os.path.exists(exe_path):
            return None
        
        try:
            # Load the icon from the executable
            large, small = win32gui.ExtractIconEx(exe_path, 0)
            
            hIcon = None
            if large:
                hIcon = large[0]
            elif small:
                hIcon = small[0]
            else:
                return None
            
            # Create a PyCBitmap from the icon
            ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
            ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)

            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
            hdc = hdc.CreateCompatibleDC()
            
            hdc.SelectObject(hbmp)
            hdc.DrawIcon((0, 0), hIcon)
            
            # Convert to PIL Image
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)

            # Save
            safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            save_path = os.path.join(self.icons_dir, f"{safe_name}.png")
            img.save(save_path)
            
            # Cleanup
            win32gui.DestroyIcon(hIcon)
            
            return save_path

        except Exception as e:
            print(f"Error extracting icon for {name}: {e}")
            return None

    def save_user_icon(self, source_path, name):
        """Saves a user-uploaded icon."""
        try:
            img = Image.open(source_path)
            safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            save_path = os.path.join(self.icons_dir, f"{safe_name}.png")
            img.save(save_path)
            return save_path
        except Exception as e:
            print(f"Error saving user icon: {e}")
            return None
