"""YAML parsing and serialization helpers for espanso matches.

Provides a line-based YAML parser and serializer that avoids adding
a yaml library dependency.
"""

from __future__ import annotations

import re
from pathlib import Path


__all__ = ["_parse_espanso_yml", "_unescape_yaml"]


def _unescape_yaml(text: str) -> str:
    # raw docstring to avoid Python interpreting escape sequences
    r"""Unescape a YAML double-quoted scalar.

    Handles ``\\``, ``\"``, ``\/``, ``\n``, ``\r``, ``\t``, ``\b``,
    ``\f``, ``\xXX``, ``\uXXXX``, and ``\UXXXXXXXX`` escape sequences.

    Args:
        text: Raw content between the outer double quotes

    Returns:
        Unescaped string
    """
    result: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            c = text[i + 1]
            if c == "n":
                result.append("\n")
                i += 2
            elif c == "t":
                result.append("\t")
                i += 2
            elif c == "r":
                result.append("\r")
                i += 2
            elif c == "\\":
                result.append("\\")
                i += 2
            elif c == '"':
                result.append('"')
                i += 2
            elif c == "/":
                result.append("/")
                i += 2
            elif c == "b":
                result.append("\b")
                i += 2
            elif c == "f":
                result.append("\f")
                i += 2
            elif c == "x" and i + 3 < len(text):
                result.append(chr(int(text[i + 2 : i + 4], 16)))
                i += 4
            elif c == "u" and i + 5 < len(text):
                result.append(chr(int(text[i + 2 : i + 6], 16)))
                i += 6
            elif c == "U" and i + 9 < len(text):
                result.append(chr(int(text[i + 2 : i + 10], 16)))
                i += 10
            else:
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def _parse_espanso_yml(path: Path) -> list[tuple[str, str]]:
    """Line-based parser for espanso match YAML files.

    Handles the formats produced by ``sync_espanso_config``:
        - ``trigger: ':xyz'`` (single-quoted)
        - ``replace: 'text'`` (single-quoted flow scalar)
        - ``replace: "text"`` (double-quoted flow scalar with escapes)
        - ``replace: |`` / ``replace: |-`` (literal block scalar)
        - ``replace: text`` (unquoted, legacy)

    Avoids adding a yaml library dependency.

    Args:
        path: Path to YAML file

    Returns:
        List of (trigger, replace_text) tuples
    """
    content = path.read_text()
    matches: list[tuple[str, str]] = []
    current_trigger: str | None = None
    current_replace: str | None = None
    in_block_literal: bool = False
    block_indent: int | None = None
    block_lines: list[str] = []

    def _save_pair() -> None:
        """Save the current trigger/replace pair if complete."""
        nonlocal current_trigger, current_replace
        if current_trigger is not None and current_replace is not None:
            matches.append((current_trigger, current_replace))
        current_trigger = None
        current_replace = None

    def _finish_block() -> None:
        """Finalise block literal content and save pair."""
        nonlocal in_block_literal, block_indent, block_lines, current_replace
        in_block_literal = False
        block_indent = None
        current_replace = "\n".join(block_lines)
        block_lines = []
        _save_pair()

    for line in content.splitlines():
        # --- Block literal continuation ---
        if in_block_literal:
            if block_indent is None:
                # First non-empty line sets the indentation level
                if line.strip():
                    block_indent = len(line) - len(line.lstrip())
                    block_lines.append(line[block_indent:])
                else:
                    block_lines.append("")
                continue
            # Blank lines or lines at/above indent → add to block
            if not line.strip() or len(line) - len(line.lstrip()) >= block_indent:
                content_line = line[block_indent:] if line else ""
                block_lines.append(content_line)
                continue
            # Indent decreased → block ended
            _finish_block()
            # Fall through to process this line normally

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # --- trigger: '...' ---
        trigger_match = re.match(r"^-?\s*trigger:\s*'([^']*)'", stripped)
        if trigger_match:
            if current_trigger is not None and current_replace is not None:
                matches.append((current_trigger, current_replace))
            current_trigger = trigger_match.group(1)
            current_replace = None
            continue

        # --- replace: '...' (single-quoted flow scalar) ---
        replace_match = re.match(r"^\s*replace:\s*'([^']*)'", stripped)
        if replace_match and current_trigger is not None:
            current_replace = replace_match.group(1)
            continue

        # --- replace: "..." (double-quoted flow scalar with escapes) ---
        dq_re = r'^\s*replace:\s*"((?:[^"\\]|\\.)*)"'
        replace_match = re.match(dq_re, stripped)
        if replace_match and current_trigger is not None:
            current_replace = _unescape_yaml(replace_match.group(1))
            continue

        # --- replace: | or |- (literal block scalar start) ---
        block_match = re.match(r"^\s*replace:\s*(\|[-+]?\d*)\s*$", stripped)
        if block_match and current_trigger is not None:
            in_block_literal = True
            block_indent = None
            block_lines = []
            continue

        # --- replace: <unquoted> (legacy fallback) ---
        replace_match = re.match(r"^\s*replace:\s*(\S.*)", stripped)
        if replace_match and current_trigger is not None:
            current_replace = replace_match.group(1)

    # End of file: finalise block or save last pair
    if in_block_literal and block_lines is not None:
        _finish_block()
    elif current_trigger is not None and current_replace is not None:
        matches.append((current_trigger, current_replace))

    return matches
