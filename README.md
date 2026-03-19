# tapctl

kubectl-style CLI for Axis Scene Metadata streaming over MQTT.

tapctl discovers Axis cameras with Scene Metadata support, configures MQTT streaming via declarative YAML manifests, and provides real-time monitoring of metadata flows.

## Install

```bash
# From source (development)
uv venv --python 3.12
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

## Quick Start

### Discover cameras with Scene Metadata support

```bash
# Scan a subnet
tapctl discover --range 192.168.1.0/24 -u root -p your-password

# Probe specific cameras
tapctl discover --targets 10.0.0.10,10.0.0.11 -u root -p pass

# Generate a manifest scaffold from discovery
tapctl discover --range 10.1.1.0/24 -o yaml > my-site.yaml
```

### Apply a manifest (Phase 2)

```bash
# Configure MQTT streaming on all cameras in the manifest
tapctl apply -f my-site.yaml

# Dry run — show what would be configured
tapctl apply -f my-site.yaml --dry-run

# Apply to specific cameras only
tapctl apply -f my-site.yaml --filter "zone=entrance"
```

### Monitor streams (Phase 3)

```bash
# Watch live metadata from all cameras
tapctl tap -f my-site.yaml

# Monitor a single camera
tapctl tap --target 192.168.1.10 -u root -p pass

# JSON output for piping
tapctl tap -f my-site.yaml -o json | jq '.objects'
```

## Manifest Format

```yaml
apiVersion: tapctl/v1
kind: MetadataStream
metadata:
  name: quick-start-demo
  site: "My Test Site"

broker:
  host: 192.168.1.200
  port: 1883
  protocol: tcp
  topic_prefix: "axis/metadata"

defaults:
  credentials:
    username: root
    password: ${AXIS_PASSWORD}

cameras:
  - name: front-door
    ip: 192.168.1.10
    labels:
      zone: entrance

data_sources:
  - name: realtime
    type: analytics_scene_description
    topic_suffix: "realtime"

best_snapshot:
  enabled: true
  margin: true
```

Environment variables are supported via `${VAR_NAME}` syntax.

## Output Formats

All commands support `--output` / `-o`:

- **table** (default) — Rich terminal table
- **json** — Machine-readable JSON
- **yaml** — YAML output (useful for generating manifests)

## Development

```bash
# Run tests
pytest tests/ -v

# Type check
mypy tapctl/

# Lint
ruff check tapctl/ tests/
```

## License

MIT
