"""Event system for application-wide events."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class EventType(Enum):
    """Event types."""

    # Player events
    TRACK_CHANGED = "track_changed"
    PLAYBACK_STARTED = "playback_started"
    PLAYBACK_PAUSED = "playback_paused"
    PLAYBACK_STOPPED = "playback_stopped"
    VOLUME_CHANGED = "volume_changed"

    # Queue events
    QUEUE_UPDATED = "queue_updated"
    QUEUE_CLEARED = "queue_cleared"

    # Library events
    LIBRARY_SCANNED = "library_scanned"
    TRACK_ADDED = "track_added"
    TRACK_REMOVED = "track_removed"

    # UI events
    VIEW_CHANGED = "view_changed"
    SEARCH_PERFORMED = "search_performed"
    SELECTION_CHANGED = "selection_changed"

    # User events
    COMMAND_EXECUTED = "command_executed"
    KEYBIND_TRIGGERED = "keybind_triggered"


@dataclass
class Event:
    """Event container."""

    type: EventType
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None


class EventBus:
    """Central event bus for application-wide events."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[Callable]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._history: list[Event] = []
        self._history_size = 100
        self._processing = False

    def subscribe(self, event_type: EventType, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def emit(self, event: Event) -> None:
        """Emit an event."""
        # Add to history
        self._history.append(event)
        if len(self._history) > self._history_size:
            self._history.pop(0)

        # Add to processing queue
        await self._queue.put(event)

    async def process_events(self) -> None:
        """Process event queue."""
        self._processing = True
        while self._processing:
            event = await self._queue.get()

            # Call handlers
            handlers = self._handlers.get(event.type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    # Log error but don't stop processing
                    print(f"Event handler error: {e}")

    def stop_processing(self) -> None:
        """Stop processing events."""
        self._processing = False
