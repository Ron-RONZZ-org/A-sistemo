"""Espanso match database service.

Manages espanso text expansion matches in a SQLite database.
Generates a read-only YAML file consumed by espanso.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from A.data.base import SQLiteDB


# Espanso match directory
_ESPANSO_MATCH_DIR = Path.home() / ".config" / "espanso" / "match"
_A_ESPANSO_FILE = _ESPANSO_MATCH_DIR / "A_espanso.yml"


@dataclass
class EspansoMatch:
    """Represents a single espanso text expansion match."""

    uid: int
    trigger: str
    replace_text: str
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# Schema for the matches table
SCHEMA = {
    "matches": """
        CREATE TABLE IF NOT EXISTS matches (
            uid INTEGER PRIMARY KEY,
            trigger TEXT UNIQUE NOT NULL,
            replace_text TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """,
    "idx_trigger": "CREATE INDEX IF NOT EXISTS idx_trigger ON matches(trigger)",
    "idx_created_at": "CREATE INDEX IF NOT EXISTS idx_created_at2 ON matches(created_at)",
}


class EspansoMatchDB:
    """Espanso match database using A.data.base.SQLiteDB."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = SQLiteDB(db_path, SCHEMA)

    def _row_to_match(self, row: dict) -> EspansoMatch:
        """Convert database row to EspansoMatch dataclass."""
        return EspansoMatch(
            uid=row["uid"],
            trigger=row["trigger"],
            replace_text=row["replace_text"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def add_match(self, trigger: str, replace_text: str, notes: Optional[str] = None) -> int:
        """Add a new espanso match."""
        now = datetime.now(timezone.utc).isoformat()
        with self._db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO matches (trigger, replace_text, notes, created_at) VALUES (?, ?, ?, ?)",
                (trigger, replace_text, notes, now),
            )
            return cursor.lastrowid

    def get_match(self, uid: int) -> Optional[EspansoMatch]:
        """Get match by uid."""
        row = self._db.execute_one(
            "SELECT uid, trigger, replace_text, notes, created_at, updated_at FROM matches WHERE uid = ?",
            (uid,),
        )
        return self._row_to_match(row) if row else None

    def list_matches(self, sort_by: str = "created_at", descending: bool = True) -> list[EspansoMatch]:
        """List all matches."""
        valid_sort = {"trigger", "created_at", "updated_at"}
        if sort_by not in valid_sort:
            sort_by = "created_at"
        order = "DESC" if descending else "ASC"
        rows = self._db.execute(
            f"SELECT uid, trigger, replace_text, notes, created_at, updated_at FROM matches ORDER BY {sort_by} {order}"
        )
        return [self._row_to_match(r) for r in rows]

    def update_match(
        self,
        uid: int,
        trigger: Optional[str] = None,
        replace_text: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Update an existing match."""
        updates = []
        values = []
        if trigger is not None:
            updates.append("trigger = ?")
            values.append(trigger)
        if replace_text is not None:
            updates.append("replace_text = ?")
            values.append(replace_text)
        if notes is not None:
            updates.append("notes = ?")
            values.append(notes)
        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now(timezone.utc).isoformat())
            values.append(uid)
            with self._db.transaction() as conn:
                conn.execute(f"UPDATE matches SET {', '.join(updates)} WHERE uid = ?", tuple(values))
            return True
        return False

    def delete_match(self, uid: int) -> bool:
        """Delete a match by uid."""
        with self._db.transaction() as conn:
            conn.execute("DELETE FROM matches WHERE uid = ?", (uid,))
        return True

    def search_matches(self, query: str) -> list[EspansoMatch]:
        """Search matches by trigger, replace_text, or notes."""
        rows = self._db.execute(
            "SELECT uid, trigger, replace_text, notes, created_at, updated_at FROM matches "
            "WHERE trigger LIKE ? OR replace_text LIKE ? OR notes LIKE ?",
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        )
        return [self._row_to_match(r) for r in rows]

    def sync_espanso_config(self) -> None:
        """Sync matches to espanso match file (generated, read-only)."""
        matches = self.list_matches()
        lines = ["matches:"]
        for m in matches:
            trigger_val = m.trigger
            replace_val = m.replace_text
            # Use single quotes for clean YAML quoting
            lines.append(f'- trigger: \'{trigger_val}\'')
            lines.append(f"  replace: '{replace_val}'")

        # Ensure espanso match directory exists
        _ESPANSO_MATCH_DIR.mkdir(parents=True, exist_ok=True)

        config = _A_ESPANSO_FILE
        if config.exists():
            config.chmod(0o644)  # Make writable before overwriting
        config.write_text("\n".join(lines) + "\n")
        config.chmod(0o444)  # Read-only to prevent user edits

    def close(self) -> None:
        """Close database connection (no-op for SQLiteDB)."""
        pass


def migrate_from_existing(target_db: EspansoMatchDB) -> dict:
    """Import existing espanso match files into the A database.

    Reads all .yml files from ~/.config/espanso/match/ (except A_espanso.yml)
    and imports any matches found.

    Args:
        target_db: Target EspansoMatchDB to migrate into

    Returns:
        Dict with migration results
    """
    results = {
        "files_found": 0,
        "matches_found": 0,
        "migrated": 0,
        "skipped": 0,
        "errors": [],
    }

    if not _ESPANSO_MATCH_DIR.exists():
        return results

    # Get existing triggers for idempotency
    existing = {m.trigger for m in target_db.list_matches()}

    for yml_path in sorted(_ESPANSO_MATCH_DIR.glob("*.yml")):
        # Skip our own generated file
        if yml_path.name == "A_espanso.yml":
            continue

        results["files_found"] += 1

        # Simple YAML parser for espanso match format.
        # We parse line-by-line instead of using yaml lib to avoid a dependency.
        matches = _parse_espanso_yml(yml_path)
        results["matches_found"] += len(matches)

        for trigger, replace_text in matches:
            if trigger in existing:
                results["skipped"] += 1
                continue

            try:
                target_db.add_match(trigger=trigger, replace_text=replace_text)
                results["migrated"] += 1
                existing.add(trigger)
            except Exception as e:
                results["errors"].append(f"{trigger} ({yml_path.name}): {e}")

    return results


def _parse_espanso_yml(path: Path) -> list[tuple[str, str]]:
    """Simple line-based parser for espanso match YAML files.

    Only handles basic format:
        matches:
        - trigger: ':xyz'
          replace: 'text'

    Args:
        path: Path to YAML file

    Returns:
        List of (trigger, replace_text) tuples
    """
    content = path.read_text()
    matches: list[tuple[str, str]] = []
    current_trigger = None
    current_replace = None

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Detect trigger field
        trigger_match = re.match(r"^-?\s*trigger:\s*'([^']*)'", stripped)
        if trigger_match:
            # Save previous pair if exists
            if current_trigger is not None and current_replace is not None:
                matches.append((current_trigger, current_replace))
            current_trigger = trigger_match.group(1)
            current_replace = None
            continue

        # Detect replace field
        replace_match = re.match(r"^\s*replace:\s*'([^']*)'", stripped)
        if replace_match and current_trigger is not None:
            current_replace = replace_match.group(1)

        # Handle unquoted values
        if current_replace is None:
            replace_match = re.match(r"^\s*replace:\s*\"([^\"]*)\"", stripped)
            if replace_match and current_trigger is not None:
                current_replace = replace_match.group(1)

        if current_replace is None:
            replace_match = re.match(r"^\s*replace:\s*(\S.*)", stripped)
            if replace_match and current_trigger is not None:
                current_replace = replace_match.group(1)

    # Save last pair
    if current_trigger is not None and current_replace is not None:
        matches.append((current_trigger, current_replace))

    return matches


__all__ = ["EspansoMatch", "EspansoMatchDB", "migrate_from_existing"]
