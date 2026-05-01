"""A-sistemo services."""

from A_sistemo.services.system_info import SystemInfo, collect_system_info
from A_sistemo.services.wifi_service import WiFiNetwork, scan_networks, list_connections, connect, disconnect, forget, restart
from A_sistemo.services.bluetooth_service import BluetoothDevice, list_paired, connect, disconnect, get_info, is_powered, power_on
from A_sistemo.services.usb_service import USBDevice, list_devices, bind, unbind
from A_sistemo.services.disk_service import DiskDevice, SMARTInfo, list_devices, get_smart_info, mount, unmount
from A_sistemo.services.recycle_bin import TrashItem, list_items, move_to_trash, restore, delete_permanent
from A_sistemo.services.bash_alias_db import BashAlias, BashAliasDB
from A_sistemo.services.partition_service import shrink, create, format
from A_sistemo.services.installer import get_poetry_env_path, install_binary, generate_shell_aliases, setup_bashrc

__all__ = [
    "SystemInfo",
    "collect_system_info",
    "WiFiNetwork",
    "scan_networks",
    "list_connections", 
    "connect",
    "disconnect",
    "forget",
    "restart",
    "BluetoothDevice",
    "list_paired",
    "get_info",
    "is_powered",
    "power_on",
    "USBDevice",
    "list_devices",
    "bind",
    "unbind",
    "DiskDevice",
    "SMARTInfo",
    "get_smart_info",
    "mount",
    "unmount",
    "TrashItem",
    "list_items",
    "move_to_trash",
    "restore",
    "delete_permanent",
    "BashAlias",
    "BashAliasDB",
    "shrink",
    "create",
    "format",
    "get_poetry_env_path",
    "install_binary",
    "generate_shell_aliases",
    "setup_bashrc",
]