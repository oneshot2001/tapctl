"""Scene Metadata capability detection for Axis cameras."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from axelib.vapix.client import VapixClient, VapixError

from tapctl.models.device import SceneMetadataCapability, TapctlDeviceInfo

if TYPE_CHECKING:
    from axelib.models.device import DeviceInfo

logger = logging.getLogger(__name__)

_SCENE_DESCRIPTION_PRODUCER = "AnalyticsSceneDescription"


async def check_scene_metadata(client: VapixClient) -> SceneMetadataCapability:
    """Check if a camera supports Scene Metadata.

    Probes the following VAPIX endpoints:
    1. listProducers — check for AnalyticsSceneDescription producer
    2. GET /config/rest/analytics-mqtt/v1beta/data_sources — available MQTT sources
    3. getClientStatus — MQTT client state
    4. GET /config/rest/best-snapshot/v1 — snapshot configuration status
    5. GET /config/rest/analytics-mqtt/v1beta/publishers — active publishers

    Args:
        client: An authenticated VapixClient for the target camera.

    Returns:
        SceneMetadataCapability with all probed information.
    """
    cap = SceneMetadataCapability()

    # 1. Check for AnalyticsSceneDescription producer
    producers = await _probe_producers(client)
    cap.producers = producers
    cap.supported = any(
        _SCENE_DESCRIPTION_PRODUCER in str(p.get("name", "")) for p in producers
    )

    if not cap.supported:
        return cap

    # 2. Get available MQTT data sources
    cap.mqtt_sources = await _probe_mqtt_sources(client)

    # 3. Get MQTT client status
    cap.mqtt_state = await _probe_mqtt_state(client)

    # 4. Get best-snapshot config
    cap.best_snapshot = await _probe_best_snapshot(client)

    # 5. Get active publishers
    cap.active_publishers = await _probe_publishers(client)

    return cap


async def enrich_with_scene_metadata(
    device: DeviceInfo, client: VapixClient
) -> TapctlDeviceInfo:
    """Enrichment callback for axelib's scan_subnet.

    Converts a base DeviceInfo to TapctlDeviceInfo with Scene Metadata capability data.

    Args:
        device: Base device info from axelib discovery.
        client: Still-open VapixClient for the device.

    Returns:
        TapctlDeviceInfo with scene_metadata populated.
    """
    cap = await check_scene_metadata(client)
    return TapctlDeviceInfo(
        ip=device.ip,
        model=device.model,
        full_name=device.full_name,
        serial=device.serial,
        firmware=device.firmware,
        soc=device.soc,
        device_type=device.device_type,
        scene_metadata=cap,
    )


async def _probe_producers(client: VapixClient) -> list[dict[str, Any]]:
    """Probe listProducers for analytics producers."""
    try:
        resp = await client.post(
            "/axis-cgi/analytics/listProducers.cgi",
            data='{"apiVersion": "1.0", "method": "listProducers"}',
        )
        producers: list[dict[str, Any]] = resp.get("data", {}).get("producers", [])
        return producers
    except VapixError:
        logger.debug("listProducers not available on %s", client.ip)
        return []
    except Exception:
        logger.debug("listProducers probe failed for %s", client.ip, exc_info=True)
        return []


async def _probe_mqtt_sources(client: VapixClient) -> list[str]:
    """Get available MQTT data sources."""
    try:
        resp = await client.get("/config/rest/analytics-mqtt/v1beta/data_sources")
        raw = resp.get("raw", "")
        if isinstance(raw, str) and raw.strip():
            return []
        sources: list[dict[str, Any]] = resp.get("data_sources", [])
        return [s.get("id", "") for s in sources if s.get("id")]
    except VapixError:
        logger.debug("MQTT data_sources not available on %s", client.ip)
        return []
    except Exception:
        logger.debug("MQTT data_sources probe failed for %s", client.ip, exc_info=True)
        return []


async def _probe_mqtt_state(client: VapixClient) -> dict[str, Any]:
    """Get MQTT client status."""
    try:
        resp = await client.post(
            "/axis-cgi/mqtt/client.cgi",
            data='{"apiVersion": "1.0", "method": "getClientStatus"}',
        )
        status: dict[str, Any] = resp.get("data", {})
        return status
    except VapixError:
        logger.debug("MQTT client status not available on %s", client.ip)
        return {}
    except Exception:
        logger.debug("MQTT client status probe failed for %s", client.ip, exc_info=True)
        return {}


async def _probe_best_snapshot(client: VapixClient) -> dict[str, Any]:
    """Get best-snapshot configuration."""
    try:
        resp = await client.get("/config/rest/best-snapshot/v1")
        return dict(resp)
    except VapixError:
        logger.debug("best-snapshot not available on %s", client.ip)
        return {}
    except Exception:
        logger.debug("best-snapshot probe failed for %s", client.ip, exc_info=True)
        return {}


async def _probe_publishers(client: VapixClient) -> list[dict[str, Any]]:
    """Get active MQTT publishers."""
    try:
        resp = await client.get("/config/rest/analytics-mqtt/v1beta/publishers")
        publishers: list[dict[str, Any]] = resp.get("publishers", [])
        return publishers
    except VapixError:
        logger.debug("MQTT publishers not available on %s", client.ip)
        return []
    except Exception:
        logger.debug("MQTT publishers probe failed for %s", client.ip, exc_info=True)
        return []
