"""
Command Pattern base interfaces and CommandRegistry for LiteDis.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class ICommand(ABC):
    @abstractmethod
    def execute(self, litedis: Any, *args: Any) -> Any:
        pass


class PingCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        return args[0] if args else "PONG"


class EchoCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        return args[0] if args else ""


class DelCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if not args:
            return Exception("ERR wrong number of arguments for 'del' command")
        return litedis.delete(*args)


class ExistsCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if not args:
            return Exception("ERR wrong number of arguments for 'exists' command")
        return 1 if litedis.exists(args[0]) else 0


class ExpireCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if len(args) < 2:
            return Exception("ERR wrong number of arguments for 'expire' command")
        return 1 if litedis.expire(args[0], float(args[1])) else 0


class TtlCommand(ICommand):
    def execute(self, litedis: Any, *args: Any) -> Any:
        if not args:
            return Exception("ERR wrong number of arguments for 'ttl' command")
        ttl_val = litedis.ttl(args[0])
        return int(ttl_val)


class CommandRegistry:
    """Registry Pattern holding all registered executable Redis command objects."""

    def __init__(self):
        self._commands: Dict[str, ICommand] = {}
        self._register_default_utility_commands()

    def register(self, name: str, cmd: ICommand):
        self._commands[name.upper()] = cmd

    def get_command(self, name: str) -> Optional[ICommand]:
        return self._commands.get(name.upper())

    def _register_default_utility_commands(self):
        self.register("PING", PingCommand())
        self.register("ECHO", EchoCommand())
        self.register("DEL", DelCommand())
        self.register("EXISTS", ExistsCommand())
        self.register("EXPIRE", ExpireCommand())
        self.register("TTL", TtlCommand())
