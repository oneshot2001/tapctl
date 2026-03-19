"""Global configuration and credential management for tapctl."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class TapctlConfig:
    """Runtime configuration for tapctl commands."""

    user: str = "root"
    password: str = ""
    timeout: int = 10
    output: str = "table"
    verbose: bool = False
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> TapctlConfig:
        """Build config from environment variables with sensible defaults."""
        return cls(
            user=os.environ.get("TAPCTL_USER", "root"),
            password=os.environ.get("TAPCTL_PASSWORD", ""),
            timeout=int(os.environ.get("TAPCTL_TIMEOUT", "10")),
        )


@dataclass
class CredentialOverride:
    """Per-camera credential override from manifest."""

    username: str = "root"
    password: str = ""


@dataclass
class RuntimeContext:
    """Bag of state threaded through Click context."""

    config: TapctlConfig = field(default_factory=TapctlConfig)
