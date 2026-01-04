from __future__ import annotations

import functools
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional

MAX_EVENTS = 300
_events: Deque[Dict[str, Any]] = deque(maxlen=MAX_EVENTS)


def log_event(event_name: str, **fields: Any) -> None:
    """
    Append an event to the in-memory event stream.

    Notes:
      - Reserved keys: "event", "ts" are owned by the event stream.
      - If callers pass these keys, we drop them to avoid collisions.
    """
    # prevent callers overwriting our reserved fields
    fields.pop("event", None)
    fields.pop("ts", None)

    _events.appendleft(
        {
            "ts": time.time(),
            "event": event_name,
            **fields,
        }
    )


def get_events(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Return most recent events (newest first).
    """
    limit = max(1, min(int(limit), MAX_EVENTS))
    return list(_events)[:limit]


def clear_events() -> None:
    """
    Clear in-memory event stream (handy for dev/tests).
    """
    _events.clear()


def log_request(
    event_name: str,
    include_fields: Optional[Iterable[str]] = None,
    exclude_fields: Optional[Iterable[str]] = None,
) -> Callable:
    """
    Decorator to auto-log a FastAPI route after it returns successfully.

    Args:
      event_name: name written to event stream
      include_fields: if provided, only these keys from the returned dict are logged
      exclude_fields: keys to remove from logged payload (applied after include_fields)

    Usage:
        @router.get("/sentiment")
        @log_request("ai.sentiment", include_fields=["market_mood","confidence"])
        def handler(): ...
    """
    include_set = set(include_fields) if include_fields else None
    exclude_set = set(exclude_fields) if exclude_fields else set()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            if isinstance(result, dict):
                data = dict(result)

                # avoid collision with reserved keys / stream fields
                data.pop("event", None)
                data.pop("ts", None)

                if include_set is not None:
                    data = {k: data[k] for k in include_set if k in data}

                for k in exclude_set:
                    data.pop(k, None)

                log_event(event_name, **data)
            else:
                log_event(event_name)

            return result

        return wrapper

    return decorator
