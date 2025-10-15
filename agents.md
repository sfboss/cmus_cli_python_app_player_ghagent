# CMUS CLI Wrapper - Comprehensive Agent Implementation Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Core Architecture](#core-architecture)
3. [UI/UX Components](#uiux-components)
4. [Music Player Features](#music-player-features)
5. [Technical Implementation](#technical-implementation)
6. [Developer Experience](#developer-experience)
7. [Configuration System](#configuration-system)
8. [Error Handling](#error-handling)
9. [Platform Support](#platform-support)
10. [Performance Optimization](#performance-optimization)
11. [Security](#security)
12. [Appendices](#appendices)

## Project Overview

### Mission Statement
Build a modern, feature-rich terminal music player that wraps CMUS, providing an intuitive and powerful interface while maintaining the efficiency and reliability of the underlying player.

### Technology Stack
- **Language**: Python 3.10+
- **Primary UI Framework**: Rich (rich>=13.0.0)
- **Async Runtime**: asyncio
- **Database**: SQLite3
- **Configuration**: TOML (tomli, tomli-w)
- **IPC**: Unix domain sockets / Named pipes
- **Testing**: pytest, pytest-asyncio, pytest-mock

### Project Structure
```
cmus-rich/
├── src/
│   ├── cmus_rich/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── app.py              # Main application class
│   │   │   ├── config.py           # Configuration management
│   │   │   ├── state.py            # Global state management
│   │   │   ├── events.py           # Event system
│   │   │   └── cmus_interface.py   # CMUS communication layer
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py        # Main dashboard view
│   │   │   ├── layouts.py          # Layout manager
│   │   │   ├── components/         # Reusable UI components
│   │   │   ├── themes.py           # Theme system
│   │   │   └── widgets/            # Custom Rich widgets
│   │   ├── features/
│   │   │   ├── __init__.py
│   │   │   ├── playback.py         # Playback control
│   │   │   ├── queue.py            # Queue management
│   │   │   ├── playlists.py        # Playlist operations
│   │   │   ├── library.py          # Library management
│   │   │   ├── search.py           # Search & filtering
│   │   │   ├── visualization.py    # Audio visualizations
│   │   │   ├── lyrics.py           # Lyrics integration
│   │   │   ├── scrobbling.py       # Scrobbling services
│   │   │   ├── statistics.py       # Analytics & stats
│   │   │   └── recommendations.py  # Recommendation engine
│   │   ├── plugins/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py          # Plugin manager
│   │   │   └── api.py              # Plugin API
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── audio.py            # Audio processing utilities
│   │   │   ├── cache.py            # Caching system
│   │   │   ├── db.py               # Database helpers
│   │   │   └── network.py          # Network utilities
│   │   └── cli.py                  # CLI entry point
├── tests/
├── plugins/                         # External plugins
├── themes/                          # Custom themes
├── config/                          # Default configurations
└── docs/
```

## Core Architecture

### 1. Application Core (`core/app.py`)

```python
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from rich.console import Console
from rich.layout import Layout
import signal
import sys

@dataclass
class AppConfig:
    """Application configuration"""
    refresh_rate: float = 0.1  # 10 FPS minimum
    debug_mode: bool = False
    single_instance: bool = True
    cache_size_mb: int = 50
    thread_pool_size: int = 4
    
class CMUSRichApp:
    """Main application controller"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.console = Console()
        self.config = self._load_config(config_path)
        self.state = AppState()
        self.event_bus = EventBus()
        self.cmus = CMUSInterface()
        self.ui_manager = UIManager(self.console)
        self.plugin_manager = PluginManager()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
    async def initialize(self):
        """Initialize all application components"""
        # Check single instance
        if self.config.single_instance:
            await self._ensure_single_instance()
            
        # Initialize CMUS connection
        await self.cmus.connect()
        
        # Load plugins
        await self.plugin_manager.load_plugins()
        
        # Initialize UI
        await self.ui_manager.initialize()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Load saved state
        await self.state.load()
        
    async def run(self):
        """Main application loop"""
        self._running = True
        
        try:
            # Start background tasks
            self._tasks.append(
                asyncio.create_task(self._update_loop())
            )
            self._tasks.append(
                asyncio.create_task(self._event_loop())
            )
            
            # Run UI
            await self.ui_manager.run()
            
        finally:
            await self.shutdown()
            
    async def _update_loop(self):
        """Background update loop for live data"""
        while self._running:
            try:
                # Update player status
                status = await self.cmus.get_status()
                self.state.update_player_status(status)
                
                # Update UI components
                await self.ui_manager.update()
                
                # Sleep for refresh interval
                await asyncio.sleep(self.config.refresh_rate)
                
            except Exception as e:
                self._handle_error(e)
                
    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self._signal_handler)
            
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        asyncio.create_task(self.shutdown())
        
    async def shutdown(self):
        """Graceful shutdown"""
        self._running = False
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
            
        # Save state
        await self.state.save()
        
        # Cleanup
        await self.cmus.disconnect()
        await self.plugin_manager.unload_plugins()
```

### 2. CMUS Interface Layer (`core/cmus_interface.py`)

```python
import asyncio
import subprocess
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re
import socket

@dataclass
class TrackInfo:
    """Track information container"""
    file: str
    artist: Optional[str] = None
    album: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[int] = None
    position: Optional[int] = None
    date: Optional[str] = None
    genre: Optional[str] = None
    
@dataclass
class PlayerStatus:
    """Player status information"""
    status: str  # playing, paused, stopped
    track: Optional[TrackInfo] = None
    volume: int = 100
    repeat: bool = False
    shuffle: bool = False
    
class CMUSInterface:
    """CMUS remote control interface"""
    
    def __init__(self):
        self._socket_path = None
        self._process = None
        self._connected = False
        
    async def connect(self):
        """Connect to CMUS instance"""
        # Try to connect to existing instance
        socket_path = self._find_socket()
        
        if socket_path:
            self._socket_path = socket_path
            self._connected = True
        else:
            # Start new CMUS instance
            await self._start_cmus()
            
    async def _start_cmus(self):
        """Start CMUS process"""
        self._process = await asyncio.create_subprocess_exec(
            'cmus',
            '--listen', '/tmp/cmus-socket',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for socket to be available
        for _ in range(10):
            await asyncio.sleep(0.5)
            if self._find_socket():
                self._connected = True
                return
                
        raise ConnectionError("Failed to start CMUS")
        
    def _find_socket(self) -> Optional[str]:
        """Find CMUS socket path"""
        # Check common locations
        paths = [
            '/tmp/cmus-socket',
            f'{os.environ.get("HOME")}/.cmus/socket',
            f'{os.environ.get("XDG_RUNTIME_DIR")}/cmus-socket'
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
                
        return None
        
    async def execute_command(self, command: str) -> str:
        """Execute CMUS remote command"""
        if not self._connected:
            raise ConnectionError("Not connected to CMUS")
            
        proc = await asyncio.create_subprocess_exec(
            'cmus-remote',
            *command.split(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"CMUS command failed: {stderr.decode()}")
            
        return stdout.decode()
        
    async def get_status(self) -> PlayerStatus:
        """Get current player status"""
        output = await self.execute_command('-Q')
        return self._parse_status(output)
        
    def _parse_status(self, output: str) -> PlayerStatus:
        """Parse CMUS status output"""
        lines = output.strip().split('\n')
        status = PlayerStatus(status='stopped')
        track_info = {}
        
        for line in lines:
            if line.startswith('status '):
                status.status = line.split()[1]
            elif line.startswith('file '):
                track_info['file'] = line[5:]
            elif line.startswith('tag '):
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    tag_name = parts[1]
                    tag_value = parts[2]
                    track_info[tag_name.lower()] = tag_value
            elif line.startswith('duration '):
                track_info['duration'] = int(line.split()[1])
            elif line.startswith('position '):
                track_info['position'] = int(line.split()[1])
                
        if track_info.get('file'):
            status.track = TrackInfo(**track_info)
            
        return status
        
    # Playback control methods
    async def play(self):
        await self.execute_command('-p')
        
    async def pause(self):
        await self.execute_command('-u')
        
    async def stop(self):
        await self.execute_command('-s')
        
    async def next(self):
        await self.execute_command('-n')
        
    async def previous(self):
        await self.execute_command('-r')
        
    async def seek(self, position: int):
        await self.execute_command(f'-k {position}')
        
    async def set_volume(self, volume: int):
        await self.execute_command(f'-v {volume}%')
```

### 3. State Management (`core/state.py`)

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import asyncio
import json
import aiofiles
from datetime import datetime

@dataclass
class AppState:
    """Global application state"""
    
    # Player state
    player_status: Optional[PlayerStatus] = None
    current_queue: List[TrackInfo] = field(default_factory=list)
    
    # UI state
    active_view: str = "dashboard"
    selected_items: List[Any] = field(default_factory=list)
    search_query: str = ""
    
    # User data
    playlists: Dict[str, List[str]] = field(default_factory=dict)
    play_history: List[Dict] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    # Cache
    library_cache: Dict[str, TrackInfo] = field(default_factory=dict)
    album_art_cache: Dict[str, str] = field(default_factory=dict)
    
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _observers: List[Callable] = field(default_factory=list)
    
    def subscribe(self, callback: Callable):
        """Subscribe to state changes"""
        self._observers.append(callback)
        
    async def update(self, **kwargs):
        """Update state and notify observers"""
        async with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    
            # Notify observers
            for observer in self._observers:
                await observer(self, kwargs.keys())
                
    async def save(self, path: str = "~/.config/cmus-rich/state.json"):
        """Persist state to disk"""
        state_dict = {
            'playlists': self.playlists,
            'play_history': self.play_history[-1000:],  # Keep last 1000
            'statistics': self.statistics,
            'ui_state': {
                'active_view': self.active_view,
                'search_query': self.search_query
            }
        }
        
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(state_dict, indent=2))
            
    async def load(self, path: str = "~/.config/cmus-rich/state.json"):
        """Load state from disk"""
        try:
            async with aiofiles.open(path, 'r') as f:
                state_dict = json.loads(await f.read())
                
            self.playlists = state_dict.get('playlists', {})
            self.play_history = state_dict.get('play_history', [])
            self.statistics = state_dict.get('statistics', {})
            
            ui_state = state_dict.get('ui_state', {})
            self.active_view = ui_state.get('active_view', 'dashboard')
            self.search_query = ui_state.get('search_query', '')
            
        except FileNotFoundError:
            pass  # First run
```

### 4. Event System (`core/events.py`)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List
import asyncio
from datetime import datetime

class EventType(Enum):
    # Player events
    TRACK_CHANGED = "track_changed"
    PLAYBACK_STARTED = "playback_started"
    PLAYBACK_PAUSED = "playback_paused"
    PLAYBACK_STOPPED = "playback_stopped"
    VOLUME_CHANGED = "volume_changed"
    
    # Queue events
    QUEUE_UPDATED = "queue_updated"
    QUEUE_CLEARED = "queue_cleared"
    
    # Library events
    LIBRARY_SCANNED = "library_scanned"
    TRACK_ADDED = "track_added"
    TRACK_REMOVED = "track_removed"
    
    # UI events
    VIEW_CHANGED = "view_changed"
    SEARCH_PERFORMED = "search_performed"
    SELECTION_CHANGED = "selection_changed"
    
    # User events
    COMMAND_EXECUTED = "command_executed"
    KEYBIND_TRIGGERED = "keybind_triggered"
    
@dataclass
class Event:
    """Event container"""
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
class EventBus:
    """Central event bus for application-wide events"""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._history: List[Event] = []
        self._history_size = 100
        
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            
    async def emit(self, event: Event):
        """Emit an event"""
        # Add to history
        self._history.append(event)
        if len(self._history) > self._history_size:
            self._history.pop(0)
            
        # Add to processing queue
        await self._queue.put(event)
        
    async def process_events(self):
        """Process event queue"""
        while True:
            event = await self._queue.get()
            
            # Call handlers
            handlers = self._handlers.get(event.type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    # Log error but don't stop processing
                    print(f"Event handler error: {e}")
```

## UI/UX Components

### 1. Dashboard View (`ui/dashboard.py`)

```python
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TimeRemainingColumn
from rich.console import Group
from rich.align import Align
from rich.text import Text
from typing import Optional
import asyncio

class DashboardView:
    """Main dashboard with live updates"""
    
    def __init__(self, console: Console, state: AppState):
        self.console = console
        self.state = state
        self.layout = self._create_layout()
        self._widgets = {}
        self._init_widgets()
        
    def _create_layout(self) -> Layout:
        """Create dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="sidebar", ratio=1),
            Layout(name="content", ratio=3),
            Layout(name="info", ratio=1)
        )
        
        return layout
        
    def _init_widgets(self):
        """Initialize dashboard widgets"""
        # Now playing widget
        self._widgets['now_playing'] = NowPlayingWidget(self.state)
        
        # Progress bar
        self._widgets['progress'] = ProgressWidget(self.state)
        
        # Spectrum analyzer
        self._widgets['spectrum'] = SpectrumAnalyzer()
        
        # Queue view
        self._widgets['queue'] = QueueWidget(self.state)
        
        # Library browser
        self._widgets['library'] = LibraryBrowser(self.state)
        
    async def render(self):
        """Render dashboard"""
        # Update header
        self.layout["header"].update(
            self._widgets['now_playing'].render()
        )
        
        # Update main content
        self.layout["content"].update(
            self._widgets['library'].render()
        )
        
        # Update sidebar
        self.layout["sidebar"].update(
            Panel(
                self._widgets['queue'].render(),
                title="Queue",
                border_style="blue"
            )
        )
        
        # Update info panel
        self.layout["info"].update(
            Panel(
                Group(
                    self._widgets['spectrum'].render(),
                    self._render_stats()
                ),
                title="Info",
                border_style="green"
            )
        )
        
        # Update footer
        self.layout["footer"].update(
            self._widgets['progress'].render()
        )
        
        self.console.print(self.layout)
        
    def _render_stats(self) -> Table:
        """Render playback statistics"""
        table = Table(show_header=False, box=None)
        
        if self.state.player_status:
            status = self.state.player_status
            table.add_row("Status:", status.status.capitalize())
            table.add_row("Volume:", f"{status.volume}%")
            table.add_row("Repeat:", "✓" if status.repeat else "✗")
            table.add_row("Shuffle:", "✓" if status.shuffle else "✗")
            
        return table

class NowPlayingWidget:
    """Now playing information widget"""
    
    def __init__(self, state: AppState):
        self.state = state
        
    def render(self) -> Panel:
        """Render now playing info"""
        if not self.state.player_status or not self.state.player_status.track:
            return Panel(
                Align.center("No track playing", vertical="middle"),
                style="dim"
            )
            
        track = self.state.player_status.track
        
        # Create fancy display
        content = Group(
            Text(track.title or "Unknown Title", style="bold cyan", justify="center"),
            Text(f"by {track.artist or 'Unknown Artist'}", style="yellow", justify="center"),
            Text(f"from {track.album or 'Unknown Album'}", style="blue", justify="center")
        )
        
        return Panel(
            Align.center(content, vertical="middle"),
            title="♪ Now Playing ♪",
            border_style="cyan"
        )

class ProgressWidget:
    """Playback progress bar widget"""
    
    def __init__(self, state: AppState):
        self.state = state
        
    def render(self) -> Panel:
        """Render progress bar"""
        if not self.state.player_status or not self.state.player_status.track:
            return Panel("━" * 50, style="dim")
            
        track = self.state.player_status.track
        
        if track.duration and track.position is not None:
            progress = track.position / track.duration
            filled = int(50 * progress)
            bar = "█" * filled + "━" * (50 - filled)
            
            time_str = f"{self._format_time(track.position)} / {self._format_time(track.duration)}"
            
            return Panel(
                Group(
                    Text(bar, style="cyan"),
                    Text(time_str, justify="center", style="dim")
                ),
                box=None
            )
            
        return Panel("━" * 50, style="dim")
        
    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format seconds to MM:SS"""
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

class SpectrumAnalyzer:
    """ASCII spectrum analyzer widget"""
    
    def __init__(self, bands: int = 16):
        self.bands = bands
        self.history = []
        self.max_history = 5
        
    def render(self) -> Text:
        """Render spectrum analyzer"""
        # Simulated spectrum data (replace with actual audio analysis)
        import random
        spectrum = [random.random() for _ in range(self.bands)]
        
        # Add to history for smoothing
        self.history.append(spectrum)
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
        # Average with history for smoothing
        if self.history:
            averaged = []
            for i in range(self.bands):
                avg = sum(h[i] for h in self.history) / len(self.history)
                averaged.append(avg)
            spectrum = averaged
            
        # Create visualization
        bars = []
        bar_chars = " ▁▂▃▄▅▆▇█"
        
        for value in spectrum:
            height = int(value * (len(bar_chars) - 1))
            bars.append(bar_chars[height] * 2)
            
        return Text("".join(bars), style="cyan")
```

### 2. Interactive Menu System (`ui/menu.py`)

```python
from typing import List, Optional, Callable, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.text import Text
import asyncio

class MenuItem:
    """Menu item definition"""
    
    def __init__(
        self,
        label: str,
        action: Optional[Callable] = None,
        submenu: Optional['Menu'] = None,
        keybind: Optional[str] = None,
        description: Optional[str] = None
    ):
        self.label = label
        self.action = action
        self.submenu = submenu
        self.keybind = keybind
        self.description = description

class Menu:
    """Interactive menu with vim-like navigation"""
    
    def __init__(self, title: str, items: List[MenuItem]):
        self.title = title
        self.items = items
        self.selected_index = 0
        self.search_query = ""
        self.filtered_items = items
        
    def move_up(self):
        """Move selection up"""
        if self.selected_index > 0:
            self.selected_index -= 1
            
    def move_down(self):
        """Move selection down"""
        if self.selected_index < len(self.filtered_items) - 1:
            self.selected_index += 1
            
    def filter_items(self, query: str):
        """Filter items with fuzzy search"""
        self.search_query = query
        
        if not query:
            self.filtered_items = self.items
        else:
            # Fuzzy matching
            self.filtered_items = [
                item for item in self.items
                if self._fuzzy_match(query.lower(), item.label.lower())
            ]
            
        self.selected_index = 0
        
    def _fuzzy_match(self, query: str, text: str) -> bool:
        """Simple fuzzy matching algorithm"""
        query_idx = 0
        
        for char in text:
            if query_idx < len(query) and char == query[query_idx]:
                query_idx += 1
                
        return query_idx == len(query)
        
    def render(self) -> Table:
        """Render menu as table"""
        table = Table(title=self.title, show_header=False)
        
        for i, item in enumerate(self.filtered_items):
            # Build row content
            label = Text(item.label)
            
            if item.keybind:
                label.append(f" [{item.keybind}]", style="dim")
                
            if item.submenu:
                label.append(" ▶", style="blue")
                
            # Highlight selected
            style = "bold cyan" if i == self.selected_index else ""
            
            table.add_row(label, style=style)
            
        return table

class CommandPalette:
    """VS Code style command palette"""
    
    def __init__(self, commands: Dict[str, Callable]):
        self.commands = commands
        self.history = []
        self.search_query = ""
        self.filtered_commands = []
        self.selected_index = 0
        
    def search(self, query: str):
        """Search commands"""
        self.search_query = query
        
        if not query:
            # Show recent commands
            self.filtered_commands = self.history[-10:]
        else:
            # Fuzzy search
            results = []
            for name, func in self.commands.items():
                score = self._calculate_score(query.lower(), name.lower())
                if score > 0:
                    results.append((score, name, func))
                    
            # Sort by score
            results.sort(reverse=True)
            self.filtered_commands = [(name, func) for _, name, func in results[:20]]
            
        self.selected_index = 0
        
    def _calculate_score(self, query: str, text: str) -> float:
        """Calculate fuzzy match score"""
        if query in text:
            return 2.0  # Exact substring match
            
        score = 0.0
        query_idx = 0
        consecutive = 0
        
        for i, char in enumerate(text):
            if query_idx < len(query) and char == query[query_idx]:
                score += 1.0
                
                # Bonus for consecutive matches
                consecutive += 1
                score += consecutive * 0.1
                
                # Bonus for matching at word boundary
                if i == 0 or text[i-1] in ' -_':
                    score += 0.5
                    
                query_idx += 1
            else:
                consecutive = 0
                
        # Only return score if all query chars matched
        return score if query_idx == len(query) else 0.0
        
    def execute_selected(self):
        """Execute selected command"""
        if self.filtered_commands and self.selected_index < len(self.filtered_commands):
            name, func = self.filtered_commands[self.selected_index]
            
            # Add to history
            self.history.append((name, func))
            
            # Execute
            return func()
```

### 3. Multi-pane Layout System (`ui/layouts.py`)

```python
from rich.layout import Layout
from rich.console import Console
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class PaneType(Enum):
    LIBRARY = "library"
    PLAYLIST = "playlist"
    QUEUE = "queue"
    LYRICS = "lyrics"
    VISUALIZER = "visualizer"
    SEARCH = "search"
    INFO = "info"

@dataclass
class PaneConfig:
    """Configuration for a pane"""
    type: PaneType
    title: str
    ratio: float = 1.0
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    visible: bool = True

class LayoutManager:
    """Manages multi-pane layouts with dynamic resizing"""
    
    def __init__(self, console: Console):
        self.console = console
        self.layouts = self._define_layouts()
        self.current_layout = "default"
        self.panes: Dict[str, Pane] = {}
        self.focused_pane = None
        
    def _define_layouts(self) -> Dict[str, List[PaneConfig]]:
        """Define available layouts"""
        return {
            "default": [
                PaneConfig(PaneType.LIBRARY, "Library", ratio=2),
                PaneConfig(PaneType.QUEUE, "Queue", ratio=1),
                PaneConfig(PaneType.INFO, "Info", ratio=1)
            ],
            "focused": [
                PaneConfig(PaneType.LIBRARY, "Library", ratio=3),
                PaneConfig(PaneType.INFO, "Info", ratio=1)
            ],
            "visualization": [
                PaneConfig(PaneType.VISUALIZER, "Visualizer", ratio=2),
                PaneConfig(PaneType.LYRICS, "Lyrics", ratio=1),
                PaneConfig(PaneType.QUEUE, "Queue", ratio=1)
            ],
            "search": [
                PaneConfig(PaneType.SEARCH, "Search", ratio=3),
                PaneConfig(PaneType.INFO, "Info", ratio=1)
            ]
        }
        
    def build_layout(self) -> Layout:
        """Build current layout"""
        layout = Layout()
        
        # Get current layout config
        config = self.layouts[self.current_layout]
        
        # Create layout structure
        if len(config) == 1:
            # Single pane
            layout.update(self._create_pane(config[0]))
        elif len(config) == 2:
            # Two panes
            layout.split_row(
                Layout(self._create_pane(config[0]), ratio=config[0].ratio),
                Layout(self._create_pane(config[1]), ratio=config[1].ratio)
            )
        else:
            # Three or more panes - create nested splits
            layout.split_row(
                Layout(self._create_pane(config[0]), ratio=config[0].ratio),
                Layout(name="right")
            )
            
            right = layout["right"]
            right.split_column(
                *[Layout(self._create_pane(c), ratio=c.ratio) for c in config[1:]]
            )
            
        return layout
        
    def _create_pane(self, config: PaneConfig):
        """Create pane from config"""
        if config.type not in self.panes:
            self.panes[config.type] = Pane(config)
            
        return self.panes[config.type].render()
        
    def switch_layout(self, layout_name: str):
        """Switch to different layout"""
        if layout_name in self.layouts:
            self.current_layout = layout_name
            
    def focus_pane(self, pane_type: PaneType):
        """Focus on specific pane"""
        self.focused_pane = pane_type
        
        # Update pane borders to show focus
        for ptype, pane in self.panes.items():
            pane.focused = (ptype == pane_type)

class Pane:
    """Individual pane in layout"""
    
    def __init__(self, config: PaneConfig):
        self.config = config
        self.content = None
        self.focused = False
        
    def render(self):
        """Render pane content"""
        from rich.panel import Panel
        
        border_style = "cyan" if self.focused else "dim"
        
        return Panel(
            self.content or "Empty",
            title=self.config.title,
            border_style=border_style
        )

### 4. Theme System (`ui/themes.py`)

```python
from dataclasses import dataclass
from typing import Dict, Optional
from rich.style import Style
from rich.theme import Theme
import toml

@dataclass
class ThemeConfig:
    """Theme configuration"""
    name: str
    primary: str = "cyan"
    secondary: str = "blue"
    accent: str = "yellow"
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"
    background: Optional[str] = None
    foreground: Optional[str] = None
    
    # Component specific
    header_style: str = "bold cyan"
    border_style: str = "dim"
    selected_style: str = "reverse"
    playing_style: str = "bold green"
    paused_style: str = "bold yellow"
    
class ThemeManager:
    """Manages application themes"""
    
    def __init__(self):
        self.themes = self._load_builtin_themes()
        self.current_theme = "default"
        self._load_custom_themes()
        
    def _load_builtin_themes(self) -> Dict[str, ThemeConfig]:
        """Load built-in themes"""
        return {
            "default": ThemeConfig(
                name="Default",
                primary="cyan",
                secondary="blue",
                accent="yellow"
            ),
            "dark": ThemeConfig(
                name="Dark",
                primary="bright_cyan",
                secondary="bright_blue",
                accent="bright_yellow",
                background="grey0",
                foreground="grey93"
            ),
            "dracula": ThemeConfig(
                name="Dracula",
                primary="#bd93f9",
                secondary="#8be9fd",
                accent="#f1fa8c",
                success="#50fa7b",
                error="#ff5555",
                background="#282a36",
                foreground="#f8f8f2"
            ),
            "nord": ThemeConfig(
                name="Nord",
                primary="#88C0D0",
                secondary="#81A1C1",
                accent="#EBCB8B",
                success="#A3BE8C",
                error="#BF616A",
                background="#2E3440",
                foreground="#D8DEE9"
            ),
            "gruvbox": ThemeConfig(
                name="Gruvbox",
                primary="#83a598",
                secondary="#458588",
                accent="#fabd2f",
                success="#b8bb26",
                error="#fb4934",
                background="#282828",
                foreground="#ebdbb2"
            )
        }
        
    def _load_custom_themes(self):
        """Load custom themes from themes/ directory"""
        import os
        from pathlib import Path
        
        themes_dir = Path("themes")
        if themes_dir.exists():
            for theme_file in themes_dir.glob("*.toml"):
                try:
                    with open(theme_file) as f:
                        config = toml.load(f)
                        theme = ThemeConfig(**config)
                        self.themes[theme_file.stem] = theme
                except Exception as e:
                    print(f"Failed to load theme {theme_file}: {e}")
                    
    def get_rich_theme(self) -> Theme:
        """Get Rich Theme object for current theme"""
        config = self.themes[self.current_theme]
        
        styles = {
            "primary": Style(color=config.primary),
            "secondary": Style(color=config.secondary),
            "accent": Style(color=config.accent),
            "success": Style(color=config.success),
            "warning": Style(color=config.warning),
            "error": Style(color=config.error),
            "header": Style.parse(config.header_style),
            "border": Style.parse(config.border_style),
            "selected": Style.parse(config.selected_style),
            "playing": Style.parse(config.playing_style),
            "paused": Style.parse(config.paused_style)
        }
        
        if config.background:
            styles["background"] = Style(bgcolor=config.background)
        if config.foreground:
            styles["foreground"] = Style(color=config.foreground)
            
        return Theme(styles)
        
    def switch_theme(self, theme_name: str):
        """Switch to different theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name

## Music Player Features

### 1. Playback Control (`features/playback.py`)

```python
import asyncio
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

class PlaybackMode(Enum):
    NORMAL = "normal"
    REPEAT_ONE = "repeat_one"
    REPEAT_ALL = "repeat_all"
    SHUFFLE = "shuffle"
    SMART_SHUFFLE = "smart_shuffle"

@dataclass
class PlaybackSettings:
    """Playback configuration"""
    mode: PlaybackMode = PlaybackMode.NORMAL
    crossfade: int = 0  # seconds
    gapless: bool = True
    replay_gain: bool = True
    replay_gain_mode: str = "album"  # album, track, auto
    speed: float = 1.0  # 0.5x - 2.0x

class PlaybackController:
    """Advanced playback control"""
    
    def __init__(self, cmus: CMUSInterface, state: AppState):
        self.cmus = cmus
        self.state = state
        self.settings = PlaybackSettings()
        self._fade_task: Optional[asyncio.Task] = None
        self._position_timer: Optional[asyncio.Task] = None
        
    async def play_pause(self):
        """Toggle play/pause with smooth transition"""
        if self.state.player_status.status == "playing":
            await self._fade_out()
            await self.cmus.pause()
        else:
            await self.cmus.play()
            await self._fade_in()
            
    async def _fade_out(self):
        """Fade out volume"""
        if self.settings.crossfade > 0:
            current_volume = self.state.player_status.volume
            steps = 10
            step_time = self.settings.crossfade / steps
            
            for i in range(steps):
                volume = int(current_volume * (1 - (i + 1) / steps))
                await self.cmus.set_volume(volume)
                await asyncio.sleep(step_time)
                
    async def _fade_in(self):
        """Fade in volume"""
        if self.settings.crossfade > 0:
            target_volume = self.state.player_status.volume
            steps = 10
            step_time = self.settings.crossfade / steps
            
            for i in range(steps):
                volume = int(target_volume * ((i + 1) / steps))
                await self.cmus.set_volume(volume)
                await asyncio.sleep(step_time)
                
    async def skip_forward(self, seconds: int = 10):
        """Skip forward in track"""
        if self.state.player_status.track:
            current = self.state.player_status.track.position
            await self.cmus.seek(current + seconds)
            
    async def skip_backward(self, seconds: int = 10):
        """Skip backward in track"""
        if self.state.player_status.track:
            current = self.state.player_status.track.position
            await self.cmus.seek(max(0, current - seconds))
            
    async def set_speed(self, speed: float):
        """Set playback speed"""
        self.settings.speed = max(0.5, min(2.0, speed))
        # Note: CMUS doesn't natively support speed control
        # This would require audio processing pipeline
        
    async def set_ab_repeat(self, a: Optional[int], b: Optional[int]):
        """Set A-B repeat points"""
        self.ab_repeat_a = a
        self.ab_repeat_b = b
        
        if a is not None and b is not None:
            # Start monitoring position
            if self._position_timer:
                self._position_timer.cancel()
            self._position_timer = asyncio.create_task(self._monitor_ab_repeat())
            
    async def _monitor_ab_repeat(self):
        """Monitor position for A-B repeat"""
        while self.ab_repeat_a is not None and self.ab_repeat_b is not None:
            status = await self.cmus.get_status()
            if status.track and status.track.position >= self.ab_repeat_b:
                await self.cmus.seek(self.ab_repeat_a)
            await asyncio.sleep(0.1)

### 2. Queue Management (`features/queue.py`)

```python
from typing import List, Optional
from dataclasses import dataclass
import random
from collections import deque

@dataclass
class QueueItem:
    """Queue item with metadata"""
    track: TrackInfo
    added_by: str = "user"
    added_at: datetime = field(default_factory=datetime.now)
    priority: int = 0
    
class QueueManager:
    """Advanced queue management"""
    
    def __init__(self, state: AppState):
        self.state = state
        self.queue: List[QueueItem] = []
        self.history: deque = deque(maxlen=100)
        self.shuffle_history: deque = deque(maxlen=50)
        
    async def add_track(self, track: TrackInfo, position: Optional[int] = None):
        """Add track to queue"""
        item = QueueItem(track=track)
        
        if position is not None:
            self.queue.insert(position, item)
        else:
            self.queue.append(item)
            
        await self._update_state()
        
    async def remove_track(self, index: int):
        """Remove track from queue"""
        if 0 <= index < len(self.queue):
            removed = self.queue.pop(index)
            await self._update_state()
            return removed
            
    async def move_track(self, from_idx: int, to_idx: int):
        """Move track in queue (drag-drop simulation)"""
        if 0 <= from_idx < len(self.queue) and 0 <= to_idx < len(self.queue):
            item = self.queue.pop(from_idx)
            self.queue.insert(to_idx, item)
            await self._update_state()
            
    async def clear_queue(self):
        """Clear entire queue"""
        self.queue.clear()
        await self._update_state()
        
    async def save_queue(self, name: str):
        """Save current queue as playlist"""
        tracks = [item.track.file for item in self.queue]
        self.state.playlists[name] = tracks
        await self.state.save()
        
    async def load_queue(self, name: str):
        """Load playlist into queue"""
        if name in self.state.playlists:
            self.queue.clear()
            for file_path in self.state.playlists[name]:
                # Load track info from file
                track = await self._load_track_info(file_path)
                self.queue.append(QueueItem(track=track))
            await self._update_state()
            
    def smart_shuffle(self):
        """Shuffle avoiding recently played tracks"""
        # Separate into buckets
        recent = set(self.shuffle_history)
        available = [item for item in self.queue if item.track.file not in recent]
        recent_items = [item for item in self.queue if item.track.file in recent]
        
        # Shuffle available tracks
        random.shuffle(available)
        
        # Add recent tracks at the end
        self.queue = available + recent_items
        
    async def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        total_duration = sum(
            item.track.duration for item in self.queue
            if item.track.duration
        )
        
        return {
            "total_tracks": len(self.queue),
            "total_duration": total_duration,
            "estimated_end_time": datetime.now() + timedelta(seconds=total_duration),
            "genres": self._count_genres(),
            "artists": self._count_artists()
        }
        
    def _count_genres(self) -> Dict[str, int]:
        """Count tracks by genre"""
        genres = {}
        for item in self.queue:
            if item.track.genre:
                genres[item.track.genre] = genres.get(item.track.genre, 0) + 1
        return genres
        
    def _count_artists(self) -> Dict[str, int]:
        """Count tracks by artist"""
        artists = {}
        for item in self.queue:
            if item.track.artist:
                artists[item.track.artist] = artists.get(item.track.artist, 0) + 1
        return artists

### 3. Library Management (`features/library.py`)

```python
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Set, Optional
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import mutagen

class LibraryScanner:
    """Scan and index music library"""
    
    def __init__(self, db_path: str = "~/.config/cmus-rich/library.db"):
        self.db_path = os.path.expanduser(db_path)
        self.conn = None
        self._init_db()
        
    def _init_db(self):
        """Initialize database"""
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        
        # Create tables
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
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
                composer TEXT,
                comment TEXT,
                last_modified REAL,
                play_count INTEGER DEFAULT 0,
                skip_count INTEGER DEFAULT 0,
                rating INTEGER,
                last_played REAL,
                added_date REAL
            )
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_artist ON tracks(artist);
            CREATE INDEX IF NOT EXISTS idx_album ON tracks(album);
            CREATE INDEX IF NOT EXISTS idx_genre ON tracks(genre);
        """)
        
    async def scan_directory(self, path: str, recursive: bool = True):
        """Scan directory for music files"""
        path = Path(path).expanduser()
        
        extensions = {'.mp3', '.flac', '.ogg', '.m4a', '.opus', '.wav'}
        files_found = 0
        
        for file_path in self._walk_directory(path, recursive):
            if file_path.suffix.lower() in extensions:
                await self._process_file(file_path)
                files_found += 1
                
                # Yield control periodically
                if files_found % 100 == 0:
                    await asyncio.sleep(0)
                    
        self.conn.commit()
        return files_found
        
    def _walk_directory(self, path: Path, recursive: bool):
        """Walk directory tree"""
        if recursive:
            for root, dirs, files in os.walk(path):
                for file in files:
                    yield Path(root) / file
        else:
            for file in path.iterdir():
                if file.is_file():
                    yield file
                    
    async def _process_file(self, file_path: Path):
        """Process single music file"""
        try:
            # Get file metadata
            metadata = mutagen.File(str(file_path))
            if metadata is None:
                return
                
            # Calculate file hash for duplicate detection
            file_hash = self._calculate_hash(file_path)
            
            # Check if already in database
            existing = self.conn.execute(
                "SELECT file_hash FROM tracks WHERE file_path = ?",
                (str(file_path),)
            ).fetchone()
            
            if existing and existing[0] == file_hash:
                return  # File unchanged
                
            # Extract metadata
            track_data = {
                'file_path': str(file_path),
                'file_hash': file_hash,
                'title': self._get_tag(metadata, 'title'),
                'artist': self._get_tag(metadata, 'artist'),
                'album': self._get_tag(metadata, 'album'),
                'genre': self._get_tag(metadata, 'genre'),
                'year': self._get_tag_int(metadata, 'date'),
                'duration': int(metadata.info.length) if metadata.info else None,
                'track_number': self._get_tag_int(metadata, 'tracknumber'),
                'disc_number': self._get_tag_int(metadata, 'discnumber'),
                'album_artist': self._get_tag(metadata, 'albumartist'),
                'composer': self._get_tag(metadata, 'composer'),
                'comment': self._get_tag(metadata, 'comment'),
                'last_modified': file_path.stat().st_mtime,
                'added_date': datetime.now().timestamp()
            }
            
            # Insert or update in database
            self._upsert_track(track_data)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate file hash for duplicate detection"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Read first and last 1MB for performance
            hasher.update(f.read(1024 * 1024))
            f.seek(-1024 * 1024, 2)
            hasher.update(f.read(1024 * 1024))
        return hasher.hexdigest()

class LibraryWatcher(FileSystemEventHandler):
    """Watch library directories for changes"""
    
    def __init__(self, scanner: LibraryScanner):
        self.scanner = scanner
        self.observer = Observer()
        
    def start_watching(self, paths: List[str]):
        """Start watching directories"""
        for path in paths:
            self.observer.schedule(self, path, recursive=True)
        self.observer.start()
        
    def on_created(self, event):
        """Handle file creation"""
        if not event.is_directory:
            asyncio.create_task(
                self.scanner._process_file(Path(event.src_path))
            )
            
    def on_modified(self, event):
        """Handle file modification"""
        if not event.is_directory:
            asyncio.create_task(
                self.scanner._process_file(Path(event.src_path))
            )

### 4. Search and Filtering (`features/search.py`)

```python
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class SearchField(Enum):
    ALL = "all"
    TITLE = "title"
    ARTIST = "artist"
    ALBUM = "album"
    GENRE = "genre"
    YEAR = "year"
    COMMENT = "comment"

@dataclass
class SearchQuery:
    """Search query representation"""
    text: str
    field: SearchField = SearchField.ALL
    regex: bool = False
    case_sensitive: bool = False
    
class SearchEngine:
    """Advanced search and filtering"""
    
    def __init__(self, db_conn):
        self.db = db_conn
        self.search_history = []
        self.saved_searches = {}
        
    async def search(
        self,
        query: SearchQuery,
        limit: Optional[int] = None
    ) -> List[TrackInfo]:
        """Execute search query"""
        
        # Add to history
        self.search_history.append(query)
        if len(self.search_history) > 100:
            self.search_history.pop(0)
            
        # Build SQL query
        sql, params = self._build_sql(query)
        
        if limit:
            sql += f" LIMIT {limit}"
            
        # Execute query
        cursor = self.db.execute(sql, params)
        results = []
        
        for row in cursor:
            results.append(self._row_to_track(row))
            
        return results
        
    def _build_sql(self, query: SearchQuery) -> Tuple[str, List]:
        """Build SQL query from search query"""
        base_sql = "SELECT * FROM tracks WHERE "
        
        if query.regex:
            # Use regex matching
            condition = f"{query.field.value} REGEXP ?"
            params = [query.text]
        else:
            # Use LIKE matching
            if query.field == SearchField.ALL:
                # Search all text fields
                conditions = []
                params = []
                for field in ['title', 'artist', 'album', 'genre']:
                    conditions.append(f"{field} LIKE ?")
                    params.append(f"%{query.text}%")
                condition = " OR ".join(conditions)
            else:
                condition = f"{query.field.value} LIKE ?"
                params = [f"%{query.text}%"]
                
        # Handle case sensitivity
        if not query.case_sensitive:
            condition = f"LOWER({condition})"
            params = [p.lower() for p in params]
            
        return base_sql + condition, params
        
    async def create_smart_playlist(
        self,
        name: str,
        rules: List[Dict]
    ) -> List[TrackInfo]:
        """Create smart playlist from rules"""
        
        # Build complex query from rules
        conditions = []
        params = []
        
        for rule in rules:
            field = rule['field']
            operator = rule['operator']
            value = rule['value']
            
            if operator == 'equals':
                conditions.append(f"{field} = ?")
                params.append(value)
            elif operator == 'contains':
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{value}%")
            elif operator == 'greater_than':
                conditions.append(f"{field} > ?")
                params.append(value)
            elif operator == 'less_than':
                conditions.append(f"{field} < ?")
                params.append(value)
            elif operator == 'between':
                conditions.append(f"{field} BETWEEN ? AND ?")
                params.extend(value)
                
        sql = f"SELECT * FROM tracks WHERE {' AND '.join(conditions)}"
        
        cursor = self.db.execute(sql, params)
        results = [self._row_to_track(row) for row in cursor]
        
        # Save smart playlist definition
        self.saved_searches[name] = {
            'rules': rules,
            'sql': sql,
            'params': params
        }
        
        return results

### 5. Visualization (`features/visualization.py`)

```python
import numpy as np
from typing import List, Optional
import subprocess
import asyncio

class AudioVisualizer:
    """Audio visualization components"""
    
    def __init__(self):
        self.fft_size = 2048
        self.sample_rate = 44100
        self.bands = 32
        self.smoothing = 0.8
        self.history = []
        
    async def get_spectrum_data(self) -> List[float]:
        """Get current spectrum data"""
        # Get audio data from CMUS (via FIFO or audio tap)
        audio_data = await self._get_audio_chunk()
        
        if audio_data is None:
            return [0.0] * self.bands
            
        # Perform FFT
        spectrum = self._compute_fft(audio_data)
        
        # Smooth with history
        if self.history:
            smoothed = []
            for i in range(len(spectrum)):
                smoothed.append(
                    spectrum[i] * (1 - self.smoothing) +
                    self.history[-1][i] * self.smoothing
                )
            spectrum = smoothed
            
        self.history.append(spectrum)
        if len(self.history) > 10:
            self.history.pop(0)
            
        return spectrum
        
    def _compute_fft(self, audio_data: np.ndarray) -> List[float]:
        """Compute FFT and return frequency bands"""
        # Apply window function
        window = np.hanning(len(audio_data))
        audio_data = audio_data * window
        
        # Compute FFT
        fft_result = np.fft.rfft(audio_data)
        magnitude = np.abs(fft_result)
        
        # Convert to dB
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        
        # Group into bands (logarithmic scaling)
        bands = []
        freq_bins = len(magnitude_db)
        
        for i in range(self.bands):
            # Logarithmic frequency mapping
            start = int(freq_bins * (i / self.bands) ** 2)
            end = int(freq_bins * ((i + 1) / self.bands) ** 2)
            
            if start < end:
                band_value = np.mean(magnitude_db[start:end])
                # Normalize to 0-1
                normalized = (band_value + 60) / 60  # Assuming -60dB to 0dB range
                bands.append(max(0, min(1, normalized)))
            else:
                bands.append(0)
                
        return bands

class ASCIIArtGenerator:
    """Generate ASCII art for album covers"""
    
    def __init__(self):
        self.char_ramp = " .:-=+*#%@"
        self.width = 40
        self.height = 20
        
    async def generate_album_art(self, image_path: str) -> List[str]:
        """Convert album art to ASCII"""
        try:
            from PIL import Image
            
            # Load and resize image
            img = Image.open(image_path)
            img = img.convert('L')  # Convert to grayscale
            img = img.resize((self.width, self.height))
            
            # Convert to ASCII
            pixels = np.array(img)
            ascii_art = []
            
            for row in pixels:
                ascii_row = ""
                for pixel in row:
                    # Map pixel value to character
                    char_idx = int(pixel / 255 * (len(self.char_ramp) - 1))
                    ascii_row += self.char_ramp[char_idx]
                ascii_art.append(ascii_row)
                
            return ascii_art
            
        except Exception as e:
            # Return placeholder if image processing fails
            return ["[Album Art]"] * self.height

### 6. Lyrics Integration (`features/lyrics.py`)

```python
import aiohttp
import asyncio
from typing import Optional, List, Dict
from dataclasses import dataclass

@dataclass
class LyricsLine:
    """Single line of lyrics with timing"""
    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class LyricsProvider:
    """Base class for lyrics providers"""
    
    async def search(self, artist: str, title: str) -> Optional[str]:
        raise NotImplementedError

class GeniusProvider(LyricsProvider):
    """Genius lyrics provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.genius.com"
        
    async def search(self, artist: str, title: str) -> Optional[str]:
        """Search for lyrics on Genius"""
        async with aiohttp.ClientSession() as session:
            # Search for song
            search_url = f"{self.base_url}/search"
            params = {'q': f"{artist} {title}"}
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            async with session.get(search_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    return None
                    
                data = await resp.json()
                hits = data['response']['hits']
                
                if not hits:
                    return None
                    
                # Get lyrics URL
                song_url = hits[0]['result']['url']
                
                # Scrape lyrics from web page
                # Note: This would require additional HTML parsing
                return await self._scrape_lyrics(song_url)

class LyricsManager:
    """Manage lyrics fetching and display"""
    
    def __init__(self, cache_dir: str = "~/.cache/cmus-rich/lyrics"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.providers = [
            # Add configured providers
        ]
        
        self.current_lyrics: Optional[List[LyricsLine]] = None
        
    async def fetch_lyrics(self, track: TrackInfo) -> Optional[str]:
        """Fetch lyrics for track"""
        if not track.artist or not track.title:
            return None
            
        # Check cache first
        cached = self._get_cached(track)
        if cached:
            return cached
            
        # Try each provider
        for provider in self.providers:
            try:
                lyrics = await provider.search(track.artist, track.title)
                if lyrics:
                    # Cache the lyrics
                    self._cache_lyrics(track, lyrics)
                    return lyrics
            except Exception as e:
                print(f"Provider error: {e}")
                continue
                
        return None
        
    def _get_cache_path(self, track: TrackInfo) -> Path:
        """Get cache file path for track"""
        # Create safe filename
        filename = f"{track.artist}_{track.title}.txt".replace('/', '_')
        return self.cache_dir / filename
        
    def _get_cached(self, track: TrackInfo) -> Optional[str]:
        """Get cached lyrics"""
        cache_path = self._get_cache_path(track)
        if cache_path.exists():
            return cache_path.read_text()
        return None
        
    def _cache_lyrics(self, track: TrackInfo, lyrics: str):
        """Cache lyrics to disk"""
        cache_path = self._get_cache_path(track)
        cache_path.write_text(lyrics)
        
    def parse_lrc(self, lrc_content: str) -> List[LyricsLine]:
        """Parse LRC (synchronized lyrics) format"""
        lines = []
        
        for line in lrc_content.split('\n'):
            # Parse timestamp [mm:ss.xx]
            import re
            match = re.match(r'\[(\d+):(\d+\.\d+)\](.*)', line)
            if match:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                text = match.group(3).strip()
                
                timestamp = minutes * 60 + seconds
                lines.append(LyricsLine(text=text, start_time=timestamp))
            else:
                # Non-timestamped line
                lines.append(LyricsLine(text=line))
                
        return lines
        
    def get_current_line(self, position: float) -> Optional[LyricsLine]:
        """Get current lyrics line based on playback position"""
        if not self.current_lyrics:
            return None
            
        for line in self.current_lyrics:
            if line.start_time and line.start_time <= position:
                if line.end_time is None or position < line.end_time:
                    return line
                    
        return None

### 7. Scrobbling (`features/scrobbling.py`)

```python
import hashlib
import time
from typing import Dict, Optional
import aiohttp

class LastFMScrobbler:
    """Last.fm scrobbling integration"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session_key = None
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
        self.offline_queue = []
        
    async def authenticate(self, username: str, password: str):
        """Authenticate with Last.fm"""
        # Get session key
        params = {
            'method': 'auth.getMobileSession',
            'username': username,
            'password': password,
            'api_key': self.api_key
        }
        
        # Sign request
        params['api_sig'] = self._sign_request(params)
        params['format'] = 'json'
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, data=params) as resp:
                data = await resp.json()
                if 'session' in data:
                    self.session_key = data['session']['key']
                    return True
                    
        return False
        
    async def scrobble(self, track: TrackInfo):
        """Scrobble track to Last.fm"""
        if not self.session_key:
            # Queue for later
            self.offline_queue.append({
                'track': track,
                'timestamp': int(time.time())
            })
            return
            
        params = {
            'method': 'track.scrobble',
            'artist': track.artist,
            'track': track.title,
            'timestamp': int(time.time()),
            'api_key': self.api_key,
            'sk': self.session_key
        }
        
        if track.album:
            params['album'] = track.album
            
        # Sign request
        params['api_sig'] = self._sign_request(params)
        params['format'] = 'json'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, data=params) as resp:
                    if resp.status == 200:
                        # Process offline queue if online
                        await self._process_offline_queue()
                        
        except aiohttp.ClientError:
            # Queue for later
            self.offline_queue.append({
                'track': track,
                'timestamp': int(time.time())
            })
            
    async def update_now_playing(self, track: TrackInfo):
        """Update now playing status"""
        if not self.session_key:
            return
            
        params = {
            'method': 'track.updateNowPlaying',
            'artist': track.artist,
            'track': track.title,
            'api_key': self.api_key,
            'sk': self.session_key
        }
        
        if track.album:
            params['album'] = track.album
            
        params['api_sig'] = self._sign_request(params)
        params['format'] = 'json'
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(self.base_url, data=params)
        except:
            pass  # Ignore errors for now playing
            
    def _sign_request(self, params: Dict) -> str:
        """Sign API request"""
        # Sort parameters
        sorted_params = sorted(params.items())
        
        # Create signature string
        sig_string = ""
        for key, value in sorted_params:
            if key != 'format':
                sig_string += f"{key}{value}"
                
        sig_string += self.api_secret
        
        # Return MD5 hash
        return hashlib.md5(sig_string.encode()).hexdigest()

### 8. Statistics and Analytics (`features/statistics.py`)

```python
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import sqlite3

class StatisticsTracker:
    """Track and analyze listening statistics"""
    
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)
        self._init_tables()
        
    def _init_tables(self):
        """Initialize statistics tables"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS play_history (
                id INTEGER PRIMARY KEY,
                track_id INTEGER,
                started_at REAL,
                completed BOOLEAN,
                skip_position INTEGER,
                FOREIGN KEY (track_id) REFERENCES tracks(id)
            )
        """)
        
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date TEXT PRIMARY KEY,
                total_plays INTEGER,
                total_time INTEGER,
                unique_tracks INTEGER,
                unique_artists INTEGER
            )
        """)
        
    async def track_play(self, track: TrackInfo, completed: bool = True):
        """Track a play event"""
        # Record in history
        self.db.execute("""
            INSERT INTO play_history (track_id, started_at, completed)
            VALUES ((SELECT id FROM tracks WHERE file_path = ?), ?, ?)
        """, (track.file, datetime.now().timestamp(), completed))
        
        # Update play count
        self.db.execute("""
            UPDATE tracks
            SET play_count = play_count + 1,
                last_played = ?
            WHERE file_path = ?
        """, (datetime.now().timestamp(), track.file))
        
        if not completed:
            # Update skip count
            self.db.execute("""
                UPDATE tracks
                SET skip_count = skip_count + 1
                WHERE file_path = ?
            """, (track.file,))
            
        self.db.commit()
        
    def get_top_tracks(self, limit: int = 10, days: Optional[int] = None) -> List[Dict]:
        """Get most played tracks"""
        if days:
            since = datetime.now() - timedelta(days=days)
            query = """
                SELECT t.*, COUNT(p.id) as plays
                FROM tracks t
                JOIN play_history p ON t.id = p.track_id
                WHERE p.started_at > ?
                GROUP BY t.id
                ORDER BY plays DESC
                LIMIT ?
            """
            cursor = self.db.execute(query, (since.timestamp(), limit))
        else:
            query = """
                SELECT *, play_count as plays
                FROM tracks
                ORDER BY play_count DESC
                LIMIT ?
            """
            cursor = self.db.execute(query, (limit,))
            
        return [dict(row) for row in cursor]
        
    def get_listening_time_heatmap(self) -> Dict[int, Dict[int, int]]:
        """Get heatmap of listening by hour and day"""
        query = """
            SELECT started_at
            FROM play_history
            WHERE started_at > ?
        """
        
        # Last 30 days
        since = datetime.now() - timedelta(days=30)
        cursor = self.db.execute(query, (since.timestamp(),))
        
        heatmap = defaultdict(lambda: defaultdict(int))
        
        for row in cursor:
            dt = datetime.fromtimestamp(row[0])
            heatmap[dt.weekday()][dt.hour] += 1
            
        return dict(heatmap)
        
    def get_genre_distribution(self) -> Dict[str, int]:
        """Get play distribution by genre"""
        query = """
            SELECT genre, SUM(play_count) as plays
            FROM tracks
            WHERE genre IS NOT NULL
            GROUP BY genre
            ORDER BY plays DESC
        """
        
        cursor = self.db.execute(query)
        return {row[0]: row[1] for row in cursor}
        
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get statistics about music discovery"""
        # Tracks discovered this month
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        
        new_tracks = self.db.execute("""
            SELECT COUNT(*)
            FROM tracks
            WHERE added_date > ?
        """, (month_start.timestamp(),)).fetchone()[0]
        
        # Variety score (unique artists/total plays)
        unique_artists = self.db.execute("""
            SELECT COUNT(DISTINCT artist)
            FROM tracks
            WHERE play_count > 0
        """).fetchone()[0]
        
        total_plays = self.db.execute("""
            SELECT SUM(play_count)
            FROM tracks
        """).fetchone()[0]
        
        variety_score = unique_artists / max(total_plays, 1) * 100
        
        return {
            'new_tracks_this_month': new_tracks,
            'variety_score': variety_score,
            'unique_artists': unique_artists
        }

## Technical Implementation

### 1. Caching System (`utils/cache.py`)

```python
from typing import Any, Optional, Callable
import asyncio
import pickle
import time
from pathlib import Path

class Cache:
    """LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.access_times = {}
        self.lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        async with self.lock:
            if key in self.cache:
                # Check TTL
                if time.time() - self.access_times[key] < self.ttl:
                    # Update access time
                    self.access_times[key] = time.time()
                    return self.cache[key]
                else:
                    # Expired
                    del self.cache[key]
                    del self.access_times[key]
                    
        return None
        
    async def set(self, key: str, value: Any):
        """Set item in cache"""
        async with self.lock:
            # Check size limit
            if len(self.cache) >= self.max_size:
                # Remove oldest item
                oldest = min(self.access_times.items(), key=lambda x: x[1])
                del self.cache[oldest[0]]
                del self.access_times[oldest[0]]
                
            self.cache[key] = value
            self.access_times[key] = time.time()
            
    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable
    ) -> Any:
        """Get from cache or compute if missing"""
        value = await self.get(key)
        
        if value is None:
            value = await compute_func()
            await self.set(key, value)
            
        return value

class PersistentCache:
    """Disk-based persistent cache"""
    
    def __init__(self, cache_dir: str = "~/.cache/cmus-rich"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_path(self, key: str) -> Path:
        """Get file path for cache key"""
        # Hash key to avoid filesystem issues
        import hashlib
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
        
    async def get(self, key: str) -> Optional[Any]:
        """Get from persistent cache"""
        path = self._get_path(key)
        
        if path.exists():
            try:
                async with aiofiles.open(path, 'rb') as f:
                    data = await f.read()
                    return pickle.loads(data)
            except:
                # Corrupted cache file
                path.unlink()
                
        return None
        
    async def set(self, key: str, value: Any):
        """Save to persistent cache"""
        path = self._get_path(key)
        
        async with aiofiles.open(path, 'wb') as f:
            await f.write(pickle.dumps(value))

### 2. Performance Optimization

```python
# Memory-efficient data structures for large libraries
class TrackIndex:
    """Memory-efficient track index using slots"""
    
    __slots__ = ['id', 'path', 'artist', 'album', 'title', 'duration']
    
    def __init__(self, id: int, path: str, **kwargs):
        self.id = id
        self.path = path
        self.artist = kwargs.get('artist')
        self.album = kwargs.get('album')
        self.title = kwargs.get('title')
        self.duration = kwargs.get('duration')

# Lazy loading for large collections
class LazyLibrary:
    """Lazy-loading library implementation"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._index = None
        self._page_size = 100
        
    async def get_page(self, offset: int, limit: int) -> List[TrackInfo]:
        """Get page of tracks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM tracks LIMIT ? OFFSET ?",
            (limit, offset)
        )
        
        tracks = []
        for row in cursor:
            tracks.append(self._row_to_track(row))
            
        conn.close()
        return tracks
        
    async def search_index(self, query: str) -> List[int]:
        """Search using index only"""
        if self._index is None:
            await self._build_index()
            
        # Search in memory index
        results = []
        query_lower = query.lower()
        
        for track_id, text in self._index.items():
            if query_lower in text.lower():
                results.append(track_id)
                
        return results

# Connection pooling for database
class DatabasePool:
    """SQLite connection pool"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = asyncio.Queue(maxsize=pool_size)
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            self._pool.put_nowait(conn)
            
    async def acquire(self):
        """Acquire connection from pool"""
        return await self._pool.get()
        
    async def release(self, conn):
        """Release connection back to pool"""
        await self._pool.put(conn)
        
    @contextlib.asynccontextmanager
    async def connection(self):
        """Context manager for connections"""
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

## Configuration System

### 1. Configuration File Format (config.toml)

```toml
# CMUS Rich Configuration

[general]
theme = "dracula"
single_instance = true
auto_save = true
save_interval = 300  # seconds

[ui]
refresh_rate = 0.1  # 10 FPS
show_album_art = true
show_visualizer = true
show_lyrics = true
layout = "default"

[playback]
crossfade = 3  # seconds
gapless = true
replay_gain = true
replay_gain_mode = "album"  # album, track, auto

[library]
paths = [
    "~/Music",
    "/media/music"
]
auto_scan = true
scan_interval = 3600  # seconds
watch_changes = true

[search]
fuzzy = true
regex_enabled = true
history_size = 100
default_fields = ["title", "artist", "album"]

[keybindings]
play_pause = "space"
next_track = "n"
previous_track = "p"
volume_up = "+"
volume_down = "-"
seek_forward = "l"
seek_backward = "h"
search = "/"
command_palette = "ctrl+p"
quit = "q"

# Vim-like navigation
move_up = "k"
move_down = "j"
move_left = "h"
move_right = "l"
page_up = "ctrl+u"
page_down = "ctrl+d"

[scrobbling]
lastfm_enabled = false
lastfm_api_key = ""
lastfm_api_secret = ""
listenbrainz_enabled = false
listenbrainz_token = ""

[network]
timeout = 10
retry_count = 3
cache_size_mb = 50

[plugins]
enabled = [
    "discord_presence",
    "mpris",
    "notifications"
]

[logging]
level = "INFO"  # DEBUG, INFO, WARNING, ERROR
file = "~/.local/share/cmus-rich/app.log"
max_size_mb = 10
rotate_count = 5

[advanced]
thread_pool_size = 4
db_path = "~/.local/share/cmus-rich/library.db"
cache_dir = "~/.cache/cmus-rich"
```

### 2. Configuration Manager (`core/config.py`)

```python
import toml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Config:
    """Application configuration"""
    
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
    library_paths: List[str] = field(default_factory=list)
    auto_scan: bool = True
    scan_interval: int = 3600
    watch_changes: bool = True
    
    # Keybindings
    keybindings: Dict[str, str] = field(default_factory=dict)
    
    # Network
    timeout: int = 10
    retry_count: int = 3
    cache_size_mb: int = 50
    
    # Plugins
    enabled_plugins: List[str] = field(default_factory=list)
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "~/.local/share/cmus-rich/app.log"
    
class ConfigManager:
    """Manage application configuration with hot reload"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(
            config_path or "~/.config/cmus-rich/config.toml"
        ).expanduser()
        
        self.config = Config()
        self._watchers = []
        self._last_modified = None
        
        # Load configuration
        self.load()
        
    def load(self):
        """Load configuration from file"""
        if not self.config_path.exists():
            # Create default config
            self._create_default_config()
            
        try:
            with open(self.config_path) as f:
                data = toml.load(f)
                
            # Update config object
            self._update_config(data)
            
            self._last_modified = self.config_path.stat().st_mtime
            
        except Exception as e:
            print(f"Failed to load config: {e}")
            
    def _update_config(self, data: Dict[str, Any]):
        """Update config object from dictionary"""
        # General section
        general = data.get('general', {})
        self.config.theme = general.get('theme', self.config.theme)
        self.config.single_instance = general.get('single_instance', self.config.single_instance)
        
        # UI section
        ui = data.get('ui', {})
        self.config.refresh_rate = ui.get('refresh_rate', self.config.refresh_rate)
        self.config.show_album_art = ui.get('show_album_art', self.config.show_album_art)
        
        # Keybindings
        self.config.keybindings = data.get('keybindings', {})
        
        # Library paths
        library = data.get('library', {})
        self.config.library_paths = library.get('paths', [])
        
    async def watch_changes(self):
        """Watch for configuration file changes"""
        while True:
            await asyncio.sleep(1)
            
            if self.config_path.exists():
                mtime = self.config_path.stat().st_mtime
                if mtime != self._last_modified:
                    self.load()
                    
                    # Notify watchers
                    for watcher in self._watchers:
                        await watcher(self.config)

## Error Handling

```python
class CMUSError(Exception):
    """Base exception for CMUS errors"""
    pass

class ConnectionError(CMUSError):
    """CMUS connection error"""
    pass

class CommandError(CMUSError):
    """CMUS command execution error"""
    pass

class ErrorHandler:
    """Central error handling"""
    
    def __init__(self, logger):
        self.logger = logger
        self.error_count = 0
        self.last_errors = []
        
    def handle_error(self, error: Exception, context: str = ""):
        """Handle application error"""
        self.error_count += 1
        self.last_errors.append({
            'error': str(error),
            'type': type(error).__name__,
            'context': context,
            'timestamp': datetime.now()
        })
        
        # Keep only last 100 errors
        if len(self.last_errors) > 100:
            self.last_errors.pop(0)
            
        # Log error
        self.logger.error(f"{context}: {error}", exc_info=True)
        
        # Handle specific error types
        if isinstance(error, ConnectionError):
            return self._handle_connection_error(error)
        elif isinstance(error, CommandError):
            return self._handle_command_error(error)
        elif isinstance(error, FileNotFoundError):
            return self._handle_file_error(error)
        else:
            return self._handle_generic_error(error)
            
    def _handle_connection_error(self, error):
        """Handle CMUS connection errors"""
        return {
            'retry': True,
            'message': "Failed to connect to CMUS. Retrying...",
            'action': 'restart_cmus'
        }
```

## Performance Targets and Benchmarks

```python
class PerformanceBenchmark:
    """Performance testing utilities"""
    
    async def benchmark_startup(self):
        """Benchmark application startup"""
        start = time.time()
        
        app = CMUSRichApp()
        await app.initialize()
        
        startup_time = time.time() - start
        assert startup_time < 0.1, f"Startup too slow: {startup_time}s"
        
    async def benchmark_search(self, library_size: int = 10000):
        """Benchmark search performance"""
        # Create test library
        search = SearchEngine(db)
        
        start = time.time()
        results = await search.search(SearchQuery("test"))
        search_time = time.time() - start
        
        assert search_time < 0.05, f"Search too slow: {search_time}s"
        
    async def benchmark_ui_refresh(self):
        """Benchmark UI refresh rate"""
        ui = DashboardView(console, state)
        
        frame_times = []
        for _ in range(100):
            start = time.time()
            await ui.render()
            frame_times.append(time.time() - start)
            
        avg_frame_time = sum(frame_times) / len(frame_times)
        fps = 1 / avg_frame_time
        
        assert fps > 30, f"UI refresh too slow: {fps} FPS"
```

## Appendices

### A. Plugin Development Guide

```python
class Plugin:
    """Base class for plugins"""
    
    def __init__(self, app):
        self.app = app
        self.name = "unnamed"
        self.version = "1.0.0"
        
    async def initialize(self):
        """Initialize plugin"""
        pass
        
    async def on_track_change(self, track: TrackInfo):
        """Called when track changes"""
        pass
        
    async def on_playback_start(self):
        """Called when playback starts"""
        pass
        
    def register_command(self, name: str, handler: Callable):
        """Register a command"""
        self.app.commands[name] = handler
        
    def register_keybinding(self, key: str, handler: Callable):
        """Register a keybinding"""
        self.app.keybindings[key] = handler

# Example plugin
class DiscordPresencePlugin(Plugin):
    """Discord Rich Presence integration"""
    
    def __init__(self, app):
        super().__init__(app)
        self.name = "discord_presence"
        self.rpc = None
        
    async def initialize(self):
        """Initialize Discord RPC"""
        try:
            from pypresence import AioPresence
            self.rpc = AioPresence("your_discord_app_id")
            await self.rpc.connect()
        except:
            pass  # Discord not available
            
    async def on_track_change(self, track: TrackInfo):
        """Update Discord presence"""
        if self.rpc:
            await self.rpc.update(
                details=f"{track.title}",
                state=f"by {track.artist}",
                large_image="music",
                large_text=track.album or "Unknown Album"
            )

### B. Terminal Compatibility Matrix

| Terminal          | Unicode | True Color | Sixel | Kitty Graphics |
|------------------|---------|------------|-------|----------------|
| Alacritty        | ✓       | ✓          | ✗     | ✗              |
| iTerm2           | ✓       | ✓          | ✓     | ✗              |
| Kitty            | ✓       | ✓          | ✗     | ✓              |
| Konsole          | ✓       | ✓          | ✗     | ✗              |
| Terminal.app     | ✓       | ✗          | ✗     | ✗              |
| Windows Terminal | ✓       | ✓          | ✗     | ✗              |
| WezTerm          | ✓       | ✓          | ✓     | ✓              |
| xterm            | ✓       | ✓          | ✓     | ✗              |

### C. Debugging Utilities

```python
class DebugPanel:
    """Debug information panel"""
    
    def __init__(self, app):
        self.app = app
        self.enabled = False
        
    def render(self) -> Panel:
        """Render debug information"""
        if not self.enabled:
            return None
            
        info = {
            "State": {
                "Active View": self.app.state.active_view,
                "Queue Size": len(self.app.state.current_queue),
                "Cache Size": len(self.app.state.library_cache),
            },
            "Performance": {
                "FPS": self._calculate_fps(),
                "Memory": f"{self._get_memory_usage()} MB",
                "CPU": f"{self._get_cpu_usage()}%",
            },
            "CMUS": {
                "Connected": self.app.cmus._connected,
                "Status": self.app.state.player_status.status if self.app.state.player_status else "N/A",
            }
        }
        
        table = Table(show_header=False, box=None)
        for category, items in info.items():
            table.add_row(Text(category, style="bold"))
            for key, value in items.items():
                table.add_row(f"  {key}:", str(value))
                
        return Panel(table, title="Debug Info", border_style="red")

class CommandRecorder:
    """Record and replay command sequences"""
    
    def __init__(self):
        self.recording = False
        self.commands = []
        self.macros = {}
        
    def start_recording(self, name: str):
        """Start recording commands"""
        self.recording = True
        self.commands = []
        self.current_macro = name
        
    def stop_recording(self):
        """Stop recording and save macro"""
        if self.recording and self.commands:
            self.macros[self.current_macro] = self.commands
        self.recording = False
        
    def record_command(self, command: str, args: Dict):
        """Record a command"""
        if self.recording:
            self.commands.append({
                'command': command,
                'args': args,
                'timestamp': time.time()
            })
            
    async def replay_macro(self, name: str, app):
        """Replay recorded macro"""
        if name not in self.macros:
            return
            
        for cmd in self.macros[name]:
            # Execute command
            if cmd['command'] in app.commands:
                await app.commands[cmd['command']](**cmd['args'])
                
            # Maintain timing
            await asyncio.sleep(0.1)

### D. Example Implementations

#### Complex Feature: Smart Shuffle Implementation

```python
class SmartShuffle:
    """Intelligent shuffle that avoids repetition and considers preferences"""
    
    def __init__(self, history_size: int = 50):
        self.history = deque(maxlen=history_size)
        self.artist_cooldown = 10  # tracks
        self.album_cooldown = 5   # tracks
        
    def shuffle(self, tracks: List[TrackInfo]) -> List[TrackInfo]:
        """Smart shuffle algorithm"""
        if len(tracks) <= 1:
            return tracks
            
        # Build scoring system
        scores = {}
        for i, track in enumerate(tracks):
            score = self._calculate_score(track)
            scores[i] = score
            
        # Sort by score (higher = play sooner)
        sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        # Add some randomness
        result = []
        while sorted_indices:
            # Take from top 20% with weighted random
            cutoff = max(1, len(sorted_indices) // 5)
            weights = [1 / (i + 1) for i in range(min(cutoff, len(sorted_indices)))]
            
            idx = random.choices(sorted_indices[:cutoff], weights=weights)[0]
            result.append(tracks[sorted_indices[idx]])
            sorted_indices.remove(sorted_indices[idx])
            
        return result
        
    def _calculate_score(self, track: TrackInfo) -> float:
        """Calculate track score for shuffling"""
        score = random.random() * 100  # Base randomness
        
        # Check recent history
        recent_artists = [t.artist for t in self.history[-self.artist_cooldown:]]
        recent_albums = [t.album for t in self.history[-self.album_cooldown:]]
        
        # Penalize recently played artists/albums
        if track.artist in recent_artists:
            score -= 50
        if track.album in recent_albums:
            score -= 30
            
        # Boost based on rating/play count (if available)
        if hasattr(track, 'rating'):
            score += track.rating * 10
            
        return score

#### Complex Feature: Recommendation Engine

```python
class RecommendationEngine:
    """Generate music recommendations"""
    
    def __init__(self, db_conn):
        self.db = db_conn
        self.similarity_cache = {}
        
    async def get_similar_tracks(self, track: TrackInfo, limit: int = 10) -> List[TrackInfo]:
        """Find similar tracks using collaborative filtering"""
        
        # Get tracks frequently played together
        query = """
            WITH target_sessions AS (
                SELECT DISTINCT session_id
                FROM play_history
                WHERE track_id = (SELECT id FROM tracks WHERE file_path = ?)
            )
            SELECT t.*, COUNT(*) as co_plays
            FROM tracks t
            JOIN play_history p ON t.id = p.track_id
            WHERE p.session_id IN (SELECT session_id FROM target_sessions)
                AND t.file_path != ?
            GROUP BY t.id
            ORDER BY co_plays DESC
            LIMIT ?
        """
        
        cursor = self.db.execute(query, (track.file, track.file, limit))
        return [self._row_to_track(row) for row in cursor]
        
    async def generate_mood_playlist(self, mood: str) -> List[TrackInfo]:
        """Generate playlist based on mood"""
        
        mood_mappings = {
            'energetic': {
                'min_tempo': 120,
                'genres': ['rock', 'electronic', 'dance'],
                'energy': 0.7
            },
            'relaxing': {
                'max_tempo': 100,
                'genres': ['ambient', 'classical', 'jazz'],
                'energy': 0.3
            },
            'focus': {
                'genres': ['instrumental', 'classical', 'lo-fi'],
                'vocals': False
            }
        }
        
        if mood not in mood_mappings:
            return []
            
        criteria = mood_mappings[mood]
        
        # Build query based on criteria
        conditions = []
        params = []
        
        if 'genres' in criteria:
            placeholders = ','.join(['?' for _ in criteria['genres']])
            conditions.append(f"genre IN ({placeholders})")
            params.extend(criteria['genres'])
            
        # Add more conditions based on audio features
        # (would require audio analysis)
        
        query = f"SELECT * FROM tracks WHERE {' AND '.join(conditions)}"
        cursor = self.db.execute(query, params)
        
        tracks = [self._row_to_track(row) for row in cursor]
        
        # Smart shuffle the results
        return SmartShuffle().shuffle(tracks)

### E. Installation Script

```bash
#!/bin/bash
# Installation script for CMUS Rich

echo "Installing CMUS Rich..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [[ $(echo "$python_version >= 3.10" | bc) -ne 1 ]]; then
    echo "Error: Python 3.10+ is required"
    exit 1
fi

# Check for CMUS
if ! command -v cmus &> /dev/null; then
    echo "Warning: CMUS not found. Please install CMUS first."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install rich>=13.0.0
pip install aiofiles
pip install aiohttp
pip install tomli tomli-w
pip install watchdog
pip install mutagen
pip install pytest pytest-asyncio pytest-mock

# Create directories
mkdir -p ~/.config/cmus-rich
mkdir -p ~/.cache/cmus-rich
mkdir -p ~/.local/share/cmus-rich

# Copy default configuration
cp config/default.toml ~/.config/cmus-rich/config.toml

echo "Installation complete!"
echo "Run 'python -m cmus_rich' to start the application"
```

### F. Testing Suite

```python
import pytest
import asyncio
from unittest.mock import Mock, patch

@pytest.fixture
async def app():
    """Create test application"""
    app = CMUSRichApp(config_path="test_config.toml")
    await app.initialize()
    yield app
    await app.shutdown()

@pytest.fixture
def mock_cmus():
    """Mock CMUS interface"""
    cmus = Mock(spec=CMUSInterface)
    cmus.get_status.return_value = PlayerStatus(
        status="playing",
        track=TrackInfo(
            file="/test/track.mp3",
            artist="Test Artist",
            title="Test Track"
        )
    )
    return cmus

class TestPlayback:
    """Test playback functionality"""
    
    @pytest.mark.asyncio
    async def test_play_pause(self, app, mock_cmus):
        """Test play/pause toggle"""
        app.cmus = mock_cmus
        controller = PlaybackController(mock_cmus, app.state)
        
        await controller.play_pause()
        mock_cmus.pause.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_crossfade(self, app, mock_cmus):
        """Test crossfade functionality"""
        app.cmus = mock_cmus
        controller = PlaybackController(mock_cmus, app.state)
        controller.settings.crossfade = 2
        
        await controller._fade_out()
        
        # Should have called set_volume multiple times
        assert mock_cmus.set_volume.call_count > 5

class TestSearch:
    """Test search functionality"""
    
    @pytest.mark.asyncio
    async def test_fuzzy_search(self):
        """Test fuzzy search matching"""
        search = SearchEngine(db_conn=Mock())
        
        # Test fuzzy matching
        query = SearchQuery("btles", field=SearchField.ARTIST)
        query.text = "btles"  # Should match "Beatles"
        
        # Mock database response
        search.db.execute.return_value = [
            ("file.mp3", "The Beatles", "Abbey Road", "Come Together")
        ]
        
        results = await search.search(query)
        assert len(results) > 0

class TestUI:
    """Test UI components"""
    
    def test_menu_navigation(self):
        """Test menu navigation"""
        items = [
            MenuItem("Item 1"),
            MenuItem("Item 2"),
            MenuItem("Item 3")
        ]
        menu = Menu("Test Menu", items)
        
        # Test navigation
        assert menu.selected_index == 0
        menu.move_down()
        assert menu.selected_index == 1
        menu.move_down()
        menu.move_down()  # Should stop at end
        assert menu.selected_index == 2
        
    def test_fuzzy_filter(self):
        """Test fuzzy filtering"""
        items = [
            MenuItem("Play Track"),
            MenuItem("Pause Playback"),
            MenuItem("Stop Player")
        ]
        menu = Menu("Commands", items)
        
        menu.filter_items("ply")
        assert len(menu.filtered_items) == 2  # Play and Player

### G. FAQ and Troubleshooting

**Q: CMUS won't connect**
A: Ensure CMUS is running and the socket is accessible. Check `~/.cmus/socket` permissions.

**Q: High CPU usage during visualization**
A: Reduce refresh rate in config or disable visualizer. Some terminals handle updates poorly.

**Q: Search is slow with large library**
A: Ensure database indices are created. Run `cmus-rich --rebuild-index` to optimize.

**Q: Keybindings not working**
A: Check for conflicts in config.toml. Some terminals intercept certain key combinations.

**Q: Album art not displaying**
A: Ensure terminal supports your chosen display method (Sixel/Kitty graphics). Install ueberzug for fallback.

### H. External Resources

- CMUS Documentation: https://cmus.github.io/
- Rich Documentation: https://rich.readthedocs.io/
- Terminal Graphics Protocol: https://sw.kovidgoyal.net/kitty/graphics-protocol/
- Last.fm API: https://www.last.fm/api
- MusicBrainz API: https://musicbrainz.org/doc/Development

## Implementation Checklist

- [ ] Core Architecture
  - [ ] Application controller
  - [ ] CMUS interface layer  
  - [ ] State management
  - [ ] Event system
  - [ ] Configuration management
  
- [ ] UI Components
  - [ ] Dashboard view
  - [ ] Menu system
  - [ ] Command palette
  - [ ] Layout manager
  - [ ] Theme system
  
- [ ] Music Features
  - [ ] Playback control
  - [ ] Queue management
  - [ ] Library scanner
  - [ ] Search engine
  - [ ] Playlist manager
  - [ ] Visualization
  - [ ] Lyrics integration
  - [ ] Scrobbling
  
- [ ] Advanced Features
  - [ ] Statistics tracking
  - [ ] Recommendation engine
  - [ ] Smart shuffle
  - [ ] Audio effects
  - [ ] Remote control
  
- [ ] Infrastructure
  - [ ] Database setup
  - [ ] Caching system
  - [ ] Plugin system
  - [ ] Error handling
  - [ ] Logging
  
- [ ] Testing & Deployment
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] Performance benchmarks
  - [ ] Installation script
  - [ ] Documentation
