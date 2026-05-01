"""CLI for disko particio command."""

from __future__ import annotations

import typer

from A import info
from A_sistemo._shared import CommandError
from A_sistemo.services import shrink, create, format

app = typer.Typer(
    name="particio",
    help="Partition management",
)


@app.command("srumpi")
def srumpi(
    device: str = typer.Argument(..., help="Device"),
    new_size: str = typer.Argument(..., help="Nova grandeco"),
    justa: bool = typer.Option(False, "-j", "--justa", help="Sen kontrolo"),
) -> None:
    """Shrink partition."""
    try:
        ok, msg = shrink(device, new_size, justa)
        if ok:
            info(f"Sukcese: {msg}")
        else:
            info(f"Malsukcese: {msg}")
            raise typer.Exit(1)
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


@app.command("krei")
def krei(
    device: str = typer.Argument(..., help="Device"),
    size: str = typer.Argument(..., help="Grandeco"),
    fs_type: str = typer.Option("ext4", "-t", "--tipo", help="Filesystem tipo"),
    justa: bool = typer.Option(False, "-j", "--justa", help="Sen kontrolo"),
) -> None:
    """Create partition."""
    try:
        ok, msg = create(device, size, fs_type, justa)
        if ok:
            info(f"Sukcese: {msg}")
        else:
            info(f"Malsukcese: {msg}")
            raise typer.Exit(1)
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


@app.command("formati")
def formati(
    device: str = typer.Argument(..., help="Device"),
    fs_type: str = typer.Option("ext4", "-t", "--tipo", help="Filesystem tipo"),
) -> None:
    """Format partition."""
    try:
        ok, msg = format(device, fs_type)
        if ok:
            info(f"Sukcese: {msg}")
        else:
            info(f"Malsukcese: {msg}")
            raise typer.Exit(1)
    except CommandError as e:
        info(str(e))
        raise typer.Exit(1)


__all__ = ["app"]