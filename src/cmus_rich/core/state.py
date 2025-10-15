"""Global application state management."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import aiofiles

from cmus_rich.core.cmus_interface import PlayerStatus, TrackInfo


@dataclass
class AppState:
    """Global application state."""

    # Player state
    player_status: Optional[PlayerStatus] = None
    current_queue: list[TrackInfo] = field(default_factory=list)

    # UI state
    active_view: str = "dashboard"
    selected_items: list[Any] = field(default_factory=list)
    search_query: str = ""

    # User data
    playlists: dict[str, list[str]] = field(default_factory=dict)
    play_history: list[dict] = field(default_factory=list)
    statistics: dict[str, Any] = field(default_factory=dict)

    # Cache
    library_cache: dict[str, TrackInfo] = field(default_factory=dict)
    album_art_cache: dict[str, str] = field(default_factory=dict)

    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _observers: list[Callable] = field(default_factory=list)

    def subscribe(self, callback: Callable) -> None:
        """Subscribe to state changes."""
        self._observers.append(callback)

    async def update(self, **kwargs: Any) -> None:
        """Update state and notify observers."""
        async with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)

            # Notify observers
            for observer in self._observers:
                await observer(self, kwargs.keys())

    def update_player_status(self, status: PlayerStatus) -> None:
        """Update player status (sync version for convenience)."""
        self.player_status = status

    async def save(self, path: Optional[str] = None) -> None:
        """Persist state to disk."""
        if path is None:
            path = "~/.config/cmus-rich/state.json"

        state_path = Path(path).expanduser()
        state_path.parent.mkdir(parents=True, exist_ok=True)

        state_dict = {
            "playlists": self.playlists,
            "play_history": self.play_history[-1000:],  # Keep last 1000
            "statistics": self.statistics,
            "ui_state": {
                "active_view": self.active_view,
                "search_query": self.search_query,
            },
        }

        async with aiofiles.open(state_path, "w") as f:
            await f.write(json.dumps(state_dict, indent=2))

    async def load(self, path: Optional[str] = None) -> None:
        """Load state from disk."""
        if path is None:
            path = "~/.config/cmus-rich/state.json"

        state_path = Path(path).expanduser()

        try:
            async with aiofiles.open(state_path, "r") as f:
                state_dict = json.loads(await f.read())

            self.playlists = state_dict.get("playlists", {})
            self.play_history = state_dict.get("play_history", [])
            self.statistics = state_dict.get("statistics", {})

            ui_state = state_dict.get("ui_state", {})
            self.active_view = ui_state.get("active_view", "dashboard")
            self.search_query = ui_state.get("search_query", "")

        except FileNotFoundError:
            pass  # First run, use defaults
