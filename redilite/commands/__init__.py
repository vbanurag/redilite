"""
LiteDis Commands subpackage.
"""

from .base import ICommand, CommandRegistry, PingCommand, EchoCommand, DelCommand, ExistsCommand, ExpireCommand, TtlCommand
from .string_commands import register_string_commands
from .hash_commands import register_hash_commands
from .list_commands import register_list_commands
from .set_commands import register_set_commands
from .zset_commands import register_zset_commands


def build_default_command_registry() -> CommandRegistry:
    registry = CommandRegistry()
    register_string_commands(registry)
    register_hash_commands(registry)
    register_list_commands(registry)
    register_set_commands(registry)
    register_zset_commands(registry)
    return registry


global_command_registry = build_default_command_registry()

__all__ = [
    "ICommand",
    "CommandRegistry",
    "global_command_registry",
    "build_default_command_registry",
]
