"""
ChitChat standalone window: opens the Koyeb-hosted app in a native window (no browser).
"""
import os
import sys

try:
    import webview
except ImportError:
    print("Install pywebview: pip install pywebview")
    sys.exit(1)

URL = "https://boiling-stacy-joemachen-05fc3544.koyeb.app"

# Icon path: PyInstaller bundle root or script directory
_ICON = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "icon.ico")

if __name__ == "__main__":
    webview.create_window(
        "No Homers Club",
        URL,
        width=1100,
        height=750,
        min_size=(800, 600),
        resizable=True,
    )
    # Icon: GTK/QT use start(icon=); Windows uses PyInstaller --icon (taskbar)
    webview.start(icon=_ICON if os.path.isfile(_ICON) else None)
