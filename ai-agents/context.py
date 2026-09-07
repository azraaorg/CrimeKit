import threading
from typing import Any, Dict, List


class SharedContext:
    """Simple threadsafe shared in-memory context/memory for agents.

    Intended for short-lived workflows and unit tests. Production deployments
    can replace this with a persistent store (Redis, DB) by implementing
    the same API.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._memory: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._memory.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._memory[key] = value

    def append(self, key: str, value: Any) -> None:
        with self._lock:
            lst = self._memory.get(key)
            if lst is None:
                lst = []
                self._memory[key] = lst
            lst.append(value)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            # return a shallow copy for inspection
            return dict(self._memory)
