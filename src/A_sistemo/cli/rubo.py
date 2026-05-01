"""CLI for rubo (recycle bin) command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from A import info, error, tr
from A_sistemo.services import TrashItem, list_items, move_to_trash, restore, delete_permanent

app = typer.Typer(
    name="rubo",
    help=tr("trash"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _show_items(items: list[TrashItem]) -> None:
    if not items:
        info(tr("trash_empty"))
        return
    table = Table(title=tr("trash"))
    table.add_column(tr("nomo"), style="green")
    table.add_column(tr("size"), justify="right")
    table.add_column(tr("deleted"), style="dim")
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
        error(str(e))
        raise typer.Exit(1)


@app.command("forigi")
def forigi(
    paths: list[str] = typer.Argument(..., help=f"{tr('files')} (Example: file.txt)"),
    definitiva: bool = typer.Option(False, "-d", "--definitiva", help=tr("permanent")),
) -> None:
    """Move files to trash."""
    for path in paths:
        try:
            if definitiva:
                delete_permanent(path)
                info(f"{tr('permanent')}: {path}")
            else:
                move_to_trash(path)
                info(f"{tr('moved_to_trash')}: {path}")
        except Exception as e:
            error(str(e))


@app.command("restarigi")
def restarigi(
    names: list[str] = typer.Argument(..., help=f"{tr('files')} (Example: file.txt)"),
    celo: str = typer.Option(None, "-c", "--celo", help=f"{tr('destination')} (Example: /home/user/)"),
) -> None:
    """Restore files from trash."""
    for name in names:
        try:
            restore(name, celo)
            info(f"{tr('restored')}: {name}")
        except Exception as e:
            error(str(e))


__all__ = ["app"]