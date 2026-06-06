"""Tests for espanso alias CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from A_sistemo.cli import app
from A_sistemo.services.espanso_alias_db import EspansoMatchDB

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolate_espanso_db(monkeypatch, tmp_path):
    """Redirect espanso DB to tmp_path to avoid touching real config."""
    test_db_path = tmp_path / "espanso_matches.db"

    def mock_get_db() -> EspansoMatchDB:
        return EspansoMatchDB(test_db_path)

    monkeypatch.setattr("A_sistemo.cli.espanso_alias._get_db", mock_get_db)


def _run(*args: str) -> tuple[int, str]:
    """Run the CLI and return (exit_code, output)."""
    result = runner.invoke(app, list(args))
    # error() uses Rich Console which writes to stdout; collect both
    return result.exit_code, result.stdout


class TestAldoniReplaceDosiero:
    """Tests for espanso aldoni --replace-dosiero."""

    def test_replace_dosiero_happy_path(self, tmp_path: Path):
        """--replace-dosiero reads file content and creates the match."""
        content_file = tmp_path / "reply.md"
        content_file.write_text("Saluton, mondo!\n\nĜis la revido!")
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":saluton",
            "-R", str(content_file),
        )
        assert exit_code == 0, f"aldoni failed: {output}"
        assert "UID" in output

        # Verify via vidi
        exit_code, vout = _run("espanso", "vidi", "1")
        assert exit_code == 0, f"vidi failed: {vout}"
        assert "Saluton, mondo!" in vout
        assert "Ĝis la revido!" in vout

    def test_replace_dosiero_multiline(self, tmp_path: Path):
        """Multi-line content from file is preserved."""
        content_file = tmp_path / "template.txt"
        content_file.write_text("Line 1\nLine 2\nLine 3")
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":multi",
            "-R", str(content_file),
        )
        assert exit_code == 0, f"aldoni failed: {output}"

        _, vout = _run("espanso", "vidi", "1")
        assert "Line 1" in vout
        assert "Line 2" in vout
        assert "Line 3" in vout

    def test_replace_dosiero_with_notes(self, tmp_path: Path):
        """--replace-dosiero works alongside --notes."""
        content_file = tmp_path / "reply.txt"
        content_file.write_text("Hello world")
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":hello",
            "-R", str(content_file),
            "-n", "my note",
        )
        assert exit_code == 0, f"aldoni failed: {output}"

        _, vout = _run("espanso", "vidi", "1")
        assert "my note" in vout

    def test_replace_dosiero_file_not_found(self, tmp_path: Path):
        """Non-existent file reports error and exits."""
        missing = tmp_path / "nonexistent.md"
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":test",
            "-R", str(missing),
        )
        assert exit_code == 1
        assert ("ne ekzistas" in output.lower()
                or "not exist" in output.lower()
                or "inexistant" in output.lower())

    def test_replace_dosiero_is_directory(self, tmp_path: Path):
        """A directory path reports error and exits."""
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":test",
            "-R", str(tmp_path),
        )
        assert exit_code == 1
        assert ("dosiero" in output.lower()
                or "not a file" in output.lower()
                or "fichier" in output.lower())

    def test_replace_dosiero_binary_file(self, tmp_path: Path):
        """Binary file (null bytes) reports error and exits."""
        binary_file = tmp_path / "data.bin"
        binary_file.write_bytes(b"Hello\x00world")
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":test",
            "-R", str(binary_file),
        )
        assert exit_code == 1
        assert ("binara" in output.lower()
                or "binary" in output.lower()
                or "binaire" in output.lower())

    def test_both_replace_and_replace_dosiero_error(self, tmp_path: Path):
        """Passing both --replace and --replace-dosiero raises error."""
        content_file = tmp_path / "data.txt"
        content_file.write_text("file content")
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":test",
            "-r", "inline text",
            "-R", str(content_file),
        )
        assert exit_code == 1
        assert ("ne eblas" in output.lower()
                or "cannot use both" in output.lower()
                or "impossible" in output.lower())

    def test_no_replace_arg_error(self):
        """Omitting both --replace and --replace-dosiero raises error."""
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":test",
        )
        assert exit_code == 1
        assert ("bezonas" in output.lower()
                or "requires" in output.lower()
                or "nécessite" in output.lower())

    def test_inline_replace_still_works(self):
        """Existing --replace still works (backward compatibility)."""
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":legacy",
            "-r", "legacy text",
        )
        assert exit_code == 0, f"aldoni failed: {output}"
        assert "UID" in output


class TestModifiReplaceDosiero:
    """Tests for espanso modifi --replace-dosiero."""

    def test_modifi_replace_dosiero(self, tmp_path: Path):
        """modifi --replace-dosiero updates the replace text from a file."""
        # First create a match
        content_file = tmp_path / "original.txt"
        content_file.write_text("original content")
        ec, out = _run("espanso", "aldoni", "-t", ":test", "-R", str(content_file))
        assert ec == 0, f"aldoni failed: {out}"

        # Now modify it
        new_file = tmp_path / "updated.txt"
        new_file.write_text("updated content")
        exit_code, output = _run(
            "espanso", "modifi", "1",
            "-R", str(new_file),
        )
        assert exit_code == 0, f"modifi failed: {output}"

        # Verify the update
        _, vout = _run("espanso", "vidi", "1")
        assert "updated content" in vout
        assert "original content" not in vout

    def test_modifi_both_replace_and_replace_dosiero_error(self, tmp_path: Path):
        """modifi with both --replace and --replace-dosiero raises error."""
        content_file = tmp_path / "data.txt"
        content_file.write_text("content")
        ec, out = _run("espanso", "aldoni", "-t", ":test", "-r", "initial")
        assert ec == 0, f"aldoni failed: {out}"

        exit_code, output = _run(
            "espanso", "modifi", "1",
            "-r", "inline",
            "-R", str(content_file),
        )
        assert exit_code == 1
        assert ("cannot use both" in output.lower()
                or "ne eblas" in output.lower())

    def test_modifi_replace_dosiero_file_not_found(self, tmp_path: Path):
        """modifi with non-existent --replace-dosiero file errors."""
        ec, out = _run("espanso", "aldoni", "-t", ":test", "-r", "initial")
        assert ec == 0, f"aldoni failed: {out}"

        missing = tmp_path / "nope.txt"
        exit_code, output = _run(
            "espanso", "modifi", "1",
            "-R", str(missing),
        )
        assert exit_code == 1
        assert ("ne ekzistas" in output.lower()
                or "not exist" in output.lower())

    def test_modifi_inline_replace_still_works(self):
        """modifi --replace still works (backward compatibility)."""
        ec, out = _run("espanso", "aldoni", "-t", ":test", "-r", "initial")
        assert ec == 0, f"aldoni failed: {out}"

        exit_code, output = _run(
            "espanso", "modifi", "1",
            "-r", "updated inline",
        )
        assert exit_code == 0, f"modifi failed: {output}"

        _, vout = _run("espanso", "vidi", "1")
        assert "updated inline" in vout
