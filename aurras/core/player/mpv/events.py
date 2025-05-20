"""
Event handling for MPV player property changes.

This module provides a weak-reference based property observer
system to prevent memory leaks in callback functions.
"""

import weakref

from aurras.utils.logger import get_logger

logger = get_logger("aurras.core.player.mpv.events", log_to_console=False)


class WeakPropertyObserver:
    """
    Weak reference-based property observer to prevent memory leaks.

    This class creates property observers that don't hold strong references
    to their parent objects, preventing memory leaks through circular references.
    """

    def __init__(self, instance, property_name, callback):
        """
        Create a weak reference observer.

        Args:
            instance: The MPV player instance
            property_name: Name of the property to observe
            callback: Callback function to call when property changes
        """
        self.instance_ref = weakref.ref(instance)
        self.property_name = property_name
        self.callback = callback
        self.registered = False

    def register(self):
        """Register the observer with the MPV instance."""
        instance = self.instance_ref()
        if instance is not None:
            instance.observe_property(self.property_name, self.callback)
            self.registered = True

    def unregister(self):
        """Unregister the observer from the MPV instance."""
        instance = self.instance_ref()
        if instance is not None and self.registered:
            try:
                instance.unobserve_property(self.property_name, self.callback)
                self.registered = False
            except Exception as e:
                logger.debug(f"Error unregistering observer: {e}")

    def __del__(self):
        """Automatically unregister when garbage collected."""
        self.unregister()


def create_property_observers(player):
    """
    Set up property observers for an MPV player using weak references.

    Args:
        player: The MPV player instance

    Returns:
        list: List of observer objects (keep reference to prevent GC)
    """
    observers = []

    pause_observer = WeakPropertyObserver(player, "pause", player._on_pause_change)
    pause_observer.register()
    observers.append(pause_observer)

    duration_observer = WeakPropertyObserver(
        player, "duration", player._on_duration_change
    )
    duration_observer.register()
    observers.append(duration_observer)

    metadata_observer = WeakPropertyObserver(
        player, "metadata", player._on_metadata_change
    )
    metadata_observer.register()
    observers.append(metadata_observer)

    playlist_observer = WeakPropertyObserver(
        player, "playlist-pos", player._on_playlist_pos_change
    )
    playlist_observer.register()
    observers.append(playlist_observer)

    return observers
