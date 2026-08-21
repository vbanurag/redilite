"""
String command implementations for LiteDis.
"""

from typing import Any
from .base import ICommand, CommandRegistry


class SetCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 2:
            return Exception("ERR wrong number of arguments for 'set' command")
        key, val = args[0], args[1]
        ex = None
        if len(args) >= 4 and args[2].upper() == "EX":
            ex = float(args[3])
        litedis.set(key, val, ex=ex)
        return "OK"


class GetCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 1:
            return Exception("ERR wrong number of arguments for 'get' command")
        return litedis.get(args[0])


def register_string_commands(registry: CommandRegistry):
    registry.register("SET", SetCommand())
    registry.register("GET", GetCommand())
