"""tapctl device model — extends axelib DeviceInfo with Scene Metadata capabilities."""

from __future__ import annotations

from axelib.models.device import DeviceInfo as _BaseDeviceInfo
from axelib.models.device import DeviceType  # noqa: F401
from pydantic import BaseModel, Field


class SceneMetadataCapability(BaseModel):
    """Scene Metadata capability information for an Axis camera."""

    supported: bool = False
    producers: list[dict[str, object]] = Field(default_factory=list)
    mqtt_sources: list[str] = Field(default_factory=list)
    mqtt_state: dict[str, object] = Field(default_factory=dict)
    best_snapshot: dict[str, object] = Field(default_factory=dict)
    active_publishers: list[dict[str, object]] = Field(default_factory=list)


class TapctlDeviceInfo(_BaseDeviceInfo):
    """Axis device with Scene Metadata capability information."""

    scene_metadata: SceneMetadataCapability = SceneMetadataCapability()

    @property
    def sm_supported(self) -> bool:
        """Shorthand for scene_metadata.supported."""
        return self.scene_metadata.supported

    @property
    def sm_sources_display(self) -> str:
        """Comma-separated MQTT source list for table display."""
        if not self.scene_metadata.mqtt_sources:
            return ""
        return ", ".join(self.scene_metadata.mqtt_sources)

    @property
    def mqtt_state_display(self) -> str:
        """Human-readable MQTT client state."""
        state = self.scene_metadata.mqtt_state
        if not state:
            return ""
        status = state.get("status", "unknown")
        return str(status)

    @property
    def best_snapshot_display(self) -> str:
        """Human-readable best-snapshot status."""
        snap = self.scene_metadata.best_snapshot
        if not snap:
            return ""
        enabled = snap.get("enabled", False)
        return "enabled" if enabled else "disabled"

    @property
    def publishers_count(self) -> int:
        """Number of active MQTT publishers."""
        return len(self.scene_metadata.active_publishers)
