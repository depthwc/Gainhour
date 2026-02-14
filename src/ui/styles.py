# Gainhour Unified Stylesheet

STYLESHEET = """
/* General */
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", "Roboto", sans-serif;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #3e3e3e;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Cards & Frames */
QFrame {
    border: none;
}

/* Navigation */
QWidget#NavFrame {
    background-color: #252526;
    border-right: 1px solid #3e3e3e;
}

QPushButton#NavButton {
    text-align: left;
    padding-left: 20px;
    border: none;
    background-color: transparent;
    color: #a0a0a0;
    font-size: 14px;
    height: 45px;
}
QPushButton#NavButton:hover {
    background-color: #37373d;
    color: white;
}
QPushButton#NavButton:checked {
    background-color: #37373d;
    color: white;
    border-left: 3px solid #007acc; /* VS Code Blue */
}

/* Activity Cards */
QFrame#ActivityCard {
    background-color: #252526;
    border-radius: 8px;
    border: 1px solid #3e3e3e;
}
QFrame#ActivityCard:hover {
    border: 1px solid #007acc;
}

/* Buttons */
QPushButton {
    padding: 5px 15px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton#PrimaryButton {
    background-color: #007acc;
    color: white;
}
QPushButton#PrimaryButton:hover {
    background-color: #0062a3;
}

QPushButton#StopButton {
    background-color: #ff9900; /* Orange/Yellow */
    color: black;
    font-weight: bold;
}
QPushButton#StopButton:hover {
    background-color: #e68a00;
}

/* Specific Active Session Card Style */
QFrame#ActiveSessionCard {
    background-color: #1e1e1e; /* Dark background */
    border: 1px solid #007acc; /* Blue border */
    border-radius: 8px;
}

QPushButton#SecondaryButton {
    background-color: #3e3e3e;
    color: white;
}
QPushButton#SecondaryButton:hover {
    background-color: #4e4e4e;
}

/* Inputs */
QLineEdit, QComboBox {
    background-color: #3c3c3c;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    color: #cccccc;
    padding: 5px;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #007acc;
}
"""
