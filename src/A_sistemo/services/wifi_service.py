"""Wi-Fi service via nmcli."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from A_sistemo._shared import run


@dataclass
class WiFiNetwork:
    name: str
    active: bool
    signal: Optional[int] = None
    security: Optional[str] = None
    device: Optional[str] = None
    uuid: Optional[str] = None


def scan_networks() -> list[WiFiNetwork]:
    """Scan available Wi-Fi networks."""
    result = run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"])
    networks = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split(":")
        if len(fields) >= 4:
            try:
                signal = int(fields[2]) if fields[2] else None
            except ValueError:
                signal = None
            networks.append(WiFiNetwork(
                name=fields[1],
                active=fields[0] == "yes",
                signal=signal,
                security=fields[3] if fields[3] else None,
            ))
    return networks


def list_connections(show_secrets: bool = False) -> list[WiFiNetwork]:
    """List saved Wi-Fi connections."""
    extra = ["--show-secrets"] if show_secrets else []
    result = run(["nmcli", *extra, "-t", "-f", "ACTIVE,SSID,UUID,DEVICE", "connection", "show"])
    networks = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split(":")
        if len(fields) >= 4 and fields[1]:
            networks.append(WiFiNetwork(
                name=fields[1],
                active=fields[0] == "yes",
                uuid=fields[2],
                device=fields[3],
            ))
    return networks


def connect(name: str, password: Optional[str] = None) -> None:
    """Connect to a Wi-Fi network."""
    cmd = ["nmcli", "device", "wifi", "connect", name]
    if password:
        cmd.extend(["password", password])
    run(cmd, timeout=30)


def disconnect() -> None:
    """Disconnect active Wi-Fi."""
    run(["nmcli", "device", "disconnect", "wifi"], timeout=10)


def forget(name: str) -> None:
    """Delete a saved Wi-Fi profile."""
    run(["nmcli", "connection", "delete", name], timeout=10)


def restart() -> None:
    """Restart Wi-Fi (radio off then on)."""
    run(["nmcli", "radio", "wifi", "off"], timeout=5)
    run(["nmcli", "radio", "wifi", "on"], timeout=5)


__all__ = ["WiFiNetwork", "scan_networks", "list_connections", "connect", "disconnect", "forget", "restart"]