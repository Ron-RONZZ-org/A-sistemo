"""CLI for sistemo bash-alias command."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from A import info, error, tr
from A_sistemo.services import BashAlias, BashAliasDB

app = typer.Typer(
    name="sxelo-aliaso",
    help=tr("bash_aliases"),
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _get_db() -> BashAliasDB:
    from pathlib import Path
    return BashAliasDB(Path.home() / ".config" / "A" / "bash_aliases.db")


def _show_aliases(aliases: list[BashAlias]) -> None:
    if not aliases:
        info(tr("neniu_aliasoj"))
        return
    table = Table(title=tr("bash_aliases"))
    table.add_column("UID", style="cyan")
    table.add_column(tr("alias"), style="green")
    table.add_column(tr("function"), style="dim")
    for a in aliases:
        table.add_row(str(a.uid), a.alias, a.function[:50])
    console.print(table)


@app.command("ls")
def ls(
    alfabeto: bool = typer.Option(False, "-A", "--alfabeto", help=tr("alfabetaordo")),
    inversigi: bool = typer.Option(False, "-i", "--inversigi", help=tr("inversaordo")),
) -> None:
    """List bash aliases."""
    db = _get_db()
    sort_by = "alias" if alfabeto else "created_at"
    aliases = db.list_aliases(sort_by=sort_by, descending=not inversigi)
    _show_aliases(aliases)


@app.command("aldoni")
def aldoni(
    alias: str = typer.Option(..., "-a", "--alias", help=f"{tr('alias')} (Example: ll)"),
    funkcio: str = typer.Option(..., "-f", "--funkcio", help=f"{tr('function')} (Example: ls -la)"),
    notes: str = typer.Option("", "-n", "--notes", help=tr("notes")),
) -> None:
    """Add new bash alias."""
    db = _get_db()
    uid = db.add_alias(alias, funkcio, notes or None)
    db.sync_shell_config()
    info(f"{tr('added')}: UID {uid}")


@app.command("modifi")
def modifi(
    uid: int = typer.Argument(..., help=f"UID (Example: 1)"),
    alias: Optional[str] = typer.Option(None, "-a", "--alias", help=f"Nova {tr('alias')}"),
    funkcio: Optional[str] = typer.Option(None, "-f", "--funkcio", help=f"Nova {tr('function')}"),
    notes: Optional[str] = typer.Option(None, "-n", "--notes", help=tr("notes")),
) -> None:
    """Modify bash alias."""
    db = _get_db()
    if db.update_alias(uid, alias, funkcio, notes):
        db.sync_shell_config()
        info(f"{tr('modified')}: UID {uid}")
    else:
        error(f"{tr('ne_trovita_uid')} {uid}")
        raise typer.Exit(1)


@app.command("forigi")
def forigi(
    uids: list[int] = typer.Argument(..., help=f"UIDs (Example: 1 2)"),
    justa: bool = typer.Option(False, "-j", "--justa", help=tr("sen_konfirmo")),
) -> None:
    """Delete bash aliases."""
    if not uids:
        error(tr("最少_unu_uid"))
        raise typer.Exit(1)
    db = _get_db()
    for uid in uids:
        db.delete_alias(uid)
    db.sync_shell_config()
    info(f"{tr('deleted_alias')}: {len(uids)} aliasoj")


@app.command("vidi")
def vidi(uid: int = typer.Argument(..., help=f"UID (Example: 1)")) -> None:
    """View bash alias details."""
    db = _get_db()
    a = db.get_alias(uid)
    if not a:
        error(f"{tr('ne_trovita_uid')} {uid}")
        raise typer.Exit(1)
    info(f"{tr('alias')}: {a.alias}")
    info(f"{tr('function')}: {a.function}")
    if a.notes:
        info(f"{tr('notes')}: {a.notes}")


@app.command("serci")
def serci(query: str = typer.Argument("", help=f"{tr('sercho_termino')} (Example: ll)")) -> None:
    """Search bash aliases."""
    db = _get_db()
    results = db.search_aliases(query)
    _show_aliases(results)


__all__ = ["app"]