import json
import os
import glob

# Load themes dynamically from the 'themes' directory
THEMES = {}

from src.utils.path_utils import get_resource_path
themes_dir = get_resource_path("themes")

# Fallback basic theme in case themes folder is empty or not found
FALLBACK_THEME = {
    "theme_name": "Fallback Night",
    "bg_main": "#1e1e1e",
    "text_main": "#e0e0e0",
    "text_secondary": "#aaaaaa",
    "bg_nav": "#252526",
    "border": "#3e3e3e",
    "nav_hover": "#37373d",
    "nav_text": "#a0a0a0",
    "primary": "#5865F2",
    "primary_hover": "#4752C4",
    "card_bg": "#252526",
    "stop_btn": "#ff9900",
    "stop_btn_hover": "#e68a00",
    "stop_btn_text": "black",
    "input_bg": "#3c3c3c",
    "input_border": "#3c3c3c",
    "input_focus": "#5865F2",
    "danger_text": "#ff4444"
}

def load_themes():
    global THEMES
    THEMES.clear()

    if os.path.exists(themes_dir):
        for filepath in glob.glob(os.path.join(themes_dir, "*.json")):
            try:
                # We do not want 'theme.json' itself to appear as a selectable button
                if os.path.basename(filepath) == "theme.json":
                    continue
                    
                with open(filepath, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    # Use the filename (without .json) as the internal theme key
                    theme_key = os.path.basename(filepath)[:-5]
                    THEMES[theme_key] = theme_data
            except Exception as e:
                print(f"Failed to load theme {filepath}: {e}")

    # Fallback if no valid themes were found
    if not THEMES:
        THEMES["night"] = FALLBACK_THEME

# Initial load
load_themes()

def generate_darker_accent_css(t):
    base_hex = t.get('primary', FALLBACK_THEME['primary'])
    # If the theme already provided a hover color, we don't need to generate a CSS fallback
    if 'primary_hover' in t:
        return ""
        
    try:
        # Simple darken by reducing rgb values by ~20%
        base_hex = base_hex.lstrip('#')
        r, g, b = tuple(int(base_hex[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, int(r * 0.8))
        g = max(0, int(g * 0.8))
        b = max(0, int(b * 0.8))
        darker_hex = f"#{r:02x}{g:02x}{b:02x}"
        t['primary_hover'] = darker_hex # Store it so the rest of the stylesheet can use it
    except:
        pass
    return ""

def get_stylesheet(theme_name="theme"):
    # Always try to read from the master `theme.json` first, 
    # if it doesn't exist, fallback to whatever is in THEMES or FALLBACK_THEME
    t = FALLBACK_THEME
    
    main_theme_path = os.path.join(themes_dir, "theme.json")
    if os.path.exists(main_theme_path):
        try:
            with open(main_theme_path, 'r', encoding='utf-8') as f:
                t = json.load(f)
        except:
            t = THEMES.get(theme_name, list(THEMES.values())[0] if THEMES else FALLBACK_THEME)
    else:
        t = THEMES.get(theme_name, list(THEMES.values())[0] if THEMES else FALLBACK_THEME)
    
    return f"""
    /* General */
    QMainWindow, QWidget {{
        background-color: {t.get('bg_main', FALLBACK_THEME['bg_main'])};
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
        font-family: "Segoe UI", "Roboto", sans-serif;
    }}

    /* ScrollBars */
    QScrollBar:vertical {{
        border: none;
        background: {t.get('bg_main', FALLBACK_THEME['bg_main'])};
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {t.get('border', FALLBACK_THEME['border'])};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    /* Cards & Frames */
    QFrame {{
        border: none;
    }}

    /* Navigation */
    QWidget#NavFrame {{
        background-color: {t.get('bg_nav', FALLBACK_THEME['bg_nav'])};
        border-right: 1px solid {t.get('border', FALLBACK_THEME['border'])};
    }}

    QPushButton#NavButton {{
        text-align: left;
        padding-left: 20px;
        border: none;
        background-color: transparent;
        color: {t.get('nav_text', FALLBACK_THEME['nav_text'])};
        font-size: 14px;
        height: 45px;
    }}
    QPushButton#NavButton:hover {{
        background-color: {t.get('nav_hover', FALLBACK_THEME['nav_hover'])};
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
    }}
    QPushButton#NavButton:checked {{
        background-color: {t.get('nav_hover', FALLBACK_THEME['nav_hover'])};
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
        border-left: 3px solid {t.get('primary', FALLBACK_THEME['primary'])};
    }}

    /* Activity Cards */
    QFrame#ActivityCard, QFrame#SettingsCard {{
        background-color: {t.get('card_bg', FALLBACK_THEME['card_bg'])};
        border-radius: 8px;
        border: 1px solid {t.get('border', FALLBACK_THEME['border'])};
    }}
    QFrame#ActivityCard:hover {{
        border: 1px solid {t.get('primary', FALLBACK_THEME['primary'])};
    }}

    /* Buttons */
    QPushButton {{
        padding: 5px 15px;
        border-radius: 4px;
        font-weight: bold;
    }}

    QPushButton#PrimaryButton {{
        background-color: {t.get('primary', FALLBACK_THEME['primary'])};
        color: white;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: {t.get('primary_hover', FALLBACK_THEME['primary_hover'])};
    }}

    QPushButton#StopButton {{
        background-color: {t.get('stop_btn', FALLBACK_THEME['stop_btn'])};
        color: {t.get('stop_btn_text', FALLBACK_THEME['stop_btn_text'])};
        font-weight: bold;
    }}
    QPushButton#StopButton:hover {{
        background-color: {t.get('stop_btn_hover', FALLBACK_THEME['stop_btn_hover'])};
    }}

    /* Specific Active Session Card Style */
    QFrame#ActiveSessionCard {{
        background-color: {t.get('bg_main', FALLBACK_THEME['bg_main'])};
        border: 1px solid {t.get('primary', FALLBACK_THEME['primary'])};
        border-radius: 8px;
    }}

    QPushButton#SecondaryButton {{
        background-color: {t.get('border', FALLBACK_THEME['border'])};
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
    }}
    QPushButton#SecondaryButton:hover {{
        background-color: {t.get('nav_hover', FALLBACK_THEME['nav_hover'])};
    }}

    /* Inputs */
    QLineEdit, QComboBox {{
        background-color: {t.get('input_bg', FALLBACK_THEME['input_bg'])};
        border: 1px solid {t.get('input_border', FALLBACK_THEME['input_border'])};
        border-radius: 4px;
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
        padding: 5px;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {t.get('input_focus', FALLBACK_THEME['input_focus'])};
    }}

    /* QScrollArea */
    QScrollArea {{
        border: 1px solid {t.get('border', FALLBACK_THEME['border'])};
        border-radius: 4px;
        background-color: {t.get('input_bg', FALLBACK_THEME['input_bg'])};
    }}
    
    QLabel {{
        background: transparent;
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
    }}
    
    QLabel#SectionHeader {{
        color: {t.get('text_secondary', FALLBACK_THEME['text_secondary'])};
    }}
    QLabel#HelperLabel {{
        color: {t.get('text_secondary', FALLBACK_THEME['text_secondary'])};
    }}
    QLabel#DangerHeader {{
        color: {t.get('danger_text', FALLBACK_THEME['danger_text'])};
    }}
    QLabel#WarningLabel {{
        color: {t.get('danger_text', FALLBACK_THEME['danger_text'])};
        font-style: italic;
    }}
    
    QLabel#AccentText {{
        color: {t.get('primary', FALLBACK_THEME['primary'])};
    }}
    
    QFrame#DangerBox {{
        background-color: {t.get('card_bg', FALLBACK_THEME['card_bg'])};
        border: 1px solid {t.get('danger_text', FALLBACK_THEME['danger_text'])};
        border-radius: 8px;
    }}
    
    QPushButton#AccentButton {{
        background-color: transparent;
        color: {t.get('primary', FALLBACK_THEME['primary'])};
        border: 1px dashed {t.get('primary', FALLBACK_THEME['primary'])};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 10px;
        text-align: left;
    }}
    QPushButton#AccentButton:hover {{
        background-color: {t.get('primary_hover', FALLBACK_THEME['primary_hover'])};
        color: white;
    }}
    
    QLabel#AppIcon {{
        background-color: {t.get('border', FALLBACK_THEME['border'])};
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
        border-radius: 4px;
        qproperty-alignment: AlignCenter;
    }}
    
    QLabel#IrlTag {{
        background-color: {t.get('input_bg', FALLBACK_THEME['input_bg'])};
        color: {t.get('text_secondary', FALLBACK_THEME['text_secondary'])};
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid {t.get('border', FALLBACK_THEME['border'])};
    }}
    
    QPushButton#SecondaryCardButton {{
        background-color: transparent;
        color: {t.get('text_secondary', FALLBACK_THEME['text_secondary'])};
        border: 1px solid {t.get('border', FALLBACK_THEME['border'])};
        border-radius: 4px;
        font-weight: bold;
        font-size: 10px;
    }}
    QPushButton#SecondaryCardButton:hover {{
        background-color: {t.get('nav_hover', FALLBACK_THEME['nav_hover'])};
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
        border-color: {t.get('text_main', FALLBACK_THEME['text_main'])};
    }}
    
    QPushButton#DangerCardButton {{
        background-color: transparent;
        color: {t.get('danger_text', FALLBACK_THEME['danger_text'])};
        border: 1px solid {t.get('border', FALLBACK_THEME['border'])};
        border-radius: 4px;
        font-size: 10px;
    }}
    QPushButton#DangerCardButton:hover {{
        background-color: {t.get('danger_text', FALLBACK_THEME['danger_text'])};
        color: white;
        border-color: {t.get('danger_text', FALLBACK_THEME['danger_text'])};
    }}
    
    QPushButton#StopCardButton {{
        background-color: transparent; 
        color: {t.get('danger_text', FALLBACK_THEME['danger_text'])}; 
        border: 1px solid {t.get('danger_text', FALLBACK_THEME['danger_text'])};
        border-radius: 4px;
        font-weight: bold;
    }}
    QPushButton#StopCardButton:hover {{ 
        background-color: {t.get('danger_text', FALLBACK_THEME['danger_text'])}; 
        color: white;
    }}
    
    QPushButton#StartCardButton {{
        background-color: transparent; 
        color: #2fa51f; 
        border: 1px solid #2fa51f;
        border-radius: 4px;
        font-weight: bold;
    }}
    QPushButton#StartCardButton:hover {{ 
        background-color: #2fa51f; 
        color: white;
    }}
    
    QPushButton#CircleNavButton {{
        background-color: transparent;
        border: 1px solid {t.get('border', FALLBACK_THEME['border'])};
        border-radius: 15px;
        padding: 0px;
    }}
    QPushButton#CircleNavButton:hover {{
        background-color: {t.get('nav_hover', FALLBACK_THEME['nav_hover'])};
        border-color: {t.get('text_main', FALLBACK_THEME['text_main'])};
    }}
    
    /* Generate Darker Accent */
    
    # Simple darken calculation using f-strings for Python eval, but in styles.py we can just do:
    # We will use the primary_hover color from the JSON if available, otherwise just use primary for both for now. 
    # Or calculate it in Python before inserting:
    {generate_darker_accent_css(t)}
    
    QPushButton#DiscordButton {{
        background-color: {t.get('primary', FALLBACK_THEME['primary'])};
        color: white;
        padding: 6px 12px;
        border-radius: 4px;
        font-size: 11px;
    }}
    QPushButton#DiscordButton:hover {{
        background-color: {t.get('primary_hover', t.get('primary', FALLBACK_THEME['primary']))};
    }}
    
    QPushButton#DangerButton {{
        background-color: transparent;
        color: {t.get('danger_text', FALLBACK_THEME['danger_text'])};
        border: 1px solid {t.get('danger_text', FALLBACK_THEME['danger_text'])};
        border-radius: 4px;
        padding: 8px;
    }}
    QPushButton#DangerButton:hover {{
        background-color: {t.get('danger_text', FALLBACK_THEME['danger_text'])};
        color: white;
    }}
    QPushButton#DangerButton:disabled {{
        border: 1px solid {t.get('border', FALLBACK_THEME['border'])};
        color: {t.get('text_secondary', FALLBACK_THEME['text_secondary'])};
    }}
    
    QCheckBox {{
        font-size: 14px;
        color: {t.get('text_main', FALLBACK_THEME['text_main'])};
    }}
    """
