"""Tests for core application components."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cmus_rich.core.app import CMUSRichApp
from cmus_rich.core.cmus_interface import CMUSInterface, PlayerStatus, TrackInfo
from cmus_rich.core.events import Event, EventBus, EventType
from cmus_rich.core.state import AppState


@pytest.fixture
def mock_cmus() -> Mock:
    """Create a mock CMUS interface."""
    cmus = Mock(spec=CMUSInterface)
    cmus._connected = True
    cmus.get_status = AsyncMock(
        return_value=PlayerStatus(
            status="playing",
            track=TrackInfo(
                file="/test/track.mp3", artist="Test Artist", title="Test Track"
            ),
        )
    )
    cmus.connect = AsyncMock()
    cmus.disconnect = AsyncMock()
    cmus.play = AsyncMock()
    cmus.pause = AsyncMock()
    cmus.stop = AsyncMock()
    return cmus


class TestCMUSInterface:
    """Test CMUS interface."""

    def test_track_info_creation(self) -> None:
        """Test TrackInfo creation."""
        track = TrackInfo(
            file="/music/song.mp3", artist="Artist", album="Album", title="Title"
        )
        assert track.file == "/music/song.mp3"
        assert track.artist == "Artist"
        assert track.album == "Album"
        assert track.title == "Title"

    def test_player_status_creation(self) -> None:
        """Test PlayerStatus creation."""
        status = PlayerStatus(status="playing", volume=75)
        assert status.status == "playing"
        assert status.volume == 75
        assert status.track is None


class TestEventBus:
    """Test event bus functionality."""

    @pytest.mark.asyncio
    async def test_event_subscription(self) -> None:
        """Test event subscription and emission."""
        bus = EventBus()
        received_events = []

        async def handler(event: Event) -> None:
            received_events.append(event)

        bus.subscribe(EventType.TRACK_CHANGED, handler)

        event = Event(type=EventType.TRACK_CHANGED, data={"track": "test"})
        await bus.emit(event)

        # Process one event
        task = asyncio.create_task(bus.process_events())
        await asyncio.sleep(0.1)
        bus.stop_processing()
        task.cancel()

        assert len(received_events) == 1
        assert received_events[0].type == EventType.TRACK_CHANGED


class TestAppState:
    """Test application state."""

    @pytest.mark.asyncio
    async def test_state_update(self) -> None:
        """Test state updates."""
        state = AppState()
        assert state.active_view == "dashboard"

        await state.update(active_view="library")
        assert state.active_view == "library"

    @pytest.mark.asyncio
    async def test_state_save_load(self, tmp_path) -> None:
        """Test state persistence."""
        state = AppState()
        state.playlists = {"test": ["/music/track1.mp3", "/music/track2.mp3"]}

        state_file = tmp_path / "test_state.json"
        await state.save(str(state_file))

        # Load into new state
        new_state = AppState()
        await new_state.load(str(state_file))

        assert new_state.playlists == state.playlists


class TestCMUSRichApp:
    """Test main application."""

    @pytest.mark.asyncio
    async def test_app_initialization(self, tmp_path) -> None:
        """Test app initialization."""
        config_path = tmp_path / "config.toml"
        app = CMUSRichApp(config_path=str(config_path))

        with patch.object(app.cmus, "connect", new_callable=AsyncMock):
            await app.initialize()

        assert app.state is not None
        assert app.event_bus is not None
        assert app.cmus is not None
