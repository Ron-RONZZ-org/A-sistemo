"""CLI for sistemo espanso command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE as BOX_SIMPLE

from A import info, error, tr, tr_multi
from A.core.paths import config_dir
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
    return EspansoMatchDB(config_dir() / "espanso_matches.db")


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


def _read_replace_file(path: Path) -> str:
    """Read replacement text from a file.

    Validates the file exists, is a regular file, and is not binary.
    Returns the UTF-8 content.

    Args:
        path: Path to the replacement file (may contain ~)

    Returns:
        File contents as string

    Raises:
        typer.Exit: If file is invalid
    """
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        error(tr_multi(
            f"Dosiero ne ekzistas: {resolved}",
            f"File does not exist: {resolved}",
            f"Fichier inexistant: {resolved}",
        ))
        raise typer.Exit(1)
    if not resolved.is_file():
        error(tr_multi(
            f"Ne estas dosiero: {resolved}",
            f"Not a file: {resolved}",
            f"Pas un fichier: {resolved}",
        ))
        raise typer.Exit(1)
    content = resolved.read_text(encoding="utf-8")
    if "\x00" in content:
        error(tr_multi(
            f"Binara dosiero ne subtenata: {resolved}",
            f"Binary file not supported: {resolved}",
            f"Fichier binaire non pris en charge: {resolved}",
        ))
        raise typer.Exit(1)
    return content


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


def _resolve_replace_text(inline_text: Optional[str], file_path: Optional[Path]) -> str:
    """Resolve replace text from either --replace or --replace-dosiero.

    Exactly one must be provided. If both are given, an error is raised.

    Args:
        inline_text: Value from --replace (may be None)
        file_path: Value from --replace-dosiero (may be None)

    Returns:
        The resolved replace text as a string

    Raises:
        typer.Exit: If neither is provided, or both are provided,
                    or the file is invalid.
    """
    if inline_text is not None and file_path is not None:
        error(tr_multi(
            "Ne eblas uzi --replace kaj --replace-dosiero samtempe",
            "Cannot use both --replace and --replace-dosiero at the same time",
            "Impossible d'utiliser --replace et --replace-dosiero en même temps",
        ))
        raise typer.Exit(1)
    if file_path is not None:
        return _read_replace_file(file_path)
    if inline_text is not None:
        return inline_text
    error(tr_multi(
            "Bezonas --replace aŭ --replace-dosiero",
            "Requires --replace or --replace-dosiero",
            "Nécessite --replace ou --replace-dosiero",
    ))
    raise typer.Exit(1)


@app.command("aldoni")
def aldoni(
    trigger: str = typer.Option(..., "-t", "--trigger", help=tr("trigger_example")),
    replace_text: Optional[str] = typer.Option(None, "-r", "--replace", help=tr("replace_text")),
    replace_file: Optional[Path] = typer.Option(None, "-R", "--replace-dosiero", help=tr("replace_dosiero")),
    notes: str = typer.Option("", "-n", "--notes", help=tr("notes")),
) -> None:
    """Add new espanso match."""
    final_replace = _resolve_replace_text(replace_text, replace_file)
    db = _get_db()
    uid = db.add_match(trigger, final_replace, notes or None)
    db.sync_espanso_config()
    info(f"{tr('added')}: UID {uid}")


@app.command("modifi")
def modifi(
    uid: int = typer.Argument(..., help="UID (Example: 1)"),
    trigger: Optional[str] = typer.Option(None, "-t", "--trigger", help=tr("trigger")),
    replace_text: Optional[str] = typer.Option(None, "-r", "--replace", help=tr("replace_text")),
    replace_file: Optional[Path] = typer.Option(None, "-R", "--replace-dosiero", help=tr("replace_dosiero")),
    notes: Optional[str] = typer.Option(None, "-n", "--notes", help=tr("notes")),
) -> None:
    """Modify espanso match."""
    db = _get_db()

    # Resolve replace_text from inline or file (skip if neither given)
    final_replace: Optional[str] = None
    if replace_text is not None or replace_file is not None:
        final_replace = _resolve_replace_text(replace_text, replace_file)

    if db.update_match(uid, trigger, final_replace, notes):
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
