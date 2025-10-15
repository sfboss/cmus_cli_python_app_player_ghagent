"""Configuration management with hot reload."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import tomli_w


@dataclass
class Config:
    """Application configuration."""

    # General
    theme: str = "default"
    single_instance: bool = True
    auto_save: bool = True
    save_interval: int = 300

    # UI
    refresh_rate: float = 0.1
    show_album_art: bool = True
    show_visualizer: bool = True
    show_lyrics: bool = True
    layout: str = "default"

    # Playback
    crossfade: int = 0
    gapless: bool = True
    replay_gain: bool = True
    replay_gain_mode: str = "album"

    # Library
    library_paths: list[str] = field(default_factory=list)
    auto_scan: bool = True
    scan_interval: int = 3600
    watch_changes: bool = True

    # Keybindings
    keybindings: dict[str, str] = field(default_factory=dict)

    # Network
    timeout: int = 10
    retry_count: int = 3
    cache_size_mb: int = 50

    # Plugins
    enabled_plugins: list[str] = field(default_factory=list)

    # Logging
    log_level: str = "INFO"
    log_file: str = "~/.local/share/cmus-rich/app.log"


class ConfigManager:
    """Manage application configuration with hot reload."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = Path(
            config_path or "~/.config/cmus-rich/config.toml"
        ).expanduser()

        self.config = Config()
        self._watchers: list[Callable] = []
        self._last_modified: Optional[float] = None

        # Load configuration
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            # Create default config
            self._create_default_config()

        try:
            with open(self.config_path, "rb") as f:
                data = tomllib.load(f)

            # Update config object
            self._update_config(data)

            self._last_modified = self.config_path.stat().st_mtime

        except Exception as e:
            print(f"Failed to load config: {e}")

    def _update_config(self, data: dict[str, Any]) -> None:
        """Update config object from dictionary."""
        # General section
        general = data.get("general", {})
        self.config.theme = general.get("theme", self.config.theme)
        self.config.single_instance = general.get(
            "single_instance", self.config.single_instance
        )
        self.config.auto_save = general.get("auto_save", self.config.auto_save)
        self.config.save_interval = general.get("save_interval", self.config.save_interval)

        # UI section
        ui = data.get("ui", {})
        self.config.refresh_rate = ui.get("refresh_rate", self.config.refresh_rate)
        self.config.show_album_art = ui.get("show_album_art", self.config.show_album_art)
        self.config.show_visualizer = ui.get("show_visualizer", self.config.show_visualizer)
        self.config.show_lyrics = ui.get("show_lyrics", self.config.show_lyrics)
        self.config.layout = ui.get("layout", self.config.layout)

        # Playback section
        playback = data.get("playback", {})
        self.config.crossfade = playback.get("crossfade", self.config.crossfade)
        self.config.gapless = playback.get("gapless", self.config.gapless)
        self.config.replay_gain = playback.get("replay_gain", self.config.replay_gain)
        self.config.replay_gain_mode = playback.get(
            "replay_gain_mode", self.config.replay_gain_mode
        )

        # Library section
        library = data.get("library", {})
        self.config.library_paths = library.get("paths", [])
        self.config.auto_scan = library.get("auto_scan", self.config.auto_scan)
        self.config.scan_interval = library.get("scan_interval", self.config.scan_interval)
        self.config.watch_changes = library.get("watch_changes", self.config.watch_changes)

        # Keybindings
        self.config.keybindings = data.get("keybindings", {})

        # Network section
        network = data.get("network", {})
        self.config.timeout = network.get("timeout", self.config.timeout)
        self.config.retry_count = network.get("retry_count", self.config.retry_count)
        self.config.cache_size_mb = network.get("cache_size_mb", self.config.cache_size_mb)

        # Plugins section
        plugins = data.get("plugins", {})
        self.config.enabled_plugins = plugins.get("enabled", [])

        # Logging section
        logging = data.get("logging", {})
        self.config.log_level = logging.get("level", self.config.log_level)
        self.config.log_file = logging.get("file", self.config.log_file)

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            "general": {
                "theme": "default",
                "single_instance": True,
                "auto_save": True,
                "save_interval": 300,
            },
            "ui": {
                "refresh_rate": 0.1,
                "show_album_art": True,
                "show_visualizer": True,
                "show_lyrics": True,
                "layout": "default",
            },
            "playback": {
                "crossfade": 0,
                "gapless": True,
                "replay_gain": True,
                "replay_gain_mode": "album",
            },
            "library": {
                "paths": ["~/Music"],
                "auto_scan": True,
                "scan_interval": 3600,
                "watch_changes": True,
            },
            "keybindings": {
                "play_pause": "space",
                "next_track": "n",
                "previous_track": "p",
                "volume_up": "+",
                "volume_down": "-",
                "seek_forward": "l",
                "seek_backward": "h",
                "search": "/",
                "command_palette": "ctrl+p",
                "quit": "q",
                "move_up": "k",
                "move_down": "j",
            },
            "network": {
                "timeout": 10,
                "retry_count": 3,
                "cache_size_mb": 50,
            },
            "plugins": {
                "enabled": [],
            },
            "logging": {
                "level": "INFO",
                "file": "~/.local/share/cmus-rich/app.log",
            },
        }

        with open(self.config_path, "wb") as f:
            tomli_w.dump(default_config, f)

    async def watch_changes(self) -> None:
        """Watch for configuration file changes."""
        while True:
            await asyncio.sleep(1)

            if self.config_path.exists():
                mtime = self.config_path.stat().st_mtime
                if mtime != self._last_modified:
                    self.load()

                    # Notify watchers
                    for watcher in self._watchers:
                        await watcher(self.config)

    def add_watcher(self, watcher: Callable) -> None:
        """Add a config change watcher."""
        self._watchers.append(watcher)
