"""A-sistemo - System management plugin for A."""

from A.core.backup_targets import BackupTarget
from A.core.paths import config_dir
from A_sistemo.cli import app


def get_backup_targets() -> list[BackupTarget]:
    """Return backup targets for A-sistemo."""
    return [
        BackupTarget(
            path=config_dir() / "bash_functions.db",
            category="config",
            module="sistemo",
            label="Sistemo bash functions database",
        ),
        BackupTarget(
            path=config_dir() / "bash_aliases.db",
            category="config",
            module="sistemo",
            label="Sistemo bash aliases database",
        ),
        BackupTarget(
            path=config_dir() / "espanso_matches.db",
            category="config",
            module="sistemo",
            label="Sistemo espanso matches database",
        ),
    ]


__all__ = ["app", "get_backup_targets"]