"""Plugin API base classes."""

from typing import Any, Callable, Optional

from cmus_rich.core.cmus_interface import TrackInfo


class Plugin:
    """Base class for plugins."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self.name = "unnamed"
        self.version = "1.0.0"
        self.enabled = True

    async def initialize(self) -> None:
        """Initialize plugin."""
        pass

    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass

    async def on_track_change(self, track: TrackInfo) -> None:
        """Called when track changes."""
        pass

    async def on_playback_start(self) -> None:
        """Called when playback starts."""
        pass

    async def on_playback_pause(self) -> None:
        """Called when playback pauses."""
        pass

    async def on_playback_stop(self) -> None:
        """Called when playback stops."""
        pass

    def register_command(self, name: str, handler: Callable) -> None:
        """Register a command."""
        if hasattr(self.app, "commands"):
            self.app.commands[name] = handler

    def register_keybinding(self, key: str, handler: Callable) -> None:
        """Register a keybinding."""
        if hasattr(self.app, "keybindings"):
            self.app.keybindings[key] = handler
