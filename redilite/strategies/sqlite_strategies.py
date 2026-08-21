"""
SQLite concrete implementations of Strategy Pattern persistence handlers.
"""

import sqlite3
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from .base import IStringStrategy, IHashStrategy, IListStrategy, ISetStrategy, IZSetStrategy


class SQLiteStringStrategy(IStringStrategy):
    def set(self, conn: sqlite3.Connection, key: str, value: str, expire_seconds: Optional[float]) -> bool:
        expire_at = (time.time() + expire_seconds) if expire_seconds is not None else None
        with conn:
            conn.execute("DELETE FROM keys WHERE key = ?", (key,))
            conn.execute("INSERT INTO keys (key, type, expire_at) VALUES (?, 'string', ?)", (key, expire_at))
            conn.execute("INSERT INTO strings (key, value) VALUES (?, ?)", (key, str(value)))
        return True

    def get(self, conn: sqlite3.Connection, key: str) -> Optional[str]:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM strings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def append(self, conn: sqlite3.Connection, key: str, value: str) -> int:
        curr = self.get(conn, key)
        new_val = (curr or "") + value
        self.set(conn, key, new_val, None)
        return len(new_val)

    def incrby(self, conn: sqlite3.Connection, key: str, amount: int) -> int:
        curr_str = self.get(conn, key)
        val = int(curr_str) if curr_str is not None else 0
        new_val = val + amount
        self.set(conn, key, str(new_val), None)
        return new_val


class SQLiteHashStrategy(IHashStrategy):
    def hset(self, conn: sqlite3.Connection, key: str, field: str, value: str) -> int:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT type FROM keys WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row and row[0] != 'hash':
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if not row:
                conn.execute("INSERT INTO keys (key, type) VALUES (?, 'hash')", (key,))

            cursor.execute("SELECT 1 FROM hashes WHERE key = ? AND field = ?", (key, field))
            is_new = cursor.fetchone() is None

            conn.execute(
                "INSERT INTO hashes (key, field, value) VALUES (?, ?, ?) "
                "ON CONFLICT(key, field) DO UPDATE SET value = excluded.value",
                (key, field, str(value))
            )
            return 1 if is_new else 0

    def hget(self, conn: sqlite3.Connection, key: str, field: str) -> Optional[str]:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM hashes WHERE key = ? AND field = ?", (key, field))
        row = cursor.fetchone()
        return row[0] if row else None

    def hdel(self, conn: sqlite3.Connection, key: str, *fields: str) -> int:
        count = 0
        with conn:
            for f in fields:
                cursor = conn.execute("DELETE FROM hashes WHERE key = ? AND field = ?", (key, f))
                count += cursor.rowcount
        return count

    def hgetall(self, conn: sqlite3.Connection, key: str) -> Dict[str, str]:
        cursor = conn.cursor()
        cursor.execute("SELECT field, value FROM hashes WHERE key = ?", (key,))
        return dict(cursor.fetchall())


class SQLiteListStrategy(IListStrategy):
    def push(self, conn: sqlite3.Connection, key: str, values: List[str], where: str = 'LEFT') -> int:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT type FROM keys WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row and row[0] != 'list':
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if not row:
                conn.execute("INSERT INTO keys (key, type) VALUES (?, 'list')", (key,))

            cursor.execute("SELECT MIN(pos), MAX(pos) FROM lists WHERE key = ?", (key,))
            min_p, max_p = cursor.fetchone()
            if min_p is None:
                min_p, max_p = 0.0, 0.0

            for v in values:
                if where == 'LEFT':
                    min_p -= 1.0
                    pos = min_p
                else:
                    max_p += 1.0
                    pos = max_p
                conn.execute("INSERT INTO lists (key, pos, value) VALUES (?, ?, ?)", (key, pos, str(v)))

            cursor.execute("SELECT COUNT(*) FROM lists WHERE key = ?", (key,))
            return cursor.fetchone()[0]

    def pop(self, conn: sqlite3.Connection, key: str, where: str = 'LEFT', count: int = 1) -> Union[Optional[str], List[str]]:
        sql_order = "ASC" if where == 'LEFT' else "DESC"
        with conn:
            cursor = conn.cursor()
            if sql_order == "ASC":
                cursor.execute("SELECT id, value FROM lists WHERE key = ? ORDER BY pos ASC LIMIT ?", (key, count))
            else:
                cursor.execute("SELECT id, value FROM lists WHERE key = ? ORDER BY pos DESC LIMIT ?", (key, count))
            rows = cursor.fetchall()
            if not rows:
                return None if count == 1 else []

            popped = []
            for row_id, val in rows:
                popped.append(val)
                conn.execute("DELETE FROM lists WHERE id = ?", (row_id,))

            cursor.execute("SELECT COUNT(*) FROM lists WHERE key = ?", (key,))
            if cursor.fetchone()[0] == 0:
                conn.execute("DELETE FROM keys WHERE key = ?", (key,))

            return popped[0] if count == 1 else popped

    def range(self, conn: sqlite3.Connection, key: str, start: int, stop: int) -> List[str]:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM lists WHERE key = ? ORDER BY pos ASC", (key,))
        all_vals = [r[0] for r in cursor.fetchall()]
        length = len(all_vals)
        if length == 0:
            return []

        if start < 0:
            start += length
        if stop < 0:
            stop += length
        start = max(0, start)
        stop = min(length - 1, stop)
        if start > stop or start >= length:
            return []
        return all_vals[start : stop + 1]


