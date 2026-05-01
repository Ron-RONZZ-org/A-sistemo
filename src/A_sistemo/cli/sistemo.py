"""Main CLI for sistemo."""

from __future__ import annotations

import typer

from A import tr
from A_sistemo.cli import info, wifi, bluetooth, usb, disko, rubo, bash_alias, particio

app = typer.Typer(
    name="sistemo",
    help=tr("system_info"),
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Add sub-apps
app.add_typer(wifi.app, name="wifi")
app.add_typer(bluetooth.app, name="bluhdento")
app.add_typer(usb.app, name="usb")
app.add_typer(disko.app, name="disko")
app.add_typer(rubo.app, name="rubo")

# Add sistemo-specific subcommands
app.add_typer(bash_alias.app, name="sxelo-aliaso")
app.add_typer(particio.app, name="particio")
app.command(name="info")(info.info)


@app.callback(invoke_without_command=True)
def sistemo_callback(ctx: typer.Context) -> None:
    """Default: show system info."""
    if ctx.invoked_subcommand is None:
        info.info()


__all__ = ["app"]