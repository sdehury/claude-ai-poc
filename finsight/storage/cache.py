import os
import diskcache
from finsight.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_CACHE_DIR = "./cache"
DEFAULT_TTL = 86400  # 24 hours


class Cache:
    """File-based cache using diskcache."""

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR, ttl: int = DEFAULT_TTL):
        os.makedirs(cache_dir, exist_ok=True)
        self.cache = diskcache.Cache(cache_dir)
        self.ttl = ttl

    def get(self, key: str):
        """Get a value from cache. Returns None if not found or expired."""
        return self.cache.get(key)

    def set(self, key: str, value, ttl: int | None = None):
        """Set a value in cache with TTL."""
        self.cache.set(key, value, expire=ttl or self.ttl)

    def clear(self):
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cache cleared")

    def close(self):
        self.cache.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
