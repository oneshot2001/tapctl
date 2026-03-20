"""Click CLI for tapctl — kubectl-style Axis Scene Metadata management."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

import click
import yaml

from tapctl import __version__
from tapctl.config import RuntimeContext, TapctlConfig
from tapctl.discovery.scene_metadata import enrich_with_scene_metadata
from tapctl.reporting.table import (
    console,
    generate_manifest_scaffold,
    render_discovery_table,
)


@click.group()
@click.version_option(version=__version__, prog_name="tapctl")
@click.option("--user", "-u", default="root", help="Device username.", show_default=True)
@click.option(
    "--password",
    "-p",
    default=None,
    help="Device password (or set TAPCTL_PASSWORD).",
)
@click.option("--timeout", default=10, help="HTTP timeout in seconds.", show_default=True)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format.",
    show_default=True,
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
@click.option("--dry-run", is_flag=True, help="Show what would happen without executing.")
@click.pass_context
def cli(
    ctx: click.Context,
    user: str,
    password: str | None,
    timeout: int,
    output: str,
    verbose: bool,
    dry_run: bool,
) -> None:
    """tapctl — kubectl-style CLI for Axis Scene Metadata streaming over MQTT."""
    resolved_password = password or os.environ.get("TAPCTL_PASSWORD", "")
    ctx.ensure_object(dict)
    ctx.obj["runtime"] = RuntimeContext(
        config=TapctlConfig(
            user=user,
            password=resolved_password,
            timeout=timeout,
            output=output,
            verbose=verbose,
            dry_run=dry_run,
        )
    )


@cli.command()
@click.option("--range", "cidr", required=False, help="CIDR range to scan (e.g. 192.168.1.0/24).")
@click.option(
    "--targets",
    required=False,
    help="Comma-separated list of IPs to probe.",
)
@click.option(
    "--scaffold",
    is_flag=True,
    default=False,
    help="Output an apply-ready MetadataStream manifest instead of SiteInventory.",
)
@click.pass_context
def discover(ctx: click.Context, cidr: str | None, targets: str | None, scaffold: bool) -> None:
    """Discover Axis cameras and check Scene Metadata capability.

    Scans a network range or specific targets, probes each for Scene Metadata
    support, and displays the results.

    Examples:

        tapctl discover --range 192.168.1.0/24

        tapctl discover --targets 10.0.0.10,10.0.0.11,10.0.0.12

        tapctl discover --range 10.1.1.0/24 -o yaml

        tapctl discover --range 10.1.1.0/24 --scaffold > manifest.yaml
    """
    if not cidr and not targets:
        console.print("[red]Error:[/red] Provide --range or --targets.")
        sys.exit(1)

    rt: RuntimeContext = ctx.obj["runtime"]
    cfg = rt.config

    devices = asyncio.run(_run_discovery(cidr, targets, cfg))

    if scaffold and devices:
        manifest = generate_manifest_scaffold(devices)
        click.echo(yaml.dump(manifest, default_flow_style=False, sort_keys=False))
    else:
        render_discovery_table(devices, output_format=cfg.output)


async def _run_discovery(
    cidr: str | None,
    targets: str | None,
    cfg: TapctlConfig,
) -> list[Any]:
    """Execute async discovery scan."""
    from axelib.discovery.scanner import probe_targets, scan_subnet

    if cidr:
        console.print(f"[bold]Scanning {cidr}...[/bold]")
        devices = await scan_subnet(
            cidr=cidr,
            username=cfg.user,
            password=cfg.password,
            timeout=cfg.timeout,
            verbose=cfg.verbose,
            enrich=enrich_with_scene_metadata,
        )
    else:
        target_list = [t.strip() for t in (targets or "").split(",") if t.strip()]
        console.print(f"[bold]Probing {len(target_list)} target(s)...[/bold]")
        devices = await probe_targets(
            targets=target_list,
            username=cfg.user,
            password=cfg.password,
            timeout=cfg.timeout,
            verbose=cfg.verbose,
            enrich=enrich_with_scene_metadata,
        )

    return devices
