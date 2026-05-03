"""Bash alias database service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from A.data.base import SQLiteDB


@dataclass
class BashAlias:
    uid: int
    alias: str
    function: str
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# Schema for the aliases table
SCHEMA = {
    "aliases": """
        CREATE TABLE IF NOT EXISTS aliases (
            uid INTEGER PRIMARY KEY,
            alias TEXT UNIQUE NOT NULL,
            function TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """,
    "idx_alias": "CREATE INDEX IF NOT EXISTS idx_alias ON aliases(alias)",
    "idx_created_at": "CREATE INDEX IF NOT EXISTS idx_created_at ON aliases(created_at)",
}


class BashAliasDB:
    """Bash alias database using A.data.base.SQLiteDB."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Use A's SQLiteDB with schema
        self._db = SQLiteDB(db_path, SCHEMA)

    def _row_to_alias(self, row: dict) -> BashAlias:
        """Convert database row to BashAlias dataclass."""
        return BashAlias(
            uid=row["uid"],
            alias=row["alias"],
            function=row["function"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def add_alias(self, alias: str, function: str, notes: Optional[str] = None) -> int:
        """Add a new bash alias."""
        now = datetime.now().isoformat()
        with self._db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO aliases (alias, function, notes, created_at) VALUES (?, ?, ?, ?)",
                (alias, function, notes, now),
            )
            return cursor.lastrowid

    def get_alias(self, uid: int) -> Optional[BashAlias]:
        """Get alias by uid."""
        row = self._db.execute_one(
            "SELECT uid, alias, function, notes, created_at, updated_at FROM aliases WHERE uid = ?",
            (uid,),
        )
        return self._row_to_alias(row) if row else None

    def list_aliases(self, sort_by: str = "created_at", descending: bool = True) -> list[BashAlias]:
        """List all aliases."""
        # Validate sort_by to prevent injection
        valid_sort = {"alias", "created_at", "updated_at"}
        if sort_by not in valid_sort:
            sort_by = "created_at"
        order = "DESC" if descending else "ASC"
        rows = self._db.execute(
            f"SELECT uid, alias, function, notes, created_at, updated_at FROM aliases ORDER BY {sort_by} {order}"
        )
        return [self._row_to_alias(r) for r in rows]

    def update_alias(
        self, uid: int, alias: Optional[str] = None, function: Optional[str] = None, notes: Optional[str] = None
    ) -> bool:
        """Update an existing alias."""
        updates = []
        values = []
        if alias:
            updates.append("alias = ?")
            values.append(alias)
        if function:
            updates.append("function = ?")
            values.append(function)
        if notes is not None:
            updates.append("notes = ?")
            values.append(notes)
        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(uid)
            with self._db.transaction() as conn:
                conn.execute(f"UPDATE aliases SET {', '.join(updates)} WHERE uid = ?", tuple(values))
            return True
        return False

    def delete_alias(self, uid: int) -> bool:
        """Delete an alias by uid."""
        with self._db.transaction() as conn:
            conn.execute("DELETE FROM aliases WHERE uid = ?", (uid,))
        return True

    def search_aliases(self, query: str) -> list[BashAlias]:
        """Search aliases by alias, function, or notes."""
        rows = self._db.execute(
            "SELECT uid, alias, function, notes, created_at, updated_at FROM aliases "
            "WHERE alias LIKE ? OR function LIKE ? OR notes LIKE ?",
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        )
        return [self._row_to_alias(r) for r in rows]

    def sync_shell_config(self) -> None:
        """Sync aliases to shell config."""
        aliases = self.list_aliases()
        output = ["#!/bin/bash", "# Auto-generated bash alias-oj", ""]
        for a in aliases:
            output.append(f'alias {a.alias}="{a.function}"')
        config = Path.home() / ".bash_aliases"
        config.write_text("\n".join(output) + "\n")

    def close(self) -> None:
        """Close database connection (no-op for SQLiteDB)."""
        pass


__all__ = ["BashAlias", "BashAliasDB"]