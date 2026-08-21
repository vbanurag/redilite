"""
RediLite Core Engine Facade - Embedded Redis-compatible Key-Value and Data Structure Store.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
from .storage import StorageEngine
from .pubsub import PubSubManager
from .commands import global_command_registry, CommandRegistry


class RediLite:
    """
    Embedded SQLite-style Redis data structure engine facade.
    Usage:
        db = RediLite("mydb.redilite")
        db.set("name", "Alice")
        print(db.get("name"))
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._storage = StorageEngine(db_path)
        self._pubsub = PubSubManager()
        self._registry = global_command_registry
        self._in_transaction = False
        self._tx_queue: List[Tuple[str, List[Any]]] = []

    def close(self):
        self._storage.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # --- Pythonic Dict Access ---

    def __getitem__(self, key: str) -> Any:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: str, value: Any):
        self.set(key, str(value))

    def __delitem__(self, key: str):
        if not self.delete(key):
            raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return self.exists(key)

    # --- Key Operations ---

    def exists(self, key: str) -> bool:
        return self._storage.exists(key)

    def delete(self, *keys: str) -> int:
        return self._storage.delete(*keys)

    def type(self, key: str) -> str:
        ktype = self._storage.get_key_type(key)
        return ktype if ktype is not None else "none"

    def keys(self, pattern: str = "*") -> List[str]:
        return self._storage.keys(pattern)

    def expire(self, key: str, seconds: float) -> bool:
        return self._storage.set_ttl(key, seconds)

    def ttl(self, key: str) -> float:
        return self._storage.get_ttl(key)

    def persist(self, key: str) -> bool:
        return self._storage.persist(key)

    def flushdb(self):
        self._storage.flush_all()

    # --- String Operations ---

    def set(self, key: str, value: Any, ex: Optional[float] = None) -> bool:
        return self._storage.string_set(key, str(value), expire_seconds=ex)

    def get(self, key: str) -> Optional[str]:
        return self._storage.string_get(key)

    def getset(self, key: str, value: Any) -> Optional[str]:
        old = self.get(key)
        self.set(key, str(value))
        return old

    def mset(self, mapping: Dict[str, Any]) -> bool:
        for k, v in mapping.items():
            self.set(k, v)
        return True

    def mget(self, *keys: str) -> List[Optional[str]]:
        return [self.get(k) for k in keys]

    def incr(self, key: str) -> int:
        return self.incrby(key, 1)

    def incrby(self, key: str, amount: int) -> int:
        return self._storage.string_incrby(key, amount)

    def decr(self, key: str) -> int:
        return self.incrby(key, -1)

    def decrby(self, key: str, amount: int) -> int:
        return self.incrby(key, -amount)

    def append(self, key: str, value: str) -> int:
        return self._storage.string_append(key, value)

    def strlen(self, key: str) -> int:
        val = self.get(key)
        return len(val) if val else 0

    # --- Hash Operations ---

    def hset(self, key: str, field: str, value: Any) -> int:
        return self._storage.hash_set(key, field, str(value))

    def hmset(self, key: str, mapping: Dict[str, Any]) -> int:
        count = 0
        for f, v in mapping.items():
            count += self.hset(key, f, v)
        return count

    def hget(self, key: str, field: str) -> Optional[str]:
        return self._storage.hash_get(key, field)

    def hmget(self, key: str, *fields: str) -> List[Optional[str]]:
        return [self.hget(key, f) for f in fields]

    def hdel(self, key: str, *fields: str) -> int:
        return self._storage.hash_del(key, *fields)

    def hexists(self, key: str, field: str) -> bool:
        return self.hget(key, field) is not None

    def hgetall(self, key: str) -> Dict[str, str]:
        return self._storage.hash_getall(key)

    def hkeys(self, key: str) -> List[str]:
        if self._storage.get_key_type(key) != 'hash':
            return []
        return list(self._storage.hash_getall(key).keys())

    def hvals(self, key: str) -> List[str]:
        if self._storage.get_key_type(key) != 'hash':
            return []
        return list(self._storage.hash_getall(key).values())

    def hlen(self, key: str) -> int:
        return len(self.hgetall(key))

    def hincrby(self, key: str, field: str, amount: int) -> int:
        curr = self.hget(key, field)
        val = int(curr) if curr else 0
        new_val = val + amount
        self.hset(key, field, str(new_val))
        return new_val

    # --- List Operations ---

    def lpush(self, key: str, *values: Any) -> int:
        return self._storage.list_push(key, [str(v) for v in values], where='LEFT')

    def rpush(self, key: str, *values: Any) -> int:
        return self._storage.list_push(key, [str(v) for v in values], where='RIGHT')

    def lpop(self, key: str, count: int = 1) -> Union[Optional[str], List[str]]:
        return self._storage.list_pop(key, where='LEFT', count=count)

    def rpop(self, key: str, count: int = 1) -> Union[Optional[str], List[str]]:
        return self._storage.list_pop(key, where='RIGHT', count=count)

    def lrange(self, key: str, start: int, stop: int) -> List[str]:
        return self._storage.list_range(key, start, stop)

    def llen(self, key: str) -> int:
        return len(self.lrange(key, 0, -1))

    def lindex(self, key: str, index: int) -> Optional[str]:
        res = self.lrange(key, index, index)
        return res[0] if res else None

    # --- Set Operations ---

    def sadd(self, key: str, *members: Any) -> int:
        return self._storage.set_add(key, *[str(m) for m in members])

    def srem(self, key: str, *members: Any) -> int:
        return self._storage.set_rem(key, *[str(m) for m in members])

    def smembers(self, key: str) -> Set[str]:
        return self._storage.set_members(key)

    def sismember(self, key: str, member: Any) -> bool:
        return str(member) in self.smembers(key)

    def scard(self, key: str) -> int:
        return len(self.smembers(key))

    def sunion(self, *keys: str) -> Set[str]:
        res = set()
        for k in keys:
            res.update(self.smembers(k))
        return res

    def sinter(self, *keys: str) -> Set[str]:
        if not keys:
            return set()
        res = self.smembers(keys[0])
        for k in keys[1:]:
            res.intersection_update(self.smembers(k))
        return res

    def sdiff(self, first_key: str, *other_keys: str) -> Set[str]:
        res = self.smembers(first_key)
        for k in other_keys:
            res.difference_update(self.smembers(k))
        return res

    # --- Sorted Set (ZSET) Operations ---

    def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        tuples = [(float(score), str(member)) for member, score in mapping.items()]
        return self._storage.zset_add(key, tuples)

    def zrem(self, key: str, *members: Any) -> int:
        return self._storage.zset_rem(key, *[str(m) for m in members])

    def zrange(self, key: str, start: int, stop: int, withscores: bool = False) -> List[Any]:
        return self._storage.zset_range(key, start, stop, with_scores=withscores, reverse=False)

    def zrevrange(self, key: str, start: int, stop: int, withscores: bool = False) -> List[Any]:
        return self._storage.zset_range(key, start, stop, with_scores=withscores, reverse=True)

    def zscore(self, key: str, member: Any) -> Optional[float]:
        res = self._storage.zset_range(key, 0, -1, with_scores=True)
        m_str = str(member)
        for i in range(0, len(res), 2):
            if res[i] == m_str:
                return float(res[i+1])
        return None

    def zcard(self, key: str) -> int:
        return len(self.zrange(key, 0, -1))

    # --- Pub/Sub ---

    def publish(self, channel: str, message: Any) -> int:
        return self._pubsub.publish(channel, str(message))

    def subscribe(self, channel: str, callback: Any):
        self._pubsub.subscribe(channel, callback)

    def unsubscribe(self, channel: str, callback: Any):
        self._pubsub.unsubscribe(channel, callback)

    # --- Transaction & Command Dispatcher via Command Pattern ---

    def execute_command(self, cmd_name: str, *args: Any) -> Any:
        cmd_str = cmd_name.upper()

        if self._in_transaction and cmd_str not in ("EXEC", "DISCARD", "MULTI"):
            self._tx_queue.append((cmd_str, list(args)))
            return "QUEUED"

        if cmd_str == "MULTI":
            self._in_transaction = True
            self._tx_queue = []
            return "OK"
        elif cmd_str == "DISCARD":
            if not self._in_transaction:
                return Exception("ERR DISCARD without MULTI")
            self._in_transaction = False
            self._tx_queue = []
            return "OK"
        elif cmd_str == "EXEC":
            if not self._in_transaction:
                return Exception("ERR EXEC without MULTI")
            self._in_transaction = False
            results = []
            for item_cmd, item_args in self._tx_queue:
                res = self.execute_command(item_cmd, *item_args)
                results.append(res)
            self._tx_queue = []
            return results

        command_obj = self._registry.get_command(cmd_str)
        if command_obj:
            try:
                return command_obj.execute(self, *args)
            except Exception as e:
                return e

        # Fallbacks
        if cmd_str in ("FLUSHDB", "FLUSHALL"):
            self.flushdb()
            return "OK"
        elif cmd_str == "PUBLISH":
            return self.publish(args[0], args[1])
        elif cmd_str == "MSET":
            mapping = {args[i]: args[i+1] for i in range(0, len(args), 2)}
            return "OK" if self.mset(mapping) else "ERR"
        elif cmd_str == "MGET":
            return self.mget(*args)
        elif cmd_str == "INCR":
            return self.incr(args[0])
        elif cmd_str == "INCRBY":
            return self.incrby(args[0], int(args[1]))
        elif cmd_str == "DECR":
            return self.decr(args[0])
        elif cmd_str == "DECRBY":
            return self.decrby(args[0], int(args[1]))
        else:
            return Exception(f"ERR unknown command '{cmd_str}'")


# Backwards compatibility alias
LiteDis = RediLite
