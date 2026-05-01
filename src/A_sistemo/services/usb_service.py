"""USB device service via lsusb."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from A_sistemo._shared import run


@dataclass
class USBDevice:
    bus: str
    device: str
    vid: str
    pid: str
    name: str
    driver: Optional[str] = None


def list_devices() -> list[USBDevice]:
    """List USB devices via lsusb."""
    result = run(["lsusb", "-v"], timeout=10, check=False)
    devices = []

    for line in result.stdout.splitlines():
        if not line.startswith("Bus"):
            continue
        # Parse: Bus 001 Device 002: ID 8087:0029 Intel Corp.
        parts = line.split()
        if len(parts) < 6 or parts[0] != "Bus":
            continue

        bus = parts[1]
        device = parts[3].rstrip(":")
        id_part = parts[5] if len(parts) > 5 else ":"
        vid, pid = id_part.split(":") if ":" in id_part else ("", "")
        name = " ".join(parts[6:]) if len(parts) > 6 else ""

        devices.append(USBDevice(
            bus=bus,
            device=device,
            vid=vid,
            pid=pid,
            name=name,
        ))
    return devices


def _resolve_device_token(token: str) -> tuple[str, str]:
    """Resolve BUS:DEV token."""
    text = token.strip()
    if ":" in text:
        bus, dev = text.split(":", 1)
        if bus.isdigit() and dev.isdigit():
            return bus.zfill(3), dev.zfill(3)
    raise ValueError("Use BUS:DEV format, e.g. 001:002")


def _sysfs_device_path(bus: str, dev: str) -> Optional[Path]:
    """Find device path in sysfs."""
    root = Path("/sys/bus/usb/devices")
    if not root.exists():
        return None

    for child in root.iterdir():
        if not child.is_dir():
            continue
        busnum = child / "busnum"
        devnum = child / "devnum"
        if not busnum.exists() or not devnum.exists():
            continue
        try:
            b = busnum.read_text().strip().zfill(3)
            d = devnum.read_text().strip().zfill(3)
        except OSError:
            continue
        if b == bus and d == dev:
            return child
    return None


def bind(device: str) -> None:
    """Bind a USB device to its driver."""
    bus, dev = _resolve_device_token(device)
    dev_path = _sysfs_device_path(bus, dev)
    if dev_path is None:
        raise RuntimeError(f"USB device {device} not found in sysfs")

    bind_path = dev_path / "driver" / "bind"
    if not bind_path.exists():
        raise RuntimeError("No driver bound to device")

    bind_path.write_text(dev_path.name)


def unbind(device: str) -> None:
    """Unbind a USB device from its driver."""
    bus, dev = _resolve_device_token(device)
    dev_path = _sysfs_device_path(bus, dev)
    if dev_path is None:
        raise RuntimeError(f"USB device {device} not found in sysfs")

    unbind_path = dev_path / "driver" / "unbind"
    if not unbind_path.exists():
        raise RuntimeError("Device not bound to any driver")

    unbind_path.write_text(dev_path.name)


__all__ = ["USBDevice", "list_devices", "bind", "unbind"]