# CMUS Rich - Modern Terminal Music Player

A modern, feature-rich terminal music player that wraps CMUS, providing an intuitive and powerful interface while maintaining the efficiency and reliability of the underlying player.

## Features

- **Modern TUI**: Beautiful terminal interface built with Rich
- **CMUS Integration**: Seamlessly wraps and controls CMUS
- **Advanced Playback**: Crossfade, replay gain, gapless playback
- **Smart Queue**: Intelligent queue management with smart shuffle
- **Event System**: Reactive architecture with event-driven updates
- **Configuration**: TOML-based configuration with hot reload
- **Extensible**: Plugin system for custom functionality

## Requirements

- Python 3.10 or higher
- CMUS (C* Music Player)
- Terminal with Unicode support

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/sfboss/cmus_cli_python_app_player_ghagent.git
cd cmus_cli_python_app_player_ghagent

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest
```

## Usage

### Basic Usage

```bash
# Start CMUS Rich
cmus-rich

# With custom config
cmus-rich -c /path/to/config.toml

# Debug mode
cmus-rich --debug
```

### Configuration

Configuration file is located at `~/.config/cmus-rich/config.toml`. A default configuration will be created on first run.

Example configuration:

```toml
[general]
theme = "default"
single_instance = true

[ui]
refresh_rate = 0.1
show_visualizer = true

[keybindings]
play_pause = "space"
next_track = "n"
previous_track = "p"
quit = "q"
```

## Project Structure

```
cmus-rich/
├── src/cmus_rich/          # Main package
│   ├── core/               # Core application components
│   │   ├── app.py          # Main application controller
│   │   ├── cmus_interface.py  # CMUS communication
│   │   ├── config.py       # Configuration management
│   │   ├── events.py       # Event system
│   │   └── state.py        # State management
│   ├── features/           # Feature modules
│   │   ├── playback.py     # Playback control
│   │   └── queue.py        # Queue management
│   ├── ui/                 # UI components
│   ├── plugins/            # Plugin system
│   ├── utils/              # Utility modules
│   ├── cli.py              # CLI entry point
│   └── __main__.py         # Module entry point
├── tests/                  # Test suite
├── config/                 # Default configurations
├── themes/                 # Custom themes
└── plugins/                # External plugins
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cmus_rich --cov-report=html

# Run specific test file
pytest tests/test_core.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Architecture

CMUS Rich is built with a modular architecture:

- **Core Layer**: Application controller, CMUS interface, state management, events
- **Feature Layer**: Playback control, queue management, library scanning, etc.
- **UI Layer**: Dashboard, menus, layouts, themes
- **Plugin Layer**: Extensible plugin system

## Roadmap

- [x] Core architecture
- [x] CMUS interface layer
- [x] Configuration management
- [x] Event system
- [x] State management
- [x] Basic playback control
- [x] Queue management
- [ ] Full UI implementation
- [ ] Library scanner
- [ ] Search engine
- [ ] Visualization
- [ ] Lyrics integration
- [ ] Scrobbling support
- [ ] Statistics tracking
- [ ] Plugin system

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- CMUS - The underlying music player
- Rich - For the beautiful terminal interface
- All contributors and users
