from collections import deque


class LRUCache:
    """
    Memory-efficient Least Recently Used (LRU) cache implementation.

    This cache maintains a fixed maximum size, automatically evicting
    the least recently used items when the cache reaches capacity.

    Attributes:
        max_size: Maximum number of items to store in the cache
    """

    def __init__(self, max_size: int = 10):
        """Initialize an empty LRU cache with specified maximum size."""
        self.max_size = max_size
        self._cache = {}
        self._access_order = deque()
        self._current_size = 0
        self._access_count = 0

    def __len__(self) -> int:
        """Return the number of items in the cache."""
        return len(self._cache)

    def get(self, key: str, default=None):
        """
        Get an item from the cache, returning default if not found.
        Updates item access time if found.
        """
        if key in self._cache:
            # Update access stats
            self._access_count += 1
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        return default

    def put(self, key: str, value):
        """
        Add an item to the cache, evicting least recently used items if needed.
        """
        # If key already exists, update value and move to most recently used
        if key in self._cache:
            self._cache[key] = value
            self._access_order.remove(key)
            self._access_order.append(key)
            return

        # Check if we need to evict items
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        # Add new item
        self._cache[key] = value
        self._access_order.append(key)
        self._current_size += 1

    def _evict_lru(self):
        """Evict the least recently used item from the cache."""
        if self._access_order:
            oldest_key = self._access_order.popleft()
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self._current_size -= 1

    def clear(self):
        """Clear all items from the cache."""
        self._cache.clear()
        self._access_order.clear()
        self._current_size = 0

    def get_stats(self) -> dict:
        """Return statistics about cache usage."""
        return {
            "size": self._current_size,
            "max_size": self.max_size,
            "access_count": self._access_count,
            "hit_rate": self._access_count / max(1, len(self._cache)),
        }
