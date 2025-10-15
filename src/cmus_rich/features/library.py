"""Library management and scanning."""

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Optional

import mutagen

from cmus_rich.utils.db import DatabaseHelper


class LibraryScanner:
    """Scan and index music library."""

    def __init__(self, db_path: str = "~/.local/share/cmus-rich/library.db") -> None:
        self.db = DatabaseHelper(db_path)
        self.db.init_schema()

    async def scan_directory(
        self, path: str, recursive: bool = True
    ) -> dict[str, int]:
        """Scan directory for music files."""
        path_obj = Path(path).expanduser()
        if not path_obj.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        extensions = {".mp3", ".flac", ".ogg", ".m4a", ".opus", ".wav"}
        files_found = 0
        files_processed = 0
        files_skipped = 0

        self.db.connect()

        try:
            for file_path in self._walk_directory(path_obj, recursive):
                files_found += 1

                if file_path.suffix.lower() in extensions:
                    success = await self._process_file(file_path)
                    if success:
                        files_processed += 1
                    else:
                        files_skipped += 1

                    # Yield control periodically
                    if files_found % 100 == 0:
                        await asyncio.sleep(0)

            self.db.commit()

        finally:
            self.db.disconnect()

        return {
            "found": files_found,
            "processed": files_processed,
            "skipped": files_skipped,
        }

    def _walk_directory(self, path: Path, recursive: bool):
        """Walk directory tree."""
        if recursive:
            for root, dirs, files in os.walk(path):
                for file in files:
                    yield Path(root) / file
        else:
            for file in path.iterdir():
                if file.is_file():
                    yield file

    async def _process_file(self, file_path: Path) -> bool:
        """Process single music file."""
        try:
            # Get file metadata
            metadata = mutagen.File(str(file_path))
            if metadata is None:
                return False

            # Calculate file hash for duplicate detection
            file_hash = self._calculate_hash(file_path)

            # Check if already in database
            existing = self.db.execute(
                "SELECT file_hash FROM tracks WHERE file_path = ?",
                (str(file_path),),
            ).fetchone()

            if existing and existing[0] == file_hash:
                return True  # File unchanged

            # Extract metadata
            track_data = {
                "file_path": str(file_path),
                "file_hash": file_hash,
                "title": self._get_tag(metadata, "title"),
                "artist": self._get_tag(metadata, "artist"),
                "album": self._get_tag(metadata, "album"),
                "genre": self._get_tag(metadata, "genre"),
                "year": self._get_tag_int(metadata, "date"),
                "duration": int(metadata.info.length) if metadata.info else None,
                "track_number": self._get_tag_int(metadata, "tracknumber"),
                "disc_number": self._get_tag_int(metadata, "discnumber"),
                "album_artist": self._get_tag(metadata, "albumartist"),
                "last_modified": file_path.stat().st_mtime,
                "added_date": file_path.stat().st_mtime,
            }

            # Insert or update in database
            self._upsert_track(track_data)
            return True

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate file hash for duplicate detection."""
        hasher = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                # Read first and last 1MB for performance
                chunk = f.read(1024 * 1024)
                hasher.update(chunk)

                # Try to seek to end
                try:
                    f.seek(-1024 * 1024, 2)
                    chunk = f.read(1024 * 1024)
                    hasher.update(chunk)
                except (OSError, IOError):
                    # File smaller than 2MB
                    pass

            return hasher.hexdigest()
        except Exception:
            return ""

    def _get_tag(self, metadata: mutagen.File, tag_name: str) -> Optional[str]:
        """Get tag value from metadata."""
        if not metadata or not metadata.tags:
            return None

        # Try different tag formats
        tag_variants = [tag_name, tag_name.upper(), tag_name.lower()]

        for variant in tag_variants:
            if variant in metadata.tags:
                value = metadata.tags[variant]
                if isinstance(value, list) and value:
                    return str(value[0])
                return str(value)

        return None

    def _get_tag_int(self, metadata: mutagen.File, tag_name: str) -> Optional[int]:
        """Get integer tag value from metadata."""
        value = self._get_tag(metadata, tag_name)
        if value:
            try:
                # Extract numbers from string (e.g., "1/10" -> 1)
                return int(value.split("/")[0])
            except (ValueError, IndexError):
                pass
        return None

    def _upsert_track(self, track_data: dict) -> None:
        """Insert or update track in database."""
        # Check if track exists
        existing = self.db.execute(
            "SELECT id FROM tracks WHERE file_path = ?",
            (track_data["file_path"],),
        ).fetchone()

        if existing:
            # Update existing track
            self.db.execute(
                """
                UPDATE tracks SET
                    file_hash = ?,
                    title = ?,
                    artist = ?,
                    album = ?,
                    genre = ?,
                    year = ?,
                    duration = ?,
                    track_number = ?,
                    disc_number = ?,
                    album_artist = ?,
                    last_modified = ?
                WHERE file_path = ?
            """,
                (
                    track_data["file_hash"],
                    track_data["title"],
                    track_data["artist"],
                    track_data["album"],
                    track_data["genre"],
                    track_data["year"],
                    track_data["duration"],
                    track_data["track_number"],
                    track_data["disc_number"],
                    track_data["album_artist"],
                    track_data["last_modified"],
                    track_data["file_path"],
                ),
            )
        else:
            # Insert new track
            self.db.execute(
                """
                INSERT INTO tracks (
                    file_path, file_hash, title, artist, album, genre, year,
                    duration, track_number, disc_number, album_artist,
                    last_modified, added_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    track_data["file_path"],
                    track_data["file_hash"],
                    track_data["title"],
                    track_data["artist"],
                    track_data["album"],
                    track_data["genre"],
                    track_data["year"],
                    track_data["duration"],
                    track_data["track_number"],
                    track_data["disc_number"],
                    track_data["album_artist"],
                    track_data["last_modified"],
                    track_data["added_date"],
                ),
            )
