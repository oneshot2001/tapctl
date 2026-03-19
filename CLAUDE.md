# Tapctl — CLAUDE.md

## Vault Memory
At session start, read these files in order:
1. [vault]/02-Projects/tapctl/context.md
2. [vault]/02-Projects/tapctl/decisions.md
3. [vault]/02-Projects/tapctl/patterns.md
4. [vault]/02-Projects/tapctl/bugs.md
5. [vault]/02-Projects/tapctl/architecture.md
6. Last 3 files (by date) in [vault]/02-Projects/tapctl/dev-log/
7. All files in [vault]/05-Knowledge/patterns/

Vault root: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Obsidian Second Brain

## Auto-Capture Rules
During this session, track:
1. Every architectural decision (what, alternatives considered, why)
2. Every bug fixed (symptom, root cause, fix, prevention rule)
3. Every reusable pattern discovered (code snippet, when to use, where it applies)
4. Architecture changes (new routes, schema changes, data flow changes)

At session end, automatically write:
- Session log to: [vault]/02-Projects/tapctl/dev-log/YYYY-MM-DD-session-N.md
- Append new decisions to: [vault]/02-Projects/tapctl/decisions.md
- Append new bugs to: [vault]/02-Projects/tapctl/bugs.md
- Update if changed: [vault]/02-Projects/tapctl/architecture.md

## Session Log Format

Use this template for dev-log entries:

```markdown
---
date: YYYY-MM-DD
session: N
project: tapctl
tags: [dev-log]
---

# Dev Session — Tapctl — YYYY-MM-DD #N

## Summary
[1-2 sentence overview of what this session accomplished]

## What Was Built
- [Feature/fix 1]: [brief description]
- [Feature/fix 2]: [brief description]

## Decisions Made
### [Decision Title]
- **Options considered:** [option A], [option B], [option C]
- **Chosen:** [option]
- **Reasoning:** [why this option won]
- **Trade-offs:** [what we gave up]

## Bugs Encountered & Fixed
### [Bug Title]
- **Symptom:** [what you saw / error message]
- **Root cause:** [why it happened]
- **Fix:** [what resolved it]
- **Prevention:** [rule to avoid it in future]
- **Files changed:** [file paths]

## Patterns Discovered
### [Pattern Name]
- **When to use:** [description]
- **Reuse in:** [[Project1]], [[Project2]]
```[language]
[code snippet]
```

## Architecture Changes
- [Change description]: [before] -> [after]

## Reasoning Chains
[For complex decisions, document the full chain of reasoning that led to the outcome]

## Open Questions
- [ ] [Question that came up but wasn't resolved this session]

## Next Session Should
- [Top priority for next session]
- [Context that would be lost without writing it down]
```

## Project Details

### Stack
Python, Click CLI, aiohttp, PyYAML, Pydantic, Rich, paho-mqtt, pytest

### Spec Reference
Full product specification: `~/Documents/AI Planning and Projects/tapctl/tapctl-spec.md`

### Build Commands
```bash
# Dev install (editable)
uv pip install -e ".[dev]"

# Run CLI
tapctl --help

# Test
pytest

# Type check
mypy tapctl/

# Lint
ruff check tapctl/
```

### Deploy
PyPI package (`pip install tapctl` / `pipx install tapctl`)

### Quality Gates
1. Tests pass (`pytest`)
2. Types verified (`mypy tapctl/`)
3. Lint clean (`ruff check tapctl/`)
4. CLI --help renders correctly
5. Git: staged, committed, pushed

### Key Patterns (shared with e2ectl)
- Async VAPIX HTTP client pattern
- Network scanner pattern
- Digest auth for Axis cameras
- Rich terminal table output
