"""Name collision detection between bash aliases and functions.

When a user has both an alias and a function with the same name, the alias
shadows the function in interactive shells (aliases are expanded at read time).
Worse, bash expands the alias inside ``name() { }``, causing a syntax error.

This module provides pre-emptive checks so the CLI can warn the user before
creating such a conflict.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from A.core.paths import config_dir

from A_sistemo.services.bash_alias_db import BashAlias, BashAliasDB
from A_sistemo.services.bash_function_db import BashFunction, BashFunctionDB


def check_name_in_aliases(
    name: str,
    alias_db_path: Optional[Path] = None,
) -> Optional[BashAlias]:
    """Check whether *name* already exists as a bash alias.

    Args:
        name: The name to look up.
        alias_db_path: Override the alias DB path (for testing).

    Returns:
        The matching BashAlias entry, or None.
    """
    path = alias_db_path or config_dir() / "bash_aliases.db"
    db = BashAliasDB(path)
    try:
        return db.get_alias_by_name(name)
    finally:
        db.close()


def check_name_in_functions(
    name: str,
    func_db_path: Optional[Path] = None,
) -> Optional[BashFunction]:
    """Check whether *name* already exists as a bash function.

    Args:
        name: The name to look up.
        func_db_path: Override the function DB path (for testing).

    Returns:
        The matching BashFunction entry, or None.
    """
    path = func_db_path or config_dir() / "bash_functions.db"
    db = BashFunctionDB(path)
    try:
        return db.get_function_by_name(name)
    finally:
        db.close()


__all__ = [
    "check_name_in_aliases",
    "check_name_in_functions",
]
