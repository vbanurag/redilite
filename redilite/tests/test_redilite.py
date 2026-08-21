"""
Exhaustive Unit, Integration, Concurrency & Strategy Test Suite for RediLite.
"""

import os
import time
import socket
import sqlite3
import threading
import unittest
import redilite
from redilite import DatabaseFactory, RediLite
from redilite.storage import StorageEngine
from redilite.strategies import (
    SQLiteStringStrategy,
    SQLiteHashStrategy,
    SQLiteListStrategy,
    SQLiteSetStrategy,
    SQLiteZSetStrategy,
)
from redilite.resp import RESPDecoder, RESPEncoder
from redilite.server import RediLiteServer
from redilite.cli import format_result


class TestRediLiteCoreOperations(unittest.TestCase):

    def setUp(self):
        self.db = DatabaseFactory.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def test_strings(self):
        self.assertTrue(self.db.set("msg", "hello"))
        self.assertEqual(self.db.get("msg"), "hello")
        self.assertEqual(self.db.getset("msg", "world"), "hello")
        self.assertEqual(self.db.get("msg"), "world")
        self.assertEqual(self.db.append("msg", "!"), 6)
        self.assertEqual(self.db.get("msg"), "world!")
        self.assertEqual(self.db.strlen("msg"), 6)

        # Incr / Decr / IncrBy / DecrBy
        self.assertEqual(self.db.incr("counter"), 1)
        self.assertEqual(self.db.incrby("counter", 5), 6)
        self.assertEqual(self.db.decr("counter"), 5)
        self.assertEqual(self.db.decrby("counter", 3), 2)

        # Mset / Mget
        self.assertTrue(self.db.mset({"k1": "v1", "k2": "v2"}))
        self.assertEqual(self.db.mget("k1", "k2", "nonexistent"), ["v1", "v2", None])

    def test_hashes(self):
        self.assertEqual(self.db.hset("user:100", "name", "Alice"), 1)
        self.assertEqual(self.db.hset("user:100", "role", "Admin"), 1)
        self.assertEqual(self.db.hget("user:100", "name"), "Alice")
        self.assertEqual(self.db.hlen("user:100"), 2)
        self.assertEqual(self.db.hgetall("user:100"), {"name": "Alice", "role": "Admin"})
        self.assertEqual(sorted(self.db.hkeys("user:100")), ["name", "role"])
        self.assertEqual(sorted(self.db.hvals("user:100")), ["Admin", "Alice"])
        self.assertEqual(self.db.hincrby("user:100", "age", 30), 30)
        self.assertEqual(self.db.hdel("user:100", "role"), 1)
        self.assertFalse(self.db.hexists("user:100", "role"))
        self.assertEqual(self.db.hmget("user:100", "name", "age", "missing"), ["Alice", "30", None])

    def test_lists(self):
        self.assertEqual(self.db.rpush("tasks", "task1", "task2"), 2)
        self.assertEqual(self.db.lpush("tasks", "task0"), 3)
        self.assertEqual(self.db.llen("tasks"), 3)
        self.assertEqual(self.db.lrange("tasks", 0, -1), ["task0", "task1", "task2"])
        self.assertEqual(self.db.lindex("tasks", 1), "task1")
        self.assertEqual(self.db.lpop("tasks"), "task0")
        self.assertEqual(self.db.rpop("tasks"), "task2")
        self.assertEqual(self.db.llen("tasks"), 1)
        self.assertEqual(self.db.lpop("tasks"), "task1")
        self.assertEqual(self.db.llen("tasks"), 0)
        self.assertFalse(self.db.exists("tasks"))

    def test_sets(self):
        self.assertEqual(self.db.sadd("tags", "python", "database", "redis"), 3)
        self.assertEqual(self.db.sadd("tags", "python"), 0)
        self.assertEqual(self.db.scard("tags"), 3)
        self.assertTrue(self.db.sismember("tags", "database"))
        self.assertFalse(self.db.sismember("tags", "nonexistent"))
        self.assertEqual(self.db.smembers("tags"), {"python", "database", "redis"})

        # Set operations (Union, Inter, Diff)
        self.db.sadd("setA", "a", "b", "c")
        self.db.sadd("setB", "b", "c", "d")
        self.assertEqual(self.db.sunion("setA", "setB"), {"a", "b", "c", "d"})
        self.assertEqual(self.db.sinter("setA", "setB"), {"b", "c"})
        self.assertEqual(self.db.sdiff("setA", "setB"), {"a"})
        self.assertEqual(self.db.srem("setA", "a"), 1)
        self.assertEqual(self.db.smembers("setA"), {"b", "c"})

    def test_zsets(self):
        self.assertEqual(self.db.zadd("leaderboard", {"alice": 100, "bob": 85, "charlie": 95}), 3)
        self.assertEqual(self.db.zcard("leaderboard"), 3)
        self.assertEqual(self.db.zscore("leaderboard", "alice"), 100.0)
        self.assertIsNone(self.db.zscore("leaderboard", "nobody"))
        self.assertEqual(self.db.zrange("leaderboard", 0, -1), ["bob", "charlie", "alice"])
        self.assertEqual(self.db.zrevrange("leaderboard", 0, 1), ["alice", "charlie"])
        self.assertEqual(self.db.zrange("leaderboard", 0, -1, withscores=True), ["bob", 85.0, "charlie", 95.0, "alice", 100.0])

    def test_keys_types_and_flushdb(self):
        self.db.set("user:1", "a")
        self.db.set("user:2", "b")
        self.db.set("config", "c")
        self.assertEqual(sorted(self.db.keys("user:*")), ["user:1", "user:2"])
        self.assertEqual(self.db.type("user:1"), "string")
        self.assertEqual(self.db.type("nonexistent"), "none")

        self.db.flushdb()
        self.assertEqual(self.db.keys("*"), [])

    def test_wrong_type_errors(self):
        self.db.set("str_key", "hello")
        with self.assertRaises(TypeError):
            self.db.hset("str_key", "field", "val")

        with self.assertRaises(TypeError):
            self.db.lpush("str_key", "item")

        with self.assertRaises(TypeError):
            self.db.sadd("str_key", "elem")

        with self.assertRaises(TypeError):
            self.db.zadd("str_key", {"member": 10})

    def test_pub_sub(self):
        received = []
        def listener(chan, msg):
            received.append((chan, msg))

        self.db.subscribe("news", listener)
        subs = self.db.publish("news", "breaking headline")
        self.assertEqual(subs, 1)
        self.assertEqual(received, [("news", "breaking headline")])

        self.db.unsubscribe("news", listener)
        subs_after = self.db.publish("news", "another news")
        self.assertEqual(subs_after, 0)

    def test_ttl_expiration(self):
        self.db.set("temp", "volatile")
        self.assertTrue(self.db.expire("temp", 0.2))
        self.assertGreater(self.db.ttl("temp"), 0)
        time.sleep(0.3)
        self.assertIsNone(self.db.get("temp"))
        self.assertFalse(self.db.exists("temp"))
        self.assertEqual(self.db.ttl("temp"), -2.0)

        # Persist test
        self.db.set("perm", "val", ex=100)
        self.assertTrue(self.db.persist("perm"))
        self.assertEqual(self.db.ttl("perm"), -1.0)

    def test_transactions(self):
        self.assertEqual(self.db.execute_command("MULTI"), "OK")
        self.assertEqual(self.db.execute_command("SET", "a", "10"), "QUEUED")
        self.assertEqual(self.db.execute_command("INCR", "a"), "QUEUED")
        res = self.db.execute_command("EXEC")
        self.assertEqual(res, ["OK", 11])
        self.assertEqual(self.db.get("a"), "11")

        # Discard
        self.assertEqual(self.db.execute_command("MULTI"), "OK")
        self.assertEqual(self.db.execute_command("SET", "b", "20"), "QUEUED")
        self.assertEqual(self.db.execute_command("DISCARD"), "OK")
        self.assertIsNone(self.db.get("b"))

    def test_python_dict_access(self):
        self.db["foo"] = "bar"
        self.assertEqual(self.db["foo"], "bar")
        self.assertTrue("foo" in self.db)
        del self.db["foo"]
        self.assertFalse("foo" in self.db)


