import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Awaitable, Callable


@dataclass
class _Entry:
    value: str
    expires_at: float


class InsightCache:
    def __init__(
        self, ttl_seconds: int = 300, max_entries: int = 128, max_concurrent: int = 2
    ):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: dict[str, _Entry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._request_limit = asyncio.Semaphore(max_concurrent)

    @staticmethod
    def _hash(data: dict) -> str:
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    async def get_or_create(
        self, scope: str, data: dict, create: Callable[[], Awaitable[str]]
    ) -> str:
        key = f"{scope}:{self._hash(data)}"
        lock = self._locks.setdefault(key, asyncio.Lock())
        try:
            async with lock:
                now = time.monotonic()
                entry = self._entries.get(key)
                if entry and entry.expires_at > now:
                    return entry.value

                async with self._request_limit:
                    value = await create()
                self._entries[key] = _Entry(value, time.monotonic() + self.ttl_seconds)
                return value
        finally:
            self._prune()

    def _prune(self) -> None:
        now = time.monotonic()
        self._entries = {
            key: entry for key, entry in self._entries.items() if entry.expires_at > now
        }
        if len(self._entries) > self.max_entries:
            oldest = sorted(self._entries, key=lambda key: self._entries[key].expires_at)
            for key in oldest[: len(self._entries) - self.max_entries]:
                del self._entries[key]
        active_keys = set(self._entries)
        self._locks = {
            key: lock
            for key, lock in self._locks.items()
            if key in active_keys or lock.locked() or any(
                not waiter.done() for waiter in (getattr(lock, "_waiters", ()) or ())
            )
        }

    def clear(self) -> None:
        self._entries.clear()
        self._locks.clear()


def _setting(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


insight_cache = InsightCache(
    ttl_seconds=_setting("ANALYTICS_INSIGHT_CACHE_TTL", 300),
    max_entries=_setting("ANALYTICS_INSIGHT_CACHE_MAX_ENTRIES", 128),
    max_concurrent=_setting("ANALYTICS_INSIGHT_MAX_CONCURRENT", 2),
)
