# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-15

### Added
- Initial release of CMUS Rich
- Core application architecture
  - Application controller with signal handling
  - CMUS interface layer for remote control
  - Event bus for reactive updates
  - State management with persistence
  - Configuration management with TOML support and hot reload
- Basic music features
  - Playback control with crossfade support
  - Queue management with smart shuffle
  - Library scanning with metadata extraction
  - Search engine with multiple field support
- UI components
  - Dashboard view with live updates
  - Now playing widget
  - Queue display
  - Progress bar with time display
- Utility modules
  - LRU cache with TTL
  - Persistent disk cache
  - Database helpers for SQLite
- Plugin system
  - Plugin API for extensions
  - Plugin manager for loading/unloading
  - Example plugin demonstrating the API
- Development tools
  - Comprehensive test suite with pytest
  - Installation script
  - Code formatting with Black
  - Linting with Ruff
  - Type checking with MyPy
- Documentation
  - Comprehensive README
  - Contributing guidelines
  - MIT License
  - Detailed specification in agents.md

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

## [Unreleased]

### Planned Features
- Full UI implementation with Rich TUI
- Advanced visualization (spectrum analyzer, waveforms)
- Lyrics integration with multiple providers
- Scrobbling support (Last.fm, ListenBrainz)
- Statistics tracking and analytics
- Smart recommendations
- Playlist management
- Keyboard shortcuts
- Custom themes
- Library watcher for automatic updates
- Discord Rich Presence
- MPRIS support
- Album art display

[0.1.0]: https://github.com/sfboss/cmus_cli_python_app_player_ghagent/releases/tag/v0.1.0
[Unreleased]: https://github.com/sfboss/cmus_cli_python_app_player_ghagent/compare/v0.1.0...HEAD
