def format_app_name(name):
    """
    Formats the application name for display.
    - Removes .exe extension (case insensitive)
    - Capitalizes the first letter (Title Case equivalent for single word, or just Capitalize)
    """
    if not name:
        return ""
    
    display_name = name
    if display_name.lower().endswith('.exe'):
        display_name = display_name[:-4]
    
    # Capitalize first letter, keep rest as is (to preserve camelCase if it exists? 
    # User asked for "first letter upper", usually .capitalize() lowers the rest.
    # Let's stick to .capitalize() as it's cleaner for file names.
    return display_name.capitalize()
