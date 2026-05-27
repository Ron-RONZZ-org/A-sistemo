"""Bash function database service.

Manages multiline bash functions in a SQLite database.
Generates a read-only shell script consumed by bash.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from A.data.base import SQLiteDB


# Generated file path
_A_BASH_FUNCTIONS = Path.home() / ".A_bash_functions"


@dataclass
class BashFunction:
    """Represents a stored bash function."""

    uid: int
    name: str
    body: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# Schema for the functions table
SCHEMA = {
    "functions": """
        CREATE TABLE IF NOT EXISTS functions (
            uid INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """,
    "idx_name": "CREATE INDEX IF NOT EXISTS idx_name ON functions(name)",
    "idx_created_at": "CREATE INDEX IF NOT EXISTS idx_ct3 ON functions(created_at)",
}


class BashFunctionDB:
    """Bash function database using A.data.base.SQLiteDB."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = SQLiteDB(db_path, SCHEMA)

    def _row_to_function(self, row: dict) -> BashFunction:
        """Convert database row to BashFunction dataclass."""
        return BashFunction(
            uid=row["uid"],
            name=row["name"],
            body=row["body"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def add_function(self, name: str, body: str) -> int:
        """Add a new bash function.

        Args:
            name: Function name
            body: Function body (inside the braces, without the name() { } wrapper)

        Returns:
            UID of the new function
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO functions (name, body, created_at) VALUES (?, ?, ?)",
                (name, body, now),
            )
            return cursor.lastrowid

    def get_function(self, uid: int) -> Optional[BashFunction]:
        """Get function by uid."""
        row = self._db.execute_one(
            "SELECT uid, name, body, created_at, updated_at FROM functions WHERE uid = ?",
            (uid,),
        )
        return self._row_to_function(row) if row else None

    def get_function_by_name(self, name: str) -> Optional[BashFunction]:
        """Get function by name."""
        row = self._db.execute_one(
            "SELECT uid, name, body, created_at, updated_at FROM functions WHERE name = ?",
            (name,),
        )
        return self._row_to_function(row) if row else None

    def list_functions(self, sort_by: str = "created_at", descending: bool = True) -> list[BashFunction]:
        """List all stored functions."""
        valid_sort = {"name", "created_at", "updated_at"}
        if sort_by not in valid_sort:
            sort_by = "created_at"
        order = "DESC" if descending else "ASC"
        rows = self._db.execute(
            f"SELECT uid, name, body, created_at, updated_at FROM functions ORDER BY {sort_by} {order}"
        )
        return [self._row_to_function(r) for r in rows]

    def update_function(
        self,
        uid: int,
        name: Optional[str] = None,
        body: Optional[str] = None,
    ) -> bool:
        """Update an existing function."""
        updates = []
        values = []
        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if body is not None:
            updates.append("body = ?")
            values.append(body)
        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now(timezone.utc).isoformat())
            values.append(uid)
            with self._db.transaction() as conn:
                conn.execute(f"UPDATE functions SET {', '.join(updates)} WHERE uid = ?", tuple(values))
            return True
        return False

    def delete_function(self, uid: int) -> bool:
        """Delete a function by uid."""
        with self._db.transaction() as conn:
            cursor = conn.execute("DELETE FROM functions WHERE uid = ?", (uid,))
            return cursor.rowcount > 0

    def search_functions(self, query: str) -> list[BashFunction]:
        """Search functions by name or body."""
        rows = self._db.execute(
            "SELECT uid, name, body, created_at, updated_at FROM functions "
            "WHERE name LIKE ? OR body LIKE ? "
            "ORDER BY name",
            (f"%{query}%", f"%{query}%"),
        )
        return [self._row_to_function(r) for r in rows]

    def sync_shell_config(self) -> None:
        """Sync functions to shell config file (generated, read-only)."""
        functions = self.list_functions()
        lines = [
            "#!/bin/bash",
            "# Auto-generated by A, DO NOT EDIT",
            "",
        ]
        for f in functions:
            lines.append(f"{f.name}() {{")
            lines.append(f.body)
            lines.append("}")
            lines.append("")

        config = _A_BASH_FUNCTIONS
        if config.exists():
            config.chmod(0o644)
        config.write_text("\n".join(lines) + "\n")
        config.chmod(0o444)

    def close(self) -> None:
        """Close database connection (no-op for SQLiteDB)."""
        pass


def parse_function_file(path: Path) -> tuple[str, str]:
    """Parse a single bash function definition from a file.

    Extracts the function name and the body (content between braces).
    Only the first function definition in the file is returned.

    Args:
        path: Path to file containing the function definition

    Returns:
        Tuple of (name, body)

    Raises:
        ValueError: If the file doesn't contain a valid function definition
    """
    functions = parse_functions_from_file(path)
    return functions[0]  # Guaranteed non-empty by parse_functions_from_file


def parse_functions_from_file(path: Path) -> list[tuple[str, str]]:
    """Parse all bash function definitions from a file.

    Supports:
    - Multiple function definitions in one file
    - All three bash function definition styles:
      1. name() { ... }
      2. function name { ... }
      3. function name() { ... }
    - Leading content (shebang, comments, whitespace)
    - Functions separated by blank lines or comments

    Args:
        path: Path to file containing function definitions

    Returns:
        List of (name, body) tuples, preserving definition order

    Raises:
        ValueError: If no valid function definition is found,
                    or if any function has an empty body
        OSError: If the file cannot be read

    Note:
        Functions with nested braces in their body (e.g. echo "{") may
        not parse correctly. This is an acceptable limitation — real
        bash functions rarely contain literal braces outside of strings.
    """
    content = path.read_text(encoding="utf-8").strip()

    # Match all three valid bash function definition styles:
    #   1. name() { ... }
    #   2. function name { ... }
    #   3. function name() { ... }
    pattern = re.compile(
        r"(?:function\s+)?(\w[\w-]*?)\s*(?:\(\))?\s*\{\s*\n?(.*?)\n?\s*\}",
        re.DOTALL,
    )
    matches = pattern.findall(content)

    if not matches:
        raise ValueError(
            f"File does not contain any valid bash function definitions.\n"
            f"Expected formats:\n"
            f"  name() {{\n"
            f"    ...\n"
            f"  }}\n"
        )

    results: list[tuple[str, str]] = []
    for name, body in matches:
        body = body.strip()
        if not body:
            raise ValueError(f"Function '{name}' has empty body.")
        results.append((name, body))

    return results


def validate_bash_syntax(name: str, body: str) -> None:
    """Validate that a function definition is syntactically valid bash.

    Args:
        name: Function name
        body: Function body

    Raises:
        ValueError: If validation fails
    """
    # Reconstruct the full function definition for bash -n
    func_def = f"{name}() {{\n{body}\n}}"
    try:
        result = subprocess.run(
            ["bash", "-n", "-c", func_def],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            msg = result.stderr.strip() or result.stdout.strip() or "syntax error"
            raise ValueError(f"Bash syntax error: {msg}")
    except FileNotFoundError:
        # bash not available — skip validation
        pass
    except subprocess.TimeoutExpired:
        raise ValueError("Bash syntax check timed out.")


__all__ = [
    "BashFunction",
    "BashFunctionDB",
    "parse_function_file",
    "parse_functions_from_file",
    "validate_bash_syntax",
]
