# RediLite 🚀
> **An Embedded, Single-File SQLite-like Key-Value & Data Structure Engine with Redis API**

[![PyPI Version](https://img.shields.io/pypi/v/redilite.svg)](https://pypi.org/project/redilite/)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://pypi.org/project/redilite/)
[![CI Status](https://github.com/vbanurag/redilite/actions/workflows/ci.yml/badge.svg)](https://github.com/vbanurag/redilite/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

RediLite brings the simplicity of **SQLite** (zero server configuration, single-file `.redilite` storage, embedded in-process library) together with the power and dynamic APIs of **Redis** (Strings, Hashes, Lists, Sets, Sorted Sets, Key Expiration, Pub/Sub, and Transactions).

It also includes a built-in **RESP Protocol TCP Server** (so standard tools like `redis-cli`, `redis-py`, `go-redis`, `ioredis`, or `jedis` can connect seamlessly), an **Interactive CLI REPL**, and a full [Command Manual (redilite/COMMANDS.md)](redilite/COMMANDS.md).

---

## 💻 Installation

### 1. Standard PyPI Installation
Install via `pip`:
```bash
pip install redilite
```

Install via `uv` (Astral package manager):
```bash
uv add redilite
# or via uv pip:
uv pip install redilite
```

### 2. Install Directly from GitHub
```bash
pip install git+https://github.com/vbanurag/redilite.git
```

### 3. Local Development Installation
Clone the repository and install in editable mode:
```bash
git clone https://github.com/vbanurag/redilite.git
cd redilite
uv pip install --system -e .
```

---

## ⚡ 100% Compatible with UV (Astral Package Manager)

RediLite fully supports **`uv`**:

```bash
# Build wheels with UV
uv build

# Run interactive RediLite shell via UV
uv run redilite cli mydb.redilite
```

---

## 📦 Usage Modes

RediLite can be used in 3 ways depending on your project requirements:

### Option 1: Native Embedded Python Library (SQLite Style)

```python
import redilite

# Connect directly to a single-file database (or ':memory:')
db = redilite.connect("mydb.redilite")

# --- String Operations ---
db.set("user:name", "Alice", ex=60)  # Expire in 60s
print(db.get("user:name"))           # "Alice"

# Pythonic Dict Syntax
db["counter"] = 100
print(db["counter"])                 # "100"

# --- Hash Operations ---
db.hset("profile:1", "age", 30)
db.hset("profile:1", "role", "Engineer")
print(db.hgetall("profile:1"))       # {'age': '30', 'role': 'Engineer'}

# --- List Operations ---
db.rpush("queue", "job1", "job2", "job3")
print(db.lpop("queue"))              # "job1"
print(db.lrange("queue", 0, -1))     # ['job2', 'job3']

# --- Set Operations ---
db.sadd("skills", "python", "sqlite", "redis")
print(db.smembers("skills"))         # {'python', 'sqlite', 'redis'}

# --- Sorted Sets (ZSets) ---
db.zadd("scores", {"player1": 150, "player2": 220})
print(db.zrevrange("scores", 0, -1, withscores=True))  # ['player2', 220.0, 'player1', 150.0]

# Always close when done (or use context manager)
db.close()
```

### Option 2: Embedded Local Folder (Zero Installation)
Simply copy the `redilite/` directory into your project codebase:
```
my_project/
├── redilite/           <-- Copy package folder here
│   ├── __init__.py
│   ├── core.py
│   └── storage.py
└── app.py              <-- Write: import redilite
```

### Option 3: Remote RESP TCP Server (For Java, Go, Node.js, or Microservices)
Start the TCP server process:
```bash
python3 -m redilite.cli server --port 6379 --db mydb.redilite
```
Now clients in **Node.js, Go, Java, or Python** connect over TCP port `6379`.

---

## 🔌 Connecting to RediLite (Multi-Language Examples)

### 🐍 Python (`redis-py`)
```python
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
r.set('msg', 'Hello RediLite from Python!')
print(r.get('msg'))
```

### 💚 Node.js / JavaScript (`ioredis`)
```javascript
const Redis = require('ioredis');
const redis = new Redis({ host: '127.0.0.1', port: 6379 });
await redis.set('app:status', 'online');
console.log(await redis.get('app:status'));
```

### 🐹 Go (`go-redis`)
```go
rdb := redis.NewClient(&redis.Options{ Addr: "localhost:6379" })
rdb.Set(ctx, "greeting", "Hello from Go!", 0)
```

### ☕ Java (`Jedis`)
```java
try (Jedis jedis = new Jedis("localhost", 6379)) {
    jedis.set("server:name", "RediLite Engine");
}
```

---

## 🏗️ Software Design Patterns Architecture

1. **Repository Pattern (`BaseStorageRepository`, `StorageEngine`)**: Decouples persistence from domain logic.
2. **Strategy Pattern (`SQLiteStringStrategy`, `SQLiteHashStrategy`, etc.)**: Modular storage handlers per data type.
3. **Command Pattern (`ICommand`, `CommandRegistry`)**: Encapsulated Redis commands and transaction queueing.
4. **Observer Pattern (`IObserver`, `PubSubManager`)**: Event bus for Pub/Sub messaging.
5. **Factory Pattern (`DatabaseFactory`)**: Factory method for instantiating database connections (`redilite.connect()`).

---

## ⚡ Performance Benchmarks

Run benchmark suite:
```bash
python3 benchmark.py --iterations 1000 --disk
```

| Operation | In-Memory (`:memory:`) | Disk WAL (`.redilite`) | Avg Latency |
| :--- | :--- | :--- | :--- |
| **KEY TTL** | **447,392 ops/sec** | **275,560 ops/sec** | `0.002ms` |
| **STRING GET** | **377,083 ops/sec** | **222,179 ops/sec** | `0.003ms` |
| **HASH HGET** | **371,440 ops/sec** | **203,795 ops/sec** | `0.003ms` |
| **HASH HSET** | **281,686 ops/sec** | **75,665 ops/sec** | `0.004ms` |
| **STRING SET** | **218,487 ops/sec** | **43,821 ops/sec** | `0.005ms` |
| **SET SADD** | **207,988 ops/sec** | **43,617 ops/sec** | `0.005ms` |
| **ZSET ZADD** | **177,176 ops/sec** | **48,830 ops/sec** | `0.006ms` |
| **TRANSACTION** | **56,966 ops/sec** | **17,368 ops/sec** | `0.018ms` |

---

## 🖥️ Interactive CLI REPL

Run RediLite interactive terminal shell:
```bash
redilite cli mydb.redilite
```

```
redilite [mydb.redilite]> SET greeting "Hello RediLite"
"OK"
redilite [mydb.redilite]> GET greeting
"Hello RediLite"
redilite [mydb.redilite]> HSET user:100 name "Bob" email "bob@example.com"
(integer) 2
```

---

## 🧪 Running Tests

Run the full unit and multi-threading concurrency test suite:

```bash
python3 -m unittest discover -s redilite/tests -p "test_*.py"
```
