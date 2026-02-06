"""Thread-safe LRU cache with TTL for LLM responses."""

import hashlib
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CacheEntry:
    """A single cache entry with value and expiration time."""

    value: str
    expires_at: float


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LLMCache:
    """Thread-safe LRU cache with TTL for LLM responses.

    Uses SHA-256 hashing for cache keys derived from image bytes, model, and prompt.
    """

    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600,
    ) -> None:
        """Initialize the LLM cache.

        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._stats = CacheStats()

    @staticmethod
    def generate_key(
        image_bytes: bytes,
        model: str,
        prompt: str,
    ) -> str:
        """Generate a cache key from image bytes, model, and prompt.

        Args:
            image_bytes: Raw image bytes
            model: LLM model name
            prompt: Prompt used for extraction

        Returns:
            SHA-256 hash as hex string
        """
        hasher = hashlib.sha256()
        hasher.update(image_bytes)
        hasher.update(model.encode("utf-8"))
        hasher.update(prompt.encode("utf-8"))
        return hasher.hexdigest()

    def get(self, key: str) -> str | None:
        """Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return None

            # Check if expired
            if time.time() > entry.expires_at:
                # Remove expired entry
                del self._cache[key]
                self._stats.misses += 1
                logger.debug("Cache entry expired", key=key[:16])
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._stats.hits += 1
            logger.debug("Cache hit", key=key[:16])
            return entry.value

    def set(self, key: str, value: str) -> None:
        """Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # If key exists, update and move to end
            if key in self._cache:
                self._cache[key] = CacheEntry(
                    value=value,
                    expires_at=time.time() + self.ttl_seconds,
                )
                self._cache.move_to_end(key)
                return

            # Evict oldest entries if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.evictions += 1
                logger.debug("Cache eviction (LRU)", evicted_key=oldest_key[:16])

            # Add new entry
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=time.time() + self.ttl_seconds,
            )
            logger.debug("Cache set", key=key[:16])

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of entries removed
        """
        removed = 0
        current_time = time.time()

        with self._lock:
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if current_time > entry.expires_at
            ]
            for key in expired_keys:
                del self._cache[key]
                removed += 1

        if removed > 0:
            logger.debug("Expired entries cleaned up", count=removed)

        return removed

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats

    @property
    def size(self) -> int:
        """Get current number of entries in cache."""
        with self._lock:
            return len(self._cache)

    def __len__(self) -> int:
        """Return the number of entries in the cache."""
        return self.size
