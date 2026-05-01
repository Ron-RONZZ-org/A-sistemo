"""CLI for sistemo bash-alias command."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from A import info
from A_sistemo.services import BashAlias, BashAliasDB

app = typer.Typer(
    name="bash-alias",
    help="Bash alias management",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _get_db() -> BashAliasDB:
    from pathlib import Path
    return BashAliasDB(Path.home() / ".config" / "A" / "bash_aliases.db")


def _show_aliases(aliases: list[BashAlias]) -> None:
    if not aliases:
        info("Neniuj aliasoj")
        return
    table = Table(title="Bash Aliasoj")
    table.add_column("UID", style="cyan")
    table.add_column("Alias", style="green")
    table.add_column("Funkcio", style="dim")
    for a in aliases:
        table.add_row(str(a.uid), a.alias, a.function[:50])
    console.print(table)


@app.command("ls")
def ls(
    alfabeto: bool = typer.Option(False, "-al", "--alfabeto", help="Alfabetaordo"),
    inversigi: bool = typer.Option(False, "-i", "--inversigi", help="Inversaordo"),
) -> None:
    """List bash aliases."""
    db = _get_db()
    sort_by = "alias" if alfabeto else "created_at"
    aliases = db.list_aliases(sort_by=sort_by, descending=not inversigi)
    _show_aliases(aliases)


@app.command("aldoni")
def aldoni(
    alias: str = typer.Option(..., "-a", "--alias", help="Alias nomo"),
    funkcio: str = typer.Option(..., "-f", "--funkcio", help="Funkcio"),
    notes: str = typer.Option("", "-n", "--notes", help="Notoj"),
) -> None:
    """Add new bash alias."""
    db = _get_db()
    uid = db.add_alias(alias, funkcio, notes or None)
    db.sync_shell_config()
    info(f"Aldonita: UID {uid}")


@app.command("modifi")
def modifi(
    uid: int = typer.Argument(..., help="UID"),
    alias: Optional[str] = typer.Option(None, "-a", "--alias", help="Nova alias"),
    funkcio: Optional[str] = typer.Option(None, "-f", "--funkcio", help="Nova funkcio"),
    notes: Optional[str] = typer.Option(None, "-n", "--notes", help="Notoj"),
) -> None:
    """Modify bash alias."""
    db = _get_db()
    if db.update_alias(uid, alias, funkcio, notes):
        db.sync_shell_config()
        info(f"Modifita: UID {uid}")
    else:
        info(f"Ne trovita: UID {uid}")
        raise typer.Exit(1)


@app.command("forigi")
def forigi(
    uids: list[int] = typer.Argument(..., help="UIDs"),
    justa: bool = typer.Option(False, "-j", "--justa", help="Sen konfirmo"),
) -> None:
    """Delete bash aliases."""
    if not uids:
        info("最少 unu UID bezonata")
        raise typer.Exit(1)
    db = _get_db()
    for uid in uids:
        db.delete_alias(uid)
    db.sync_shell_config()
    info(f"Forigitaj: {len(uids)} aliasoj")


@app.command("vidi")
def vidi(uid: int = typer.Argument(..., help="UID")) -> None:
    """View bash alias details."""
    db = _get_db()
    a = db.get_alias(uid)
    if not a:
        info(f"Ne trovita: UID {uid}")
        raise typer.Exit(1)
    info(f"Alias: {a.alias}")
    info(f"Funkcio: {a.function}")
    if a.notes:
        info(f"Notoj: {a.notes}")


@app.command("serci")
def serci(query: str = typer.Argument("", help="Sercha termino")) -> None:
    """Search bash aliases."""
    db = _get_db()
    results = db.search_aliases(query)
    _show_aliases(results)


__all__ = ["app"]