"""Pydantic models for tapctl manifest format."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TlsConfig(BaseModel):
    """TLS configuration for MQTT broker."""

    ca_cert: str = ""
    client_cert: str = ""
    client_key: str = ""
    insecure: bool = False


class LastWillConfig(BaseModel):
    """MQTT last will and testament."""

    topic: str = ""
    payload: str = ""
    qos: int = 0
    retain: bool = False


class BrokerConfig(BaseModel):
    """MQTT broker connection settings."""

    host: str
    port: int = 1883
    protocol: Literal["tcp", "ssl", "ws", "wss"] = "tcp"
    username: str = ""
    password: str = ""
    client_id_prefix: str = "tapctl"
    keep_alive: int = 60
    clean_session: bool = True
    tls: TlsConfig | None = None
    topic_prefix: str = "axis/metadata"
    last_will: LastWillConfig | None = None


class CredentialsConfig(BaseModel):
    """Camera credential pair."""

    username: str = "root"
    password: str = ""


class CameraConfig(BaseModel):
    """Single camera definition in a manifest."""

    name: str
    ip: str
    model: str | None = None
    credentials: CredentialsConfig | None = None
    labels: dict[str, str] = Field(default_factory=dict)


class DataSourceConfig(BaseModel):
    """Scene metadata data source configuration."""

    name: str
    type: Literal["analytics_scene_description", "consolidated_track"] = (
        "analytics_scene_description"
    )
    topic_suffix: str = ""
    channels: list[int] = Field(default_factory=lambda: [1])


class BestSnapshotConfig(BaseModel):
    """Best-snapshot configuration."""

    enabled: bool = True
    margin: bool = True


class BufferConfig(BaseModel):
    """Bridge buffer configuration."""

    max_size: int = 10000
    flush_on_shutdown: bool = True


class BridgeConfig(BaseModel):
    """Upstream bridge configuration."""

    enabled: bool = False
    endpoint: str = ""
    api_key: str = ""
    batch_size: int = 50
    flush_interval: int = 5
    strip_snapshots: bool = False
    buffer: BufferConfig | None = None


class ManifestMetadata(BaseModel):
    """Manifest-level metadata."""

    name: str
    site: str = ""
    project: str = ""
    created: str = ""


class DefaultsConfig(BaseModel):
    """Default settings applied to all cameras."""

    credentials: CredentialsConfig = Field(default_factory=CredentialsConfig)
    timeout: int = 15


class AoaEventsConfig(BaseModel):
    """AOA (Axis Object Analytics) event forwarding config."""

    enabled: bool = False
    scenarios: list[str] = Field(default_factory=list)


class MetadataStream(BaseModel):
    """Top-level tapctl manifest model.

    Represents a complete metadata streaming configuration:
    broker, cameras, data sources, and optional bridge.
    """

    apiVersion: str = "tapctl/v1"  # noqa: N815
    kind: str = "MetadataStream"
    metadata: ManifestMetadata
    broker: BrokerConfig
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    cameras: list[CameraConfig] = Field(default_factory=list)
    data_sources: list[DataSourceConfig] = Field(default_factory=list)
    best_snapshot: BestSnapshotConfig = Field(default_factory=BestSnapshotConfig)
    aoa_events: AoaEventsConfig | None = None
    bridge: BridgeConfig | None = None
