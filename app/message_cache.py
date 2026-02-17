"""In-memory cache of last N messages per room. Speeds up join/reconnect."""
from collections import deque
from threading import Lock

from app.models import Message

# Config
CACHE_SIZE = 100  # Messages per room
MAX_CONTENT_LEN = 50_000  # Reject oversized payloads (Matrix-inspired validation)

_cache: dict[int, deque[dict]] = {}
_lock = Lock()


def _get_cache_key(room_id: int) -> deque:
    if room_id not in _cache:
        _cache[room_id] = deque(maxlen=CACHE_SIZE)
    return _cache[room_id]


def cache_append(room_id: int, msg_dict: dict) -> None:
    """Append message to room cache."""
    with _lock:
        q = _get_cache_key(room_id)
        q.append(msg_dict)


def cache_update(room_id: int, msg_id: int, updates: dict) -> None:
    """Update cached message (e.g. on edit)."""
    with _lock:
        q = _cache.get(room_id)
        if not q:
            return
        for i, m in enumerate(q):
            if m.get("id") == msg_id:
                m.update(updates)
                break


def cache_remove(room_id: int, msg_id: int) -> None:
    """Remove message from cache (e.g. on delete)."""
    with _lock:
        q = _cache.get(room_id)
        if not q:
            return
        new_q = deque([m for m in q if m.get("id") != msg_id], maxlen=CACHE_SIZE)
        _cache[room_id] = new_q


def cache_clear_room(room_id: int) -> None:
    """Clear cache for room (e.g. on wipe)."""
    with _lock:
        if room_id in _cache:
            _cache[room_id].clear()


def get_cached_messages(room_id: int, limit: int = 50) -> list[dict] | None:
    """
    Return up to `limit` most recent messages from cache, or None if cache empty/incomplete.
    Result is in ascending order (oldest first) for display.
    """
    with _lock:
        q = _cache.get(room_id)
        if not q or len(q) == 0:
            return None
        # deque is newest at right; [-limit:] gives last N in ascending order (oldest first)
        return list(q)[-limit:]


def validate_message_payload(content: str | None, max_len: int = MAX_CONTENT_LEN) -> bool:
    """Matrix-inspired: reject oversized or invalid payloads."""
    if content is None:
        return False
    if len(content) > max_len:
        return False
    return True
