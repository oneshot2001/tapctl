"""Tests for Scene Metadata capability detection with mocked VAPIX responses."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from axelib.models.device import DeviceInfo, DeviceType

from tapctl.discovery.scene_metadata import check_scene_metadata, enrich_with_scene_metadata
from tapctl.models.device import TapctlDeviceInfo


def _make_mock_client(
    producers_response: dict | None = None,
    mqtt_sources_response: dict | None = None,
    mqtt_state_response: dict | None = None,
    best_snapshot_response: dict | None = None,
    publishers_response: dict | None = None,
) -> AsyncMock:
    """Create a mock VapixClient with configurable responses."""
    client = AsyncMock()
    client.ip = "10.0.0.1"

    async def mock_post(path: str, data: str | None = None) -> dict:  # type: ignore[type-arg]
        if "listProducers" in path:
            return producers_response or {"data": {"producers": []}}
        if "mqtt/client" in path:
            return mqtt_state_response or {"data": {}}
        return {}

    async def mock_get(path: str, params: dict | None = None) -> dict:  # type: ignore[type-arg]
        if "data_sources" in path:
            return mqtt_sources_response or {"data_sources": []}
        if "best-snapshot" in path:
            return best_snapshot_response or {}
        if "publishers" in path:
            return publishers_response or {"publishers": []}
        return {}

    client.post = mock_post
    client.get = mock_get
    return client


class TestCheckSceneMetadata:
    """Test check_scene_metadata probing logic."""

    @pytest.mark.asyncio
    async def test_camera_without_scene_metadata(self) -> None:
        """Camera with no AnalyticsSceneDescription producer."""
        client = _make_mock_client(
            producers_response={"data": {"producers": [{"name": "ObjectAnalytics"}]}},
        )
        cap = await check_scene_metadata(client)
        assert cap.supported is False
        assert cap.mqtt_sources == []

    @pytest.mark.asyncio
    async def test_camera_with_scene_metadata(self) -> None:
        """Camera with AnalyticsSceneDescription producer."""
        client = _make_mock_client(
            producers_response={
                "data": {
                    "producers": [
                        {"name": "AnalyticsSceneDescription", "version": "1.0"},
                        {"name": "ObjectAnalytics", "version": "1.0"},
                    ]
                }
            },
            mqtt_sources_response={
                "data_sources": [
                    {"id": "com.axis.analytics_scene_description.v0.beta#1"},
                ]
            },
            mqtt_state_response={"data": {"status": "connected", "server": "10.0.0.200"}},
            best_snapshot_response={"enabled": True, "margin": True},
            publishers_response={"publishers": [{"id": "pub1", "active": True}]},
        )
        cap = await check_scene_metadata(client)
        assert cap.supported is True
        assert "com.axis.analytics_scene_description.v0.beta#1" in cap.mqtt_sources
        assert cap.mqtt_state.get("status") == "connected"
        assert cap.best_snapshot.get("enabled") is True
        assert len(cap.active_publishers) == 1

    @pytest.mark.asyncio
    async def test_empty_producers_response(self) -> None:
        """Camera returns empty producers list."""
        client = _make_mock_client(
            producers_response={"data": {"producers": []}},
        )
        cap = await check_scene_metadata(client)
        assert cap.supported is False

    @pytest.mark.asyncio
    async def test_probe_failure_graceful(self) -> None:
        """Probes that raise exceptions return safe defaults."""
        client = AsyncMock()
        client.ip = "10.0.0.1"
        client.post = AsyncMock(side_effect=Exception("connection refused"))
        client.get = AsyncMock(side_effect=Exception("connection refused"))

        cap = await check_scene_metadata(client)
        assert cap.supported is False
        assert cap.producers == []


class TestEnrichWithSceneMetadata:
    """Test the enrichment callback for scan_subnet."""

    @pytest.mark.asyncio
    async def test_enrichment_returns_tapctl_device(self) -> None:
        """Enrichment converts DeviceInfo to TapctlDeviceInfo."""
        base = DeviceInfo(
            ip="10.0.0.5",
            model="AXIS P3268-LVE",
            serial="ABCD1234",
            firmware="11.8.60",
            soc="ARTPEC-8",
            device_type=DeviceType.CAMERA,
        )
        client = _make_mock_client(
            producers_response={
                "data": {"producers": [{"name": "AnalyticsSceneDescription"}]}
            },
        )
        result = await enrich_with_scene_metadata(base, client)
        assert isinstance(result, TapctlDeviceInfo)
        assert result.ip == "10.0.0.5"
        assert result.model == "AXIS P3268-LVE"
        assert result.sm_supported is True
