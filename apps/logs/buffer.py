import time
import datetime
from collections import deque

# In-memory circular ring buffer for real-time and fallback logging
LOG_BUFFER = deque(maxlen=500)
SERVER_START_TIME = time.time()


def add_to_buffer(entry: dict):
    """
    Append log entry to memory buffer.
    Ensures that even if DB is unavailable, logs remain visible in admin dashboard.
    """
    if "id" not in entry:
        entry["id"] = f"mem-{int(time.time() * 1000)}-{len(LOG_BUFFER)}"
    if "created_at" not in entry:
        entry["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    LOG_BUFFER.appendleft(entry)


def get_buffer_logs(limit=100, level=None, search=None, status_code=None):
    results = [
        l for l in list(LOG_BUFFER)
        if not (str(l.get('path', '')).startswith('/api/logs/') and (l.get('status_code') or 200) < 400)
    ]
    
    if level and level.lower() != 'all':
        results = [l for l in results if str(l.get('level', '')).upper() == level.upper()]
        
    if status_code and status_code.lower() != 'all':
        try:
            sc = int(status_code)
            results = [l for l in results if l.get('status_code') == sc]
        except ValueError:
            pass

    if search:
        s_lower = search.lower()
        results = [
            l for l in results
            if s_lower in str(l.get('path', '')).lower()
            or s_lower in str(l.get('message', '')).lower()
            or s_lower in str(l.get('traceback', '')).lower()
            or s_lower in str(l.get('ip_address', '')).lower()
            or s_lower in str(l.get('method', '')).lower()
        ]

    return results[:limit]


def clear_buffer():
    LOG_BUFFER.clear()
