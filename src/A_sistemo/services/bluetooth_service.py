"""Bluetooth service via bluetoothctl."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from A_sistemo._shared import run


@dataclass
class BluetoothDevice:
    mac: str
    name: str
    connected: bool = False


def list_paired() -> list[BluetoothDevice]:
    """List paired Bluetooth devices."""
    paired = run(["bluetoothctl", "devices", "Paired"], timeout=5)
    connected = run(["bluetoothctl", "devices", "Connected"], timeout=5)

    connected_macs = {
        line.split(" ", 2)[1]
        for line in connected.stdout.strip().splitlines()
        if len(line.split(" ", 2)) >= 2
    }

    devices = []
    for line in paired.stdout.strip().splitlines():
        parts = line.split(" ", 2)
        if len(parts) >= 2:
            devices.append(BluetoothDevice(
                mac=parts[1],
                name=parts[2] if len(parts) > 2 else "",
                connected=parts[1] in connected_macs,
            ))
    return devices


def connect(mac: str) -> None:
    """Connect to a Bluetooth device."""
    run(["bluetoothctl", "connect", mac], timeout=15)


def disconnect(mac: Optional[str] = None) -> None:
    """Disconnect a Bluetooth device (or all if no MAC)."""
    if mac:
        run(["bluetoothctl", "disconnect", mac], timeout=10)
    else:
        # Disconnect all connected
        for dev in list_paired():
            if dev.connected:
                run(["bluetoothctl", "disconnect", dev.mac], timeout=10)


def get_info(mac: str) -> str:
    """Get info for a specific device."""
    result = run(["bluetoothctl", "info", mac])
    return result.stdout.strip()


def is_powered() -> bool:
    """Check if Bluetooth is powered on."""
    try:
        result = run(["bluetoothctl", "show"], timeout=5, check=False)
        return "Powered: yes" in result.stdout
    except RuntimeError:
        return False


def power_on() -> bool:
    """Try to power on Bluetooth."""
    result = run(["bluetoothctl", "power", "on"], timeout=5, check=False)
    return result.returncode == 0


__all__ = ["BluetoothDevice", "list_paired", "connect", "disconnect", "get_info", "is_powered", "power_on"]