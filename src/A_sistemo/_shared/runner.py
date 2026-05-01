"""Unified subprocess runner for A-sistemo - wraps A.utils.run."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from A.utils import run as _run, SubprocessResult


class CommandError(RuntimeError):
    """Raised when a command fails or times out."""


class CommandNotFound(CommandError):
    """Raised when the command binary doesn't exist."""


class CommandTimeout(CommandError):
    """Raised when a command exceeds its timeout."""


def run(
    cmd: Sequence[str],
    *,
    timeout: float = 10.0,
    check: bool = True,
    sudo: bool = False,
    input_text: Optional[str] = None,
) -> SubprocessResult:
    """Run a subprocess with unified error handling."""
    full_cmd = list(cmd)
    if sudo:
        full_cmd = ["sudo", *full_cmd]

    result = _run(*full_cmd, timeout=timeout, input=input_text)

    if check and result.returncode != 0:
        raise CommandError(result.stderr.strip() or f"Command failed (rc={result.returncode})")

    return result


__all__ = ["run", "CommandError", "CommandNotFound", "CommandTimeout"]