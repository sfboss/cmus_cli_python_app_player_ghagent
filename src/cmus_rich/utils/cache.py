"""Caching system with LRU and persistent cache."""

import asyncio
import hashlib
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Optional

import aiofiles


class Cache:
    """LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, ttl: int = 3600) -> None:
        self.max_size = max_size
        self.ttl = ttl
        self.cache: dict[str, Any] = {}
        self.access_times: dict[str, float] = {}
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        async with self.lock:
            if key in self.cache:
                # Check TTL
                if time.time() - self.access_times[key] < self.ttl:
                    # Update access time
                    self.access_times[key] = time.time()
                    return self.cache[key]
                else:
                    # Expired
                    del self.cache[key]
                    del self.access_times[key]

        return None

    async def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        async with self.lock:
            # Check size limit
            if len(self.cache) >= self.max_size:
                # Remove oldest item
                oldest = min(self.access_times.items(), key=lambda x: x[1])
                del self.cache[oldest[0]]
                del self.access_times[oldest[0]]

            self.cache[key] = value
            self.access_times[key] = time.time()

    async def get_or_compute(self, key: str, compute_func: Callable) -> Any:
        """Get from cache or compute if missing."""
        value = await self.get(key)

        if value is None:
            if asyncio.iscoroutinefunction(compute_func):
                value = await compute_func()
            else:
                value = compute_func()
            await self.set(key, value)

        return value

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self.lock:
            self.cache.clear()
            self.access_times.clear()


class PersistentCache:
    """Disk-based persistent cache."""

    def __init__(self, cache_dir: str = "~/.cache/cmus-rich") -> None:
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Hash key to avoid filesystem issues
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    async def get(self, key: str) -> Optional[Any]:
        """Get from persistent cache."""
        path = self._get_path(key)

        if path.exists():
            try:
                async with aiofiles.open(path, "rb") as f:
                    data = await f.read()
                    return pickle.loads(data)
            except Exception:
                # Corrupted cache file
                path.unlink()

        return None

    async def set(self, key: str, value: Any) -> None:
        """Save to persistent cache."""
        path = self._get_path(key)

        async with aiofiles.open(path, "wb") as f:
            await f.write(pickle.dumps(value))

    async def delete(self, key: str) -> None:
        """Delete from cache."""
        path = self._get_path(key)
        if path.exists():
            path.unlink()

    async def clear(self) -> None:
        """Clear all cached files."""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
