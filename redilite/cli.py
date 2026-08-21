"""
Interactive CLI REPL and server launcher for RediLite.
"""

import argparse
import sys
import shlex
from typing import Any, List
from .core import RediLite
from .server import RediLiteServer


def format_result(res: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if res is None:
        return f"{pad}(nil)"
    elif isinstance(res, bool):
        return f"{pad}(boolean) {str(res).lower()}"
    elif isinstance(res, int):
        return f"{pad}(integer) {res}"
    elif isinstance(res, float):
        return f"{pad}(float) {res}"
    elif isinstance(res, str):
        return f'{pad}"{res}"'
    elif isinstance(res, Exception):
        return f"{pad}(error) {res}"
    elif isinstance(res, (list, tuple, set)):
        if not res:
            return f"{pad}(empty list or set)"
        lines = []
        for i, item in enumerate(res, 1):
            if isinstance(item, (list, tuple, set)):
                lines.append(f"{pad}{i})")
                lines.append(format_result(item, indent + 1))
            else:
                lines.append(f"{pad}{i}) {format_result(item)}")
        return "\n".join(lines)
    elif isinstance(res, dict):
        if not res:
            return f"{pad}(empty hash)"
        lines = []
        i = 1
        for k, v in res.items():
            lines.append(f"{pad}{i}) \"{k}\"")
            lines.append(f"{pad}{i+1}) \"{v}\"")
            i += 2
        return "\n".join(lines)
    return f"{pad}{res}"


def run_repl(db_path: str = ":memory:"):
    print(f"RediLite Interactive Shell (SQLite-style embedded Redis engine)")
    print(f"Database: '{db_path}'")
    print("Type 'HELP' or commands (e.g. SET foo bar, GET foo, HSET user name Alice). Type 'exit' or 'quit' to end.\n")

    db = RediLite(db_path)
    try:
        while True:
            try:
                line = input(f"redilite [{db_path}]> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not line:
                continue

            if line.lower() in ("exit", "quit"):
                print("Goodbye!")
                break

            if line.upper() == "HELP":
                print("\nSupported Commands:")
                print("  Generic:  EXISTS, DEL, TYPE, KEYS, EXPIRE, TTL, PERSIST, FLUSHDB")
                print("  Strings:  SET, GET, GETSET, MSET, MGET, INCR, DECR, APPEND, STRLEN")
                print("  Hashes:   HSET, HGET, HDEL, HEXISTS, HGETALL, HKEYS, HVALS, HLEN, HINCRBY")
                print("  Lists:    LPUSH, RPUSH, LPOP, RPOP, LRANGE, LLEN, LINDEX")
                print("  Sets:     SADD, SREM, SMEMBERS, SISMEMBER, SCARD, SUNION, SINTER, SDIFF")
                print("  ZSets:    ZADD, ZREM, ZRANGE, ZREVRANGE, ZSCORE, ZCARD")
                print("  Tx:       MULTI, EXEC, DISCARD")
                print("  Utility:  PING, ECHO, CLEAR\n")
                continue

            if line.upper() == "CLEAR":
                print("\033[H\033[J", end="")
                continue

            try:
                parts = shlex.split(line)
            except Exception as e:
                print(f"(error) Invalid syntax: {e}")
                continue

            cmd = parts[0]
            args = parts[1:]

            result = db.execute_command(cmd, *args)
            print(format_result(result))

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="RediLite - Embedded SQLite-style Redis Engine & RESP Server")
    subparsers = parser.add_subparsers(dest="subcommand")

    # REPL mode (default)
    repl_parser = subparsers.add_parser("cli", help="Start interactive CLI REPL")
    repl_parser.add_argument("db", nargs="?", default="mydb.redilite", help="Path to database file (default: mydb.redilite)")

    # Server mode
    server_parser = subparsers.add_parser("server", help="Start RESP TCP Server")
    server_parser.add_argument("--port", "-p", type=int, default=6379, help="TCP port (default: 6379)")
    server_parser.add_argument("--host", "-H", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    server_parser.add_argument("--db", "-d", default="mydb.redilite", help="Path to database file (default: mydb.redilite)")

    args, remaining = parser.parse_known_args()

    if args.subcommand == "server":
        print(f"Starting RediLite RESP Server on {args.host}:{args.port} using storage '{args.db}'...")
        srv = RediLiteServer(host=args.host, port=args.port, db_path=args.db)
        srv.run()
    else:
        db_path = args.db if hasattr(args, "db") and args.db else "mydb.redilite"
        if remaining and not args.subcommand:
            db_path = remaining[0]
        run_repl(db_path)


if __name__ == "__main__":
    main()
