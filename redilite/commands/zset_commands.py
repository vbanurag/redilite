"""
Sorted Set (ZSet) command implementations for LiteDis.
"""

from typing import Any
from .base import ICommand, CommandRegistry


class ZAddCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 3:
            return Exception("ERR wrong number of arguments for 'zadd' command")
        key = args[0]
        mapping = {args[i+1]: float(args[i]) for i in range(1, len(args), 2)}
        return litedis.zadd(key, mapping)


class ZRangeCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 3:
            return Exception("ERR wrong number of arguments for 'zrange' command")
        key, start, stop = args[0], int(args[1]), int(args[2])
        withscores = len(args) > 3 and args[3].upper() == "WITHSCORES"
        return litedis.zrange(key, start, stop, withscores=withscores)


def register_zset_commands(registry: CommandRegistry):
    registry.register("ZADD", ZAddCommand())
    registry.register("ZRANGE", ZRangeCommand())
