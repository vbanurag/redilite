# RediLite Command Manual (Man Pages) 📖

Complete reference guide for all Redis commands supported in **RediLite**, including syntax, descriptions, arguments, return values, embedded Python code, and CLI/RESP examples.

---

## Table of Contents

1. [Generic Key Operations](#1-generic-key-operations)
2. [String Operations](#2-string-operations)
3. [Hash Operations](#3-hash-operations)
4. [List Operations](#4-list-operations)
5. [Set Operations](#5-set-operations)
6. [Sorted Set (ZSet) Operations](#6-sorted-set-zset-operations)
7. [Transactions & Pub/Sub Operations](#7-transactions--pubsub-operations)
8. [Utility & Management Commands](#8-utility--management-commands)

---

## 1. Generic Key Operations

### `EXISTS`
- **Syntax**: `EXISTS key`
- **Description**: Returns whether `key` exists in the database and is not expired.
- **Return Value**: `1` if key exists, `0` if not.
- **Python**: `db.exists("user:100")`
- **CLI**: `EXISTS user:100`

---

### `DEL`
- **Syntax**: `DEL key [key ...]`
- **Description**: Deletes one or more keys and their associated values.
- **Return Value**: `int` (Number of keys deleted).
- **Python**: `db.delete("k1", "k2")`
- **CLI**: `DEL k1 k2`

---

### `TYPE`
- **Syntax**: `TYPE key`
- **Description**: Returns the data structure type stored at `key`.
- **Return Value**: `"string"`, `"hash"`, `"list"`, `"set"`, `"zset"`, or `"none"`.
- **Python**: `db.type("mykey")`
- **CLI**: `TYPE mykey`

---

### `KEYS`
- **Syntax**: `KEYS pattern`
- **Description**: Returns all key names matching glob pattern (e.g. `user:*`, `*`).
- **Return Value**: `list` of matching key names.
- **Python**: `db.keys("user:*")`
- **CLI**: `KEYS user:*`

---

### `EXPIRE`
- **Syntax**: `EXPIRE key seconds`
- **Description**: Sets a Time-To-Live (TTL) timeout on `key` in seconds.
- **Return Value**: `1` if timeout set, `0` if key does not exist.
- **Python**: `db.expire("session", 3600)`
- **CLI**: `EXPIRE session 3600`

---

### `TTL`
- **Syntax**: `TTL key`
- **Description**: Gets remaining TTL of `key` in seconds.
- **Return Value**: Remaining seconds, `-1` if persistent key, `-2` if key does not exist.
- **Python**: `db.ttl("session")`
- **CLI**: `TTL session`

---

### `PERSIST`
- **Syntax**: `PERSIST key`
- **Description**: Removes expiration from `key`, converting it back to persistent storage.
- **Return Value**: `1` if TTL removed, `0` if key does not exist or has no TTL.
- **Python**: `db.persist("session")`
- **CLI**: `PERSIST session`

---

### `FLUSHDB`
- **Syntax**: `FLUSHDB`
- **Description**: Wipes all keys and values from the active database.
- **Return Value**: `"OK"`
- **Python**: `db.flushdb()`
- **CLI**: `FLUSHDB`

---

## 2. String Operations

### `SET`
- **Syntax**: `SET key value [EX seconds]`
- **Description**: Stores `value` string at `key`, optionally setting expiration in seconds.
- **Return Value**: `True` / `"OK"`
- **Python**: `db.set("msg", "hello", ex=60)`
- **CLI**: `SET msg "hello" EX 60`

---

### `GET`
- **Syntax**: `GET key`
- **Description**: Retrieves string value stored at `key`.
- **Return Value**: `str` value or `None` / `(nil)` if not found.
- **Python**: `db.get("msg")`
- **CLI**: `GET msg`

---

### `GETSET`
- **Syntax**: `GETSET key value`
- **Description**: Sets `key` to `value` and returns the previous old value.
- **Return Value**: Old `str` value or `None`.
- **Python**: `db.getset("msg", "new_val")`
- **CLI**: `GETSET msg new_val`

---

### `INCR` / `INCRBY`
- **Syntax**: `INCR key` / `INCRBY key increment`
- **Description**: Increments integer value stored at `key` by `1` or `increment`.
- **Return Value**: `int` (New value after increment).
- **Python**: `db.incr("counter")` / `db.incrby("counter", 5)`
- **CLI**: `INCR counter` / `INCRBY counter 5`

---

### `DECR` / `DECRBY`
- **Syntax**: `DECR key` / `DECRBY key decrement`
- **Description**: Decrements integer value stored at `key` by `1` or `decrement`.
- **Return Value**: `int` (New value after decrement).
- **Python**: `db.decr("counter")` / `db.decrby("counter", 3)`
- **CLI**: `DECR counter` / `DECRBY counter 3`

---

### `APPEND`
- **Syntax**: `APPEND key value`
- **Description**: Appends `value` suffix to string stored at `key`.
- **Return Value**: `int` (Total string length after append).
- **Python**: `db.append("msg", " world")`
- **CLI**: `APPEND msg " world"`

---

### `STRLEN`
- **Syntax**: `STRLEN key`
- **Description**: Returns length of string stored at `key`.
- **Return Value**: `int` length.
- **Python**: `db.strlen("msg")`
- **CLI**: `STRLEN msg`

---

## 3. Hash Operations

### `HSET`
- **Syntax**: `HSET key field value [field value ...]`
- **Description**: Sets specified `field`-`value` pairs in the hash stored at `key`.
- **Return Value**: `int` (Number of new fields added).
- **Python**: `db.hset("user:1", "name", "Alice")`
- **CLI**: `HSET user:1 name "Alice" age 30`

---

### `HGET` / `HMGET`
- **Syntax**: `HGET key field` / `HMGET key field [field ...]`
- **Description**: Retrieves value of one or multiple fields in hash at `key`.
- **Return Value**: `str` value or list of values.
- **Python**: `db.hget("user:1", "name")` / `db.hmget("user:1", "name", "age")`
- **CLI**: `HGET user:1 name` / `HMGET user:1 name age`

---

### `HDEL`
- **Syntax**: `HDEL key field [field ...]`
- **Description**: Deletes specified fields from hash at `key`.
- **Return Value**: `int` (Number of fields removed).
- **Python**: `db.hdel("user:1", "age")`
- **CLI**: `HDEL user:1 age`

---

### `HEXISTS`
- **Syntax**: `HEXISTS key field`
- **Description**: Checks if `field` exists in hash at `key`.
- **Return Value**: `True` / `1` if field exists, `False` / `0` if not.
- **Python**: `db.hexists("user:1", "name")`
- **CLI**: `HEXISTS user:1 name`

---

### `HGETALL`
- **Syntax**: `HGETALL key`
- **Description**: Returns all field-value pairs stored in hash at `key`.
- **Return Value**: `dict` of field-value pairs.
- **Python**: `db.hgetall("user:1")`
- **CLI**: `HGETALL user:1`

---

### `HKEYS` / `HVALS` / `HLEN`
- **Syntax**: `HKEYS key` / `HVALS key` / `HLEN key`
- **Description**: Returns list of all fields, list of all values, or total count of fields in hash.
- **Python**: `db.hkeys("user:1")`, `db.hvals("user:1")`, `db.hlen("user:1")`
- **CLI**: `HKEYS user:1`, `HVALS user:1`, `HLEN user:1`

---

## 4. List Operations

### `LPUSH` / `RPUSH`
- **Syntax**: `LPUSH key value [value ...]` / `RPUSH key value [value ...]`
- **Description**: Inserts values at head (left) or tail (right) of list at `key`.
- **Return Value**: `int` (Length of list after push).
- **Python**: `db.lpush("tasks", "t1")`, `db.rpush("tasks", "t2")`
- **CLI**: `LPUSH tasks t1`, `RPUSH tasks t2`

---

### `LPOP` / `RPOP`
- **Syntax**: `LPOP key [count]` / `RPOP key [count]`
- **Description**: Removes and returns elements from head (left) or tail (right) of list at `key`.
- **Return Value**: Popped element `str` or `list` of popped elements.
- **Python**: `db.lpop("tasks")`, `db.rpop("tasks")`
- **CLI**: `LPOP tasks`, `RPOP tasks`

---

### `LRANGE`
- **Syntax**: `LRANGE key start stop`
- **Description**: Returns slice of elements from list at `key` between `start` and `stop` indices (supports `-1` for last element).
- **Return Value**: `list` of elements.
- **Python**: `db.lrange("tasks", 0, -1)`
- **CLI**: `LRANGE tasks 0 -1`

---

### `LLEN` / `LINDEX`
- **Syntax**: `LLEN key` / `LINDEX key index`
- **Description**: Returns length of list, or element at specific 0-based index.
- **Python**: `db.llen("tasks")`, `db.lindex("tasks", 0)`
- **CLI**: `LLEN tasks`, `LINDEX tasks 0`

---

## 5. Set Operations

### `SADD` / `SREM`
- **Syntax**: `SADD key member [member ...]` / `SREM key member [member ...]`
- **Description**: Adds or removes members in unordered set at `key`.
- **Return Value**: `int` (Number of new members added or removed).
- **Python**: `db.sadd("tags", "py", "sql")`, `db.srem("tags", "sql")`
- **CLI**: `SADD tags py sql`, `SREM tags sql`

---

### `SMEMBERS` / `SISMEMBER` / `SCARD`
- **Syntax**: `SMEMBERS key` / `SISMEMBER key member` / `SCARD key`
- **Description**: Returns set of all members, checks membership, or returns member count.
- **Python**: `db.smembers("tags")`, `db.sismember("tags", "py")`, `db.scard("tags")`
- **CLI**: `SMEMBERS tags`, `SISMEMBER tags py`, `SCARD tags`

---

### `SUNION` / `SINTER` / `SDIFF`
- **Syntax**: `SUNION key [key ...]` / `SINTER key [key ...]` / `SDIFF key [key ...]`
- **Description**: Computes Union, Intersection, or Difference across multiple sets.
- **Python**: `db.sunion("setA", "setB")`, `db.sinter("setA", "setB")`, `db.sdiff("setA", "setB")`
- **CLI**: `SUNION setA setB`, `SINTER setA setB`, `SDIFF setA setB`

---

## 6. Sorted Set (ZSet) Operations

### `ZADD`
- **Syntax**: `ZADD key score member [score member ...]`
- **Description**: Adds or updates member scores in sorted set at `key`.
- **Return Value**: `int` (Number of new members added).
- **Python**: `db.zadd("ranks", {"alice": 100.0, "bob": 85.5})`
- **CLI**: `ZADD ranks 100.0 alice 85.5 bob`

---

### `ZRANGE` / `ZREVRANGE`
- **Syntax**: `ZRANGE key start stop [WITHSCORES]` / `ZREVRANGE key start stop [WITHSCORES]`
- **Description**: Returns range of members sorted ascending or descending by score.
- **Python**: `db.zrange("ranks", 0, -1, withscores=True)`
- **CLI**: `ZRANGE ranks 0 -1 WITHSCORES`

---

### `ZSCORE` / `ZCARD` / `ZREM`
- **Syntax**: `ZSCORE key member` / `ZCARD key` / `ZREM key member [member ...]`
- **Description**: Returns member score, total count of members, or removes members.
- **Python**: `db.zscore("ranks", "alice")`, `db.zcard("ranks")`, `db.zrem("ranks", "bob")`
- **CLI**: `ZSCORE ranks alice`, `ZCARD ranks`, `ZREM ranks bob`

---

## 7. Transactions & Pub/Sub Operations

### `MULTI` / `EXEC` / `DISCARD`
- **Syntax**: `MULTI` ... commands ... `EXEC` or `DISCARD`
- **Description**: Groups commands into an atomic transaction block. `EXEC` runs all queued commands, `DISCARD` cancels transaction.
- **Python**:
  ```python
  db.execute_command("MULTI")
  db.execute_command("SET", "a", "10")
  db.execute_command("INCR", "a")
  results = db.execute_command("EXEC") # ["OK", 11]
  ```
- **CLI**:
  ```
  redilite> MULTI
  redilite> SET a 10
  redilite> INCR a
  redilite> EXEC
  ```

---

### `PUBLISH` / `subscribe`
- **Syntax**: `PUBLISH channel message`
- **Description**: Publishes `message` to all observers listening on `channel`.
- **Python**: `db.publish("news", "headline")`
- **CLI**: `PUBLISH news headline`

---

## 8. Utility & Management Commands

### `PING`
- **Syntax**: `PING [message]`
- **Description**: Ping test command.
- **Return Value**: `"PONG"` or `message`.
- **CLI**: `PING`

---

### `ECHO`
- **Syntax**: `ECHO message`
- **Description**: Echoes back input `message`.
- **CLI**: `ECHO "hello"`
