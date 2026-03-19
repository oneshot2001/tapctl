"""tapctl-specific Rich table rendering for Scene Metadata discovery."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import yaml
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from tapctl.models.device import TapctlDeviceInfo

console = Console()


def render_discovery_table(
    devices: list[TapctlDeviceInfo],
    output_format: str = "table",
) -> None:
    """Render discovered devices with Scene Metadata capability info.

    Args:
        devices: List of TapctlDeviceInfo objects from discovery.
        output_format: One of "table", "json", or "yaml".
    """
    if output_format == "json":
        data = [d.model_dump(mode="json") for d in devices]
        console.print_json(json.dumps(data))
        return

    if output_format == "yaml":
        data = [d.model_dump(mode="json") for d in devices]
        console.print(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return

    # Rich table output
    table = Table(title="tapctl — Scene Metadata Discovery", show_lines=True)
    table.add_column("IP", style="cyan", no_wrap=True)
    table.add_column("Model", style="bold")
    table.add_column("SoC")
    table.add_column("Firmware")
    table.add_column("SM Supported", justify="center")
    table.add_column("MQTT Sources")
    table.add_column("MQTT State", justify="center")
    table.add_column("Best Snapshot", justify="center")
    table.add_column("Publishers", justify="center")

    for d in devices:
        sm_icon = "[green]✓[/green]" if d.sm_supported else "[dim]—[/dim]"
        table.add_row(
            d.ip,
            d.model,
            d.soc,
            d.firmware,
            sm_icon,
            d.sm_sources_display or "[dim]—[/dim]",
            d.mqtt_state_display or "[dim]—[/dim]",
            d.best_snapshot_display or "[dim]—[/dim]",
            str(d.publishers_count) if d.publishers_count > 0 else "[dim]0[/dim]",
        )

    console.print(table)
    sm_count = sum(1 for d in devices if d.sm_supported)
    console.print(
        f"\n[bold]{len(devices)}[/bold] device(s) found, "
        f"[bold green]{sm_count}[/bold green] with Scene Metadata support."
    )


def generate_manifest_scaffold(devices: list[TapctlDeviceInfo]) -> dict[str, Any]:
    """Generate a manifest scaffold YAML dict from discovered devices.

    Only includes cameras that support Scene Metadata.

    Args:
        devices: List of TapctlDeviceInfo objects.

    Returns:
        Dict suitable for YAML serialization as a tapctl manifest.
    """
    sm_devices = [d for d in devices if d.sm_supported]
    cameras: list[dict[str, Any]] = []
    for d in sm_devices:
        cam: dict[str, Any] = {"name": d.model.lower().replace(" ", "-"), "ip": d.ip}
        if d.model:
            cam["model"] = d.model
        cameras.append(cam)

    return {
        "apiVersion": "tapctl/v1",
        "kind": "MetadataStream",
        "metadata": {"name": "discovered-site", "site": "CHANGEME"},
        "broker": {
            "host": "CHANGEME",
            "port": 1883,
            "protocol": "tcp",
            "topic_prefix": "axis/metadata",
        },
        "defaults": {"credentials": {"username": "root", "password": "CHANGEME"}, "timeout": 15},
        "cameras": cameras,
        "data_sources": [
            {
                "name": "realtime",
                "type": "analytics_scene_description",
                "topic_suffix": "realtime",
            }
        ],
        "best_snapshot": {"enabled": True, "margin": True},
    }
