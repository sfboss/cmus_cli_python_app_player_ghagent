"""Example plugin demonstrating the plugin API."""

from cmus_rich.core.cmus_interface import TrackInfo
from cmus_rich.plugins.api import Plugin


class ExamplePlugin(Plugin):
    """Example plugin that logs track changes."""

    def __init__(self, app):
        super().__init__(app)
        self.name = "example"
        self.version = "1.0.0"

    async def initialize(self):
        """Initialize the plugin."""
        print(f"[{self.name}] Plugin initialized")

    async def on_track_change(self, track: TrackInfo):
        """Called when track changes."""
        print(f"[{self.name}] Track changed to: {track.title} by {track.artist}")

    async def on_playback_start(self):
        """Called when playback starts."""
        print(f"[{self.name}] Playback started")

    async def on_playback_pause(self):
        """Called when playback pauses."""
        print(f"[{self.name}] Playback paused")

    async def on_playback_stop(self):
        """Called when playback stops."""
        print(f"[{self.name}] Playback stopped")

    async def cleanup(self):
        """Cleanup plugin resources."""
        print(f"[{self.name}] Plugin cleanup")
