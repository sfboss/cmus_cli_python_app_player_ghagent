"""CMUS remote control interface."""

import asyncio
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TrackInfo:
    """Track information container."""

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
    """Player status information."""

    status: str  # playing, paused, stopped
    track: Optional[TrackInfo] = None
    volume: int = 100
    repeat: bool = False
    shuffle: bool = False


class CMUSInterface:
    """CMUS remote control interface."""

    def __init__(self) -> None:
        self._socket_path: Optional[str] = None
        self._process: Optional[asyncio.subprocess.Process] = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to CMUS instance."""
        # Try to connect to existing instance
        socket_path = self._find_socket()

        if socket_path:
            self._socket_path = socket_path
            self._connected = True
        else:
            # Start new CMUS instance
            await self._start_cmus()

    async def _start_cmus(self) -> None:
        """Start CMUS process."""
        self._process = await asyncio.create_subprocess_exec(
            "cmus",
            "--listen",
            "/tmp/cmus-socket",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Wait for socket to be available
        for _ in range(10):
            await asyncio.sleep(0.5)
            if self._find_socket():
                self._connected = True
                return

        raise ConnectionError("Failed to start CMUS")

    def _find_socket(self) -> Optional[str]:
        """Find CMUS socket path."""
        # Check common locations
        paths = [
            "/tmp/cmus-socket",
            f"{os.environ.get('HOME', '')}/.cmus/socket",
            f"{os.environ.get('XDG_RUNTIME_DIR', '')}/cmus-socket",
        ]

        for path in paths:
            if path and os.path.exists(path):
                return path

        return None

    async def execute_command(self, command: str) -> str:
        """Execute CMUS remote command."""
        if not self._connected:
            raise ConnectionError("Not connected to CMUS")

        cmd_parts = ["cmus-remote"] + command.split()
        proc = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"CMUS command failed: {stderr.decode()}")

        return stdout.decode()

    async def get_status(self) -> PlayerStatus:
        """Get current player status."""
        output = await self.execute_command("-Q")
        return self._parse_status(output)

    def _parse_status(self, output: str) -> PlayerStatus:
        """Parse CMUS status output."""
        lines = output.strip().split("\n")
        status = PlayerStatus(status="stopped")
        track_info: dict[str, any] = {}

        for line in lines:
            if line.startswith("status "):
                status.status = line.split()[1]
            elif line.startswith("file "):
                track_info["file"] = line[5:]
            elif line.startswith("tag "):
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    tag_name = parts[1]
                    tag_value = parts[2]
                    track_info[tag_name.lower()] = tag_value
            elif line.startswith("duration "):
                track_info["duration"] = int(line.split()[1])
            elif line.startswith("position "):
                track_info["position"] = int(line.split()[1])
            elif line.startswith("set vol_left ") or line.startswith("set vol_right "):
                # Extract volume (use left channel)
                if line.startswith("set vol_left "):
                    status.volume = int(line.split()[2])
            elif line.startswith("set repeat "):
                status.repeat = line.split()[2] == "true"
            elif line.startswith("set shuffle "):
                status.shuffle = line.split()[2] == "true"

        if track_info.get("file"):
            status.track = TrackInfo(**track_info)

        return status

    # Playback control methods
    async def play(self) -> None:
        """Start playback."""
        await self.execute_command("-p")

    async def pause(self) -> None:
        """Toggle pause."""
        await self.execute_command("-u")

    async def stop(self) -> None:
        """Stop playback."""
        await self.execute_command("-s")

    async def next(self) -> None:
        """Skip to next track."""
        await self.execute_command("-n")

    async def previous(self) -> None:
        """Go to previous track."""
        await self.execute_command("-r")

    async def seek(self, position: int) -> None:
        """Seek to position in seconds."""
        await self.execute_command(f"-k {position}")

    async def set_volume(self, volume: int) -> None:
        """Set volume (0-100)."""
        await self.execute_command(f"-v {volume}%")

    async def disconnect(self) -> None:
        """Disconnect from CMUS."""
        self._connected = False
        if self._process:
            self._process.terminate()
            await self._process.wait()
