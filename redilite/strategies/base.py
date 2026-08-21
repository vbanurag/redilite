"""
Strategy Pattern abstract interfaces for LiteDis persistence strategies.
"""

from abc import ABC, abstractmethod
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class IStringStrategy(ABC):
    @abstractmethod
    def set(self, conn: sqlite3.Connection, key: str, value: str, expire_seconds: Optional[float]) -> bool:
        pass

    @abstractmethod
    def get(self, conn: sqlite3.Connection, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def append(self, conn: sqlite3.Connection, key: str, value: str) -> int:
        pass

    @abstractmethod
    def incrby(self, conn: sqlite3.Connection, key: str, amount: int) -> int:
        pass


class IHashStrategy(ABC):
    @abstractmethod
    def hset(self, conn: sqlite3.Connection, key: str, field: str, value: str) -> int:
        pass

    @abstractmethod
    def hget(self, conn: sqlite3.Connection, key: str, field: str) -> Optional[str]:
        pass

    @abstractmethod
    def hdel(self, conn: sqlite3.Connection, key: str, *fields: str) -> int:
        pass

    @abstractmethod
    def hgetall(self, conn: sqlite3.Connection, key: str) -> Dict[str, str]:
        pass


class IListStrategy(ABC):
    @abstractmethod
    def push(self, conn: sqlite3.Connection, key: str, values: List[str], where: str) -> int:
        pass

    @abstractmethod
    def pop(self, conn: sqlite3.Connection, key: str, where: str, count: int) -> Union[Optional[str], List[str]]:
        pass

    @abstractmethod
    def range(self, conn: sqlite3.Connection, key: str, start: int, stop: int) -> List[str]:
        pass


class ISetStrategy(ABC):
    @abstractmethod
    def sadd(self, conn: sqlite3.Connection, key: str, *members: str) -> int:
        pass

    @abstractmethod
    def srem(self, conn: sqlite3.Connection, key: str, *members: str) -> int:
        pass

    @abstractmethod
    def smembers(self, conn: sqlite3.Connection, key: str) -> Set[str]:
        pass


class IZSetStrategy(ABC):
    @abstractmethod
    def zadd(self, conn: sqlite3.Connection, key: str, score_member_tuples: List[Tuple[float, str]]) -> int:
        pass

    @abstractmethod
    def zrem(self, conn: sqlite3.Connection, key: str, *members: str) -> int:
        pass

    @abstractmethod
    def zrange(self, conn: sqlite3.Connection, key: str, start: int, stop: int, with_scores: bool, reverse: bool) -> List[Any]:
        pass
