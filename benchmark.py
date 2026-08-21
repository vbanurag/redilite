"""
RediLite Performance Benchmark Suite.
Measures Operations Per Second (OPS/sec) and Latency Distribution across all Redis data types.
Supports both In-Memory (':memory:') and Disk Persistence ('.redilite' SQLite WAL file) modes.
"""

import argparse
import os
import time
import statistics
import redilite
from redilite import DatabaseFactory


def run_benchmark(db_path: str, iterations: int):
    print("=" * 70)
    print(f" REDILITE PERFORMANCE BENCHMARK")
    print(f" Target DB: {'In-Memory (:memory:)' if db_path == ':memory:' else f'Disk File ({db_path})'}")
    print(f" Iterations per test: {iterations}")
    print("=" * 70)

    db = DatabaseFactory.connect(db_path)

    def benchmark_op(name: str, fn):
        latencies_ms = []
        start_total = time.time()
        for i in range(iterations):
            t0 = time.perf_counter()
            fn(i)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)
        total_time = time.time() - start_total

        ops_per_sec = iterations / total_time
        avg_lat = statistics.mean(latencies_ms)
        p95_lat = statistics.quantiles(latencies_ms, n=20)[18] if len(latencies_ms) >= 20 else max(latencies_ms)
        p99_lat = statistics.quantiles(latencies_ms, n=100)[98] if len(latencies_ms) >= 100 else max(latencies_ms)

        print(f" [{name:^22}] | {ops_per_sec:>9.1f} ops/sec | avg: {avg_lat:.3f}ms | p95: {p95_lat:.3f}ms | p99: {p99_lat:.3f}ms")

    try:
        # 1. String Benchmarks
        benchmark_op("STRING SET", lambda i: db.set(f"bench:str:{i}", f"value_{i}"))
        benchmark_op("STRING GET", lambda i: db.get(f"bench:str:{i}"))
        benchmark_op("STRING INCR", lambda i: db.incr("bench:counter"))

        # 2. Hash Benchmarks
        benchmark_op("HASH HSET", lambda i: db.hset("bench:hash", f"field_{i}", f"val_{i}"))
        benchmark_op("HASH HGET", lambda i: db.hget("bench:hash", f"field_{i}"))
        benchmark_op("HASH HGETALL", lambda i: db.hgetall("bench:hash"))

        # 3. List Benchmarks
        benchmark_op("LIST LPUSH", lambda i: db.lpush("bench:list", f"item_{i}"))
        benchmark_op("LIST LRANGE 100", lambda i: db.lrange("bench:list", 0, 99))
        benchmark_op("LIST RPOP", lambda i: db.rpop("bench:list"))

        # 4. Set Benchmarks
        benchmark_op("SET SADD", lambda i: db.sadd("bench:set", f"member_{i}"))
        benchmark_op("SET SISMEMBER", lambda i: db.sismember("bench:set", f"member_{i}"))
        benchmark_op("SET SMEMBERS", lambda i: db.smembers("bench:set"))

        # 5. Sorted Set (ZSet) Benchmarks
        benchmark_op("ZSET ZADD", lambda i: db.zadd("bench:zset", {f"player_{i}": float(i)}))
        benchmark_op("ZSET ZRANGE", lambda i: db.zrange("bench:zset", 0, 50))

        # 6. TTL / Expiration Benchmarks
        benchmark_op("KEY EXPIRE", lambda i: db.expire(f"bench:str:{i}", 300))
        benchmark_op("KEY TTL", lambda i: db.ttl(f"bench:str:{i}"))

        # 7. Transaction MULTI/EXEC Benchmarks
        def tx_op(i):
            db.execute_command("MULTI")
            db.execute_command("SET", f"tx:{i}", "10")
            db.execute_command("INCR", f"tx:{i}")
            db.execute_command("EXEC")
        benchmark_op("TRANSACTION (3 cmd)", tx_op)

    finally:
        db.close()
        if db_path != ":memory:" and os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass

    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="RediLite Benchmark Suite")
    parser.add_argument("--iterations", "-n", type=int, default=1000, help="Number of ops per method (default: 1000)")
    parser.add_argument("--disk", action="store_true", help="Also benchmark disk persistence (.redilite file)")
    args = parser.parse_args()

    run_benchmark(":memory:", args.iterations)

    if args.disk:
        run_benchmark("benchmark_disk.redilite", args.iterations)


if __name__ == "__main__":
    main()
