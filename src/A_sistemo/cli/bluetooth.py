"""CLI for bluetooth (bluhdento) command."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from A import info
from A_sistemo._shared import CommandError, run
from A_sistemo.services import BluetoothDevice, list_paired, connect, disconnect

app = typer.Typer(
    name="bluhdento",
    help="Bluetooth management",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _show_devices(devices: list[BluetoothDevice]) -> None:
    if not devices:
        info("Neniuj pareigitaj aparatoj")
        return
    table = Table(title="Bluetooth Aparatoj")
    table.add_column("MAC", style="cyan")
    table.add_column("Nomo", style="green")
    table.add_column("Statuso", style="dim")
    for dev in devices:
        table.add_row(dev.mac, dev.name, "Konektita" if dev.connected else "")
    console.print(table)


@app.command("ls")
def ls(mac: Optional[str] = typer.Argument(None, help="MAC")) -> None:
    """List paired Bluetooth devices."""
    try:
        if mac:
            result = run(["bluetoothctl", "info", mac])
            info(result.stdout.strip())
            return
        devices = list_paired()
        _show_devices(devices)
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


@app.command("konekti")
def konekti(mac: str = typer.Argument(..., help="MAC")) -> None:
    """Connect to Bluetooth device."""
    try:
        connect(mac)
        info(f"Konektita al {mac}")
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


@app.command("malkonekti")
def malkonekti(mac: Optional[str] = typer.Argument(None, help="MAC")) -> None:
    """Disconnect Bluetooth device."""
    try:
        disconnect(mac)
        info("Malkonektita")
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


__all__ = ["app"]