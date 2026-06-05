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
            lines.append(f"unalias {f.name} 2>/dev/null || true")
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


def _find_matching_brace(content: str, start: int) -> int:
    """Find the position of the closing brace matching the opening ``{``.

    Iterates character by character through *content* beginning at *start*,
    tracking brace depth while correctly skipping over:
    - Single-quoted strings (``'...'``)
    - Double-quoted strings (``"..."``)

    Bash comments (``# ...``) are skipped only when the ``#`` appears at
    the function-body level (``depth == 1``). Inside nested ``${...}``
    constructs (``depth >= 2``), ``#`` is part of bash variable expansion
    syntax (e.g. ``${#var}`` length operator, ``${var#pattern}`` removal)
    and is **not** treated as a comment.

    This correctly handles ``${parameter}`` expansions, ``$(command)``
    substitutions, and other constructs containing braces inside
    quoted strings or nested brace blocks.

    Args:
        content: The full file content.
        start: Position of the first character after the opening ``{``.

    Returns:
        Position of the matching closing ``}``.

    Raises:
        ValueError: If no matching closing brace is found before end of content.
    """
    depth = 1
    i = start

    while i < len(content):
        ch = content[i]

        # Skip single-quoted strings (no escape processing in bash)
        if ch == "'":
            i += 1
            while i < len(content) and content[i] != "'":
                i += 1
            i += 1  # Skip closing quote
            continue

        # Skip double-quoted strings (handle \ escapes)
        if ch == '"':
            i += 1
            while i < len(content):
                if content[i] == '\\':
                    i += 1  # Skip escaped character
                elif content[i] == '"':
                    break
                i += 1
            i += 1  # Skip closing quote
            continue

        # Track brace depth BEFORE comment check.
        # This ordering is critical: when inside `${...}` (depth >= 2),
        # a `#` character is part of bash variable expansion syntax
        # (e.g. `${#var}` length operator or `${var#pattern}` removal),
        # NOT a comment. Only at depth == 1 (function body level) does
        # `#` start a real comment.
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i

        # Skip comments (only at function-body level, not inside ${...})
        if ch == '#' and depth == 1:
            i += 1
            while i < len(content) and content[i] != '\n':
                i += 1
            continue

        i += 1

    raise ValueError("Unterminated function body: no matching closing brace.")


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

    Uses a brace-aware parser that tracks ``{}`` depth while correctly
    skipping over quoted strings (``''``, ``\"\"``) and comments (``#``).
    This ensures that braces inside ``${parameter}`` expansions or string
    literals do not interfere with the function boundary detection.

    Args:
        path: Path to file containing function definitions

    Returns:
        List of (name, body) tuples, preserving definition order

    Raises:
        ValueError: If no valid function definition is found,
                    or if any function has an empty body
        OSError: If the file cannot be read

    Note:
        Here-documents (``<<EOF``) and nested brace groups outside of
        quoted strings may cause incorrect function boundary detection.
        These are uncommon in real bash functions and are an accepted
        limitation.
    """
    content = path.read_text(encoding="utf-8").strip()

    # Pattern to find function definition headers
    header_pattern = re.compile(
        r"(?:function\s+)?(\w[\w-]*?)\s*(?:\(\))?\s*\{",
    )

    results: list[tuple[str, str]] = []
    pos = 0

    while pos < len(content):
        match = header_pattern.search(content, pos)
        if not match:
            break

        name = match.group(1)
        brace_pos = match.end() - 1  # Position of the opening {

        try:
            end_pos = _find_matching_brace(content, brace_pos + 1)
        except ValueError:
            # Unterminated function body — stop scanning
            break

        # Extract body between braces and strip leading/trailing whitespace
        body = content[brace_pos + 1:end_pos].strip()

        if not body:
            raise ValueError(f"Function '{name}' has empty body.")

        results.append((name, body))
        pos = end_pos + 1  # Continue after the closing brace

    if not results:
        raise ValueError(
            f"File does not contain any valid bash function definitions.\n"
            f"Expected formats:\n"
            f"  name() {{\n"
            f"    ...\n"
            f"  }}\n"
        )

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
