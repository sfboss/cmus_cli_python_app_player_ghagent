"""Queue management features."""

import random
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from cmus_rich.core.cmus_interface import TrackInfo
from cmus_rich.core.state import AppState


@dataclass
class QueueItem:
    """Queue item with metadata."""

    track: TrackInfo
    added_by: str = "user"
    added_at: datetime = field(default_factory=datetime.now)
    priority: int = 0


class QueueManager:
    """Advanced queue management."""

    def __init__(self, state: AppState) -> None:
        self.state = state
        self.queue: list[QueueItem] = []
        self.history: deque = deque(maxlen=100)
        self.shuffle_history: deque = deque(maxlen=50)

    async def add_track(self, track: TrackInfo, position: Optional[int] = None) -> None:
        """Add track to queue."""
        item = QueueItem(track=track)

        if position is not None:
            self.queue.insert(position, item)
        else:
            self.queue.append(item)

        await self._update_state()

    async def remove_track(self, index: int) -> Optional[QueueItem]:
        """Remove track from queue."""
        if 0 <= index < len(self.queue):
            removed = self.queue.pop(index)
            await self._update_state()
            return removed
        return None

    async def move_track(self, from_idx: int, to_idx: int) -> None:
        """Move track in queue."""
        if 0 <= from_idx < len(self.queue) and 0 <= to_idx < len(self.queue):
            item = self.queue.pop(from_idx)
            self.queue.insert(to_idx, item)
            await self._update_state()

    async def clear_queue(self) -> None:
        """Clear entire queue."""
        self.queue.clear()
        await self._update_state()

    async def save_queue(self, name: str) -> None:
        """Save current queue as playlist."""
        tracks = [item.track.file for item in self.queue]
        self.state.playlists[name] = tracks
        await self.state.save()

    def smart_shuffle(self) -> None:
        """Shuffle avoiding recently played tracks."""
        # Separate into buckets
        recent = set(self.shuffle_history)
        available = [item for item in self.queue if item.track.file not in recent]
        recent_items = [item for item in self.queue if item.track.file in recent]

        # Shuffle available tracks
        random.shuffle(available)

        # Add recent tracks at the end
        self.queue = available + recent_items

    async def get_statistics(self) -> dict[str, Any]:
        """Get queue statistics."""
        total_duration = sum(
            item.track.duration for item in self.queue if item.track.duration
        )

        return {
            "total_tracks": len(self.queue),
            "total_duration": total_duration,
            "genres": self._count_genres(),
            "artists": self._count_artists(),
        }

    def _count_genres(self) -> dict[str, int]:
        """Count tracks by genre."""
        genres: dict[str, int] = {}
        for item in self.queue:
            if item.track.genre:
                genres[item.track.genre] = genres.get(item.track.genre, 0) + 1
        return genres

    def _count_artists(self) -> dict[str, int]:
        """Count tracks by artist."""
        artists: dict[str, int] = {}
        for item in self.queue:
            if item.track.artist:
                artists[item.track.artist] = artists.get(item.track.artist, 0) + 1
        return artists

    async def _update_state(self) -> None:
        """Update application state with current queue."""
        self.state.current_queue = [item.track for item in self.queue]
