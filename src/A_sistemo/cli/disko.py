"""CLI for disko command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from A import info, error, tr
from A_sistemo._shared import CommandError
from A_sistemo.services import DiskDevice, SMARTInfo, list_devices, get_smart_info, mount, unmount
from A_sistemo.cli import particio

app = typer.Typer(
    name="disko",
    help=tr("disks"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()

particio_app = particio.app
app.add_typer(particio_app)


def _show_disks(devices: list[DiskDevice]) -> None:
    if not devices:
        info(tr("neniu_diskoj"))
        return
    table = Table(title=tr("disks"))
    table.add_column(tr("nomo"), style="yellow")
    table.add_column(tr("type"), style="dim")
    table.add_column(tr("loko"), style="dim")
    table.add_column(tr("size"), justify="right")
    for dev in devices:
        table.add_row(dev.name, dev.type, dev.mountpoint, dev.size)
    console.print(table)


@app.command("ls")
def ls() -> None:
    """List storage devices."""
    try:
        devices = list_devices()
        _show_disks(devices)
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("sano")
def sano(nomo: str = typer.Argument(..., help=f"{tr('device')} (Example: /dev/sda1)")) -> None:
    """Check disk health (SMART)."""
    try:
        smart = get_smart_info(nomo)
        info(f"{tr('health')}: {smart.health}")
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("munti")
def munti(
    nomo: str = typer.Argument(..., help=f"{tr('device')} (Example: /dev/sdb1)"),
    loko: str = typer.Option(None, "-l", "--loko", help=f"{tr('loko')} (Example: /mnt/backup)"),
) -> None:
    """Mount disk."""
    try:
        mount(nomo, loko)
        info(f"{tr('mounted_')} {nomo}")
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("malmunti")
def malmunti(nomo: str = typer.Argument(..., help=f"{tr('device')} (Example: /dev/sdb1)")) -> None:
    """Unmount disk."""
    try:
        unmount(nomo)
        info(f"{tr('malmuntita_')} {nomo}")
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


__all__ = ["app"]