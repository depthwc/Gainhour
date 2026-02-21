# Gainhour

Gainhour is a comprehensive Python-based desktop application designed to help you track the time you spend on various applications, programs, and real-life (IRL) activities.

## Features

- **Automatic Application Tracking:** Automatically monitors your active window and calculates the time spent on different applications running on your device.
- **Manual Activity Tracking:** Allows you to manually add and track real-life tasks (e.g., Reading, Exercising) with a start and stop timer.
- **Discord Rich Presence Integration:** Optionally broadcast what you are currently doing (whether an app or a manual session) directly to your Discord status.
- **Detailed Statistics & Charts:** View your daily and lifetime statistics. Includes visually appealing clustered column charts and lifetime stacked charts to analyze your habits.
- **Customizable Themes:** Switch between pre-built themes (Night, White, Afternoon) or customize your own advanced colors for the application interface.
- **System Tray & Startup:** Runs quietly in the background via the system tray and can be configured to launch automatically on system startup.
- **Privacy-First:** All tracked data is stored locally in an SQLite database (`gainhour.db`) on your machine.

## Technologies Used

- **Python 3**
- **PySide6** (Qt for Python) for the modern graphical user interface.
- **Matplotlib** for rendering statistic charts.
- **SQLAlchemy & SQLite** for robust local data storage.
- **psutil & pywin32** for Windows process and active window tracking.
- **pypresence** for Discord Rich Presence integration.
- **Pillow** for dynamic application icon extraction.

## Installation & Setup

### Prerequisites
- Python 3.8+
- Windows OS (due to active window tracking dependencies like `pywin32`)

### Running from Source
1. Clone the repository or download the source code.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

### Building the Executable
You can package the application into a standalone Windows executable using PyInstaller:
```bash
pyinstaller Gainhour.spec
```
The built executable will be located in the `dist/Gainhour` directory.

## Usage

- **Home Tab:** View your currently active auto-tracked applications and manual sessions. You can start/stop manual sessions and toggle Discord visibility per app directly from here.
- **Activities Tab:** Browse the list of all tracked applications and IRL activities, view total time, and manually adjust their visibility.
- **Statistics Tab:** Visualize your tracked time through daily breakdowns and lifetime charts. Create custom groupings to compare specific apps.
- **Settings Tab:** Configure startup behavior, manage log history, toggle Discord integration globally, choose UI themes, and manage or reset your underlying database.