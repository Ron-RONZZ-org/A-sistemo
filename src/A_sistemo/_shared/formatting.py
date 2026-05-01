"""Shared formatting utilities."""

from __future__ import annotations


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human-readable (B/KB/MB/GB/TB/PB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


def format_gib(bytes_: int) -> str:
    """Format bytes as GiB string."""
    return f"{bytes_ / 1024**3:.1f} GiB"


__all__ = ["format_bytes", "format_gib"]