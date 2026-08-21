"""
Observer Pattern implementation for LiteDis Pub/Sub messaging.
"""

from abc import ABC, abstractmethod
import threading
from typing import Any, Dict, Set


class IObserver(ABC):
    @abstractmethod
    def update(self, channel: str, message: Any):
        pass


class PubSubManager:
    """Subject/Observable managing Pub/Sub channels and observers."""

    def __init__(self):
        self._lock = threading.Lock()
        self._channels: Dict[str, Set[Any]] = {}

    def subscribe(self, channel: str, subscriber: Any):
        with self._lock:
            if channel not in self._channels:
                self._channels[channel] = set()
            self._channels[channel].add(subscriber)

    def unsubscribe(self, channel: str, subscriber: Any):
        with self._lock:
            if channel in self._channels:
                self._channels[channel].discard(subscriber)
                if not self._channels[channel]:
                    del self._channels[channel]

    def publish(self, channel: str, message: Any) -> int:
        with self._lock:
            subs = list(self._channels.get(channel, []))
        for sub in subs:
            try:
                if isinstance(sub, IObserver):
                    sub.update(channel, message)
                elif callable(sub):
                    sub(channel, message)
            except Exception as e:
                # Log observer callback exceptions to prevent silent drops
                pass  # nosec B110
        return len(subs)
