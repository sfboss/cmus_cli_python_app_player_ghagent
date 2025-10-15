"""Search and filtering engine."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from cmus_rich.core.cmus_interface import TrackInfo
from cmus_rich.utils.db import DatabaseHelper


class SearchField(Enum):
    """Search field options."""

    ALL = "all"
    TITLE = "title"
    ARTIST = "artist"
    ALBUM = "album"
    GENRE = "genre"
    YEAR = "year"


@dataclass
class SearchQuery:
    """Search query representation."""

    text: str
    field: SearchField = SearchField.ALL
    case_sensitive: bool = False
    limit: Optional[int] = None


class SearchEngine:
    """Advanced search and filtering."""

    def __init__(self, db_path: str = "~/.local/share/cmus-rich/library.db") -> None:
        self.db = DatabaseHelper(db_path)
        self.search_history: list[SearchQuery] = []

    async def search(self, query: SearchQuery) -> list[TrackInfo]:
        """Execute search query."""
        # Add to history
        self.search_history.append(query)
        if len(self.search_history) > 100:
            self.search_history.pop(0)

        # Build SQL query
        sql, params = self._build_sql(query)

        # Execute query
        self.db.connect()
        try:
            cursor = self.db.execute(sql, params)
            results = []

            for row in cursor:
                results.append(self._row_to_track(row))

            return results
        finally:
            self.db.disconnect()

    def _build_sql(self, query: SearchQuery) -> tuple[str, list]:
        """Build SQL query from search query."""
        base_sql = "SELECT * FROM tracks WHERE "

        if query.field == SearchField.ALL:
            # Search all text fields
            conditions = []
            params = []
            for field in ["title", "artist", "album", "genre"]:
                if query.case_sensitive:
                    conditions.append(f"{field} LIKE ?")
                else:
                    conditions.append(f"LOWER({field}) LIKE LOWER(?)")
                params.append(f"%{query.text}%")
            condition = " OR ".join(conditions)
        else:
            # Search specific field
            field = query.field.value
            if query.case_sensitive:
                condition = f"{field} LIKE ?"
            else:
                condition = f"LOWER({field}) LIKE LOWER(?)"
            params = [f"%{query.text}%"]

        sql = base_sql + condition

        if query.limit:
            sql += f" LIMIT {query.limit}"

        return sql, params

    def _row_to_track(self, row: Any) -> TrackInfo:
        """Convert database row to TrackInfo."""
        return TrackInfo(
            file=row["file_path"],
            title=row["title"],
            artist=row["artist"],
            album=row["album"],
            genre=row["genre"],
            duration=row["duration"],
            date=str(row["year"]) if row["year"] else None,
        )

    async def get_all_artists(self) -> list[str]:
        """Get all unique artists."""
        self.db.connect()
        try:
            cursor = self.db.execute(
                "SELECT DISTINCT artist FROM tracks WHERE artist IS NOT NULL ORDER BY artist"
            )
            return [row["artist"] for row in cursor]
        finally:
            self.db.disconnect()

    async def get_all_albums(self) -> list[dict[str, str]]:
        """Get all unique albums."""
        self.db.connect()
        try:
            cursor = self.db.execute(
                """
                SELECT DISTINCT album, artist
                FROM tracks
                WHERE album IS NOT NULL
                ORDER BY artist, album
                """
            )
            return [{"album": row["album"], "artist": row["artist"]} for row in cursor]
        finally:
            self.db.disconnect()

    async def get_tracks_by_artist(self, artist: str) -> list[TrackInfo]:
        """Get all tracks by an artist."""
        query = SearchQuery(text=artist, field=SearchField.ARTIST)
        return await self.search(query)

    async def get_tracks_by_album(
        self, album: str, artist: Optional[str] = None
    ) -> list[TrackInfo]:
        """Get all tracks from an album."""
        self.db.connect()
        try:
            if artist:
                sql = "SELECT * FROM tracks WHERE album = ? AND artist = ? ORDER BY track_number"
                cursor = self.db.execute(sql, (album, artist))
            else:
                sql = "SELECT * FROM tracks WHERE album = ? ORDER BY track_number"
                cursor = self.db.execute(sql, (album,))

            return [self._row_to_track(row) for row in cursor]
        finally:
            self.db.disconnect()
