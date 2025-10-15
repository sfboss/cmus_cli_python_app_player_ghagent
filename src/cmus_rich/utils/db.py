"""Database helper utilities."""

import sqlite3
from pathlib import Path
from typing import Any, Optional


class DatabaseHelper:
    """SQLite database helper."""

    def __init__(self, db_path: str = "~/.local/share/cmus-rich/library.db") -> None:
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Connect to database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    def disconnect(self) -> None:
        """Disconnect from database."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query."""
        if not self.conn:
            self.connect()
        return self.conn.execute(query, params)

    def commit(self) -> None:
        """Commit changes."""
        if self.conn:
            self.conn.commit()

    def init_schema(self) -> None:
        """Initialize database schema."""
        if not self.conn:
            self.connect()

        # Tracks table
        self.conn.execute(
            """
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
                last_modified REAL,
                play_count INTEGER DEFAULT 0,
                skip_count INTEGER DEFAULT 0,
                rating INTEGER,
                last_played REAL,
                added_date REAL
            )
        """
        )

        # Create indices
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_artist ON tracks(artist)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_album ON tracks(album)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_genre ON tracks(genre)")

        # Play history table
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS play_history (
                id INTEGER PRIMARY KEY,
                track_id INTEGER,
                started_at REAL,
                completed BOOLEAN,
                skip_position INTEGER,
                FOREIGN KEY (track_id) REFERENCES tracks(id)
            )
        """
        )

        self.commit()

    def __enter__(self) -> "DatabaseHelper":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()
