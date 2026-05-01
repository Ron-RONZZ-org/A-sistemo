"""System information gathering service."""

from __future__ import annotations

import platform
import socket
from dataclasses import dataclass
from typing import Optional

import psutil

from A_sistemo._shared import format_gib, run


@dataclass
class StorageInfo:
    mountpoint: str
    used_gib: str
    total_gib: str


@dataclass
class BatteryInfo:
    percent: float
    plugged: bool


@dataclass
class NetworkInfo:
    hostname: str
    ip_address: str
    active_interfaces: list[str]


@dataclass
class BluetoothInfo:
    powered: bool
    connected_devices: int
    available: bool


@dataclass
class SystemInfo:
    os_name: str
    os_release: str
    os_machine: str
    os_pretty: Optional[str]
    cpu_model: str
    cpu_percent: float
    ram_used_gib: str
    ram_total_gib: str
    storage: list[StorageInfo]
    battery: Optional[BatteryInfo]
    network: NetworkInfo
    bluetooth: BluetoothInfo


def collect_system_info() -> SystemInfo:
    """Gather all system information."""
    uname = platform.uname()
    try:
        os_pretty = platform.freedesktop_os_release().get("PRETTY_NAME", "")
    except (AttributeError, OSError):
        os_pretty = None

    cpu_model = platform.processor() or uname.processor or "unknown"
    cpu_pct = psutil.cpu_percent(interval=0.5)

    vm = psutil.virtual_memory()
    ram_used = format_gib(vm.used)
    ram_total = format_gib(vm.total)

    storage = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        storage.append(StorageInfo(
            mountpoint=part.mountpoint,
            used_gib=format_gib(usage.used),
            total_gib=format_gib(usage.total),
        ))

    battery_raw = psutil.sensors_battery()
    battery = None
    if battery_raw:
        battery = BatteryInfo(percent=battery_raw.percent, plugged=battery_raw.power_plugged)

    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
    except OSError:
        hostname = "unknown"
        ip_address = "unknown"

    net_if = psutil.net_if_stats()
    active = [iface for iface, stat in net_if.items() if stat.isup and iface != "lo"]

    bt_info = _collect_bluetooth_info()

    return SystemInfo(
        os_name=uname.system,
        os_release=uname.release,
        os_machine=uname.machine,
        os_pretty=os_pretty or None,
        cpu_model=cpu_model,
        cpu_percent=cpu_pct,
        ram_used_gib=ram_used,
        ram_total_gib=ram_total,
        storage=storage,
        battery=battery,
        network=NetworkInfo(hostname=hostname, ip_address=ip_address, active_interfaces=active),
        bluetooth=bt_info,
    )


def _collect_bluetooth_info() -> BluetoothInfo:
    """Query Bluetooth status via bluetoothctl."""
    try:
        result = run(["bluetoothctl", "show"], timeout=5, check=False)
        powered = "Powered: yes" in result.stdout
        devices = run(["bluetoothctl", "devices", "Connected"], timeout=5, check=False)
        connected_count = len([ln for ln in devices.stdout.splitlines() if ln.strip()])
        return BluetoothInfo(powered=powered, connected_devices=connected_count, available=True)
    except (FileNotFoundError, RuntimeError):
        return BluetoothInfo(powered=False, connected_devices=0, available=False)


__all__ = ["SystemInfo", "StorageInfo", "BatteryInfo", "NetworkInfo", "BluetoothInfo", "collect_system_info"]