"""CLI for sistemo selo-funkcio command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE as BOX_SIMPLE

from A import info, error, tr
from A.core.paths import config_dir
from A_sistemo.services import BashFunction, BashFunctionDB
from A_sistemo.services.bash_function_db import parse_function_file, validate_bash_syntax

app = typer.Typer(
    name="selo-funkcio",
    help=tr("bash_functions"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


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
        exists=True,
        readable=True,
    ),
) -> None:
    """Add bash function from file."""
    try:
        name, body = parse_function_file(file_path)
        validate_bash_syntax(name, body)
    except (ValueError, OSError) as e:
        error(f"{e}")
        raise typer.Exit(1)

    db = _get_db()
    existing = db.get_function_by_name(name)
    if existing:
        error(f"Function '{name}' already exists (UID {existing.uid}).")
        info("Use 'selo-funkcio modifi' to update it.")
        raise typer.Exit(1)

    uid = db.add_function(name=name, body=body)
    db.sync_shell_config()
    info(f"{tr('added')}: {name} (UID {uid})")


@app.command("modifi")
def modifi(
    uid: int = typer.Argument(..., help="UID (Example: 1)"),
    file_path: Optional[Path] = typer.Option(
        None,
        "-D", "--dosiero",
        help=tr("path_to_function_file"),
        exists=True,
        readable=True,
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

    if file_path:
        try:
            parsed_name, new_body = parse_function_file(file_path)
            if new_name is None:
                new_name = parsed_name
        except (ValueError, OSError) as e:
            error(f"{e}")
            raise typer.Exit(1)

    if new_name or new_body:
        try:
            validate_bash_syntax(
                new_name or func.name,
                new_body or func.body,
            )
        except ValueError as e:
            error(f"{e}")
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
