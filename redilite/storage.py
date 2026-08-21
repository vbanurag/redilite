"""
LiteDis Storage Engine - Repository Pattern Persistence Layer.
Delegates persistence operations to Strategy Pattern handlers.
"""

from abc import ABC, abstractmethod
import sqlite3
import time
import threading
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .strategies import (
    SQLiteStringStrategy,
    SQLiteHashStrategy,
    SQLiteListStrategy,
    SQLiteSetStrategy,
    SQLiteZSetStrategy,
)


class BaseStorageRepository(ABC):
    @abstractmethod
    def purge_expired(self):
        pass

    @abstractmethod
    def get_key_type(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def delete(self, *keys: str) -> int:
        pass

    @abstractmethod
    def close(self):
        pass


class StorageEngine(BaseStorageRepository):
    """
    Concrete SQLite Repository using Strategy Pattern handlers.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._conn = self._create_connection()
        self._init_db()

        # Strategy Pattern instances
        self.string_strategy = SQLiteStringStrategy()
        self.hash_strategy = SQLiteHashStrategy()
        self.list_strategy = SQLiteListStrategy()
        self.set_strategy = SQLiteSetStrategy()
        self.zset_strategy = SQLiteZSetStrategy()

    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        if self.db_path != ":memory:":
            try:
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA synchronous = NORMAL;")
            except sqlite3.OperationalError:
                pass
        return conn

    def _init_db(self):
        with self._lock:
            with self._conn:
                cursor = self._conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS keys (
                        key TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        expire_at REAL
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_keys_expire ON keys(expire_at);")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strings (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        FOREIGN KEY(key) REFERENCES keys(key) ON DELETE CASCADE
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hashes (
                        key TEXT NOT NULL,
                        field TEXT NOT NULL,
                        value TEXT,
                        PRIMARY KEY(key, field),
                        FOREIGN KEY(key) REFERENCES keys(key) ON DELETE CASCADE
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS lists (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT NOT NULL,
                        pos REAL NOT NULL,
                        value TEXT,
                        FOREIGN KEY(key) REFERENCES keys(key) ON DELETE CASCADE
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_lists_key_pos ON lists(key, pos);")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sets (
                        key TEXT NOT NULL,
                        member TEXT NOT NULL,
                        PRIMARY KEY(key, member),
                        FOREIGN KEY(key) REFERENCES keys(key) ON DELETE CASCADE
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS zsets (
                        key TEXT NOT NULL,
                        score REAL NOT NULL,
                        member TEXT NOT NULL,
                        PRIMARY KEY(key, member),
                        FOREIGN KEY(key) REFERENCES keys(key) ON DELETE CASCADE
                    );
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_zsets_score ON zsets(key, score);")

    def purge_expired(self):
        now = time.time()
        with self._lock:
            with self._conn:
                self._conn.execute("DELETE FROM keys WHERE expire_at IS NOT NULL AND expire_at <= ?", (now,))

    def is_expired(self, key: str) -> bool:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT expire_at FROM keys WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row:
                return False
            expire_at = row[0]
            if expire_at is not None and time.time() >= expire_at:
                with self._conn:
                    self._conn.execute("DELETE FROM keys WHERE key = ?", (key,))
                return True
            return False

    def get_key_type(self, key: str) -> Optional[str]:
        if self.is_expired(key):
            return None
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT type FROM keys WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None

    def exists(self, key: str) -> bool:
        return self.get_key_type(key) is not None

    def delete(self, *keys: str) -> int:
        count = 0
        with self._lock:
            with self._conn:
                for k in keys:
                    cursor = self._conn.execute("DELETE FROM keys WHERE key = ?", (k,))
                    count += cursor.rowcount
        return count

    def set_ttl(self, key: str, seconds: float) -> bool:
        if not self.exists(key):
            return False
        expire_at = time.time() + seconds
        with self._lock:
            with self._conn:
                self._conn.execute("UPDATE keys SET expire_at = ? WHERE key = ?", (expire_at, key))
        return True

    def get_ttl(self, key: str) -> float:
        if self.is_expired(key):
            return -2.0
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT expire_at FROM keys WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row:
                return -2.0
            expire_at = row[0]
            if expire_at is None:
                return -1.0
            return max(0.0, expire_at - time.time())

    def persist(self, key: str) -> bool:
        if not self.exists(key):
            return False
        with self._lock:
            with self._conn:
                self._conn.execute("UPDATE keys SET expire_at = NULL WHERE key = ?", (key,))
        return True

    def keys(self, pattern: str = "*") -> List[str]:
        self.purge_expired()
        sql_pattern = pattern.replace("*", "%").replace("?", "_")
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT key FROM keys WHERE key LIKE ?", (sql_pattern,))
            return [row[0] for row in cursor.fetchall()]

    def flush_all(self):
        with self._lock:
            with self._conn:
                self._conn.execute("DELETE FROM keys")

    # Delegate Strategy methods
    def string_set(self, key: str, value: str, expire_seconds: Optional[float] = None) -> bool:
        with self._lock:
            return self.string_strategy.set(self._conn, key, value, expire_seconds)

    def string_get(self, key: str) -> Optional[str]:
        if self.get_key_type(key) != 'string':
            return None
        with self._lock:
            return self.string_strategy.get(self._conn, key)

    def string_append(self, key: str, value: str) -> int:
        with self._lock:
            return self.string_strategy.append(self._conn, key, value)

    def string_incrby(self, key: str, amount: int) -> int:
        with self._lock:
            return self.string_strategy.incrby(self._conn, key, amount)

    def hash_set(self, key: str, field: str, value: str) -> int:
        with self._lock:
            return self.hash_strategy.hset(self._conn, key, field, value)

    def hash_get(self, key: str, field: str) -> Optional[str]:
        if self.get_key_type(key) != 'hash':
            return None
        with self._lock:
            return self.hash_strategy.hget(self._conn, key, field)

    def hash_del(self, key: str, *fields: str) -> int:
        if self.get_key_type(key) != 'hash':
            return 0
        with self._lock:
            return self.hash_strategy.hdel(self._conn, key, *fields)

    def hash_getall(self, key: str) -> Dict[str, str]:
        if self.get_key_type(key) != 'hash':
            return {}
        with self._lock:
            return self.hash_strategy.hgetall(self._conn, key)

    def list_push(self, key: str, values: List[str], where: str = 'LEFT') -> int:
        with self._lock:
            return self.list_strategy.push(self._conn, key, values, where)

    def list_pop(self, key: str, where: str = 'LEFT', count: int = 1) -> Union[Optional[str], List[str]]:
        if self.get_key_type(key) != 'list':
            return None if count == 1 else []
        with self._lock:
            return self.list_strategy.pop(self._conn, key, where, count)

    def list_range(self, key: str, start: int, stop: int) -> List[str]:
        if self.get_key_type(key) != 'list':
            return []
        with self._lock:
            return self.list_strategy.range(self._conn, key, start, stop)

    def set_add(self, key: str, *members: str) -> int:
        with self._lock:
            return self.set_strategy.sadd(self._conn, key, *members)

    def set_rem(self, key: str, *members: str) -> int:
        if self.get_key_type(key) != 'set':
            return 0
        with self._lock:
            return self.set_strategy.srem(self._conn, key, *members)

    def set_members(self, key: str) -> Set[str]:
        if self.get_key_type(key) != 'set':
            return set()
        with self._lock:
            return self.set_strategy.smembers(self._conn, key)

    def zset_add(self, key: str, score_member_tuples: List[Tuple[float, str]]) -> int:
        with self._lock:
            return self.zset_strategy.zadd(self._conn, key, score_member_tuples)

    def zset_rem(self, key: str, *members: str) -> int:
        if self.get_key_type(key) != 'zset':
            return 0
        with self._lock:
            return self.zset_strategy.zrem(self._conn, key, *members)

    def zset_range(self, key: str, start: int, stop: int, with_scores: bool = False, reverse: bool = False) -> List[Any]:
        if self.get_key_type(key) != 'zset':
            return []
        with self._lock:
            return self.zset_strategy.zrange(self._conn, key, start, stop, with_scores, reverse)

    def close(self):
        with self._lock:
            self._conn.close()
