"""CLI for sistemo selo-funkcio command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE as BOX_SIMPLE

from A import info, error, tr, tr_multi
from A.core.paths import config_dir
from A_sistemo.services import (
    BashFunction,
    BashFunctionDB,
    parse_function_file,
    parse_functions_from_file,
    validate_bash_syntax,
)
from A_sistemo.services.collision import check_name_in_aliases

app = typer.Typer(
    name="selo-funkcio",
    help=tr("bash_functions"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _resolve_path(path: Path) -> Path | None:
    """Expand tilde and resolve a path, validating it exists.

    Args:
        path: Path to resolve (may contain ~)

    Returns:
        Resolved absolute Path, or None if invalid
    """
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        error(tr_multi(
            f"Dosiero ne ekzistas: {resolved}",
            f"File does not exist: {resolved}",
            f"Fichier inexistant: {resolved}",
        ))
        return None
    if not resolved.is_file():
        error(tr_multi(
            f"Ne estas dosiero: {resolved}",
            f"Not a file: {resolved}",
            f"Pas un fichier: {resolved}",
        ))
        return None
    return resolved


def _get_db() -> BashFunctionDB:
    """Get the bash function database."""
    return BashFunctionDB(config_dir() / "bash_functions.db")


def _show_functions(functions: list[BashFunction]) -> None:
    """Display functions in a rich table."""
    if not functions:
        info(tr("neniu_funkcio"))
        return
    table = Table(box=BOX_SIMPLE, title=tr("bash_functions"))
    table.add_column("UID", style="bold")
    table.add_column(tr("name"))
    for f in functions:
        # Show first line of body as preview
        preview = f.body.splitlines()[0] if f.body else ""
        table.add_row(str(f.uid), f.name, preview[:60])
    console.print(table)


@app.command("ls")
def ls(
    alfabeto: bool = typer.Option(False, "-A", "--alfabeto", help=tr("alfabetaordo")),
) -> None:
    """List bash functions."""
    db = _get_db()
    sort_by = "name" if alfabeto else "created_at"
    functions = db.list_functions(sort_by=sort_by, descending=False if alfabeto else True)
    _show_functions(functions)


@app.command("aldoni")
def aldoni(
    file_path: Path = typer.Argument(
        ...,
        help=tr("path_to_function_file"),
    ),
    jes: bool = typer.Option(
        False,
        "--jes", "-y",
        help=tr_multi(
            "Aŭtomate ĝisdatigi duplikatojn sen konfirmo.",
            "Auto-confirm duplicate updates.",
            "Mettre à jour automatiquement les doublons.",
        ),
    ),
) -> None:
    """Add bash functions from file.

    Supports files with multiple function definitions.
    If a function name already exists, prompts to update it
    (use --jes to auto-confirm).
    """
    # Problem 1: Expand tilde manually
    path = _resolve_path(file_path)
    if path is None:
        raise typer.Exit(1)

    # Problem 3: Parse multiple functions
    try:
        functions = parse_functions_from_file(path)
    except (ValueError, OSError) as e:
        error(f"{e}")
        raise typer.Exit(1)

    # Validate ALL functions before inserting (fail-fast)
    for name, body in functions:
        try:
            validate_bash_syntax(name, body)
        except ValueError as e:
            error(f"{name}: {e}")
            raise typer.Exit(1)

    db = _get_db()
    added = 0
    updated = 0

    for name, body in functions:
        # Pre-emptive name collision check against aliases
        existing_alias = check_name_in_aliases(name)
        if existing_alias:
            msg = tr_multi(
                f"Funkcio '{name}' kolizias kun aliaso (UID {existing_alias.uid}). "
                f"Aliashoj supersemas funkciojn en interagaj ŝeloj. Daŭrigi?",
                f"Function '{name}' collides with alias (UID {existing_alias.uid}). "
                f"Aliases shadow functions in interactive shells. Continue?",
                f"La fonction '{name}' entre en collision avec l'alias (UID {existing_alias.uid}). "
                f"Les alias priment sur les fonctions. Continuer ?",
            )
            if jes:
                info(tr_multi(
                    f"Funkcio '{name}' kolizias — daŭrigas (--jes).",
                    f"Function '{name}' collides — continuing (--jes).",
                    f"Fonction '{name}' en collision — continue (--jes).",
                ))
            else:
                answer = typer.prompt(msg, default="N")
                if answer.strip().lower() not in {
                    "j", "jes", "y", "yes", "o", "oui",
                }:
                    error(tr_multi(
                        f"Preterlasita: {name}",
                        f"Skipped: {name}",
                        f"Passé: {name}",
                    ))
                    continue

        existing = db.get_function_by_name(name)

        if existing:
            # Problem 2: Offer to update on duplicate
            if jes:
                should_update = True
            else:
                answer = typer.prompt(
                    tr_multi(
                        f"Funkcio '{name}' jam ekzistas (UID {existing.uid}). "
                        f"Ĉu ĝisdatigi? (J/n)",
                        f"Function '{name}' already exists (UID {existing.uid}). "
                        f"Update? (Y/n)",
                        f"Fonction '{name}' existe déjà (UID {existing.uid}). "
                        f"Mettre à jour ? (O/n)",
                    ),
                    default="J",
                )
                should_update = answer.strip().lower() in {
                    "j", "jes", "y", "yes", "o", "oui", "",
                }

            if should_update:
                db.update_function(existing.uid, body=body)
                updated += 1
                info(f"{tr('modified')}: {name} (UID {existing.uid})")
            else:
                info(tr_multi(
                    f"Preterlasita: {name}",
                    f"Skipped: {name}",
                    f"Passé: {name}",
                ))
        else:
            uid = db.add_function(name=name, body=body)
            added += 1
            info(f"{tr('added')}: {name} (UID {uid})")

    # Sync shell config once after all changes
    if added > 0 or updated > 0:
        db.sync_shell_config()

    if added == 0 and updated == 0:
        info(tr_multi(
            "Neniu funkcio aldonita.",
            "No functions added.",
            "Aucune fonction ajoutée.",
        ))
        raise typer.Exit(1)


@app.command("modifi")
def modifi(
    uid: int = typer.Argument(..., help="UID (Example: 1)"),
    file_path: Optional[Path] = typer.Option(
        None,
        "-D", "--dosiero",
        help=tr("path_to_function_file"),
    ),
    name: Optional[str] = typer.Option(None, "-n", "--nomo", help=tr("new_name")),
) -> None:
    """Modify a bash function."""
    db = _get_db()
    func = db.get_function(uid)
    if not func:
        error(f"{tr('ne_trovita_uid')} {uid}")
        raise typer.Exit(1)

    new_name = name
    new_body = None

    if file_path is not None:
        resolved = _resolve_path(file_path)
        if resolved is None:
            raise typer.Exit(1)
        try:
            parsed_name, new_body = parse_function_file(resolved)
            if new_name is None:
                new_name = parsed_name
        except (ValueError, OSError) as e:
            error(f"{e}")
            raise typer.Exit(1)

    # Determine effective new name for collision check
    effective_name = new_name if new_name is not None else func.name

    if new_name or new_body:
        try:
            validate_bash_syntax(
                effective_name,
                new_body or func.body,
            )
        except ValueError as e:
            error(f"{e}")
            raise typer.Exit(1)

    # Pre-emptive collision check when renaming
    if new_name is not None and new_name != func.name:
        existing_alias = check_name_in_aliases(new_name)
        if existing_alias:
            msg = tr_multi(
                f"Funkcio '{new_name}' kolizias kun aliaso (UID {existing_alias.uid}). Daŭrigi?",
                f"Function '{new_name}' collides with alias (UID {existing_alias.uid}). Continue?",
                f"La fonction '{new_name}' entre en collision avec l'alias (UID {existing_alias.uid}). Continuer ?",
            )
            answer = typer.prompt(msg, default="N")
            if answer.strip().lower() not in {
                "j", "jes", "y", "yes", "o", "oui",
            }:
                error(tr_multi("Nuligita.", "Aborted.", "Annulé."))
                raise typer.Exit(1)

    if db.update_function(uid, name=new_name, body=new_body):
        db.sync_shell_config()
        info(f"{tr('modified')}: UID {uid}")
    else:
        error(f"{tr('ne_trovita_uid')} {uid}")
        raise typer.Exit(1)


@app.command("forigi")
def forigi(
    uids: list[int] = typer.Argument(..., help="UIDs (Example: 1 2)"),
) -> None:
    """Delete bash functions."""
    if not uids:
        error(tr("minimun_unu_uid"))
        raise typer.Exit(1)
    db = _get_db()
    deleted = 0
    not_found: list[int] = []
    for uid in uids:
        if db.delete_function(uid):
            deleted += 1
        else:
            not_found.append(uid)
    if not_found:
        for uid in not_found:
            error(f"UID {uid}: {tr('ne_trovita_uid')}")
    if deleted > 0:
        db.sync_shell_config()
        info(f"{tr('forigita')}: {deleted} funkcioj")
    else:
        raise typer.Exit(1)


@app.command("vidi")
def vidi(uid: int = typer.Argument(..., help="UID (Example: 1)")) -> None:
    """View bash function details."""
    db = _get_db()
    f = db.get_function(uid)
    if not f:
        error(f"{tr('ne_trovita_uid')} {uid}")
        raise typer.Exit(1)

    info(f"Name: {f.name}")
    console.print(f"Body:")
    console.print(f"{f.name}() {{")
    for line in f.body.splitlines():
        console.print(f"  {line}")
    console.print("}")


@app.command("serci")
def serci(query: str = typer.Argument("", help=tr("sercho_termino"))) -> None:
    """Search bash functions."""
    db = _get_db()
    results = db.search_functions(query)
    _show_functions(results)


__all__ = ["app"]
