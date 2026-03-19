"""Tests for tapctl manifest parser."""

from __future__ import annotations

from pathlib import Path

import pytest
from axelib.manifest import ManifestError as AxelibManifestError

from tapctl.manifest.parser import ManifestError, load_manifest

FIXTURES = Path(__file__).parent / "fixtures"


class TestLoadManifest:
    """Test loading and validating YAML manifests."""

    def test_load_sample_manifest(self) -> None:
        """Sample manifest loads and validates correctly."""
        stream = load_manifest(FIXTURES / "sample-manifest.yaml", strict_env=False)
        assert stream.apiVersion == "tapctl/v1"
        assert stream.kind == "MetadataStream"
        assert stream.metadata.name == "quick-start-demo"
        assert stream.metadata.site == "My Test Site"

    def test_broker_config(self) -> None:
        """Broker configuration is parsed correctly."""
        stream = load_manifest(FIXTURES / "sample-manifest.yaml", strict_env=False)
        assert stream.broker.host == "192.168.1.200"
        assert stream.broker.port == 1883
        assert stream.broker.protocol == "tcp"
        assert stream.broker.topic_prefix == "axis/metadata"

    def test_cameras_parsed(self) -> None:
        """Camera list is parsed with labels."""
        stream = load_manifest(FIXTURES / "sample-manifest.yaml", strict_env=False)
        assert len(stream.cameras) == 1
        cam = stream.cameras[0]
        assert cam.name == "front-door"
        assert cam.ip == "192.168.1.10"
        assert cam.labels == {"zone": "entrance"}

    def test_data_sources_parsed(self) -> None:
        """Data sources are parsed correctly."""
        stream = load_manifest(FIXTURES / "sample-manifest.yaml", strict_env=False)
        assert len(stream.data_sources) == 1
        ds = stream.data_sources[0]
        assert ds.name == "realtime"
        assert ds.type == "analytics_scene_description"
        assert ds.topic_suffix == "realtime"

    def test_defaults_parsed(self) -> None:
        """Default credentials and timeout are parsed."""
        stream = load_manifest(FIXTURES / "sample-manifest.yaml", strict_env=False)
        assert stream.defaults.credentials.username == "root"
        assert stream.defaults.credentials.password == "test-password"

    def test_best_snapshot_config(self) -> None:
        """Best snapshot configuration is parsed."""
        stream = load_manifest(FIXTURES / "sample-manifest.yaml", strict_env=False)
        assert stream.best_snapshot.enabled is True
        assert stream.best_snapshot.margin is True

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        """Missing manifest file raises ManifestError."""
        with pytest.raises((ManifestError, AxelibManifestError)):
            load_manifest(tmp_path / "nonexistent.yaml")

    def test_invalid_manifest_raises_error(self, tmp_path: Path) -> None:
        """Invalid manifest content raises ManifestError."""
        bad = tmp_path / "bad.yaml"
        bad.write_text("apiVersion: tapctl/v1\nkind: MetadataStream\n")
        with pytest.raises(ManifestError, match="validation failed"):
            load_manifest(bad, strict_env=False)
