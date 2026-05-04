"""Wi-Fi service via nmcli."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from A_sistemo._shared import run, CommandError


@dataclass
class WiFiNetwork:
    name: str
    active: bool
    signal: Optional[int] = None
    security: Optional[str] = None
    device: Optional[str] = None
    uuid: Optional[str] = None
    ap_count: int = 1


def _deduplicate_networks(networks: list[WiFiNetwork]) -> list[WiFiNetwork]:
    """Deduplicate networks by SSID, keeping the entry with highest signal.

    For each SSID, only the entry with the strongest signal is kept.
    The active flag is OR'd across all duplicate entries for the same SSID.
    The ``ap_count`` field records how many access points (BSSIDs) were
    found for that SSID.
    Entries with an empty SSID (hidden networks) pass through unchanged.
    """
    empty_ssid = [n for n in networks if not n.name]

    best: dict[str, WiFiNetwork] = {}
    counts: dict[str, int] = {}
    for n in networks:
        if not n.name:
            continue
        counts[n.name] = counts.get(n.name, 0) + 1
        if n.name not in best:
            best[n.name] = n
        else:
            cur = best[n.name]
            # Higher signal wins
            if (n.signal or 0) > (cur.signal or 0):
                best[n.name] = n
            elif (n.signal or 0) == (cur.signal or 0) and n.active and not cur.active:
                best[n.name] = n
            # Propagate active flag across duplicates
            best[n.name].active = best[n.name].active or cur.active

    for name, net in best.items():
        net.ap_count = counts[name]

    return list(best.values()) + empty_ssid


def scan_networks() -> list[WiFiNetwork]:
    """Scan available Wi-Fi networks.

    Returns scan results merged with the currently active connection
    (so the connected network always appears even if not visible in scan).
    """
    result = run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"])
    networks: list[WiFiNetwork] = []
    seen_ssids: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split(":")
        if len(fields) >= 4:
            try:
                signal = int(fields[2]) if fields[2] else None
            except ValueError:
                signal = None
            # Rejoin SSID in case it contained ':'
            ssid = ":".join(fields[1:-2])
            networks.append(WiFiNetwork(
                name=ssid,
                active=fields[0] == "yes",
                signal=signal,
                security=fields[3] if fields[3] else None,
            ))
            seen_ssids.add(ssid)

    # Ensure the active connection appears even if not in scan range
    # Issue #6 attempted fix but used profile name instead of actual SSID
    try:
        active = run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"],
            check=False,
        )
        for line in active.stdout.splitlines():
            parts = line.split(":", 1)
            if len(parts) == 2 and parts[1] == "wifi" and parts[0] not in seen_ssids:
                # Query actual SSID from the profile (not profile name)
                ssid_result = run(
                    ["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", parts[0]],
                    check=False,
                )
                actual_ssids = ssid_result.stdout.strip()
                if actual_ssids:
                    for ssid in actual_ssids.splitlines():
                        ssid = ssid.strip()
                        if ssid and ssid not in seen_ssids:
                            networks.append(WiFiNetwork(name=ssid, active=True))
    except (CommandError, RuntimeError):
        pass

    return _deduplicate_networks(networks)


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