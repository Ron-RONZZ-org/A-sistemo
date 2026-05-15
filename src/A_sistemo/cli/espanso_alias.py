"""CLI for sistemo espanso command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE as BOX_SIMPLE

from A import info, error, tr
from A_sistemo.services import EspansoMatch, EspansoMatchDB

app = typer.Typer(
    name="espanso",
    help=tr("espanso_matches"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _get_db() -> EspansoMatchDB:
    """Get the espanso match database."""
    return EspansoMatchDB(Path.home() / ".config" / "A" / "espanso_matches.db")


def _show_matches(matches: list[EspansoMatch]) -> None:
    """Display matches in a rich table."""
    if not matches:
        info(tr("neniu_matches"))
        return
    table = Table(box=BOX_SIMPLE, title=tr("espanso_matches"))
    table.add_column("UID", style="bold")
    table.add_column(tr("trigger"))
    table.add_column(tr("replace"))
    for m in matches:
        table.add_row(str(m.uid), m.trigger, m.replace_text[:60])
    console.print(table)


@app.command("ls")
def ls(
    alfabeto: bool = typer.Option(False, "-A", "--alfabeto", help=tr("alfabetaordo")),
    inversigi: bool = typer.Option(False, "-i", "--inversigi", help=tr("inversaordo")),
) -> None:
    """List espanso matches."""
    db = _get_db()
    sort_by = "trigger" if alfabeto else "created_at"
    matches = db.list_matches(sort_by=sort_by, descending=not inversigi)
    _show_matches(matches)


@app.command("aldoni")
def aldoni(
    trigger: str = typer.Option(..., "-t", "--trigger", help=tr("trigger_example")),
    replace_text: str = typer.Option(..., "-r", "--replace", help=tr("replace_text")),
    notes: str = typer.Option("", "-n", "--notes", help=tr("notes")),
) -> None:
    """Add new espanso match."""
    db = _get_db()
    uid = db.add_match(trigger, replace_text, notes or None)
    db.sync_espanso_config()
    info(f"{tr('added')}: UID {uid}")


@app.command("modifi")
def modifi(
    uid: int = typer.Argument(..., help="UID (Example: 1)"),
    trigger: Optional[str] = typer.Option(None, "-t", "--trigger", help=tr("trigger")),
    replace_text: Optional[str] = typer.Option(None, "-r", "--replace", help=tr("replace_text")),
    notes: Optional[str] = typer.Option(None, "-n", "--notes", help=tr("notes")),
) -> None:
    """Modify espanso match."""
    db = _get_db()
    if db.update_match(uid, trigger, replace_text, notes):
        db.sync_espanso_config()
        info(f"{tr('modified')}: UID {uid}")
    else:
        error(f"{tr('ne_trovita_uid')} {uid}")
        raise typer.Exit(1)


@app.command("forigi")
def forigi(
    uids: list[int] = typer.Argument(..., help="UIDs (Example: 1 2)"),
    justa: bool = typer.Option(False, "-j", "--justa", help=tr("sen_konfirmo")),
) -> None:
    """Delete espanso matches."""
    if not uids:
        error(tr("minimun_unu_uid"))
        raise typer.Exit(1)
    db = _get_db()
    deleted = 0
    not_found: list[int] = []
    for uid in uids:
        if db.delete_match(uid):
            deleted += 1
        else:
            not_found.append(uid)
    if not_found:
        for uid in not_found:
            error(f"UID {uid}: {tr('ne_trovita_uid')}")
    if deleted > 0:
        db.sync_espanso_config()
        info(f"{tr('deleted')}: {deleted} matchoj")
    else:
        raise typer.Exit(1)


@app.command("vidi")
def vidi(uid: int = typer.Argument(..., help="UID (Example: 1)")) -> None:
    """View espanso match details."""
    db = _get_db()
    m = db.get_match(uid)
    if not m:
        error(f"{tr('ne_trovita_uid')} {uid}")
        raise typer.Exit(1)
    info(f"{tr('trigger')}: {m.trigger}")
    info(f"{tr('replace')}: {m.replace_text}")
    if m.notes:
        info(f"{tr('notes')}: {m.notes}")


@app.command("serci")
def serci(query: str = typer.Argument("", help=tr("sercho_termino"))) -> None:
    """Search espanso matches."""
    db = _get_db()
    results = db.search_matches(query)
    _show_matches(results)


@app.command("migri")
def migri() -> None:
    """Import existing espanso matches from config files."""
    from A import success, confirm_action
    from A_sistemo.services.espanso_alias_db import (
        migrate_from_existing,
        backup_old_match_files,
    )

    db = _get_db()
    result = migrate_from_existing(db)

    if result["files_found"] == 0:
        info("No espanso config files found.")
        return

    info(f"Files found: {result['files_found']}, matches: {result['matches_found']}")
    success(f"Migrated: {result['migrated']}, skipped (duplicates): {result['skipped']}")

    for err in result.get("errors", []):
        from A import warning
        warning(f"  {err}")

    if result["migrated"] > 0:
        db.sync_espanso_config()
        info("Espanso config synced to A_espanso.yml.")

        # Offer to archive old .yml files to avoid duplicate expansions
        if confirm_action(
            "Move old espanso match files to match-bak/ to avoid duplication?",
            default=True,
        ):
            bak_count = backup_old_match_files()
            info(f"Moved {bak_count} files to match-bak/")


__all__ = ["app"]
