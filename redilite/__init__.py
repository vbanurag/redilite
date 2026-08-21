"""
RediLite - Embedded SQLite-like Key-Value & Data Structure Engine (Redis API).
"""

from .core import RediLite, LiteDis
from .server import RediLiteServer, LiteDisServer
from .storage import StorageEngine
from .pubsub import PubSubManager

__version__ = "1.0.0"


class DatabaseFactory:
    """Factory Pattern for instantiating RediLite database instances."""

    @staticmethod
    def connect(db_path: str = ":memory:") -> RediLite:
        """
        Creates and connects to a RediLite instance.
        Usage:
            db = redilite.connect("mydb.redilite")
        """
        return RediLite(db_path)


def connect(db_path: str = ":memory:") -> RediLite:
    """Convenience alias for DatabaseFactory.connect()"""
    return DatabaseFactory.connect(db_path)


__all__ = [
    "RediLite",
    "LiteDis",
    "RediLiteServer",
    "LiteDisServer",
    "StorageEngine",
    "PubSubManager",
    "DatabaseFactory",
    "connect",
]
