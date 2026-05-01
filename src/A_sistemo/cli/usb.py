"""CLI for usb command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from A import info
from A_sistemo._shared import CommandError, run
from A_sistemo.services import USBDevice, list_devices, bind, unbind

app = typer.Typer(
    name="usb",
    help="USB device listing",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _show_devices(devices: list[USBDevice]) -> None:
    if not devices:
        info("Neniuj USB aparatoj")
        return
    table = Table(title="USB Aparatoj")
    table.add_column("Bus", style="cyan")
    table.add_column("Aparato", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Nomo", style="green")
    for dev in devices:
        table.add_row(dev.bus, dev.device, f"{dev.vid}:{dev.pid}", dev.name)
    console.print(table)


@app.command("ls")
def ls() -> None:
    """List USB devices."""
    try:
        devices = list_devices()
        _show_devices(devices)
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


@app.command("konekti")
def konekti(device: str = typer.Argument(..., help="BUS:DEV")) -> None:
    """Bind USB device to driver."""
    try:
        bind(device)
        info(f"Konektita: {device}")
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


@app.command("malkonekti")
def malkonekti(device: str = typer.Argument(..., help="BUS:DEV")) -> None:
    """Unbind USB device from driver."""
    try:
        unbind(device)
        info(f"Malkonektita: {device}")
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


__all__ = ["app"]