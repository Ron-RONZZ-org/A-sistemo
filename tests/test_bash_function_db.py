"""Tests for A-sistemo bash_function_db service."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from A_sistemo.services.bash_function_db import (
    BashFunction,
    BashFunctionDB,
    parse_function_file,
    parse_functions_from_file,
)


@pytest.fixture
def temp_db() -> BashFunctionDB:
    with tempfile.TemporaryDirectory() as tmpdir:
        db = BashFunctionDB(Path(tmpdir) / "test.db")
        yield db
        db.close()


# ── parse_functions_from_file tests ──────────────────────────────────────


def _write_func_file(content: str) -> Path:
    """Write a temp file with the given content and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".bash", delete=False)
    f.write(content)
    f.close()
    return Path(f.name)


def test_parse_single_function() -> None:
    """Parse a file with a single function definition."""
    path = _write_func_file("greet() {\n  echo hello\n}")
    result = parse_functions_from_file(path)
    assert result == [("greet", "echo hello")]
    path.unlink()


def test_parse_multiple_functions() -> None:
    """Parse a file with multiple function definitions."""
    path = _write_func_file(
        "hello() {\n  echo hi\n}\n\n"
        "bye() {\n  echo adios\n}\n"
    )
    result = parse_functions_from_file(path)
    assert result == [
        ("hello", "echo hi"),
        ("bye", "echo adios"),
    ]
    path.unlink()


def test_parse_function_keyword_style() -> None:
    """Parse 'function name { ... }' style."""
    path = _write_func_file("function greet {\n  echo hello\n}")
    result = parse_functions_from_file(path)
    assert result == [("greet", "echo hello")]
    path.unlink()


def test_parse_function_keyword_with_parens() -> None:
    """Parse 'function name() { ... }' style."""
    path = _write_func_file("function greet() {\n  echo hello\n}")
    result = parse_functions_from_file(path)
    assert result == [("greet", "echo hello")]
    path.unlink()


def test_parse_with_shebang_and_comments() -> None:
    """Parse a file with leading shebang, comments, and blank lines."""
    path = _write_func_file(
        "#!/bin/bash\n"
        "# Helper functions\n"
        "\n"
        "foo() {\n"
        "  echo foo\n"
        "}\n"
    )
    result = parse_functions_from_file(path)
    assert result == [("foo", "echo foo")]
    path.unlink()


def test_parse_with_comments_between_functions() -> None:
    """Parse functions separated by comments."""
    path = _write_func_file(
        "a() {\n  echo a\n}\n"
        "# Separator comment\n"
        "b() {\n  echo b\n}\n"
    )
    result = parse_functions_from_file(path)
    assert result == [
        ("a", "echo a"),
        ("b", "echo b"),
    ]
    path.unlink()


def test_parse_empty_file_raises() -> None:
    """An empty file raises ValueError."""
    path = _write_func_file("")
    with pytest.raises(ValueError, match="does not contain any valid"):
        parse_functions_from_file(path)
    path.unlink()


def test_parse_no_function_definition_raises() -> None:
    """A file without a function definition raises ValueError."""
    path = _write_func_file("echo hello\necho world")
    with pytest.raises(ValueError, match="does not contain any valid"):
        parse_functions_from_file(path)
    path.unlink()


def test_parse_empty_body_raises() -> None:
    """A function with an empty body raises ValueError."""
    path = _write_func_file("empty() {\n}")
    with pytest.raises(ValueError, match="has empty body"):
        parse_functions_from_file(path)
    path.unlink()


def test_parse_function_with_hyphen_in_name() -> None:
    """Function names can contain hyphens in bash."""
    path = _write_func_file("my-func() {\n  echo works\n}")
    result = parse_functions_from_file(path)
    assert result == [("my-func", "echo works")]
    path.unlink()


def test_parse_function_with_nested_if() -> None:
    """Functions with nested if/fi blocks parse correctly."""
    path = _write_func_file(
        "check() {\n"
        "  if [[ -f /tmp/x ]]; then\n"
        "    echo found\n"
        "  fi\n"
        "}\n"
    )
    result = parse_functions_from_file(path)
    assert result == [("check", 'if [[ -f /tmp/x ]]; then\n    echo found\n  fi')]
    path.unlink()


# ── parse_function_file (singular, backward compat) tests ────────────────


