"""Dashboard view with live updates."""

from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cmus_rich.core.state import AppState


class DashboardView:
    """Main dashboard with live updates."""

    def __init__(self, console: Console, state: AppState) -> None:
        self.console = console
        self.state = state
        self.layout = self._create_layout()

    def _create_layout(self) -> Layout:
        """Create dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )

        layout["main"].split_row(
            Layout(name="sidebar", ratio=1),
            Layout(name="content", ratio=3),
        )

        return layout

    def render(self) -> Layout:
        """Render dashboard."""
        # Update header with now playing
        self.layout["header"].update(self._render_now_playing())

        # Update main content
        self.layout["content"].update(self._render_library())

        # Update sidebar with queue
        self.layout["sidebar"].update(self._render_queue())

        # Update footer with controls
        self.layout["footer"].update(self._render_footer())

        return self.layout

    def _render_now_playing(self) -> Panel:
        """Render now playing information."""
        if not self.state.player_status or not self.state.player_status.track:
            return Panel(
                Align.center("No track playing", vertical="middle"),
                title="♪ Now Playing",
                border_style="dim",
            )

        track = self.state.player_status.track
        status = self.state.player_status

        # Create track info display
        content = Group(
            Text(track.title or "Unknown Title", style="bold cyan", justify="center"),
            Text(f"by {track.artist or 'Unknown Artist'}", style="yellow", justify="center"),
            Text(f"from {track.album or 'Unknown Album'}", style="blue", justify="center"),
        )

        # Add playback status indicator
        status_indicator = "▶" if status.status == "playing" else "⏸" if status.status == "paused" else "⏹"
        border_style = "green" if status.status == "playing" else "yellow" if status.status == "paused" else "dim"

        return Panel(
            Align.center(content, vertical="middle"),
            title=f"♪ {status_indicator} Now Playing",
            border_style=border_style,
        )

    def _render_queue(self) -> Panel:
        """Render queue view."""
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("#", width=3)
        table.add_column("Track")

        if self.state.current_queue:
            for i, track in enumerate(self.state.current_queue[:20], 1):
                table.add_row(
                    str(i), f"{track.title or 'Unknown'} - {track.artist or 'Unknown'}"
                )
        else:
            table.add_row("", "[dim]Queue is empty[/dim]")

        return Panel(table, title=f"Queue ({len(self.state.current_queue)})", border_style="blue")

    def _render_library(self) -> Panel:
        """Render library browser."""
        content = Text("Library browser coming soon...", style="dim", justify="center")
        return Panel(
            Align.center(content, vertical="middle"),
            title="Library",
            border_style="cyan",
        )

    def _render_footer(self) -> Panel:
        """Render footer with controls and progress."""
        if not self.state.player_status or not self.state.player_status.track:
            return Panel(
                Text("━" * 80, style="dim"),
                box=None,
            )

        track = self.state.player_status.track
        status = self.state.player_status

        # Create progress bar
        if track.duration and track.position is not None:
            progress = track.position / track.duration
            bar_width = 60
            filled = int(bar_width * progress)
            bar = "█" * filled + "━" * (bar_width - filled)

            time_str = f"{self._format_time(track.position)} / {self._format_time(track.duration)}"

            # Volume and status
            vol_str = f"Vol: {status.volume}%"
            shuffle_str = "🔀" if status.shuffle else ""
            repeat_str = "🔁" if status.repeat else ""

            content = Group(
                Text(bar, style="cyan"),
                Text(
                    f"{time_str}  {vol_str}  {shuffle_str} {repeat_str}",
                    justify="center",
                    style="dim",
                ),
            )

            return Panel(content, box=None)

        return Panel(Text("━" * 80, style="dim"), box=None)

    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format seconds to MM:SS."""
        return f"{seconds // 60:02d}:{seconds % 60:02d}"


class NowPlayingWidget:
    """Standalone now playing widget."""

    def __init__(self, state: AppState) -> None:
        self.state = state

    def render(self) -> Panel:
        """Render now playing info."""
        if not self.state.player_status or not self.state.player_status.track:
            return Panel(
                Align.center("No track playing", vertical="middle"), style="dim"
            )

        track = self.state.player_status.track

        content = Group(
            Text(track.title or "Unknown Title", style="bold cyan", justify="center"),
            Text(
                f"by {track.artist or 'Unknown Artist'}",
                style="yellow",
                justify="center",
            ),
            Text(
                f"from {track.album or 'Unknown Album'}", style="blue", justify="center"
            ),
        )

        return Panel(
            Align.center(content, vertical="middle"),
            title="♪ Now Playing ♪",
            border_style="cyan",
        )
