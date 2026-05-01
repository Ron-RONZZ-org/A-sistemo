"""CLI for usb command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from A import info, error, tr
from A_sistemo._shared import CommandError
from A_sistemo.services import USBDevice, list_devices, bind, unbind

app = typer.Typer(
    name="usb",
    help=tr("usb_devices"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _show_devices(devices: list[USBDevice]) -> None:
    if not devices:
        info(tr("neniu_usb"))
        return
    table = Table(title=tr("usb_aparoj"))
    table.add_column(tr("bus"), style="cyan")
    table.add_column(tr("device"), style="cyan")
    table.add_column(tr("vendor"), style="dim")
    table.add_column(tr("nomo"), style="green")
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
        error(str(e))
        raise typer.Exit(1)


@app.command("konekti")
def konekti(device: str = typer.Argument(..., help=f"{tr('device')} (Example: 1-1.2)")) -> None:
    """Bind USB device to driver."""
    try:
        bind(device)
        info(f"{tr('connected')}: {device}")
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("malkonekti")
def malkonekti(device: str = typer.Argument(..., help=f"{tr('device')} (Example: 1-1.2)")) -> None:
    """Unbind USB device from driver."""
    try:
        unbind(device)
        info(f"{tr('disconnected')}: {device}")
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


__all__ = ["app"]