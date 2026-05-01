"""Unified subprocess runner for A-sistemo."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from typing import Optional


class CommandError(RuntimeError):
    """Raised when a command fails or times out."""


class CommandNotFound(CommandError):
    """Raised when the command binary doesn't exist."""


class CommandTimeout(CommandError):
    """Raised when a command exceeds its timeout."""


def run(
    cmd: Sequence[str],
    *,
    timeout: int = 10,
    check: bool = True,
    sudo: bool = False,
    input_text: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with unified error handling."""
    full_cmd = list(cmd)
    if sudo:
        full_cmd = ["sudo", *full_cmd]

    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            input=input_text,
        )
    except FileNotFoundError as exc:
        raise CommandNotFound(f"Binary not found: {cmd[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CommandTimeout(f"Command timed out after {timeout}s") from exc

    if check and result.returncode != 0:
        raise CommandError(result.stderr.strip() or f"Command failed (rc={result.returncode})")

    return result


__all__ = ["run", "CommandError", "CommandNotFound", "CommandTimeout"]