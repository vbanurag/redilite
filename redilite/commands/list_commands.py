"""
List command implementations for LiteDis.
"""

from typing import Any
from .base import ICommand, CommandRegistry


class LPushCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 2:
            return Exception("ERR wrong number of arguments for 'lpush' command")
        return litedis.lpush(args[0], *args[1:])


class RPushCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 2:
            return Exception("ERR wrong number of arguments for 'rpush' command")
        return litedis.rpush(args[0], *args[1:])


class LPopCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if not args:
            return Exception("ERR wrong number of arguments for 'lpop' command")
        count = int(args[1]) if len(args) > 1 else 1
        return litedis.lpop(args[0], count=count)


class RPopCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if not args:
            return Exception("ERR wrong number of arguments for 'rpop' command")
        count = int(args[1]) if len(args) > 1 else 1
        return litedis.rpop(args[0], count=count)


class LRangeCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 3:
            return Exception("ERR wrong number of arguments for 'lrange' command")
        return litedis.lrange(args[0], int(args[1]), int(args[2]))


def register_list_commands(registry: CommandRegistry):
    registry.register("LPUSH", LPushCommand())
    registry.register("RPUSH", RPushCommand())
    registry.register("LPOP", LPopCommand())
    registry.register("RPOP", RPopCommand())
    registry.register("LRANGE", LRangeCommand())
