"""In-memory audit ring buffer for the guardrails demo.

Stores the most recent N pipeline decisions for surfacing in the UI.
Process-local; cleared on restart.
"""

from __future__ import annotations

import threading
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

from app.config import settings


_lock = threading.Lock()
_buffer: Deque[Dict[str, Any]] = deque(maxlen=settings.demo_audit_max)


def record(entry: Dict[str, Any]) -> str:
    """Append an audit entry. Returns the assigned audit_id."""
    audit_id = entry.get("audit_id") or str(uuid.uuid4())
    timestamp = entry.get("timestamp") or datetime.now(timezone.utc).isoformat()
    full = {**entry, "audit_id": audit_id, "timestamp": timestamp}
    with _lock:
        _buffer.append(full)
    return audit_id


def list_entries(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return entries newest-first, optionally capped at *limit*."""
    with _lock:
        items = list(_buffer)
    items.reverse()
    if limit is not None:
        items = items[:limit]
    return items


def clear() -> int:
    """Clear all entries. Returns the number removed."""
    with _lock:
        n = len(_buffer)
        _buffer.clear()
    return n


def size() -> int:
    with _lock:
        return len(_buffer)
