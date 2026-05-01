"""A-sistemo - System management commands.

Usage:
    A sistemo           # Show system info (default)
    A sistemo wifi     # Wi-Fi management
    A sistemo bluhdento  # Bluetooth management
    A sistemo usb     # USB device listing
    A sistemo disko   # Disk management
    A sistemo rubo    # Recycle bin management
"""

from __future__ import annotations

import datetime
import json
import platform
import socket
import subprocess
from pathlib import Path
from typing import Optional

import psutil
import typer

from rich.console import Console
from rich.table import Table

from A.utils import info

app = typer.Typer(
    name="sistemo",
    help="System management: info, wifi, bluetooth, usb, disk, rubo",
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


def _run(cmd: list[str], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)


def _bytes_to_gib(n: int) -> str:
    """Convert bytes to GiB string."""
    return f"{n / 1024**3:.1f} GiB"


# =============================================================================
# INFO SUBCOMMAND
# =============================================================================

info_app = typer.Typer(name="info", help="Show system information")
app.add_typer(info_app)


@info_app.command()
def show_info() -> None:
    """Show system information."""
    lines: list[str] = []

    # OS
    uname = platform.uname()
    lines.append(f"OS       : {uname.system} {uname.release} ({uname.machine})")
    try:
        os_pretty = platform.freedesktop_os_release().get("PRETTY_NAME", "")
        if os_pretty:
            lines.append(f"         : {os_pretty}")
    except (AttributeError, OSError):
        pass

    # CPU
    cpu_model = platform.processor() or uname.processor or "unknown"
    cpu_pct = psutil.cpu_percent(interval=0.5)
    lines.append(f"CPU      : {cpu_model}  ({cpu_pct}% used)")

    # RAM
    vm = psutil.virtual_memory()
    ram_used = _bytes_to_gib(vm.used)
    ram_total = _bytes_to_gib(vm.total)
    lines.append(f"RAM      : {ram_used} / {ram_total} used")

    # Storage
    lines.append("Storage  :")
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        lines.append(
            f"  {part.mountpoint:20s} "
            f"{_bytes_to_gib(usage.used)} / {_bytes_to_gib(usage.total)}"
        )

    # Battery
    battery = psutil.sensors_battery()
    if battery is not None:
        status = "charging" if battery.power_plugged else "discharging"
        lines.append(f"Battery  : {battery.percent:.0f}% ({status})")
    else:
        lines.append("Battery  : n/a")

    # Network
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except OSError:
        hostname, ip = "unknown", "unknown"
    lines.append(f"Network  : {hostname} ({ip})")

    # Active network interfaces
    net_if = psutil.net_if_stats()
    active = [iface for iface, stat in net_if.items() if stat.isup and iface != "lo"]
    if active:
        lines.append(f"           interfaces up: {', '.join(active)}")

    # Bluetooth
    bt_output = _run(["bluetoothctl", "show"])
    if bt_output:
        powered = "yes" if "Powered: yes" in bt_output.stdout else "no"
        bt_devices = _run(["bluetoothctl", "devices", "Connected"])
        connected_count = len([ln for ln in bt_devices.stdout.splitlines() if ln.strip()])
        lines.append(f"Bluetooth: powered={powered}, {connected_count} device(s) connected")
    else:
        lines.append("Bluetooth: unavailable")

    info("\n".join(lines))


# =============================================================================
# WIFI SUBCOMMAND
# =============================================================================

wifi_app = typer.Typer(
    name="wifi",
    help="Wi-Fi management",
    no_args_is_help=True,
)
app.add_typer(wifi_app)


@wifi_app.command("ls")
def wifi_ls(
    name: Optional[str] = typer.Argument(None, help="SSID to show"),
    pasvorto: bool = typer.Option(False, "-p", help="Show password"),
) -> None:
    """List Wi-Fi networks."""
    if name:
        extra = ["--show-secrets"] if pasvorto else []
        result = _run(["nmcli", *extra, "connection", "show", name])
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)
        info(result.stdout.strip())
        return

    result = _run(["nmcli", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"])
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    info(result.stdout.strip())


@wifi_app.command("konekti")
def wifi_konekti(
    nomo: str = typer.Argument(..., help="SSID"),
    pasvorto: Optional[str] = typer.Option(None, "-p", help="Password"),
) -> None:
    """Connect to Wi-Fi."""
    cmd = ["nmcli", "device", "wifi", "connect", nomo]
    if pasvorto:
        cmd += ["password", pasvorto]

    result = _run(cmd)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    info(result.stdout.strip())


@wifi_app.command("malkonekti")
def wifi_malkonekti() -> None:
    """Disconnect from Wi-Fi."""
    result = _run(["nmcli", "device", "wifi", "off"])
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    info("Malkonektita")


@wifi_app.command("forigi")
def wifi_forigi(nomo: str = typer.Argument(..., help="SSID")) -> None:
    """Delete saved Wi-Fi network."""
    result = _run(["nmcli", "connection", "delete", nomo])
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    info("Forigita")


# =============================================================================
# BLUHDENTO (BLUETOOTH) SUBCOMMAND
# =============================================================================

bluetooth_app = typer.Typer(
    name="bluhdento",
    help="Bluetooth management",
    no_args_is_help=True,
)
app.add_typer(bluetooth_app)


def _bluetoothctl(*args: str) -> subprocess.CompletedProcess[str]:
    return _run(["bluetoothctl", *args])


@bluetooth_app.command("ls")
def bluetooth_ls(
    mac: Optional[str] = typer.Argument(None, help="MAC address"),
) -> None:
    """List paired Bluetooth devices."""
    if mac:
        result = _bluetoothctl("info", mac)
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)
        info(result.stdout.strip())
        return

    paired = _bluetoothctl("devices", "Paired")
    if paired.returncode != 0:
        raise typer.Exit(code=paired.returncode)

    devices = paired.stdout.strip().splitlines()
    if devices:
        info("\n".join(devices))
    else:
        info("No paired devices")


@bluetooth_app.command("konekti")
def bluetooth_konekti(mac: str = typer.Argument(..., help="MAC address")) -> None:
    """Connect to Bluetooth device."""
    result = _bluetoothctl("connect", mac)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    info(result.stdout.strip() or "Konektita")


@bluetooth_app.command("malkonekti")
def bluetooth_malkonekti(
    mac: Optional[str] = typer.Argument(None, help="MAC address"),
) -> None:
    """Disconnect Bluetooth device."""
    if mac:
        result = _bluetoothctl("disconnect", mac)
    else:
        result = _bluetoothctl("disconnect")

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    info("Malkonektita")


# =============================================================================
# USB SUBCOMMAND
# =============================================================================

usb_app = typer.Typer(name="usb", help="USB device listing", no_args_is_help=True)
app.add_typer(usb_app)


@usb_app.command("ls")
def usb_ls() -> None:
    """List USB devices."""
    result = _run(["lsusb"])
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)
    info(result.stdout.strip())


