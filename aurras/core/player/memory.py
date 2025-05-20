"""
Memory Management Module

This module provides tools for monitoring and optimizing memory usage within the
application. It includes decorators for tracking memory consumption, automated
garbage collection, and caching strategies to prevent memory leaks.
"""

import gc
import time
import tracemalloc
from functools import wraps
from typing import Dict, Any
from dataclasses import dataclass, field

from aurras.utils.logger import get_logger

logger = get_logger("aurras.core.player.memory", log_to_console=False)


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
        """Determine if garbage collection should run based on time."""
        current_time = time.time()
        time_since_last_gc = current_time - self.last_gc_time
        return time_since_last_gc >= self.gc_frequency_seconds

    def record_gc_run(self) -> None:
        """Record that garbage collection was run."""
        self.last_gc_time = time.time()
        self.collection_count += 1

    def get_memory_report(self) -> Dict[str, Any]:
        """
        Generate a complete memory usage report.
        
        Returns:
            Dictionary containing memory statistics including uptime,
            peak memory usage, garbage collection runs, and component sizes.
        """
        return {
            "uptime_seconds": time.time() - self.start_time,
            "peak_memory_mb": self.peak_memory_usage,
            "gc_runs": self.collection_count,
            "component_sizes": self.component_sizes,
            "last_gc_time": self.last_gc_time,
        }


# Memory settings constant
MEMORY_GC_THRESHOLD_MB = 50  # Trigger GC after 50MB growth


def optimize_memory_usage():
    """
    Decorator to optimize memory usage in a method.
    
    This decorator performs memory optimization tasks:
    1. Runs garbage collection before and after the method
    2. Limits the maximum size of caches and other collections
    3. Ensures circular references are properly broken
    
    Returns:
        Decorator function that wraps methods with memory optimization
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Run garbage collection before the method
            collected = gc.collect()
            logger.debug(f"Pre-method GC collected {collected} objects")

            # Reset caches when they grow too large
            if hasattr(self, "_lyrics_cache") and len(self._lyrics_cache) > 5:
                self._lyrics_cache.clear()

            if hasattr(self, "_metadata_cache") and len(self._metadata_cache) > 10:
                self._metadata_cache.clear()

            result = func(self, *args, **kwargs)

            if hasattr(self, "_active_futures"):
                # Remove done futures from tracking
                done_futures = [f for f in self._active_futures if f.done()]

                if hasattr(self._active_futures, "difference_update"):
                    self._active_futures.difference_update(done_futures)
                elif hasattr(self._active_futures, "remove"):
                    for future in done_futures:
                        try:
                            self._active_futures.remove(future)
                        except (ValueError, KeyError):
                            pass
                else:
                    logger.warning(
                        f"Unsupported _active_futures type: {type(self._active_futures)}"
                    )

            # Run garbage collection after the method
            collected = gc.collect()
            logger.debug(f"Post-method GC collected {collected} objects")

            return result

        return wrapper

    return decorator


def memory_stats_decorator(interval_seconds=60):
    """
    Decorator to periodically log memory usage statistics.
    
    Memory monitoring is always enabled. This decorator will track memory usage,
    log statistics at regular intervals, and trigger garbage collection when
    memory growth exceeds the threshold.

    Args:
        interval_seconds: How often to log memory stats (in seconds)

    Returns:
        Decorator function that wraps methods with memory monitoring
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                import psutil
                process = psutil.Process()
            except ImportError:
                logger.debug("psutil not available, limited memory monitoring available")
                process = None

            last_check_time = time.time()

            # Start detailed memory tracking with tracemalloc
            if tracemalloc:
                try:
                    tracemalloc.start()
                except RuntimeError:
                    pass

            # Get initial memory usage
            initial_memory = 0
            if process:
                initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

            def log_memory_stats():
                nonlocal last_check_time

                current_time = time.time()
                if current_time - last_check_time < interval_seconds:
                    return

                last_check_time = current_time

                # Get current memory usage
                if process:
                    current_memory = process.memory_info().rss / (1024 * 1024)  # MB
                    memory_delta = current_memory - initial_memory

                    logger.info(
                        f"Memory usage: {current_memory:.2f} MB (Δ {memory_delta:+.2f} MB)"
                    )

                    gc_counts = gc.get_count()
                    logger.debug(f"GC state: {gc_counts} collections")

                    # Log tracemalloc stats if available
                    if tracemalloc.is_tracing():
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
                    gc_threshold = MEMORY_GC_THRESHOLD_MB
                    if memory_delta > gc_threshold:
                        logger.warning(
                            f"Memory growth detected: {memory_delta:.2f} MB - triggering garbage collection"
                        )
                        collected = gc.collect()
                        logger.info(f"Garbage collected {collected} objects")
                else:
                    gc_counts = gc.get_count()
                    logger.debug(f"GC state: {gc_counts} collections")
                    collected = gc.collect()
                    logger.debug(f"Garbage collected {collected} objects")

            # Create a memory monitoring hook for the player
            args[0]._log_memory_stats = log_memory_stats

            try:
                return func(*args, **kwargs)
            finally:
                if tracemalloc.is_tracing():
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
