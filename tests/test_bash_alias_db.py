"""Tests for A-sistemo bash_alias_db service."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from A_sistemo.services.bash_alias_db import BashAlias, BashAliasDB


@pytest.fixture
def temp_db() -> BashAliasDB:
    with tempfile.TemporaryDirectory() as tmpdir:
        db = BashAliasDB(Path(tmpdir) / "test.db")
        yield db
        db.close()


def test_add_alias(temp_db: BashAliasDB) -> None:
    """Test adding an alias."""
    uid = temp_db.add_alias("ll", "ls -la", "Long list")
    assert uid == 1
    alias = temp_db.get_alias(1)
    assert alias is not None
    assert alias.alias == "ll"
    assert alias.function == "ls -la"
    assert alias.notes == "Long list"


def test_list_aliases(temp_db: BashAliasDB) -> None:
    """Test listing aliases."""
    temp_db.add_alias("ll", "ls -la")
    temp_db.add_alias("la", "ls -a")
    aliases = temp_db.list_aliases()
    assert len(aliases) == 2


def test_update_alias(temp_db: BashAliasDB) -> None:
    """Test updating an alias."""
    uid = temp_db.add_alias("ll", "ls -la")
    result = temp_db.update_alias(uid, alias="lll", function="ls -lla")
    assert result is True
    alias = temp_db.get_alias(uid)
    assert alias is not None
    assert alias.alias == "lll"


def test_delete_alias(temp_db: BashAliasDB) -> None:
    """Test deleting an alias."""
    uid = temp_db.add_alias("ll", "ls -la")
    result = temp_db.delete_alias(uid)
    assert result is True
    alias = temp_db.get_alias(uid)
    assert alias is None


def test_search_aliases(temp_db: BashAliasDB) -> None:
    """Test searching aliases."""
    temp_db.add_alias("ll", "ls -la", "Long list")
    temp_db.add_alias("la", "ls -a")
    results = temp_db.search_aliases("ls -la")
    assert len(results) == 1
    assert results[0].alias == "ll"


def test_sort_by_alias(temp_db: BashAliasDB) -> None:
    """Test sorting by alias name."""
    temp_db.add_alias("zzz", "echo z")
    temp_db.add_alias("aaa", "echo a")
    aliases = temp_db.list_aliases(sort_by="alias", descending=False)
    assert aliases[0].alias == "aaa"
    assert aliases[1].alias == "zzz"


def test_invalid_sort_by(temp_db: BashAliasDB) -> None:
    """Test invalid sort_by falls back to created_at."""
    temp_db.add_alias("ll", "ls -la")
    aliases = temp_db.list_aliases(sort_by="invalid", descending=False)
    assert len(aliases) == 1