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

# Storage path for cookies/local storage (persists between sessions)
if sys.platform == "darwin":
    _STORAGE = os.path.expanduser("~/Library/Application Support/NoHomersClub")
elif sys.platform == "win32":
    _STORAGE = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NoHomersClub")
else:
    _STORAGE = os.path.expanduser("~/.config/NoHomersClub")

if __name__ == "__main__":
    webview.create_window(
        "No Homers Club",
        URL,
        width=1100,
        height=750,
        min_size=(800, 600),
        resizable=True,
    )
    # private_mode=False + storage_path so session cookie persists across app restarts
    webview.start(
        icon=_ICON if os.path.isfile(_ICON) else None,
        private_mode=False,
        storage_path=_STORAGE,
    )
