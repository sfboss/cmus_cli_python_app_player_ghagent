# Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CMUS Rich                               │
│                    Terminal Music Player                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  cli.py: Command-line interface & argument parsing       │  │
│  │  __main__.py: Module entry point                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Application Core                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  app.py: Main application controller                     │  │
│  │  - Event loop management                                 │  │
│  │  - Signal handling                                       │  │
│  │  - Component coordination                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        ↓               ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Config     │ │    State     │ │   Events     │ │    CMUS      │
│  Manager     │ │  Manager     │ │     Bus      │ │  Interface   │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ • TOML load  │ │ • Global     │ │ • Pub/Sub    │ │ • Connection │
│ • Hot reload │ │   state      │ │ • Async      │ │ • Commands   │
│ • Defaults   │ │ • Persist    │ │ • History    │ │ • Parsing    │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Feature Layer                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  Playback    │ │    Queue     │ │   Library    │            │
│  │  Controller  │ │   Manager    │ │   Scanner    │            │
│  ├──────────────┤ ├──────────────┤ ├──────────────┤            │
│  │ • Play/Pause │ │ • Add/Remove │ │ • Scan dirs  │            │
│  │ • Crossfade  │ │ • Shuffle    │ │ • Metadata   │            │
│  │ • Volume     │ │ • Playlists  │ │ • Database   │            │
│  │ • Seek       │ │ • Stats      │ │ • Indexing   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Search Engine                         │  │
│  │  • Multi-field search                                    │  │
│  │  • Artist/Album browsing                                 │  │
│  │  • Case-sensitive/insensitive                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         UI Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Dashboard View                         │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐           │  │
│  │  │ Now Playing│ │   Queue    │ │  Progress  │           │  │
│  │  │   Widget   │ │   Display  │ │     Bar    │           │  │
│  │  └────────────┘ └────────────┘ └────────────┘           │  │
│  │                                                           │  │
│  │  Powered by Rich library for terminal rendering          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Plugin System                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Plugin Manager                          │  │
│  │  • Dynamic loading                                        │  │
│  │  • Event hooks                                            │  │
│  │  • Lifecycle management                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │   Plugin 1   │ │   Plugin 2   │ │   Plugin N   │           │
│  │              │ │              │ │              │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Utility Layer                               │
│  ┌──────────────┐ ┌──────────────┐                             │
│  │    Cache     │ │   Database   │                             │
│  │   System     │ │   Helpers    │                             │
│  ├──────────────┤ ├──────────────┤                             │
│  │ • LRU Cache  │ │ • SQLite     │                             │
│  │ • Persistent │ │ • Schema     │                             │
│  │ • Async-safe │ │ • Queries    │                             │
│  └──────────────┘ └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   External Systems                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │     CMUS     │ │  File System │ │   Database   │           │
│  │   (Music     │ │  (Music      │ │   (SQLite)   │           │
│  │   Player)    │ │   Files)     │ │              │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Playback Control Flow

```
User Input
    ↓
CLI/Keybinding
    ↓
PlaybackController.play_pause()
    ↓
CMUSInterface.execute_command()
    ↓
CMUS Remote (subprocess)
    ↓
CMUS Player
    ↓
Status Update
    ↓
EventBus.emit(PLAYBACK_STARTED)
    ↓
Plugins + UI Update
```

### Library Scan Flow

```
LibraryScanner.scan_directory()
    ↓
Walk directory tree
    ↓
For each music file:
    ↓
Mutagen.File() → Extract metadata
    ↓
Calculate file hash
    ↓
DatabaseHelper.execute() → Store in SQLite
    ↓
Cache.set() → Cache track info
    ↓
EventBus.emit(TRACK_ADDED)
```

### Search Flow

```
SearchEngine.search(query)
    ↓
Build SQL query based on search field
    ↓
DatabaseHelper.execute(sql, params)
    ↓
Convert rows to TrackInfo objects
    ↓
Return results to UI
    ↓
Dashboard updates display
```

## Component Interactions

### Application Startup Sequence

1. **CLI Layer**: Parse arguments
2. **App Controller**: Initialize
   - Load configuration
   - Create state manager
   - Initialize event bus
   - Connect to CMUS
3. **Plugin Manager**: Load plugins
4. **State Manager**: Load saved state
5. **Event Loop**: Start background tasks
   - Update loop (poll CMUS status)
   - Event processing loop
   - Config watcher (optional)
6. **UI**: Render dashboard

### Event Processing

```
CMUS Status Update
    ↓
app._update_loop()
    ↓
cmus.get_status()
    ↓
state.update_player_status()
    ↓
Check for track change
    ↓
event_bus.emit(TRACK_CHANGED)
    ↓
Handlers execute:
    - UI updates
    - Plugin notifications
    - State save (if auto-save)
```

## Plugin Architecture

### Plugin Lifecycle

```
Application Start
    ↓
PluginManager.load_plugins()
    ↓
For each plugin file:
    ↓
Import module
    ↓
Find Plugin subclass
    ↓
Instantiate with app reference
    ↓
plugin.initialize()
    ↓
Register in plugin registry
    ↓
[Normal Operation - Event Hooks Called]
    ↓
Application Shutdown
    ↓
plugin.cleanup()
    ↓
Unload plugin
```

### Plugin Event Hooks

- `on_track_change(track)`: Track changed
- `on_playback_start()`: Playback started
- `on_playback_pause()`: Playback paused
- `on_playback_stop()`: Playback stopped

## State Management

### State Structure

```
AppState
├── player_status: PlayerStatus
│   ├── status: str (playing/paused/stopped)
│   ├── track: TrackInfo
│   ├── volume: int
│   ├── repeat: bool
│   └── shuffle: bool
├── current_queue: List[TrackInfo]
├── playlists: Dict[str, List[str]]
├── play_history: List[Dict]
├── statistics: Dict
└── library_cache: Dict[str, TrackInfo]
```

### State Persistence

State is saved to `~/.config/cmus-rich/state.json`:
- Playlists
- Play history (last 1000)
- Statistics
- UI state

## Configuration

### Config File Structure

```toml
[general]
theme = "default"
single_instance = true
auto_save = true

[ui]
refresh_rate = 0.1
show_album_art = false

[playback]
crossfade = 0
gapless = true

[library]
paths = ["~/Music"]
auto_scan = false

[keybindings]
play_pause = "space"
next_track = "n"

[plugins]
enabled = []

[logging]
level = "INFO"
```

## Database Schema

### Tracks Table

```sql
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY,
    file_path TEXT UNIQUE,
    file_hash TEXT,
    title TEXT,
    artist TEXT,
    album TEXT,
    genre TEXT,
    year INTEGER,
    duration INTEGER,
    track_number INTEGER,
    disc_number INTEGER,
    album_artist TEXT,
    last_modified REAL,
    play_count INTEGER DEFAULT 0,
    skip_count INTEGER DEFAULT 0,
    rating INTEGER,
    last_played REAL,
    added_date REAL
)
```

### Indexes

- `idx_artist` on artist
- `idx_album` on album
- `idx_genre` on genre

## Threading Model

CMUS Rich uses asyncio for concurrency:

- **Main Thread**: Event loop
- **Background Tasks**:
  - Status update loop (polls CMUS)
  - Event processing loop
  - Config file watcher
  - Plugin tasks

All I/O operations are async to prevent blocking.

## Error Handling

Errors are handled at multiple levels:

1. **Application Level**: Graceful shutdown on fatal errors
2. **Component Level**: Try/catch with error logging
3. **Event Level**: Isolated event handler errors don't crash app
4. **Plugin Level**: Plugin errors don't affect core functionality
