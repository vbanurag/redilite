# RediLite 🚀
> **An Embedded, Single-File SQLite-like Key-Value & Data Structure Engine with Redis API**

RediLite brings the simplicity of **SQLite** (zero server configuration, single-file `.redilite` storage, embedded in-process library) together with the power and dynamic APIs of **Redis** (Strings, Hashes, Lists, Sets, Sorted Sets, Key Expiration, Pub/Sub, and Transactions).

It also includes a built-in **RESP Protocol TCP Server** (so standard tools like `redis-cli`, `redis-py`, `go-redis`, `ioredis`, or `jedis` can connect seamlessly), an **Interactive CLI REPL**, and a full [Command Manual (redilite/COMMANDS.md)](redilite/COMMANDS.md).

---

## ⚡ 100% Compatible with UV (Astral Package Manager)

RediLite supports **`uv`**, Astral's fast Python package & project manager:

```bash
# Build wheels with UV
uv build

# Install system-wide via UV
uv pip install --system -e .

# Run interactive RediLite shell via UV
uv run redilite cli mydb.redilite
```

---

## 📦 How `import redilite` Works (Package & Library Setup)

RediLite can be used in 3 ways depending on your project requirements:

### Option 1: Install as a Python Library (`uv` or `pip`)
Run inside the project directory:
```bash
uv pip install --system -e .
# or standard pip:
pip install -e .
```
This registers `redilite` into your Python environment. Now **any Python script anywhere on your machine** can simply call:
```python
import redilite

db = redilite.connect("mydb.redilite")
```

### Option 2: Embedded Local Folder (Zero Installation)
Simply copy the `redilite/` directory into your project folder. Because `redilite/` contains an `__init__.py`, Python will import it directly:
```
my_project/
├── redilite/           <-- Copy directory here
│   ├── __init__.py
│   ├── core.py
│   └── storage.py
└── app.py              <-- Write: import redilite
```

### Option 3: Remote TCP Server (For Java, Go, Node.js, or Microservices)
Run the server process:
```bash
python3 -m redilite.cli server --port 6379 --db mydb.redilite
```
Now clients in **Node.js, Go, Java, or Python** connect via standard Redis drivers over TCP port `6379`.

---

## 🏗️ Software Design Patterns Architecture

RediLite is built using standard object-oriented software design patterns:

1. **Repository Pattern (`BaseStorageRepository`, `StorageEngine`)**
   - Decouples persistence technology (SQLite WAL engine) from domain business logic.
2. **Strategy Pattern (`SQLiteStringStrategy`, `SQLiteHashStrategy`, etc.)**
   - Encapsulates storage strategy implementations per Redis data structure type (`string`, `hash`, `list`, `set`, `zset`).
3. **Command Pattern (`ICommand`, `CommandRegistry`, `SetCommand`, `GetCommand`, etc.)**
   - Encapsulates Redis commands as executable objects, allowing command dispatching, parameter validation, and transaction queuing (`MULTI`/`EXEC`).
4. **Observer Pattern (`IObserver`, `PubSubManager`)**
   - Event bus providing Pub/Sub message dispatching to subscribed observers.
5. **Factory Pattern (`DatabaseFactory`)**
   - Standard factory method for instantiating database instances (`redilite.connect("mydb.redilite")`).

---

## ✨ Features & Operations

- 📦 **Embedded & Zero-Config (SQLite-style)**: Use it as a lightweight Python module without setting up databases or servers.
- 💾 **Single-File Persistence**: Stores data reliably in a single `.redilite` database file backed by SQLite WAL mode (or run entirely `:memory:`).
- ⚡ **Redis-Compatible API**:
  - **Strings**: `SET`, `GET`, `GETSET`, `INCR`, `DECR`, `MSET`, `MGET`, `APPEND`, `STRLEN`
  - **Hashes**: `HSET`, `HGET`, `HDEL`, `HEXISTS`, `HGETALL`, `HKEYS`, `HVALS`, `HLEN`, `HINCRBY`
  - **Lists**: `LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `LRANGE`, `LLEN`, `LINDEX`
  - **Sets**: `SADD`, `SREM`, `SMEMBERS`, `SISMEMBER`, `SCARD`, `SUNION`, `SINTER`, `SDIFF`
  - **Sorted Sets (ZSets)**: `ZADD`, `ZREM`, `ZRANGE`, `ZREVRANGE`, `ZSCORE`, `ZCARD`
  - **Key & TTL Expiration**: `DEL`, `EXISTS`, `EXPIRE`, `TTL`, `PERSIST`, `KEYS`, `FLUSHDB`
  - **Transactions**: `MULTI`, `EXEC`, `DISCARD`
  - **Pub/Sub**: In-memory event bus across subscribers.
- 🌐 **RESP Protocol TCP Server**: Connect using standard client drivers in Python, Java, Go, and Node.js.
- 💻 **Interactive CLI**: Dedicated SQLite/Redis-style terminal interface.

---

## 🔌 Connecting to RediLite (Multi-Language Examples)

---

### 🐍 1. Python Sample Code

#### Option A: Native Embedded Mode

```python
import redilite

