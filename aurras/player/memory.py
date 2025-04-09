import gc
import logging
import tracemalloc
from functools import wraps
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Tuple

# Import settings
from ..core.settings import Settings

# Initialize logger
logger = logging.getLogger(__name__)

# Get settings
PLAYERSETTINGS = Settings()


@dataclass
class PlayerMemoryStats:
    """
    Memory usage statistics for player components.

    This class tracks memory usage across player components to help
    identify memory leaks and optimize performance.
    """

    start_time: float = field(default_factory=time.time)
    peak_memory_usage: float = 0.0
    collection_count: int = 0
    component_sizes: Dict[str, int] = field(default_factory=dict)
    last_gc_time: float = field(default_factory=time.time)
    gc_frequency_seconds: int = 300  # Run GC every 5 minutes by default

    def record_component_size(self, component_name: str, size_bytes: int) -> None:
        """Record memory used by a specific component."""
        self.component_sizes[component_name] = size_bytes

    def should_run_gc(self) -> bool:
        """Determine if garbage collection should run based on time and memory growth."""
        current_time = time.time()
        time_since_last_gc = current_time - self.last_gc_time
        return time_since_last_gc >= self.gc_frequency_seconds

    def record_gc_run(self) -> None:
        """Record that garbage collection was run."""
        self.last_gc_time = time.time()
        self.collection_count += 1

    def get_memory_report(self) -> Dict[str, Any]:
        """Get a complete memory usage report."""
        return {
            "uptime_seconds": time.time() - self.start_time,
            "peak_memory_mb": self.peak_memory_usage,
            "gc_runs": self.collection_count,
            "component_sizes": self.component_sizes,
            "last_gc_time": self.last_gc_time,
        }


def get_memory_setting(setting_name: str, default_value: str) -> str:
    """
    Safely get a memory-related setting with a fallback default.

    Args:
        setting_name: Name of the setting to retrieve
        default_value: Default value to return if setting is not found

    Returns:
        Setting value or default
    """
    try:
        # Try to get the setting using hyphenated format (from YAML)
        hyphenated_name = f"memory-{setting_name.replace('_', '-')}"
        if hasattr(PLAYERSETTINGS, hyphenated_name):
            return getattr(PLAYERSETTINGS, hyphenated_name)

        # Try with underscores (from direct attribute)
        underscored_name = f"memory_{setting_name}"
        if hasattr(PLAYERSETTINGS, underscored_name):
            return getattr(PLAYERSETTINGS, underscored_name)

        # If neither exists, return default
        return default_value
    except Exception as e:
        logger.debug(f"Error getting memory setting {setting_name}: {e}")
        return default_value


def optimize_memory_usage():
    """
    Decorator to optimize memory usage in a method.

    This decorator performs memory optimization tasks:
    1. Runs garbage collection before and after the method
    2. Limits the maximum size of caches and other collections
    3. Makes sure circular references are properly broken
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Run garbage collection before the method
            collected = gc.collect()
            logger.debug(f"Pre-method GC collected {collected} objects")

            # Check if we need to reset caches
            if hasattr(self, "_lyrics_cache") and len(self._lyrics_cache) > 5:
                self._lyrics_cache.clear()

            if hasattr(self, "_metadata_cache") and len(self._metadata_cache) > 10:
                self._metadata_cache.clear()

            # Execute the method
            result = func(self, *args, **kwargs)

            # Clean up any resolved futures
            if hasattr(self, "_active_futures"):
                # Remove done futures from tracking
                done_futures = set(f for f in self._active_futures if f.done())
                self._active_futures -= done_futures

            # Run garbage collection after the method
            collected = gc.collect()
            logger.debug(f"Post-method GC collected {collected} objects")

            return result

        return wrapper

    return decorator


def memory_stats_decorator(interval_seconds=60):
    """
    Decorator to periodically log memory usage statistics.

    Args:
        interval_seconds: How often to log memory stats (in seconds)

    Returns:
        The decorator function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start memory tracking if enabled (with safe default)
            enable_tracking = get_memory_setting("monitoring", "no") == "yes"

            try:
                # Import psutil here to avoid requiring it if not used
                import psutil

                process = psutil.Process()
            except ImportError:
                logger.debug(
                    "psutil not available, limited memory monitoring available"
                )
                process = None

            last_check_time = time.time()

            if enable_tracking and tracemalloc:
                # Start detailed memory tracking
                try:
                    tracemalloc.start()
                except RuntimeError:
                    # Handle case where tracemalloc is already started
                    pass

            # Get initial memory usage
            initial_memory = 0
            if process:
                initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

            # Define a function to log stats
            def log_memory_stats():
                nonlocal last_check_time

                current_time = time.time()
                # Only log at specified intervals
                if current_time - last_check_time < interval_seconds:
                    return

                last_check_time = current_time

                # Get current memory usage
                if process:
                    current_memory = process.memory_info().rss / (1024 * 1024)  # MB
                    memory_delta = current_memory - initial_memory

                    # Log basic memory stats
                    logger.info(
                        f"Memory usage: {current_memory:.2f} MB (Δ {memory_delta:+.2f} MB)"
                    )

                    # Log GC stats
                    gc_counts = gc.get_count()
                    logger.debug(f"GC state: {gc_counts} collections")

                    # Log tracemalloc stats if enabled
                    if enable_tracking and tracemalloc.is_tracing():
                        try:
                            snapshot = tracemalloc.take_snapshot()
                            top_stats = snapshot.statistics("lineno")

                            logger.debug("Top 5 memory consumers:")
                            for stat in top_stats[:5]:
                                logger.debug(
                                    f"{stat.count} objects: {stat.size / 1024:.1f} KB - {stat.traceback.format()[0]}"
                                )
                        except Exception as e:
                            logger.debug(f"Error getting tracemalloc stats: {e}")

                    # Force collection if memory usage grows significantly
                    gc_threshold = int(get_memory_setting("gc-threshold", "50"))
                    if (
                        memory_delta > gc_threshold
                    ):  # More than threshold MB growth (default 50MB)
                        logger.warning(
                            f"Memory growth detected: {memory_delta:.2f} MB - triggering garbage collection"
                        )
                        collected = gc.collect()
                        logger.info(f"Garbage collected {collected} objects")
                else:
                    # Without psutil, we can still log basic GC info
                    gc_counts = gc.get_count()
                    logger.debug(f"GC state: {gc_counts} collections")
                    collected = gc.collect()
                    logger.debug(f"Garbage collected {collected} objects")

            # Create a memory monitoring hook for the player
            args[0]._log_memory_stats = log_memory_stats

            try:
                # Call the original function
                return func(*args, **kwargs)
            finally:
                # Stop tracking when done
                if enable_tracking and tracemalloc.is_tracing():
                    try:
                        tracemalloc.stop()
                    except Exception as e:
                        logger.debug(f"Error stopping tracemalloc: {e}")

                # Log final stats
                if process:
                    final_memory = process.memory_info().rss / (1024 * 1024)
                    memory_delta = final_memory - initial_memory
                    logger.info(
                        f"Final memory usage: {final_memory:.2f} MB (Δ {memory_delta:+.2f} MB)"
                    )

        return wrapper

    return decorator
