"""Tests for tapctl Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tapctl.models.device import SceneMetadataCapability, TapctlDeviceInfo
from tapctl.models.manifest import (
    BrokerConfig,
    CameraConfig,
    DataSourceConfig,
    ManifestMetadata,
    MetadataStream,
)


class TestSceneMetadataCapability:
    """Test SceneMetadataCapability model."""

    def test_defaults(self) -> None:
        cap = SceneMetadataCapability()
        assert cap.supported is False
        assert cap.producers == []
        assert cap.mqtt_sources == []

    def test_with_data(self) -> None:
        cap = SceneMetadataCapability(
            supported=True,
            mqtt_sources=["com.axis.analytics_scene_description.v0.beta#1"],
        )
        assert cap.supported is True
        assert len(cap.mqtt_sources) == 1


class TestTapctlDeviceInfo:
    """Test TapctlDeviceInfo model."""

    def test_basic_creation(self) -> None:
        device = TapctlDeviceInfo(ip="10.0.0.1", model="AXIS P3268-LVE")
        assert device.ip == "10.0.0.1"
        assert device.model == "AXIS P3268-LVE"
        assert device.sm_supported is False

    def test_with_scene_metadata(self) -> None:
        device = TapctlDeviceInfo(
            ip="10.0.0.1",
            model="AXIS P3268-LVE",
            scene_metadata=SceneMetadataCapability(
                supported=True,
                mqtt_sources=["source1", "source2"],
                mqtt_state={"status": "connected"},
                best_snapshot={"enabled": True},
                active_publishers=[{"id": "pub1"}],
            ),
        )
        assert device.sm_supported is True
        assert device.sm_sources_display == "source1, source2"
        assert device.mqtt_state_display == "connected"
        assert device.best_snapshot_display == "enabled"
        assert device.publishers_count == 1

    def test_empty_displays(self) -> None:
        device = TapctlDeviceInfo(ip="10.0.0.1", model="AXIS M3068")
        assert device.sm_sources_display == ""
        assert device.mqtt_state_display == ""
        assert device.best_snapshot_display == ""
        assert device.publishers_count == 0


class TestBrokerConfig:
    """Test BrokerConfig model."""

    def test_minimal(self) -> None:
        broker = BrokerConfig(host="192.168.1.200")
        assert broker.port == 1883
        assert broker.protocol == "tcp"
        assert broker.client_id_prefix == "tapctl"

    def test_invalid_protocol(self) -> None:
        with pytest.raises(ValidationError):
            BrokerConfig(host="192.168.1.200", protocol="invalid")  # type: ignore[arg-type]


class TestCameraConfig:
    """Test CameraConfig model."""

    def test_minimal(self) -> None:
        cam = CameraConfig(name="front", ip="10.0.0.1")
        assert cam.labels == {}
        assert cam.model is None

    def test_with_labels(self) -> None:
        cam = CameraConfig(name="lobby", ip="10.0.0.2", labels={"zone": "entry", "floor": "1"})
        assert cam.labels["zone"] == "entry"


class TestDataSourceConfig:
    """Test DataSourceConfig model."""

    def test_defaults(self) -> None:
        ds = DataSourceConfig(name="realtime")
        assert ds.type == "analytics_scene_description"
        assert ds.channels == [1]

    def test_consolidated_track(self) -> None:
        ds = DataSourceConfig(name="tracks", type="consolidated_track", channels=[1, 2])
        assert ds.type == "consolidated_track"
        assert ds.channels == [1, 2]


class TestMetadataStream:
    """Test top-level MetadataStream model."""

    def test_full_manifest(self) -> None:
        stream = MetadataStream(
            metadata=ManifestMetadata(name="test"),
            broker=BrokerConfig(host="10.0.0.1"),
            cameras=[CameraConfig(name="cam1", ip="10.0.0.10")],
            data_sources=[DataSourceConfig(name="rt")],
        )
        assert stream.apiVersion == "tapctl/v1"
        assert stream.kind == "MetadataStream"
        assert len(stream.cameras) == 1

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            MetadataStream()  # type: ignore[call-arg]

    def test_defaults_applied(self) -> None:
        stream = MetadataStream(
            metadata=ManifestMetadata(name="test"),
            broker=BrokerConfig(host="10.0.0.1"),
        )
        assert stream.defaults.timeout == 15
        assert stream.best_snapshot.enabled is True
        assert stream.defaults.credentials.username == "root"