# Connect directly to single-file database
db = redilite.connect("mydb.redilite")

db.set("user:100", "Alice")
print(db.get("user:100"))  # "Alice"

db.hset("session", "token", "abc12345")
print(db.hgetall("session"))  # {'token': 'abc12345'}

db.close()
```

#### Option B: Over TCP using `redis-py` Driver

```python
import redis

# Connect to RediLite RESP Server running on port 6379
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

r.set('msg', 'Hello RediLite from Python!')
print(r.get('msg'))  # "Hello RediLite from Python!"

r.hset('user:200', 'name', 'Bob')
print(r.hgetall('user:200'))
```

---

### 💚 2. Node.js / JavaScript Sample Code

#### Using `ioredis` or `redis` npm packages:

```javascript
const Redis = require('ioredis');

// Connect to RediLite RESP Server
const redis = new Redis({
  host: '127.0.0.1',
  port: 6379,
});

async function run() {
  await redis.set('app:status', 'online');
  const status = await redis.get('app:status');
  console.log('Status:', status); // "online"

  await redis.hset('player:1', 'score', 500, 'level', 3);
  const player = await redis.hgetall('player:1');
  console.log('Player Profile:', player);

  redis.disconnect();
}

run();
```

---

### 🐹 3. Go (Golang) Sample Code

#### Using `github.com/redis/go-redis/v9`:

```go
package main

import (
	"context"
	"fmt"
	"github.com/redis/go-redis/v9"
)

func main() {
	ctx := context.Background()

	// Connect to RediLite RESP Server
	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})

	// Set & Get String
	err := rdb.Set(ctx, "greeting", "Hello RediLite from Go!", 0).Err()
	if err != nil {
		panic(err)
	}

	val, err := rdb.Get(ctx, "greeting").Result()
	if err != nil {
		panic(err)
	}
	fmt.Println("Greeting:", val)

	// Hash Operations
	rdb.HSet(ctx, "user:300", "name", "Charlie", "role", "Admin")
	user, _ := rdb.HGetAll(ctx, "user:300").Result()
	fmt.Println("User:", user)
}
```

---

### ☕ 4. Java Sample Code

#### Using Jedis (`redis.clients.jedis.Jedis`):

```java
import redis.clients.jedis.Jedis;
import java.util.Map;

public class RediLiteExample {
    public static void main(String[] args) {
        // Connect to RediLite RESP Server
        try (Jedis jedis = new Jedis("localhost", 6379)) {
            
            // Ping test
            System.out.println("Response: " + jedis.ping()); // PONG
            
            // Set & Get
            jedis.set("server:name", "RediLite Core Engine");
            System.out.println("Server Name: " + jedis.get("server:name"));
            
            // Hash Operations
            jedis.hset("customer:1", "name", "David");
            jedis.hset("customer:1", "email", "david@example.com");
            
            Map<String, String> customer = jedis.hgetAll("customer:1");
            System.out.println("Customer Details: " + customer);
        }
    }
}
```

---

## ⚡ Performance Benchmarks

Run the benchmark suite:

```bash
python3 benchmark.py --iterations 1000 --disk
```

### Benchmark Metrics Summary:

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
python3 -m redilite.cli mydb.redilite
```

**Inside the CLI:**
```
redilite [mydb.redilite]> SET greeting "Hello RediLite"
"OK"
redilite [mydb.redilite]> GET greeting
"Hello RediLite"
redilite [mydb.redilite]> HSET user:100 name "Bob" email "bob@example.com"
(integer) 2
redilite [mydb.redilite]> HGETALL user:100
1) "name"
2) "Bob"
3) "email"
4) "bob@example.com"
```

---

## 🧪 Running Tests

Run the full unit and multi-threading concurrency test suite:

```bash
python3 -m unittest discover -s redilite/tests -p "test_*.py"
```
