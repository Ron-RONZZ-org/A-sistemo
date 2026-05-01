"""Recycle bin service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from A_sistemo._shared import format_bytes


@dataclass
class TrashItem:
    name: str
    original_path: str
    deleted_at: str
    size: str


def list_items() -> list[TrashItem]:
    """List items in trash."""
    trash = _get_trash_dir()
    items = []

    for f in trash.iterdir():
        if not f.is_file():
            continue
        size = f.stat().st_size
        items.append(TrashItem(
            name=f.name,
            original_path=str(f),
            deleted_at=datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            size=format_bytes(size),
        ))
    return items


def move_to_trash(path: str) -> None:
    """Move a file to trash."""
    src = Path(path).expanduser()
    if not src.exists():
        raise FileNotFoundError(f"File not found: {path}")

    target = _get_trash_dir() / src.name
    if target.exists():
        # Rename with suffix
        i = 1
        while target.exists():
            target = _get_trash_dir() / f"{src.name}.{i}"
            i += 1

    src.rename(target)


def restore(name: str, destination: Optional[str] = None) -> None:
    """Restore a file from trash."""
    trash = _get_trash_dir()
    src = trash / name
    if not src.exists():
        raise FileNotFoundError(f"Not found in trash: {name}")

    dest = Path(destination) if destination else src
    if dest.exists():
        raise FileExistsError(f"Destination exists: {dest}")

    src.rename(dest)


def delete_permanent(name: str) -> None:
    """Delete a file permanently from trash."""
    trash = _get_trash_dir()
    f = trash / name
    if f.exists():
        f.unlink()


def _get_trash_dir() -> Path:
    """Get trash directory."""
    trash = Path.home() / ".local" / "share" / "Trash" / "files"
    trash.mkdir(parents=True, exist_ok=True)
    return trash


__all__ = ["TrashItem", "list_items", "move_to_trash", "restore", "delete_permanent"]