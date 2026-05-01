"""CLI for bluetooth (bluhdento) command."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from A import info, error, tr
from A_sistemo._shared import CommandError
from A_sistemo.services import BluetoothDevice, list_paired, connect, disconnect, get_info

app = typer.Typer(
    name="bluhdento",
    help=tr("bluetooth"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _show_devices(devices: list[BluetoothDevice]) -> None:
    if not devices:
        info(tr("pareigitaj_aparoj"))
        return
    table = Table(title=tr("bluetooth_devices"))
    table.add_column(tr("mac"), style="cyan")
    table.add_column(tr("nomo"), style="green")
    table.add_column(tr("statuso"), style="dim")
    for dev in devices:
        table.add_row(dev.mac, dev.name, tr("connected") if dev.connected else "")
    console.print(table)


@app.command("ls")
def ls(mac: Optional[str] = typer.Argument(None, help=tr("mac"))) -> None:
    """List paired Bluetooth devices."""
    try:
        if mac:
            result = get_info(mac)
            info(result)
            return
        devices = list_paired()
        _show_devices(devices)
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("konekti")
def konekti(mac: str = typer.Argument(..., help=f"{tr('mac')} (Example: AA:BB:CC:DD:EE:FF)")) -> None:
    """Connect to Bluetooth device."""
    try:
        connect(mac)
        info(f"{tr('konektita_al')} {mac}")
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("malkonekti")
def malkonekti(mac: Optional[str] = typer.Argument(None, help=f"{tr('mac')} (Example: AA:BB:CC:DD:EE:FF)")) -> None:
    """Disconnect Bluetooth device."""
    try:
        disconnect(mac)
        info(tr("disconnected"))
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


__all__ = ["app"]