# =============================================================================
# DISKO SUBCOMMAND
# =============================================================================

disko_app = typer.Typer(name="disko", help="Disk management", no_args_is_help=True)
app.add_typer(disko_app)


def _format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"


@disko_app.command("ls")
def disko_ls() -> None:
    """List storage devices."""
    result = _run([
        "lsblk",
        "--json",
        "--output", "NAME,TYPE,MOUNTPOINT,SIZE,FSTYPE,MODEL",
        "--bytes"
    ])

    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise typer.Exit(code=1)

    devices = data.get("blockdevices", [])
    if not devices:
        info("Neniu disko trovita")
        return

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Nomo", style="yellow")
    table.add_column("Tipo")
    table.add_column("Loko")
    table.add_column("Grandeco", justify="right")

    def add_device(dev: dict, indent: int = 0):
        name = ("  " * indent) + dev.get("name", "?")
        tipo = dev.get("type", "?")
        mountpoint = dev.get("mountpoint") or ""
        size = dev.get("size")
        size_str = _format_size(size) if size else ""
        table.add_row(name, tipo, mountpoint, size_str)
        for child in dev.get("children", []):
            add_device(child, indent + 1)

    for device in devices:
        add_device(device)

    console.print(table)


# =============================================================================
# RUBO (RECYCLE BIN) SUBCOMMAND
# =============================================================================

rubo_app = typer.Typer(name="rubo", help="Recycle bin management", no_args_is_help=True)
app.add_typer(rubo_app)


def _rubo_dir() -> Path:
    """Get trash directory."""
    trash = Path.home() / ".local" / "share" / "Trash" / "files"
    trash.mkdir(parents=True, exist_ok=True)
    return trash


@rubo_app.command("ls")
def rubo_ls() -> None:
    """List trash contents."""
    trash = _rubo_dir()
    files = list(trash.iterdir())

    if not files:
        info("La rubujo estas malplena")
        return

    table = Table(show_header=True, header_style="bold cyan", border_style="dim")
    table.add_column("Nomo", style="green")
    table.add_column("Grandeco", justify="right")

    for f in files:
        size = f.stat().st_size if f.is_file() else 0
        table.add_row(f.name, _format_size(size))

    console.print(table)


@rubo_app.command("forigi")
def rubo_forigi(
    paths: list[str] = typer.Argument(..., help="Files to delete"),
    definitiva: bool = typer.Option(False, "-d", "--definitiva", help="Delete permanently"),
) -> None:
    """Move files to trash."""
    for path_str in paths:
        path = Path(path_str).expanduser()
        if not path.exists():
            continue

        if definitiva:
            if path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                path.unlink()
            info(f"Forigita: {path}")
        else:
            target = _rubo_dir() / path.name
            path.rename(target)
            info(f"Al rubujo: {path}")


@rubo_app.command("restarigi")
def rubo_restarigi(
    uids: list[str] = typer.Argument(..., help="File names to restore"),
) -> None:
    """Restore files from trash."""
    trash = _rubo_dir()
    for uid in uids:
        f = trash / uid
        if f.exists():
            info(f"Restarigita: {f}")
        else:
            info(f"Ne trovita: {uid}")


# =============================================================================
# CALLBACK: Default to info
# =============================================================================


@app.callback(invoke_without_command=True)
def sistemo_callback(ctx: typer.Context) -> None:
    """Default: show system info."""
    if ctx.invoked_subcommand is None:
        show_info()


__all__ = ["app"]