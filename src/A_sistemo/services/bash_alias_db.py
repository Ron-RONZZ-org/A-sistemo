"""Bash alias database service."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class BashAlias:
    uid: int
    alias: str
    function: str
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class BashAliasDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = None
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS aliases (
                uid INTEGER PRIMARY KEY,
                alias TEXT UNIQUE NOT NULL,
                function TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alias ON aliases(alias)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON aliases(created_at)")
        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def _close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def add_alias(self, alias: str, function: str, notes: Optional[str] = None) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO aliases (alias, function, notes, created_at)
            VALUES (?, ?, ?, ?)
        """, (alias, function, notes, now))
        uid = cursor.lastrowid
        conn.commit()
        return uid

    def get_alias(self, uid: int) -> Optional[BashAlias]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT uid, alias, function, notes, created_at, updated_at FROM aliases WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        if not row:
            return None
        return BashAlias(
            uid=row[0], alias=row[1], function=row[2],
            notes=row[3], created_at=row[4], updated_at=row[5]
        )

    def list_aliases(self, sort_by: str = "created_at", descending: bool = True) -> list[BashAlias]:
        # Validate sort_by to prevent injection
        valid_sort = {"alias", "created_at", "updated_at"}
        if sort_by not in valid_sort:
            sort_by = "created_at"
        order = "DESC" if descending else "ASC"
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT uid, alias, function, notes, created_at, updated_at FROM aliases ORDER BY {sort_by} {order}")
        rows = cursor.fetchall()
        return [
            BashAlias(
                uid=r[0], alias=r[1], function=r[2],
                notes=r[3], created_at=r[4], updated_at=r[5]
            )
            for r in rows
        ]

    def update_alias(self, uid: int, alias: Optional[str] = None,
                    function: Optional[str] = None, notes: Optional[str] = None) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
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
            cursor.execute(f"UPDATE aliases SET {', '.join(updates)} WHERE uid = ?", values)
            conn.commit()
        return cursor.rowcount > 0

    def delete_alias(self, uid: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM aliases WHERE uid = ?", (uid,))
        conn.commit()
        return cursor.rowcount > 0

    def search_aliases(self, query: str) -> list[BashAlias]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT uid, alias, function, notes, created_at, updated_at FROM aliases
            WHERE alias LIKE ? OR function LIKE ? OR notes LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        rows = cursor.fetchall()
        return [
            BashAlias(
                uid=r[0], alias=r[1], function=r[2],
                notes=r[3], created_at=r[4], updated_at=r[5]
            )
            for r in rows
        ]

    def sync_shell_config(self) -> None:
        """Sync aliases to shell config."""
        aliases = self.list_aliases()
        output = ["#!/bin/bash", "# Auto-generated bash alias-oj", ""]
        for a in aliases:
            output.append(f'alias {a.alias}="{a.function}"')
        config = Path.home() / ".bash_aliases"
        config.write_text("\n".join(output) + "\n")

    def close(self) -> None:
        """Close database connection."""
        self._close()

    def __del__(self) -> None:
        self._close()


__all__ = ["BashAlias", "BashAliasDB"]