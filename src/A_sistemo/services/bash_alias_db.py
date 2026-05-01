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
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
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
        conn.commit()
        conn.close()

    def add_alias(self, alias: str, function: str, notes: Optional[str] = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO aliases (alias, function, notes, created_at)
            VALUES (?, ?, ?, ?)
        """, (alias, function, notes, now))
        uid = cursor.lastrowid
        conn.commit()
        conn.close()
        return uid

    def get_alias(self, uid: int) -> Optional[BashAlias]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM aliases WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return BashAlias(
            uid=row[0], alias=row[1], function=row[2],
            notes=row[3], created_at=row[4], updated_at=row[5]
        )

    def list_aliases(self, sort_by: str = "created_at", descending: bool = True) -> list[BashAlias]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        order = "DESC" if descending else "ASC"
        cursor.execute(f"SELECT * FROM aliases ORDER BY {sort_by} {order}")
        rows = cursor.fetchall()
        conn.close()
        return [
            BashAlias(
                uid=r[0], alias=r[1], function=r[2],
                notes=r[3], created_at=r[4], updated_at=r[5]
            )
            for r in rows
        ]

    def update_alias(self, uid: int, alias: Optional[str] = None,
                    function: Optional[str] = None, notes: Optional[str] = None) -> bool:
        conn = sqlite3.connect(self.db_path)
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
        conn.close()
        return cursor.rowcount > 0

    def delete_alias(self, uid: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM aliases WHERE uid = ?", (uid,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    def search_aliases(self, query: str) -> list[BashAlias]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM aliases
            WHERE alias LIKE ? OR function LIKE ? OR notes LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        rows = cursor.fetchall()
        conn.close()
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


__all__ = ["BashAlias", "BashAliasDB"]