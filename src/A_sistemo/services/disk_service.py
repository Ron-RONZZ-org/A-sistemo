"""Disk service via lsblk, smartctl, mount."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from A_sistemo._shared import run, format_bytes


@dataclass
class DiskDevice:
    name: str
    type: str
    mountpoint: str
    size: str
    fs_type: str
    model: str


@dataclass
class SMARTInfo:
    device: str
    health: str
    attributes: list[dict]


def list_devices() -> list[DiskDevice]:
    """List storage devices via lsblk."""
    result = run([
        "lsblk",
        "--json",
        "--output", "NAME,TYPE,MOUNTPOINT,SIZE,FSTYPE,MODEL",
        "--bytes"
    ])

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    data = json.loads(result.stdout)
    devices = []

    def add_recursive(devs: list[dict], indent: int = 0):
        for d in devs:
            devices.append(DiskDevice(
                name=("  " * indent) + d.get("name", "?"),
                type=d.get("type", "?"),
                mountpoint=d.get("mountpoint") or "",
                size=format_bytes(d.get("size", 0)),
                fs_type=d.get("fstype") or "",
                model=(d.get("model") or "").strip(),
            ))
            for child in d.get("children", []):
                add_recursive([child], indent + 1)

    add_recursive(data.get("blockdevices", []))
    return devices


def get_smart_info(device: str) -> SMARTInfo:
    """Get SMART info for a device."""
    dev_path = f"/dev/{device}" if not device.startswith("/dev/") else device

    result = run(["sudo", "smartctl", "-a", dev_path], timeout=30, check=False)

    # Parse SMART output
    health = "Unknown"
    attributes = []

    for line in result.stdout.splitlines():
        if "SMART overall-health" in line or "SMART Health Status" in line:
            health = line.split(":")[-1].strip()

        if "ID# ATTRIBUTE_NAME" in line:
            continue

        parts = line.split()
        if len(parts) >= 10 and parts[0].isdigit():
            attributes.append({
                "id": parts[0],
                "name": parts[1],
                "value": parts[3],
                "worst": parts[4],
                "threshold": parts[5],
                "raw": " ".join(parts[9:]),
            })

    return SMARTInfo(device=dev_path, health=health, attributes=attributes)


def mount(device: str, location: Optional[str] = None) -> None:
    """Mount a disk."""
    dev_path = f"/dev/{device}" if not device.startswith("/dev/") else device

    # Check if already mounted
    result = run(["mount"], timeout=5, check=False)
    for line in result.stdout.splitlines():
        if dev_path in line:
            raise RuntimeError(f"Already mounted: {line}")

    # Determine mount point
    if location is None:
        result = run(["lsblk", "-no", "LABEL", dev_path], check=False)
        label = result.stdout.strip()
        location = str(Path.home() / (label or device.replace("/", "_")))

    mount_path = Path(location)
    if not mount_path.exists():
        mount_path.mkdir(parents=True)

    run(["sudo", "mount", dev_path, str(mount_path)], timeout=30)


def unmount(target: str) -> None:
    """Unmount a disk."""
    if not target.startswith("/dev/") and not target.startswith("/"):
        target = f"/dev/{target}"

    run(["sudo", "umount", target], timeout=30)


__all__ = ["DiskDevice", "SMARTInfo", "list_devices", "get_smart_info", "mount", "unmount"]