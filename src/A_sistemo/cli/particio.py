"""CLI for disko particio command."""

from __future__ import annotations

import typer

from A import info, error, tr
from A_sistemo._shared import CommandError
from A_sistemo.services import shrink, create, format

app = typer.Typer(
    name="particio",
    help=tr("partition"),
)


@app.command("ŝrumpi")
def ŝrumpi(
    device: str = typer.Argument(..., help=f"{tr('device')} (Example: /dev/sdb1)"),
    new_size: str = typer.Argument(..., help=f"{tr('size')} (Example: 10G)"),
    justa: bool = typer.Option(False, "-j", "--justa", help=tr("sen_konfirmo")),
) -> None:
    """Shrink partition."""
    try:
        ok, msg = shrink(device, new_size, justa)
        if ok:
            info(f"{tr('sukcese')}: {msg}")
        else:
            error(f"{tr('malsukcese')}: {msg}")
            raise typer.Exit(1)
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("krei")
def krei(
    device: str = typer.Argument(..., help=f"{tr('device')} (Example: /dev/sdb)"),
    size: str = typer.Argument(..., help=f"{tr('size')} (Example: 5G)"),
    fs_type: str = typer.Option("ext4", "-t", "--tipo", help=f"{tr('type')} (Example: ext4)"),
    justa: bool = typer.Option(False, "-j", "--justa", help=tr("sen_konfirmo")),
) -> None:
    """Create partition."""
    try:
        ok, msg = create(device, size, fs_type, justa)
        if ok:
            info(f"{tr('sukcese')}: {msg}")
        else:
            error(f"{tr('malsukcese')}: {msg}")
            raise typer.Exit(1)
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("formati")
def formati(
    device: str = typer.Argument(..., help=f"{tr('device')} (Example: /dev/sdb1)"),
    fs_type: str = typer.Option("ext4", "-t", "--tipo", help=f"{tr('type')} (Example: ext4)"),
) -> None:
    """Format partition."""
    try:
        ok, msg = format(device, fs_type)
        if ok:
            info(f"{tr('sukcese')}: {msg}")
        else:
            error(f"{tr('malsukcese')}: {msg}")
            raise typer.Exit(1)
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


__all__ = ["app"]