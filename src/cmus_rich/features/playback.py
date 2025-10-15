"""Advanced playback control features."""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cmus_rich.core.cmus_interface import CMUSInterface
from cmus_rich.core.state import AppState


class PlaybackMode(Enum):
    """Playback modes."""

    NORMAL = "normal"
    REPEAT_ONE = "repeat_one"
    REPEAT_ALL = "repeat_all"
    SHUFFLE = "shuffle"
    SMART_SHUFFLE = "smart_shuffle"


@dataclass
class PlaybackSettings:
    """Playback configuration."""

    mode: PlaybackMode = PlaybackMode.NORMAL
    crossfade: int = 0  # seconds
    gapless: bool = True
    replay_gain: bool = True
    replay_gain_mode: str = "album"  # album, track, auto
    speed: float = 1.0  # 0.5x - 2.0x


class PlaybackController:
    """Advanced playback control."""

    def __init__(self, cmus: CMUSInterface, state: AppState) -> None:
        self.cmus = cmus
        self.state = state
        self.settings = PlaybackSettings()
        self._fade_task: Optional[asyncio.Task] = None

    async def play_pause(self) -> None:
        """Toggle play/pause with smooth transition."""
        if self.state.player_status and self.state.player_status.status == "playing":
            await self._fade_out()
            await self.cmus.pause()
        else:
            await self.cmus.play()
            await self._fade_in()

    async def _fade_out(self) -> None:
        """Fade out volume."""
        if self.settings.crossfade > 0 and self.state.player_status:
            current_volume = self.state.player_status.volume
            steps = 10
            step_time = self.settings.crossfade / steps

            for i in range(steps):
                volume = int(current_volume * (1 - (i + 1) / steps))
                await self.cmus.set_volume(volume)
                await asyncio.sleep(step_time)

    async def _fade_in(self) -> None:
        """Fade in volume."""
        if self.settings.crossfade > 0 and self.state.player_status:
            target_volume = self.state.player_status.volume
            steps = 10
            step_time = self.settings.crossfade / steps

            for i in range(steps):
                volume = int(target_volume * ((i + 1) / steps))
                await self.cmus.set_volume(volume)
                await asyncio.sleep(step_time)

    async def skip_forward(self, seconds: int = 10) -> None:
        """Skip forward in track."""
        if self.state.player_status and self.state.player_status.track:
            current = self.state.player_status.track.position or 0
            await self.cmus.seek(current + seconds)

    async def skip_backward(self, seconds: int = 10) -> None:
        """Skip backward in track."""
        if self.state.player_status and self.state.player_status.track:
            current = self.state.player_status.track.position or 0
            await self.cmus.seek(max(0, current - seconds))

    async def next_track(self) -> None:
        """Skip to next track."""
        await self.cmus.next()

    async def previous_track(self) -> None:
        """Go to previous track."""
        await self.cmus.previous()

    async def stop(self) -> None:
        """Stop playback."""
        await self.cmus.stop()

    async def volume_up(self, step: int = 5) -> None:
        """Increase volume."""
        if self.state.player_status:
            new_volume = min(100, self.state.player_status.volume + step)
            await self.cmus.set_volume(new_volume)

    async def volume_down(self, step: int = 5) -> None:
        """Decrease volume."""
        if self.state.player_status:
            new_volume = max(0, self.state.player_status.volume - step)
            await self.cmus.set_volume(new_volume)
