# Quick Start Guide

Get up and running with CMUS Rich in minutes!

## Prerequisites

- Python 3.10 or higher
- CMUS installed on your system
- Terminal with Unicode support

## Installation

### Method 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/sfboss/cmus_cli_python_app_player_ghagent.git
cd cmus_cli_python_app_player_ghagent

# Run the installation script
chmod +x install.sh
./install.sh
```

### Method 2: Manual Install

```bash
# Clone and navigate
git clone https://github.com/sfboss/cmus_cli_python_app_player_ghagent.git
cd cmus_cli_python_app_player_ghagent

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## First Run

1. **Start CMUS** (if not already running):
   ```bash
   cmus
   ```

2. **In a new terminal, start CMUS Rich**:
   ```bash
   cmus-rich
   ```

3. **Or run as a Python module**:
   ```bash
   python -m cmus_rich
   ```

## Basic Usage

### Command Line Options

```bash
# Show version
cmus-rich --version

# Use custom config
cmus-rich -c /path/to/config.toml

# Enable debug mode
cmus-rich --debug

# Show help
cmus-rich --help
```

### Configuration

Configuration file is located at `~/.config/cmus-rich/config.toml`

Edit it to customize:
- Refresh rate
- Keybindings
- Library paths
- Plugins
- Logging level

Example configuration:
```toml
[general]
theme = "default"
single_instance = true

[ui]
refresh_rate = 0.1

[library]
paths = ["~/Music", "/media/music"]

[keybindings]
play_pause = "space"
next_track = "n"
previous_track = "p"
quit = "q"
```

## Key Features

### Library Scanning

Scan your music library:

```python
from cmus_rich.features.library import LibraryScanner

scanner = LibraryScanner()
await scanner.scan_directory("~/Music", recursive=True)
```

### Search

Search your library:

```python
from cmus_rich.features.search import SearchEngine, SearchQuery, SearchField

engine = SearchEngine()
query = SearchQuery(text="Beatles", field=SearchField.ARTIST)
results = await engine.search(query)
```

### Queue Management

Manage your playback queue:

```python
from cmus_rich.features.queue import QueueManager
from cmus_rich.core.state import AppState

state = AppState()
queue = QueueManager(state)

# Add tracks, shuffle, save playlists
await queue.add_track(track)
queue.smart_shuffle()
await queue.save_queue("my_playlist")
```

## Creating Plugins

Extend CMUS Rich with plugins:

1. Create a file in `plugins/` directory (e.g., `my_plugin.py`)

2. Define your plugin class:

```python
from cmus_rich.plugins.api import Plugin
from cmus_rich.core.cmus_interface import TrackInfo

class MyPlugin(Plugin):
    def __init__(self, app):
        super().__init__(app)
        self.name = "my_plugin"
        self.version = "1.0.0"
    
    async def initialize(self):
        print(f"[{self.name}] Initialized!")
    
    async def on_track_change(self, track: TrackInfo):
        print(f"Now playing: {track.title}")
```

3. Enable in config:

```toml
[plugins]
enabled = ["my_plugin"]
```

## Troubleshooting

### CMUS not connecting

1. Ensure CMUS is running: `pgrep cmus`
2. Check CMUS socket: `ls -la ~/.cmus/socket` or `/tmp/cmus-socket`
3. Try starting CMUS with: `cmus --listen /tmp/cmus-socket`

### Configuration not found

The default config is created on first run at `~/.config/cmus-rich/config.toml`

To recreate:
```bash
rm ~/.config/cmus-rich/config.toml
cmus-rich  # Will create new default config
```

### Library not showing

1. Configure library paths in config.toml
2. Run library scan (feature in development)
3. Check database: `~/.local/share/cmus-rich/library.db`

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# With coverage
pytest --cov=cmus_rich
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Getting Help

- Read the [full documentation](README.md)
- Check [contributing guidelines](CONTRIBUTING.md)
- Review the [changelog](CHANGELOG.md)
- Open an [issue](https://github.com/sfboss/cmus_cli_python_app_player_ghagent/issues)

## Next Steps

- Customize your configuration
- Create custom plugins
- Contribute to the project
- Report bugs or request features

Enjoy using CMUS Rich! 🎵
