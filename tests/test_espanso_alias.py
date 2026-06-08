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


class TestAldoniDuplicateHandling:
    """Tests for espanso aldoni duplicate trigger detection and update."""

    def test_get_match_by_trigger_found(self, tmp_path: Path):
        """get_match_by_trigger returns the match when found."""
        db = EspansoMatchDB(tmp_path / "espanso_matches.db")
        uid = db.add_match(":hello", "hello world", notes="greeting")
        
        match = db.get_match_by_trigger(":hello")
        assert match is not None
        assert match.uid == uid
        assert match.trigger == ":hello"
        assert match.replace_text == "hello world"
        assert match.notes == "greeting"

    def test_get_match_by_trigger_not_found(self, tmp_path: Path):
        """get_match_by_trigger returns None when trigger not found."""
        db = EspansoMatchDB(tmp_path / "espanso_matches.db")
        match = db.get_match_by_trigger(":nonexistent")
        assert match is None

    def test_aldoni_duplicate_trigger_prompt_update(self):
        """aldoni prompts user when trigger exists; accepts 'Y' to update."""
        # Create initial match
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":sig",
            "-r", "Original Signature",
        )
        assert exit_code == 0, f"aldoni failed: {output}"
        assert "UID" in output

        # Attempt to add same trigger; simulate user pressing 'y'
        result = runner.invoke(
            app,
            ["espanso", "aldoni", "-t", ":sig", "-r", "New Signature"],
            input="y\n",
        )
        assert result.exit_code == 0
        assert "modified" in result.stdout.lower() or "ĝisdatigi" in result.stdout

        # Verify the update
        _, vout = _run("espanso", "vidi", "1")
        assert "New Signature" in vout
        assert "Original Signature" not in vout

    def test_aldoni_duplicate_trigger_prompt_skip(self):
        """aldoni prompts user; accepts 'n' to skip."""
        # Create initial match
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":sig",
            "-r", "Original Signature",
        )
        assert exit_code == 0, f"aldoni failed: {output}"

        # Attempt to add same trigger; simulate user pressing 'n'
        result = runner.invoke(
            app,
            ["espanso", "aldoni", "-t", ":sig", "-r", "New Signature"],
            input="n\n",
        )
        assert result.exit_code == 0
        assert ("preterlasita" in result.stdout.lower() 
                or "skipped" in result.stdout.lower()
                or "passé" in result.stdout.lower())

        # Verify no change
        _, vout = _run("espanso", "vidi", "1")
        assert "Original Signature" in vout
        assert "New Signature" not in vout

    def test_aldoni_duplicate_with_jes_flag_auto_updates(self):
        """aldoni with --jes flag auto-confirms update without prompting."""
        # Create initial match
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":sig",
            "-r", "Original",
        )
        assert exit_code == 0, f"aldoni failed: {output}"

        # Add duplicate with --jes flag (no input needed)
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":sig",
            "-r", "Updated",
            "--jes",
        )
        assert exit_code == 0, f"aldoni with --jes failed: {output}"
        assert ("modified" in output.lower() or "modifita" in output.lower() or "ĝisdatigi" in output)

        # Verify the update
        _, vout = _run("espanso", "vidi", "1")
        assert "Updated" in vout
        assert "Original" not in vout

    def test_aldoni_duplicate_with_file_replacement(self, tmp_path: Path):
        """aldoni detects duplicate and updates replacement from file."""
        # Create initial match
        content_file = tmp_path / "sig.txt"
        content_file.write_text("Original Signature\nFrom File")
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":sig",
            "-R", str(content_file),
        )
        assert exit_code == 0, f"aldoni failed: {output}"

        # Update with new file
        new_file = tmp_path / "sig_new.txt"
        new_file.write_text("New Signature\nUpdated File")
        result = runner.invoke(
            app,
            ["espanso", "aldoni", "-t", ":sig", "-R", str(new_file)],
            input="y\n",
        )
        assert result.exit_code == 0

        # Verify the update from file
        _, vout = _run("espanso", "vidi", "1")
        assert "New Signature" in vout
        assert "Updated File" in vout
        assert "Original Signature" not in vout

    def test_aldoni_duplicate_preserves_notes_on_update(self):
        """aldoni update can change notes when updating duplicate."""
        # Create initial match with notes
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":sig",
            "-r", "Signature",
            "-n", "Original note",
        )
        assert exit_code == 0, f"aldoni failed: {output}"

        # Update trigger and notes
        result = runner.invoke(
            app,
            [
                "espanso", "aldoni",
                "-t", ":sig",
                "-r", "Updated Sig",
                "-n", "Updated note",
            ],
            input="y\n",
        )
        assert result.exit_code == 0

        # Verify the update
        _, vout = _run("espanso", "vidi", "1")
        assert "Updated Sig" in vout
        assert "Updated note" in vout
        assert "Original note" not in vout

    def test_aldoni_first_match_no_duplicate(self):
        """aldoni first match (no existing) works normally."""
        exit_code, output = _run(
            "espanso", "aldoni",
            "-t", ":first",
            "-r", "First match",
        )
        assert exit_code == 0, f"aldoni failed: {output}"
        assert "added" in output.lower() or "UID" in output

        _, vout = _run("espanso", "vidi", "1")
        assert "First match" in vout

