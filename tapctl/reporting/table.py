"""tapctl-specific Rich table rendering for Scene Metadata discovery."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import yaml
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from tapctl.models.device import TapctlDeviceInfo

console = Console()


def generate_site_inventory(devices: list[TapctlDeviceInfo]) -> dict[str, Any]:
    """Generate a SiteInventory document per spec section 5.3.

    Args:
        devices: List of TapctlDeviceInfo objects from discovery.

    Returns:
        Dict suitable for YAML serialization as a tapctl SiteInventory.
    """
    sm_count = sum(1 for d in devices if d.sm_supported)
    cameras: list[dict[str, Any]] = []
    for d in devices:
        sm = d.scene_metadata
        cam: dict[str, Any] = {
            "ip": d.ip,
            "model": d.model,
            "serial": d.serial or "",
            "firmware": d.firmware or "",
            "soc": d.soc or "",
            "scene_metadata": {
                "supported": sm.supported,
                "producers": list(sm.producers),
                "mqtt_sources": list(sm.mqtt_sources),
                "best_snapshot": dict(sm.best_snapshot),
            },
            "mqtt": {
                "state": sm.mqtt_state.get("status", "inactive") if sm.mqtt_state else "inactive",
                "publishers": list(sm.active_publishers),
            },
        }
        cameras.append(cam)

    return {
        "apiVersion": "tapctl/v1",
        "kind": "SiteInventory",
        "metadata": {
            "scan_time": datetime.now(tz=UTC).isoformat(),
            "cameras_found": len(devices),
            "scene_metadata_capable": sm_count,
        },
        "cameras": cameras,
    }


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
        inventory = generate_site_inventory(devices)
        console.print(yaml.dump(inventory, default_flow_style=False, sort_keys=False))
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