class SQLiteSetStrategy(ISetStrategy):
    def sadd(self, conn: sqlite3.Connection, key: str, *members: str) -> int:
        added = 0
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT type FROM keys WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row and row[0] != 'set':
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if not row:
                conn.execute("INSERT INTO keys (key, type) VALUES (?, 'set')", (key,))

            for m in members:
                cursor.execute("SELECT 1 FROM sets WHERE key = ? AND member = ?", (key, str(m)))
                if cursor.fetchone() is None:
                    conn.execute("INSERT INTO sets (key, member) VALUES (?, ?)", (key, str(m)))
                    added += 1
        return added

    def srem(self, conn: sqlite3.Connection, key: str, *members: str) -> int:
        removed = 0
        with conn:
            for m in members:
                cursor = conn.execute("DELETE FROM sets WHERE key = ? AND member = ?", (key, str(m)))
                removed += cursor.rowcount
        return removed

    def smembers(self, conn: sqlite3.Connection, key: str) -> Set[str]:
        cursor = conn.cursor()
        cursor.execute("SELECT member FROM sets WHERE key = ?", (key,))
        return {r[0] for r in cursor.fetchall()}


class SQLiteZSetStrategy(IZSetStrategy):
    def zadd(self, conn: sqlite3.Connection, key: str, score_member_tuples: List[Tuple[float, str]]) -> int:
        added = 0
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT type FROM keys WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row and row[0] != 'zset':
                raise TypeError("WRONGTYPE Operation against a key holding the wrong kind of value")

            if not row:
                conn.execute("INSERT INTO keys (key, type) VALUES (?, 'zset')", (key,))

            for score, member in score_member_tuples:
                cursor.execute("SELECT 1 FROM zsets WHERE key = ? AND member = ?", (key, str(member)))
                is_new = cursor.fetchone() is None
                if is_new:
                    added += 1
                conn.execute(
                    "INSERT INTO zsets (key, score, member) VALUES (?, ?, ?) "
                    "ON CONFLICT(key, member) DO UPDATE SET score = excluded.score",
                    (key, float(score), str(member))
                )
        return added

    def zrem(self, conn: sqlite3.Connection, key: str, *members: str) -> int:
        removed = 0
        with conn:
            for m in members:
                cursor = conn.execute("DELETE FROM zsets WHERE key = ? AND member = ?", (key, str(m)))
                removed += cursor.rowcount
        return removed

    def zrange(self, conn: sqlite3.Connection, key: str, start: int, stop: int, with_scores: bool = False, reverse: bool = False) -> List[Any]:
        cursor = conn.cursor()
        if reverse:
            cursor.execute("SELECT member, score FROM zsets WHERE key = ? ORDER BY score DESC, member DESC", (key,))
        else:
            cursor.execute("SELECT member, score FROM zsets WHERE key = ? ORDER BY score ASC, member ASC", (key,))
        rows = cursor.fetchall()
        length = len(rows)
        if length == 0:
            return []

        if start < 0:
            start += length
        if stop < 0:
            stop += length
        start = max(0, start)
        stop = min(length - 1, stop)
        if start > stop or start >= length:
            return []

        slice_rows = rows[start : stop + 1]
        if with_scores:
            res = []
            for m, s in slice_rows:
                res.extend([m, s])
            return res
        return [m for m, s in slice_rows]