class TestDirectStrategies(unittest.TestCase):
    """Direct Strategy Pattern unit tests."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("CREATE TABLE keys (key TEXT PRIMARY KEY, type TEXT NOT NULL, expire_at REAL);")
        self.conn.execute("CREATE TABLE strings (key TEXT PRIMARY KEY, value TEXT, FOREIGN KEY(key) REFERENCES keys(key) ON DELETE CASCADE);")
        self.conn.execute("CREATE TABLE hashes (key TEXT NOT NULL, field TEXT NOT NULL, value TEXT, PRIMARY KEY(key, field), FOREIGN KEY(key) REFERENCES keys(key) ON DELETE CASCADE);")
        self.conn.execute("CREATE TABLE lists (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL, pos REAL NOT NULL, value TEXT, FOREIGN KEY(key) REFERENCES keys(key) ON DELETE CASCADE);")

    def tearDown(self):
        self.conn.close()

    def test_string_strategy(self):
        strat = SQLiteStringStrategy()
        strat.set(self.conn, "k", "v", None)
        self.assertEqual(strat.get(self.conn, "k"), "v")
        self.assertEqual(strat.append(self.conn, "k", "123"), 4)
        self.assertEqual(strat.get(self.conn, "k"), "v123")

    def test_hash_strategy(self):
        strat = SQLiteHashStrategy()
        self.assertEqual(strat.hset(self.conn, "h", "f1", "v1"), 1)
        self.assertEqual(strat.hget(self.conn, "h", "f1"), "v1")
        self.assertEqual(strat.hgetall(self.conn, "h"), {"f1": "v1"})
        self.assertEqual(strat.hdel(self.conn, "h", "f1"), 1)
        self.assertEqual(strat.hgetall(self.conn, "h"), {})

    def test_list_strategy(self):
        strat = SQLiteListStrategy()
        self.assertEqual(strat.push(self.conn, "l", ["a", "b"], "RIGHT"), 2)
        self.assertEqual(strat.range(self.conn, "l", 0, -1), ["a", "b"])
        self.assertEqual(strat.pop(self.conn, "l", "LEFT", 1), "a")


class TestRediLiteConcurrencyAndPersistence(unittest.TestCase):

    def test_multithreaded_concurrency(self):
        db = DatabaseFactory.connect(":memory:")
        errors = []

        def worker(thread_id):
            try:
                for i in range(50):
                    key = f"key_{thread_id}_{i}"
                    db.set(key, f"val_{i}")
                    db.hset(f"hash_{thread_id}", f"field_{i}", f"hval_{i}")
                    self.assertEqual(db.get(key), f"val_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        db.close()

    def test_file_persistence(self):
        db_file = "test_persistence.redilite"
        if os.path.exists(db_file):
            os.remove(db_file)

        try:
            db1 = DatabaseFactory.connect(db_file)
            db1.set("site", "antigravity")
            db1.hset("session", "token", "xyz123")
            db1.rpush("logs", "log1", "log2")
            db1.close()

            db2 = DatabaseFactory.connect(db_file)
            self.assertEqual(db2.get("site"), "antigravity")
            self.assertEqual(db2.hget("session", "token"), "xyz123")
            self.assertEqual(db2.lrange("logs", 0, -1), ["log1", "log2"])
            db2.close()
        finally:
            if os.path.exists(db_file):
                os.remove(db_file)


class TestRESPAndCLI(unittest.TestCase):

    def test_resp_encoding_decoding(self):
        dec = RESPDecoder()
        encoded = RESPEncoder.encode(["SET", "key", "val"])
        dec.feed(encoded)
        res = dec.parse()
        self.assertEqual(res, ["SET", "key", "val"])

    def test_resp_server_socket(self):
        srv = RediLiteServer(host="127.0.0.1", port=16383, db_path=":memory:")
        srv_thread = threading.Thread(target=srv.run, daemon=True)
        srv_thread.start()
        time.sleep(0.3)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 16383))
        
        sock.sendall(b"*3\r\n$3\r\nSET\r\n$4\r\nhero\r\n$6\r\nBatman\r\n")
        resp = sock.recv(1024)
        self.assertEqual(resp, b"+OK\r\n")

        sock.sendall(b"*2\r\n$3\r\nGET\r\n$4\r\nhero\r\n")
        resp = sock.recv(1024)
        self.assertEqual(resp, b"$6\r\nBatman\r\n")

        sock.close()

    def test_cli_formatter(self):
        self.assertEqual(format_result(None), "(nil)")
        self.assertEqual(format_result(True), "(boolean) true")
        self.assertEqual(format_result(100), "(integer) 100")
        self.assertEqual(format_result("hello"), '"hello"')


if __name__ == "__main__":
    unittest.main()
