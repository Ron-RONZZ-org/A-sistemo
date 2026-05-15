"""CLI for wifi command."""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.box import SIMPLE as BOX_SIMPLE

from A import info, error, tr, tr_multi
from A_sistemo._shared import CommandError
from A_sistemo.services import WiFiNetwork, scan_networks, list_connections, connect, disconnect, forget, restart

app = typer.Typer(
    name="wifi",
    help=tr("wifi"),
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _show_networks(networks: list[WiFiNetwork]) -> None:
    if not networks:
        info(tr("neniuj"))
        return
    table = Table(box=BOX_SIMPLE, title=tr("wifi_networks"))
    table.add_column(tr("ssid"), style="green")
    table.add_column(tr("signal"))
    table.add_column(tr("security"))
    table.add_column(tr("status"), style="cyan")
    table.add_column(
        tr_multi("AP-oj", "APs", "PA")
    )
    for net in networks:
        table.add_row(
            net.name,
            f"{net.signal}%" if net.signal is not None else "-",
            net.security or "-",
            tr("connected") if net.active else "",
            str(net.ap_count),
        )
    console.print(table)


@app.command("ls")
def ls(
    name: Optional[str] = typer.Argument(None, help=f"{tr('ssid')} (Example: MyWiFi)"),
    pasvorto: bool = typer.Option(False, "-p", help=tr("password")),
    konservitaj: bool = typer.Option(False, "-k", help=tr("konservitaj")),
) -> None:
    """List Wi-Fi networks."""
    try:
        if konservitaj:
            networks = list_connections(show_secrets=pasvorto)
        else:
            networks = scan_networks()
        _show_networks(networks)
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("konekti")
def konekti(
    nomo: str = typer.Argument(..., help=f"{tr('ssid')} (Example: MyWiFi)"),
    pasvorto: Optional[str] = typer.Option(None, "-p", help=tr("password")),
) -> None:
    """Connect to Wi-Fi."""
    try:
        connect(nomo, pasvorto)
        info(f"{tr('connected')} '{nomo}'")
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("malkonekti")
def malkonekti() -> None:
    """Disconnect from Wi-Fi."""
    try:
        disconnect()
        info(tr("disconnected"))
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command("forigi")
def forigi(nomoj: Annotated[list[str], typer.Argument(..., help=f"{tr('ssid')} (Example: MyWiFi, multiple)")]) -> None:
    """Delete saved Wi-Fi networks."""
    for nomo in nomoj:
        try:
            forget(nomo)
            info(f"{tr('deleted')}: {nomo}")
        except CommandError as e:
            error(str(e))


@app.command("restarti")
def restarti() -> None:
    """Restart Wi-Fi."""
    try:
        restart()
        info(tr("status"))
    except CommandError as e:
        error(str(e))
        raise typer.Exit(1)


__all__ = ["app"]