"""CLI for rubo (recycle bin) command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from A import info
from A_sistemo.services import TrashItem, list_items, move_to_trash, restore, delete_permanent

app = typer.Typer(
    name="rubo",
    help="Recycle bin management",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _show_items(items: list[TrashItem]) -> None:
    if not items:
        info("La rubujo estas malplena")
        return
    table = Table(title="Rubujo")
    table.add_column("Nomo", style="green")
    table.add_column("Grandeco", justify="right")
    table.add_column("Forigita", style="dim")
    for item in items:
        table.add_row(item.name, item.size, item.deleted_at[:19])
    console.print(table)


@app.command("ls")
def ls() -> None:
    """List trash contents."""
    try:
        items = list_items()
        _show_items(items)
    except Exception as e:
        info(str(e))
        raise typer.Exit(1)


@app.command("forigi")
def forigi(
    paths: list[str] = typer.Argument(..., help="Files"),
    definitiva: bool = typer.Option(False, "-d", "--definitiva", help="Definitiva forigado"),
) -> None:
    """Move files to trash."""
    for path in paths:
        try:
            if definitiva:
                delete_permanent(path)
                info(f"Chapele forigita: {path}")
            else:
                move_to_trash(path)
                info(f"Al rubujo: {path}")
        except Exception as e:
            info(str(e))


@app.command("restarigi")
def restarigi(
    names: list[str] = typer.Argument(..., help="File names"),
    celo: str = typer.Option(None, "-c", "--celo", help="Destination"),
) -> None:
    """Restore files from trash."""
    for name in names:
        try:
            restore(name, celo)
            info(f"Restarigita: {name}")
        except Exception as e:
            info(str(e))


__all__ = ["app"]