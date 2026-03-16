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

    return display_name.capitalize()
