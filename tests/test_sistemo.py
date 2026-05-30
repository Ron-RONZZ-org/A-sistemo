"""Tests for A-sistemo."""

from __future__ import annotations

from unittest.mock import patch

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
        assert "wifi" in result.stdout  # Commands present

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
        """Test trash subcommand help."""
        result = runner.invoke(app, ["rubo", "--help"])
        assert result.exit_code == 0


class TestSystemInfoPsutilInstall:
    """collect_system_info() must auto-install psutil when missing."""

    def test_psutil_installed_already(self) -> None:
        """When psutil is already importable, no install needed."""
        from A_sistemo.services.system_info import collect_system_info

        # Ensure psutil is importable for this test
        import psutil  # noqa: F401

        # Should not raise — fast path
        result = collect_system_info()
        assert result.os_name is not None

    def test_psutil_missing_calls_ensure_dependency(self) -> None:
        """When psutil missing, delegates to ensure_dependency('psutil')
        and raises SystemExit on failure."""
        import builtins

        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "psutil" or name == "psutil." or name.startswith("psutil."):
                raise ImportError(f"No module named {name}")
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", fake_import):
            # Ensure dependency fails → SystemExit(1)
            with patch(
                "A.utils.deps.ensure_dependency",
                side_effect=ImportError("fail"),
            ) as mock_ed:
                from A_sistemo.services.system_info import collect_system_info

                with pytest.raises(SystemExit):
                    collect_system_info()
                mock_ed.assert_called_once_with("psutil", timeout=60)