from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Awaitable, Callable
from urllib.parse import urlsplit


@dataclass
class HTTPResponse:
    status_code: int
    json_body: dict


@dataclass
class CacheEntry:
    value: dict
    expires_at: float


Fetcher = Callable[[str, str, dict[str, str]], Awaitable[HTTPResponse]]


class HTTPCache:
    def __init__(self, ttl_seconds: float = 60.0, max_entries: int = 1024):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: dict[str, CacheEntry] = {}

    def _cache_key(self, method: str, url: str, headers: dict[str, str]) -> str:
        parsed = urlsplit(url)
        return f"{method.upper()}:{parsed.path}"

    async def get_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        fetcher: Fetcher,
    ) -> dict:
        if method.upper() != "GET":
            response = await fetcher(method, url, headers)
            return response.json_body

        now = time.monotonic()
        key = self._cache_key(method, url, headers)
        entry = self._entries.get(key)

        if entry is not None:
            if entry.expires_at <= now:
                return entry.value
            return entry.value

        response = await fetcher(method, url, headers)
        self._entries[key] = CacheEntry(
            value=response.json_body,
            expires_at=now + self.ttl_seconds,
        )
        return response.json_body
