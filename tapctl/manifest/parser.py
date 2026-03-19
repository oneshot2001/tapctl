"""YAML manifest loader — uses axelib for parsing, tapctl Pydantic models for validation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from axelib.manifest import load_yaml
from pydantic import ValidationError

from tapctl.models.manifest import MetadataStream

if TYPE_CHECKING:
    from pathlib import Path


class ManifestError(Exception):
    """Human-readable manifest validation error."""

    def __init__(self, message: str, details: list[dict[str, Any]] | None = None) -> None:
        self.details = details or []
        super().__init__(message)


def load_manifest(path: str | Path, strict_env: bool = True) -> MetadataStream:
    """Load and validate a tapctl manifest from YAML.

    Uses axelib's load_yaml for file reading and env-var interpolation,
    then validates against tapctl's MetadataStream Pydantic model.

    Args:
        path: Path to the YAML manifest file.
        strict_env: If True, fail on undefined environment variables.

    Returns:
        Validated MetadataStream model.

    Raises:
        ManifestError: On validation failure with formatted error details.
    """
    data = load_yaml(path, strict_env=strict_env)

    try:
        return MetadataStream.model_validate(data)
    except ValidationError as e:
        errors = e.errors()
        lines: list[str] = [f"Manifest validation failed ({len(errors)} error(s)):"]
        for err in errors:
            loc = " → ".join(str(part) for part in err["loc"])
            lines.append(f"  • {loc}: {err['msg']}")
        raise ManifestError("\n".join(lines), details=[dict(e) for e in errors]) from e
