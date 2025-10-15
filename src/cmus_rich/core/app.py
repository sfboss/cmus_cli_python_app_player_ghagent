"""Main application controller."""

import asyncio
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.console import Console

from cmus_rich.core.cmus_interface import CMUSInterface
from cmus_rich.core.config import ConfigManager
from cmus_rich.core.events import EventBus
from cmus_rich.core.state import AppState


@dataclass
class AppConfig:
    """Application configuration."""

    refresh_rate: float = 0.1  # 10 FPS minimum
    debug_mode: bool = False
    single_instance: bool = True
    cache_size_mb: int = 50
    thread_pool_size: int = 4


class CMUSRichApp:
    """Main application controller."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.console = Console()
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        self.state = AppState()
        self.event_bus = EventBus()
        self.cmus = CMUSInterface()
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def initialize(self) -> None:
        """Initialize all application components."""
        # Check single instance
        if self.config.single_instance:
            await self._ensure_single_instance()

        # Initialize CMUS connection
        try:
            await self.cmus.connect()
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not connect to CMUS: {e}[/yellow]")
            self.console.print("[yellow]Please ensure CMUS is running or will be started.[/yellow]")

        # Setup signal handlers
        self._setup_signal_handlers()

        # Load saved state
        await self.state.load()

    async def run(self) -> None:
        """Main application loop."""
        self._running = True

        try:
            # Start background tasks
            self._tasks.append(asyncio.create_task(self._update_loop()))
            self._tasks.append(asyncio.create_task(self.event_bus.process_events()))

            # Start config watcher if auto-reload enabled
            if self.config.auto_save:
                self._tasks.append(asyncio.create_task(self.config_manager.watch_changes()))

            # Simple status display for now
            self.console.print("[cyan]CMUS Rich Player Starting...[/cyan]")
            self.console.print(f"[dim]Config: {self.config_manager.config_path}[/dim]")
            self.console.print("[green]Press Ctrl+C to exit[/green]\n")

            # Keep running
            while self._running:
                await asyncio.sleep(0.1)

        finally:
            await self.shutdown()

    async def _update_loop(self) -> None:
        """Background update loop for live data."""
        while self._running:
            try:
                # Update player status
                if self.cmus._connected:
                    status = await self.cmus.get_status()
                    self.state.update_player_status(status)

                    # Simple status output
                    if status.track:
                        track = status.track
                        self.console.print(
                            f"\r[cyan]♪[/cyan] {track.title or 'Unknown'} - "
                            f"{track.artist or 'Unknown Artist'} "
                            f"[dim]({status.status})[/dim]",
                            end="",
                        )

                # Sleep for refresh interval
                await asyncio.sleep(self.config.refresh_rate)

            except Exception as e:
                if self.config.log_level == "DEBUG":
                    self.console.print(f"\n[dim red]Error in update loop: {e}[/dim red]")
                await asyncio.sleep(1)  # Back off on errors

    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers."""
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum: int, frame: any) -> None:
        """Handle shutdown signals."""
        self._running = False

    async def _ensure_single_instance(self) -> None:
        """Ensure only one instance is running."""
        lock_file = Path("~/.cache/cmus-rich/instance.lock").expanduser()
        lock_file.parent.mkdir(parents=True, exist_ok=True)

        if lock_file.exists():
            try:
                # Check if process is still running
                with open(lock_file) as f:
                    pid = int(f.read().strip())

                # Try to send signal 0 to check if process exists
                import os

                try:
                    os.kill(pid, 0)
                    # Process exists
                    self.console.print(
                        "[red]Another instance of CMUS Rich is already running.[/red]"
                    )
                    sys.exit(1)
                except OSError:
                    # Process doesn't exist, remove stale lock
                    lock_file.unlink()
            except Exception:
                # Invalid lock file, remove it
                lock_file.unlink()

        # Create lock file
        with open(lock_file, "w") as f:
            import os

            f.write(str(os.getpid()))

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        self.console.print("\n\n[yellow]Shutting down...[/yellow]")
        self._running = False

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Stop event processing
        self.event_bus.stop_processing()

        # Save state
        if self.config.auto_save:
            await self.state.save()

        # Cleanup
        await self.cmus.disconnect()

        # Remove lock file
        lock_file = Path("~/.cache/cmus-rich/instance.lock").expanduser()
        if lock_file.exists():
            lock_file.unlink()

        self.console.print("[green]Goodbye![/green]")
