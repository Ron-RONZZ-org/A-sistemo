"""CLI for sistemo bash-alias command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE as BOX_SIMPLE

from A import info, error, tr
from A.core.paths import config_dir
from A_sistemo.services import BashAlias, BashAliasDB

app = typer.Typer(
    name="bash-aliaso",
    help=tr("bash_aliases"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _get_db() -> BashAliasDB:
    return BashAliasDB(config_dir() / "bash_aliases.db")


def _show_aliases(aliases: list[BashAlias]) -> None:
    if not aliases:
        info(tr("neniu_aliasoj"))
        return
    table = Table(box=BOX_SIMPLE, title=tr("bash_aliases"))
    table.add_column("UID", style="bold")
    table.add_column(tr("alias"))
    table.add_column(tr("function"))
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
    deleted = 0
    not_found: list[int] = []
    for uid in uids:
        if db.delete_alias(uid):
            deleted += 1
        else:
            not_found.append(uid)
    if not_found:
        for uid in not_found:
            error(f"UID {uid}: {tr('ne_trovita_uid')}")
    if deleted > 0:
        db.sync_shell_config()
        info(f"{tr('deleted_alias')}: {deleted} aliasoj")
    else:
        raise typer.Exit(1)


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


@app.command("migri")
def migri() -> None:
    """Migrate bash aliases from autish-legacy to A."""
    from A import success, info, error
    from A_sistemo.services.bash_alias_db import migrate_from_autish, migrate_bashrc
    
    # Migrate aliases to A DB
    db = _get_db()
    result = migrate_from_autish(db)
    
    if result["source"] > 0:
        success(f"Migrateblaj: {result['source']}, migrantitaj: {result['migrated']}, ignoritaj: {result['skipped']}")
        for err in result.get("errors", []):
            from A import warning
            warning(f"  {err}")
    
    # Always update bashrc (add source line even if no aliases)
    bashrc_result = migrate_bashrc(db)
    if bashrc_result["error"]:
        error(f"bashrc eraro: {bashrc_result['error']}")
    else:
        if bashrc_result["removed_autish"]:
            info("removed autish referencoj el ~/.bashrc")
        if bashrc_result["added_A"]:
            info("added A referencoj al ~/.bashrc")
    
    # Sync the aliases file
    db.sync_shell_config()
    info("bash aliasoj sinkronigitaj")


# ── Module installation ──────────────────────────────────────────────────


_INSTALL_DIR = Path.home() / ".local" / "bin"


def _get_module_entry_points() -> dict[str, str]:
    """Get all installed A module entry points.
    
    Returns:
        Dict mapping command name -> module display name
    """
    import importlib.metadata
    eps = importlib.metadata.entry_points(group="A.commands")
    return {ep.name: ep.value for ep in eps}


def _autish_bin_path() -> Path | None:
    """Check if autish-legacy binary exists.
    
    Returns:
        Path to autish binary, or None
    """
    autish = _INSTALL_DIR / "autish"
    return autish if autish.exists() else None


def _resolve_a_path() -> str:
    """Find the A CLI executable path.
    
    Priority: .venv/bin/A (development) > shutil.which('A') (system) > assert.
    
    Returns:
        Absolute path to the A executable
    """
    import shutil
    
    # Check workspace venv first (development mode)
    venv_a = Path.cwd() / ".venv" / "bin" / "A"
    if venv_a.exists():
        return str(venv_a.resolve())
    
    # Check system PATH
    which_a = shutil.which("A")
    if which_a:
        return which_a
    
    # Fallback: assume it's in PATH after install
    return "A"


def _is_autish_wrapper(path: Path) -> bool:
    """Check if a file is a legacy autish wrapper (references 'autish' command).
    
    Args:
        path: Path to check
        
    Returns:
        True if the file references autish
    """
    if not path.exists():
        return False
    try:
        content = path.read_text()
        return "autish" in content
    except (OSError, UnicodeDecodeError):
        return False


def instali(
    force: bool = typer.Option(False, "--force", "-f",
        help=tr("forcstitui")),
) -> None:
    """Install A module commands as direct shell wrappers.
    
    Creates executable wrapper scripts in ~/.local/bin/ for every
    installed A module (e.g., vorto, encik, tempo, etc.).
    Removes ~/.local/bin/autish (legacy autish) if present.
    Replaces old autish wrappers that point to the legacy binary.
    
    After running this, you can type 'vorto' instead of 'A vorto'.
    
    Examples:
        A sistemo instali
        A sistemo instali --force
    """
    from A import success, warning
    
    _INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    a_path = _resolve_a_path()
    entries = _get_module_entry_points()
    installed = 0
    skipped = 0
    import shutil
    
    # First ensure A itself is available as ~/.local/bin/A
    a_wrapper = _INSTALL_DIR / "A"
    if not a_wrapper.exists() or force or not shutil.which("A"):
        a_wrapper.write_text(
            f"#!/bin/bash\n"
            f"# Auto-generated by A sistemo instali\n"
            f"exec {a_path} \"$@\"\n"
        )
        a_wrapper.chmod(0o755)
        if not shutil.which("A"):
            installed += 1  # Count A wrapper as installed
    
    for cmd_name in sorted(entries.keys()):
        wrapper = _INSTALL_DIR / cmd_name
        
        # Replace old autish wrappers unconditionally
        if _is_autish_wrapper(wrapper):
            warning(f"Replacing legacy autish wrapper: {cmd_name}")
            wrapper.unlink()
        
        # Skip if already exists and not force
        if wrapper.exists() and not force:
            skipped += 1
            continue
        
        # Skip real system commands (not autish wrappers)
        if not force and not _is_autish_wrapper(wrapper):
            sys_cmd = shutil.which(cmd_name)
            if sys_cmd and _INSTALL_DIR not in Path(sys_cmd).parents:
                warning(f"Skipping '{cmd_name}' — conflicts with system command at {sys_cmd}")
                skipped += 1
                continue
        
        # Create wrapper script
        wrapper.write_text(
            f"#!/bin/bash\n"
            f"# Auto-generated by A sistemo instali\n"
            f"exec A {cmd_name} \"$@\"\n"
        )
        wrapper.chmod(0o755)
        installed += 1
    
    # Remove autish-legacy binary
    autish = _autish_bin_path()
    if autish:
        autish.unlink()
        info(f"Removed autish-legacy: {autish}")
    
    success(f"Installed {installed} wrappers ({skipped} skipped)")
    if installed > 0:
        info(f"Make sure {_INSTALL_DIR} is in your PATH")


def malinstali(
    jes: bool = typer.Option(False, "--jes", "-y",
        help=tr("sen_konfirmo")),
) -> None:
    """Remove A module command wrappers installed by 'instali'.
    
    Does NOT remove the user's custom bash aliases managed by selo-aliaso.
    Only removes auto-generated wrappers in ~/.local/bin/.
    
    Examples:
        A sistemo malinstali
        A sistemo malinstali -y
    """
    from A import success, confirm_action
    
    entries = _get_module_entry_points()
    removed = 0
    
    for cmd_name in sorted(entries.keys()):
        wrapper = _INSTALL_DIR / cmd_name
        if not wrapper.exists():
            continue
        
        # Only remove files that look auto-generated
        content = wrapper.read_text()
        if "Auto-generated by A sistemo instali" not in content:
            continue
        
        if jes or confirm_action(f"Remove '{cmd_name}' wrapper?"):
            wrapper.unlink()
            removed += 1
    
    if removed == 0:
        info("No wrappers to remove")
    else:
        success(f"Removed {removed} wrappers")


__all__ = ["app", "instali", "malinstali"]