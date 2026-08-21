"""
Hash command implementations for LiteDis.
"""

from typing import Any
from .base import ICommand, CommandRegistry


class HSetCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 3:
            return Exception("ERR wrong number of arguments for 'hset' command")
        key = args[0]
        if len(args) == 3:
            return litedis.hset(key, args[1], args[2])
        mapping = {args[i]: args[i+1] for i in range(1, len(args), 2)}
        return litedis.hmset(key, mapping)


class HGetCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 2:
            return Exception("ERR wrong number of arguments for 'hget' command")
        return litedis.hget(args[0], args[1])


class HGetAllCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if not args:
            return Exception("ERR wrong number of arguments for 'hgetall' command")
        return litedis.hgetall(args[0])


def register_hash_commands(registry: CommandRegistry):
    registry.register("HSET", HSetCommand())
    registry.register("HGET", HGetCommand())
    registry.register("HGETALL", HGetAllCommand())
