"""
LiteDis Persistence Strategies subpackage.
"""

from .base import IStringStrategy, IHashStrategy, IListStrategy, ISetStrategy, IZSetStrategy
from .sqlite_strategies import (
    SQLiteStringStrategy,
    SQLiteHashStrategy,
    SQLiteListStrategy,
    SQLiteSetStrategy,
    SQLiteZSetStrategy,
)

__all__ = [
    "IStringStrategy",
    "IHashStrategy",
    "IListStrategy",
    "ISetStrategy",
    "IZSetStrategy",
    "SQLiteStringStrategy",
    "SQLiteHashStrategy",
    "SQLiteListStrategy",
    "SQLiteSetStrategy",
    "SQLiteZSetStrategy",
]
