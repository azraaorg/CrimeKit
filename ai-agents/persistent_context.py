import os
import json
from typing import Any, Dict
from .context import SharedContext
from .. import database, models


import threading


class SQLPersistentContext:
    """Lightweight file-backed sqlite persistent context that is safe
    for concurrent thread use during tests.

    This uses the stdlib `sqlite3` module with `check_same_thread=False`
    and a threading lock to serialize writes. Values are JSON-serialized
    into a TEXT column.
    """

    def __init__(self, path: str | None = None):
        import sqlite3
        import tempfile

        self._lock = threading.Lock()
        if path:
            self._db_path = path
        else:
            fd, tmp = tempfile.mkstemp(prefix='persistent_kv_', suffix='.sqlite')
            try:
                os.close(fd)
            except Exception:
                pass
            self._db_path = tmp

        self._conn = sqlite3.connect(self._db_path, check_same_thread=False, isolation_level=None)
        # enable WAL for better concurrency
        self._conn.execute('PRAGMA journal_mode=WAL;')
        self._conn.execute('CREATE TABLE IF NOT EXISTS persistent_kv (key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

    def get(self, key: str, default: Any = None) -> Any:
        import json
        cur = self._conn.execute('SELECT value FROM persistent_kv WHERE key = ?', (key,))
        row = cur.fetchone()
        if not row:
            return default
        try:
            return json.loads(row[0])
        except Exception:
            return row[0]

    def set(self, key: str, value: Any) -> None:
        import json
        with self._lock:
            v = json.dumps(value)
            self._conn.execute('INSERT INTO persistent_kv(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP', (key, v))

    def append(self, key: str, value: Any) -> None:
        import json
        with self._lock:
            cur = self._conn.execute('SELECT value FROM persistent_kv WHERE key = ?', (key,))
            row = cur.fetchone()
            if not row:
                lst = [value]
            else:
                try:
                    lst = json.loads(row[0])
                except Exception:
                    lst = [row[0]]
                lst.append(value)
            v = json.dumps(lst)
            self._conn.execute('INSERT INTO persistent_kv(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP', (key, v))

    def snapshot(self) -> Dict[str, Any]:
        import json
        cur = self._conn.execute('SELECT key, value FROM persistent_kv')
        res = {}
        for k, v in cur.fetchall():
            try:
                res[k] = json.loads(v)
            except Exception:
                res[k] = v
        return res


try:
    import redis

    class RedisPersistentContext:
        def __init__(self, url: str | None = None):
            url = url or os.getenv('REDIS_URL')
            self._r = redis.from_url(url) if url else None

        def get(self, key: str, default: Any = None) -> Any:
            if not self._r:
                return default
            v = self._r.get(key)
            if v is None:
                return default
            return json.loads(v)

        def set(self, key: str, value: Any) -> None:
            if not self._r:
                return
            self._r.set(key, json.dumps(value))

        def append(self, key: str, value: Any) -> None:
            lst = self.get(key, []) or []
            lst.append(value)
            self.set(key, lst)

        def snapshot(self) -> Dict[str, Any]:
            # Redis doesn't support listing keys without pattern; keep simple
            return {}

except Exception:
    RedisPersistentContext = None
