"""
Professional logging configuration for ChitChat.
- logs/app.log: General activity (server start, connections).
- logs/errors.log: Full stack traces and local variable context for every exception.
"""
import logging
import sys
import traceback
from pathlib import Path

# Base directory: project root (parent of app/)
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

# Max length for repr() of a single local value (avoid huge dumps)
_MAX_LOCAL_REPR = 500


def _format_frame_locals(frame):
    """Format f_locals for one frame, truncating long values."""
    lines = []
    for key, value in sorted(frame.items(), key=lambda x: x[0]):
        if key.startswith("__"):
            continue
        try:
            repr_val = repr(value)
        except Exception:
            repr_val = "<repr failed>"
        if len(repr_val) > _MAX_LOCAL_REPR:
            repr_val = repr_val[:_MAX_LOCAL_REPR] + "..."
        lines.append(f"    {key} = {repr_val}")
    return "\n".join(lines) if lines else "    (none)"


class ErrorsWithContextFormatter(logging.Formatter):
    """
    Formatter that appends full traceback and local variable context
    for each frame when exc_info is set (Recursive Learning Loop).
    """

    def formatException(self, exc_info):
        """Override to append frame locals after the standard traceback."""
        if exc_info is None:
            return ""
        lines = []
        # Standard traceback
        lines.append("".join(traceback.format_exception(*exc_info)))
        # Local variables for each frame
        tb = exc_info[2]
        if tb is not None:
            lines.append("\n--- Local variables by frame ---")
            frame = tb.tb_frame
            depth = 0
            while frame is not None and depth < 50:  # cap depth
                lines.append(f"\n  Frame {depth} ({frame.f_code.co_filename}:{frame.f_lineno} in {frame.f_code.co_name}):")
                lines.append(_format_frame_locals(frame))
                frame = frame.f_back
                depth += 1
        return "\n".join(lines)


def setup_logging() -> None:
    """Create logs directory and configure file handlers. Minimal console noise."""
    LOGS_DIR.mkdir(exist_ok=True)

    app_log_path = LOGS_DIR / "app.log"
    errors_log_path = LOGS_DIR / "errors.log"

    general_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    error_fmt = ErrorsWithContextFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app_handler = logging.FileHandler(app_log_path, encoding="utf-8")
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(general_fmt)

    errors_handler = logging.FileHandler(errors_log_path, encoding="utf-8")
    errors_handler.setLevel(logging.ERROR)
    errors_handler.setFormatter(error_fmt)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    if not root.handlers:
        root.addHandler(app_handler)
        root.addHandler(errors_handler)

    app_logger = logging.getLogger("chitchat")
    app_logger.setLevel(logging.DEBUG)


def get_logger(name: str = "chitchat") -> logging.Logger:
    """Return a logger for the given name (default: chitchat)."""
    return logging.getLogger(name)
