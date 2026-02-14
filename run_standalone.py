"""
ChitChat standalone window: runs the server in a background thread and
opens the app in a native window (no browser).
"""
import socket
import sys
import threading
import time

# Setup logging before any other app imports
from app.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger()

HOST = "127.0.0.1"
PORT_START = 5000
PORT_RANGE = 20  # try 5000..5019


def find_available_port(host, start, count=PORT_RANGE):
    """Return the first port in [start, start+count) that is free to bind."""
    for port in range(start, start + count):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return port
        except OSError:
            continue
    return start  # fallback; will likely fail with clear error


PORT = find_available_port(HOST, PORT_START)
URL = f"http://{HOST}:{PORT}"


def run_server(app):
    app.socketio.run(app, host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    try:
        import webview
    except ImportError:
        print("Run: pip install pywebview")
        sys.exit(1)

    try:
        logger.info("No Homers Club standalone starting")
        from app import create_app

        app = create_app()
        server_thread = threading.Thread(target=run_server, args=(app,), daemon=True)
        server_thread.start()

        # Wait for server to accept connections
        for _ in range(25):
            time.sleep(0.2)
            try:
                import urllib.request
                urllib.request.urlopen(URL, timeout=1)
                break
            except Exception:
                pass
        else:
            logger.warning("Server may not be ready yet; opening window anyway")

        if PORT != PORT_START:
            logger.info("Port %s in use; using %s", PORT_START, PORT)
        logger.info("No Homers Club ready — opening window at %s", URL)
        webview.create_window("No Homers Club", URL, width=900, height=700, resizable=True)
        webview.start()
    except Exception:
        logger.exception("No Homers Club standalone failed")
        sys.exit(1)
