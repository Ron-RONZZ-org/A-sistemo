"""Tests for collision detection between bash aliases and functions."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from A_sistemo.services.bash_alias_db import BashAliasDB
from A_sistemo.services.bash_function_db import BashFunctionDB
from A_sistemo.services.collision import (
    check_name_in_aliases,
    check_name_in_functions,
)


@pytest.fixture
def temp_dbs() -> tuple[Path, Path]:
    """Create two isolated DB files (aliases + functions) and yield their paths.

    Returns:
        Tuple of (alias_db_path, func_db_path)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        alias_path = Path(tmpdir) / "aliases.db"
        func_path = Path(tmpdir) / "functions.db"

        alias_db = BashAliasDB(alias_path)
        alias_db.add_alias("ll", "ls -la", "test alias")
        alias_db.close()

        func_db = BashFunctionDB(func_path)
        func_db.add_function(
            "spa",
            'A semantika predikato aldoni $1 -e "eo::$2" -e "en::$3" -e "fr::$4"',
        )
        func_db.close()

        yield alias_path, func_path


# ── get_alias_by_name (new method) ──────────────────────────────────────────


class TestGetAliasByName:
    """Tests for the newly added BashAliasDB.get_alias_by_name()."""

    def test_get_alias_by_name_found(self) -> None:
        """Look up an existing alias by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.db"
            db = BashAliasDB(path)
            db.add_alias("ll", "ls -la")
            result = db.get_alias_by_name("ll")
            assert result is not None
            assert result.alias == "ll"
            assert result.function == "ls -la"
            db.close()

    def test_get_alias_by_name_not_found(self) -> None:
        """Look up a non-existent alias by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.db"
            db = BashAliasDB(path)
            db.add_alias("ll", "ls -la")
            result = db.get_alias_by_name("unknown")
            assert result is None
            db.close()

    def test_get_alias_by_name_empty_db(self) -> None:
        """Look up in an empty database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.db"
            db = BashAliasDB(path)
            result = db.get_alias_by_name("anything")
            assert result is None
            db.close()


# ── check_name_in_aliases ────────────────────────────────────────────────────


class TestCheckNameInAliases:
    """Tests for check_name_in_aliases()."""

    def test_found(self, temp_dbs: tuple[Path, Path]) -> None:
        """Detect that 'll' exists as an alias."""
        alias_path, _func_path = temp_dbs
        result = check_name_in_aliases("ll", alias_db_path=alias_path)
        assert result is not None
        assert result.alias == "ll"

    def test_not_found(self, temp_dbs: tuple[Path, Path]) -> None:
        """Return None when name does not exist as an alias."""
        alias_path, _func_path = temp_dbs
        result = check_name_in_aliases("spa", alias_db_path=alias_path)
        assert result is None

    def test_empty_db(self) -> None:
        """Return None for an empty alias database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.db"
            BashAliasDB(path).close()  # create file
            result = check_name_in_aliases("x", alias_db_path=path)
            assert result is None


# ── check_name_in_functions ──────────────────────────────────────────────────


class TestCheckNameInFunctions:
    """Tests for check_name_in_functions()."""

    def test_found(self, temp_dbs: tuple[Path, Path]) -> None:
        """Detect that 'spa' exists as a function."""
        _alias_path, func_path = temp_dbs
        result = check_name_in_functions("spa", func_db_path=func_path)
        assert result is not None
        assert result.name == "spa"

    def test_not_found(self, temp_dbs: tuple[Path, Path]) -> None:
        """Return None when name does not exist as a function."""
        _alias_path, func_path = temp_dbs
        result = check_name_in_functions("ll", func_db_path=func_path)
        assert result is None

    def test_empty_db(self) -> None:
        """Return None for an empty function database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.db"
            BashFunctionDB(path).close()  # create file
            result = check_name_in_functions("x", func_db_path=path)
            assert result is None


# ── Cross-check: function sees alias, alias sees function ────────────────────


class TestCrossCollision:
    """Verify that each database can see entries in the other."""

    def test_function_sees_alias(self, temp_dbs: tuple[Path, Path]) -> None:
        """check_name_in_aliases must find the alias inserted in the alias DB."""
        alias_path, func_path = temp_dbs
        # Verify alias DB has 'll'
        func_result = check_name_in_functions("ll", func_db_path=func_path)
        alias_result = check_name_in_aliases("ll", alias_db_path=alias_path)
        assert alias_result is not None  # ll is an alias
        assert func_result is None       # ll is not a function

    def test_alias_sees_function(self, temp_dbs: tuple[Path, Path]) -> None:
        """check_name_in_functions must find the function in the function DB."""
        alias_path, func_path = temp_dbs
        func_result = check_name_in_functions("spa", func_db_path=func_path)
        alias_result = check_name_in_aliases("spa", alias_db_path=alias_path)
        assert func_result is not None   # spa is a function
        assert alias_result is None      # spa is not an alias
