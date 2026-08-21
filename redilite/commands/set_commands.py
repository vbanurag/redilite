"""
Set command implementations for LiteDis.
"""

from typing import Any
from .base import ICommand, CommandRegistry


class SAddCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 2:
            return Exception("ERR wrong number of arguments for 'sadd' command")
        return litedis.sadd(args[0], *args[1:])


class SMembersCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if not args:
            return Exception("ERR wrong number of arguments for 'smembers' command")
        return list(litedis.smembers(args[0]))


def register_set_commands(registry: CommandRegistry):
    registry.register("SADD", SAddCommand())
    registry.register("SMEMBERS", SMembersCommand())
