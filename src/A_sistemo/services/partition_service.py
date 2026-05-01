"""Partition service via parted."""

from __future__ import annotations

from typing import Optional

from A_sistemo._shared import run


def shrink(device: str, new_size: str, force: bool = False) -> tuple[bool, str]:
    """Shrink a partition."""
    cmd = ["sudo", "parted", "-s", f"/dev/{device}", "resizepart", "1", new_size]
    if force:
        cmd.append("--script")
    result = run(cmd, timeout=60, check=False)
    return (result.returncode == 0, result.stderr.strip() or "Done")


def create(device: str, size: str, fs_type: str = "ext4", force: bool = False) -> tuple[bool, str]:
    """Create a new partition."""
    # Using parted mkpart command
    cmd = ["sudo", "parted", "-s", f"/dev/{device}", "mkpart", fs_type, "0", size]
    if force:
        cmd.append("--script")
    result = run(cmd, timeout=60, check=False)
    return (result.returncode == 0, result.stderr.strip() or "Done")


def format(device: str, fs_type: str = "ext4") -> tuple[bool, str]:
    """Format a partition."""
    result = run(["sudo", "mkfs", "-t", fs_type, f"/dev/{device}"], timeout=120, check=False)
    return (result.returncode == 0, result.stderr.strip() or "Done")


__all__ = ["shrink", "create", "format"]