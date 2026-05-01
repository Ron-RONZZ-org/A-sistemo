"""Tests for A-sistemo."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from A_sistemo.cli import app

runner = CliRunner()


class TestSistemo:
    """Tests for sistemo CLI."""

    def test_help(self):
        """Test help displays."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "System management" in result.stdout

    def test_wifi_help(self):
        """Test wifi subcommand help."""
        result = runner.invoke(app, ["wifi", "--help"])
        assert result.exit_code == 0

    def test_bluhdento_help(self):
        """Test bluetooth subcommand help."""
        result = runner.invoke(app, ["bluhdento", "--help"])
        assert result.exit_code == 0

    def test_usb_help(self):
        """Test usb subcommand help."""
        result = runner.invoke(app, ["usb", "--help"])
        assert result.exit_code == 0

    def test_disko_help(self):
        """Test disko subcommand help."""
        result = runner.invoke(app, ["disko", "--help"])
        assert result.exit_code == 0

    def test_rubo_help(self):
        """Test rubo subcommand help."""
        result = runner.invoke(app, ["rubo", "--help"])
        assert result.exit_code == 0