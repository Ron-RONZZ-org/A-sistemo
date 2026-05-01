"""CLI for sistemo info command."""

from __future__ import annotations

import typer

from A_sistemo.services import collect_system_info
from A import info


def info() -> None:
    """Show system information."""
    sys_info = collect_system_info()

    lines = []
    lines.append(f"OS       : {sys_info.os_name} {sys_info.os_release} ({sys_info.os_machine})")
    if sys_info.os_pretty:
        lines.append(f"         : {sys_info.os_pretty}")

    lines.append(f"CPU      : {sys_info.cpu_model}  ({sys_info.cpu_percent}% used)")
    lines.append(f"RAM      : {sys_info.ram_used_gib} / {sys_info.ram_total_gib} used")

    lines.append("Storage  :")
    for s in sys_info.storage:
        lines.append(f"  {s.mountpoint:20s} {s.used_gib} / {s.total_gib}")

    if sys_info.battery:
        status = "charging" if sys_info.battery.plugged else "discharging"
        lines.append(f"Battery  : {sys_info.battery.percent:.0f}% ({status})")
    else:
        lines.append("Battery  : n/a")

    lines.append(f"Network  : {sys_info.network.hostname} ({sys_info.network.ip_address})")
    if sys_info.network.active_interfaces:
        lines.append(f"           interfaces up: {', '.join(sys_info.network.active_interfaces)}")

    bt = sys_info.bluetooth
    if bt.available:
        lines.append(f"Bluetooth: powered={'yes' if bt.powered else 'no'}, {bt.connected_devices} device(s) connected")
    else:
        lines.append("Bluetooth: unavailable")

    info("\n".join(lines))


__all__ = ["info"]