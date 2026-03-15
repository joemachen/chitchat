"""
ChitChat standalone window: opens the Koyeb-hosted app in a native window (no browser).
"""
import os
import sys
import threading
import webbrowser

try:
    import webview
except ImportError:
    print("Install pywebview: pip install pywebview")
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None

# Keep in sync with app/version.py; bump as part of each release.
CURRENT_VERSION = "3.5.38"

URL = "https://boiling-stacy-joemachen-05fc3544.koyeb.app"
RELEASES_URL = "https://github.com/joemachen/chitchat/releases"
RELEASES_API = "https://api.github.com/repos/joemachen/chitchat/releases/latest"

# Icon path: PyInstaller bundle root or script directory
_ICON = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "icon.ico")

# Storage path for cookies/local storage (persists between sessions)
if sys.platform == "darwin":
    _STORAGE = os.path.expanduser("~/Library/Application Support/NoHomersClub")
elif sys.platform == "win32":
    _STORAGE = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NoHomersClub")
else:
    _STORAGE = os.path.expanduser("~/.config/NoHomersClub")


def _parse_version(s):
    """Parse 'v3.5.15' or '3.5.15' into (3, 5, 15) for comparison."""
    s = str(s).lstrip("v")
    try:
        return tuple(int(x) for x in s.split(".")[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def _check_update(window):
    """Background thread: fetch latest release, inject banner if newer."""
    if not requests:
        return
    try:
        r = requests.get(RELEASES_API, timeout=5)
        r.raise_for_status()
        data = r.json()
        tag = data.get("tag_name")
        if not tag:
            return
        latest = _parse_version(tag)
        current = _parse_version(CURRENT_VERSION)
        if latest <= current:
            return
        # Wait for page to load
        threading.Event().wait(6)
        if not window or not getattr(window, "evaluate_js", None):
            return
        js = _banner_js(tag)
        for _ in range(3):
            try:
                window.evaluate_js(js)
                break
            except Exception:
                pass
            threading.Event().wait(2)
    except Exception:
        pass


def _banner_js(version):
    """JS to inject a dismissible update banner."""
    return f"""
(function() {{
  if (document.getElementById('chitchat-update-banner')) return;
  var b = document.createElement('div');
  b.id = 'chitchat-update-banner';
  b.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:#2563eb;color:#fff;padding:8px 16px;display:flex;align-items:center;justify-content:space-between;font-family:system-ui,sans-serif;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.2);';
  b.innerHTML = '<span>Update available: {version} — </span><a href="#" id="chitchat-update-link" style="color:#fff;font-weight:bold;text-decoration:underline;">Download</a><button id="chitchat-update-dismiss" style="background:transparent;border:none;color:#fff;cursor:pointer;font-size:20px;line-height:1;">×</button>';
  document.body.insertBefore(b, document.body.firstChild);
  var pt = parseInt(getComputedStyle(document.body).paddingTop) || 0;
  document.body.style.paddingTop = (pt + 40) + 'px';
  document.getElementById('chitchat-update-link').onclick = function(e) {{ e.preventDefault(); if (window.pywebview && window.pywebview.api && window.pywebview.api.open_releases) {{ window.pywebview.api.open_releases(); }} }};
  document.getElementById('chitchat-update-dismiss').onclick = function() {{ b.remove(); var pt2 = parseInt(getComputedStyle(document.body).paddingTop) || 0; document.body.style.paddingTop = Math.max(0, pt2 - 40) + 'px'; }};
}})();
"""


class _Api:
    def open_releases(self):
        webbrowser.open(RELEASES_URL)

    def open_url(self, url: str):
        """Open a URL in the system default browser."""
        if url and url.startswith(("http://", "https://")):
            webbrowser.open(url)


if __name__ == "__main__":
    window = webview.create_window(
        f"No Homers Club v{CURRENT_VERSION}",
        URL,
        width=1100,
        height=750,
        min_size=(800, 600),
        resizable=True,
        js_api=_Api(),
    )
    t = threading.Thread(target=_check_update, args=(window,), daemon=True)
    t.start()
    webview.start(
        icon=_ICON if os.path.isfile(_ICON) else None,
        private_mode=False,
        storage_path=_STORAGE,
    )
