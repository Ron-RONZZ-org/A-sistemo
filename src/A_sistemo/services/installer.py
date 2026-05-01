"""Installer service for A."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from A_sistemo._shared import run


def get_poetry_env_path() -> str:
    """Get Poetry environment path."""
    result = subprocess.run(
        ["poetry", "env", "info", "--path"],
        capture_output=True, text=True, check=False, timeout=5
    )
    if result.returncode != 0:
        raise RuntimeError("Could not find Poetry environment")
    return result.stdout.strip()


def install_binary(
    target: str,
    source_binary: Optional[Path] = None,
    user_scope: bool = True,
) -> None:
    """Install A binary to target location."""
    if source_binary is None:
        env_path = get_poetry_env_path()
        source_binary = Path(env_path) / "bin" / "A"

    if not source_binary.exists():
        raise FileNotFoundError(f"Binary not found: {source_binary}")

    if user_scope:
        dest_dir = Path.home() / ".local" / "bin"
    else:
        dest_dir = Path("/usr/local/bin")

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / target

    # Remove existing
    if dest_path.exists() or dest_path.is_symlink():
        dest_path.unlink()

    # Create symlink
    dest_path.symlink_to(source_binary)


def generate_shell_aliases() -> str:
    """Generate shell aliases for A commands."""
    commands = [
        "tempo", "sistemo", "wifi", "bluhdento", "usb", "disko", "rubo"
    ]
    lines = ["#!/bin/bash", "# A shell aliases", ""]
    for cmd in commands:
        lines.append(f'{cmd}() {{ A {cmd} "$@"; }}')
    return "\n".join(lines) + "\n"


def setup_bashrc(source_line: str = "source ~/.A_aliases") -> None:
    """Setup bashrc to source aliases."""
    bashrc = Path.home() / ".bashrc"
    if bashrc.exists():
        content = bashrc.read_text()
        if source_line not in content:
            bashrc.write_text(content + f"\n# A aliases\n{source_line}\n")
    else:
        bashrc.write_text(f"# A aliases\n{source_line}\n")


def install_man_pages() -> None:
    """Install man pages."""
    man_dir = Path.home() / ".local" / "share" / "man" / "man1"
    man_dir.mkdir(parents=True, exist_ok=True)

    # Would need to generate man pages from --help output
    # This is a placeholder


__all__ = [
    "get_poetry_env_path",
    "install_binary",
    "generate_shell_aliases",
    "setup_bashrc",
    "install_man_pages",
]