def test_parse_function_file_singular() -> None:
    """parse_function_file returns only the first function."""
    path = _write_func_file(
        "first() {\n  echo one\n}\n"
        "second() {\n  echo two\n}\n"
    )
    name, body = parse_function_file(path)
    assert name == "first"
    assert body == "echo one"
    path.unlink()


# ── BashFunctionDB tests ──────────────────────────────────────────────────


def test_add_and_get_function(temp_db: BashFunctionDB) -> None:
    """Test adding a function and retrieving it."""
    uid = temp_db.add_function("greet", "echo hello")
    assert uid == 1
    func = temp_db.get_function(uid)
    assert func is not None
    assert func.name == "greet"
    assert func.body == "echo hello"


def test_get_function_by_name(temp_db: BashFunctionDB) -> None:
    """Test retrieving a function by name."""
    temp_db.add_function("greet", "echo hello")
    func = temp_db.get_function_by_name("greet")
    assert func is not None
    assert func.uid == 1


def test_get_function_by_name_not_found(temp_db: BashFunctionDB) -> None:
    """get_function_by_name returns None for missing name."""
    assert temp_db.get_function_by_name("nonexistent") is None


def test_update_function_body(temp_db: BashFunctionDB) -> None:
    """Test updating a function body."""
    uid = temp_db.add_function("greet", "echo hello")
    result = temp_db.update_function(uid, body="echo bonjour")
    assert result is True
    func = temp_db.get_function(uid)
    assert func is not None
    assert func.body == "echo bonjour"


def test_update_function_no_changes(temp_db: BashFunctionDB) -> None:
    """update_function with no changes returns False (nothing to update)."""
    uid = temp_db.add_function("greet", "echo hello")
    result = temp_db.update_function(uid)
    assert result is False
    func = temp_db.get_function(uid)
    assert func is not None
    assert func.body == "echo hello"


def test_list_functions_sorts_by_created_at_desc(temp_db: BashFunctionDB) -> None:
    """List returns most recently created first by default."""
    temp_db.add_function("a", "echo a")
    temp_db.add_function("b", "echo b")
    functions = temp_db.list_functions()
    assert len(functions) == 2
    # b (uid=2) added last, should be first
    assert functions[0].name == "b"
    assert functions[1].name == "a"


def test_list_functions_alpha_order(temp_db: BashFunctionDB) -> None:
    """List with alphabetical sort."""
    temp_db.add_function("zzz", "echo z")
    temp_db.add_function("aaa", "echo a")
    functions = temp_db.list_functions(sort_by="name", descending=False)
    assert functions[0].name == "aaa"
    assert functions[1].name == "zzz"


def test_delete_function(temp_db: BashFunctionDB) -> None:
    """Test deleting a function."""
    uid = temp_db.add_function("greet", "echo hello")
    result = temp_db.delete_function(uid)
    assert result is True
    assert temp_db.get_function(uid) is None


def test_search_functions(temp_db: BashFunctionDB) -> None:
    """Test searching functions by name or body."""
    temp_db.add_function("greet", "echo hello")
    temp_db.add_function("bye", "echo farewell")
    results = temp_db.search_functions("hello")
    assert len(results) == 1
    assert results[0].name == "greet"


def test_search_functions_by_name(temp_db: BashFunctionDB) -> None:
    """Test searching functions by name prefix."""
    temp_db.add_function("greet_english", "echo hello")
    temp_db.add_function("greet_spanish", "echo hola")
    results = temp_db.search_functions("greet")
    assert len(results) == 2


def test_sync_shell_config_creates_file(temp_db: BashFunctionDB) -> None:
    """sync_shell_config generates a valid shell file."""
    temp_db.add_function("greet", "echo hello")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Monkey-patch the generated file path
        import A_sistemo.services.bash_function_db as mod
        orig_path = mod._A_BASH_FUNCTIONS
        test_path = Path(tmpdir) / ".A_bash_functions"
        mod._A_BASH_FUNCTIONS = test_path
        try:
            temp_db.sync_shell_config()
            assert test_path.exists()
            content = test_path.read_text()
            assert "#!/bin/bash" in content
            assert "greet() {" in content
            assert "echo hello" in content
        finally:
            mod._A_BASH_FUNCTIONS = orig_path
