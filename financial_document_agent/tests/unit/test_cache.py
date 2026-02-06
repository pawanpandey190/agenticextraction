"""Unit tests for LLM cache."""

import threading
import time

import pytest

from financial_agent.services.cache import LLMCache, CacheStats


class TestLLMCache:
    """Tests for LLMCache."""

    def test_generate_key(self):
        """Test cache key generation."""
        image_bytes = b"test image data"
        model = "claude-sonnet-4-20250514"
        prompt = "Extract text from image"

        key1 = LLMCache.generate_key(image_bytes, model, prompt)
        key2 = LLMCache.generate_key(image_bytes, model, prompt)

        # Same inputs should produce same key
        assert key1 == key2
        # Key should be a hex string (64 chars for SHA-256)
        assert len(key1) == 64
        assert all(c in "0123456789abcdef" for c in key1)

    def test_generate_key_different_inputs(self):
        """Test that different inputs produce different keys."""
        image_bytes = b"test image data"
        model = "claude-sonnet-4-20250514"
        prompt = "Extract text from image"

        key1 = LLMCache.generate_key(image_bytes, model, prompt)
        key2 = LLMCache.generate_key(image_bytes + b"x", model, prompt)
        key3 = LLMCache.generate_key(image_bytes, model + "-v2", prompt)
        key4 = LLMCache.generate_key(image_bytes, model, prompt + " more")

        assert key1 != key2
        assert key1 != key3
        assert key1 != key4

    def test_set_and_get(self):
        """Test setting and getting cached values."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)
        key = "test_key"
        value = "extracted text"

        cache.set(key, value)
        result = cache.get(key)

        assert result == value

    def test_get_missing_key(self):
        """Test getting a non-existent key."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)

        result = cache.get("nonexistent_key")

        assert result is None

    def test_cache_expiration(self):
        """Test that cache entries expire after TTL."""
        cache = LLMCache(max_size=100, ttl_seconds=1)
        key = "test_key"
        value = "extracted text"

        cache.set(key, value)
        assert cache.get(key) == value

        # Wait for expiration
        time.sleep(1.1)

        result = cache.get(key)
        assert result is None

    def test_lru_eviction(self):
        """Test that oldest entries are evicted when cache is full."""
        cache = LLMCache(max_size=3, ttl_seconds=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.size == 3

        # Adding a fourth entry should evict the oldest (key1)
        cache.set("key4", "value4")

        assert cache.size == 3
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_access_order(self):
        """Test that accessing an entry updates its recency."""
        cache = LLMCache(max_size=3, ttl_seconds=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1, making it most recently used
        cache.get("key1")

        # Adding a new entry should evict key2 (now the oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still present
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_update_existing_key(self):
        """Test updating an existing cache entry."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)
        key = "test_key"

        cache.set(key, "value1")
        cache.set(key, "value2")

        result = cache.get(key)
        assert result == "value2"
        assert cache.size == 1

    def test_clear(self):
        """Test clearing the cache."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.size == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = LLMCache(max_size=100, ttl_seconds=1)

        cache.set("key1", "value1")
        time.sleep(0.5)
        cache.set("key2", "value2")

        # key1 should be expired, key2 should still be valid
        time.sleep(0.6)

        removed = cache.cleanup_expired()

        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_stats_hits_and_misses(self):
        """Test cache statistics for hits and misses."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)

        cache.set("key1", "value1")

        # Hit
        cache.get("key1")
        # Miss
        cache.get("nonexistent")

        assert cache.stats.hits == 1
        assert cache.stats.misses == 1
        assert cache.stats.hit_rate == 0.5

    def test_stats_evictions(self):
        """Test cache statistics for evictions."""
        cache = LLMCache(max_size=2, ttl_seconds=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Triggers eviction

        assert cache.stats.evictions == 1

    def test_thread_safety_concurrent_writes(self):
        """Test thread safety with concurrent writes."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)
        results = []
        errors = []

        def writer(key_prefix: str, count: int):
            try:
                for i in range(count):
                    cache.set(f"{key_prefix}_{i}", f"value_{i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=(f"t{i}", 50))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Cache should have entries (max 100)
        assert cache.size <= 100

    def test_thread_safety_concurrent_reads_writes(self):
        """Test thread safety with concurrent reads and writes."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)
        errors = []

        # Pre-populate cache
        for i in range(50):
            cache.set(f"key_{i}", f"value_{i}")

        def reader():
            try:
                for i in range(100):
                    cache.get(f"key_{i % 50}")
            except Exception as e:
                errors.append(e)

        def writer():
            try:
                for i in range(50):
                    cache.set(f"new_key_{i}", f"new_value_{i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=reader) for _ in range(3)
        ] + [
            threading.Thread(target=writer) for _ in range(2)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_len_method(self):
        """Test __len__ method."""
        cache = LLMCache(max_size=100, ttl_seconds=3600)

        assert len(cache) == 0

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert len(cache) == 2


class TestCacheStats:
    """Tests for CacheStats."""

    def test_default_values(self):
        """Test default values."""
        stats = CacheStats()

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0

    def test_hit_rate_empty(self):
        """Test hit rate when no requests made."""
        stats = CacheStats()

        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=75, misses=25, evictions=10)

        assert stats.hit_rate == 0.75
