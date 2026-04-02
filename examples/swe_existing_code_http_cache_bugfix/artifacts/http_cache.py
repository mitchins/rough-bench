from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Awaitable, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit


@dataclass
class HTTPResponse:
    status_code: int
    json_body: dict


@dataclass
class CacheEntry:
    value: dict
    expires_at: float
    stored_at: float


Fetcher = Callable[[str, str, dict[str, str]], Awaitable[HTTPResponse]]


class HTTPCache:
    def __init__(self, ttl_seconds: float = 60.0, max_entries: int = 1024):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: dict[str, CacheEntry] = {}

    def _cache_key(self, method: str, url: str, headers: dict[str, str]) -> str:
        parsed = urlsplit(url)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        canonical_query = urlencode(sorted(query_pairs))
        return f"{method.upper()}:{parsed.path}?{canonical_query}"

    def _has_user_specific_context(self, headers: dict[str, str]) -> bool:
        lowered = {key.casefold(): value for key, value in headers.items()}
        return "authorization" in lowered or "cookie" in lowered

    def _evict_expired(self, now: float) -> None:
        expired_keys = [
            key for key, entry in self._entries.items() if entry.expires_at <= now
        ]
        for key in expired_keys:
            self._entries.pop(key, None)

    def _trim_to_capacity(self) -> None:
        while len(self._entries) > self.max_entries:
            oldest_key = min(
                self._entries,
                key=lambda key: self._entries[key].stored_at,
            )
            self._entries.pop(oldest_key, None)

    async def get_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        fetcher: Fetcher,
    ) -> dict:
        if method.upper() != "GET" or self._has_user_specific_context(headers):
            response = await fetcher(method, url, headers)
            return response.json_body

        now = time.monotonic()
        self._evict_expired(now)
        key = self._cache_key(method, url, headers)
        entry = self._entries.get(key)

        if entry is not None:
            return entry.value

        response = await fetcher(method, url, headers)
        if response.status_code == 200:
            self._entries[key] = CacheEntry(
                value=response.json_body,
                expires_at=now + self.ttl_seconds,
                stored_at=now,
            )
            self._trim_to_capacity()
        return response.json_body
