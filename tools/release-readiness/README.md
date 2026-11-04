# Release Readiness Gate

Weighted, evidence-based pre-submission verdict across every gate.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/release-readiness/generate_report.py . --metadata metadata.json --icon AppIcon.png --output RELEASE_REPORT.md
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- seven weighted gates: privacy 25, assets 15, metadata 15, project 15, localisation 10, widgets 10, accessibility 10
- a gate with no input is NOT INSPECTED, scores zero and forces BLOCKED
- any error or critical finding zeroes its gate
- `READY` requires every applicable gate passing AND a score of at least 90

## Findings

| Code | Meaning |
| :--- | :--- |
| `REL001` | gate not inspected |
| `REL002` | gate failed |
| `REL003` | gate has warnings |
| `REL010` | all gates passed |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "release-readiness",
  "tool_version": "2.0.0",
  "target": "/absolute/path",
  "status": "pass | warn | fail",
  "summary": {"critical": 0, "error": 0, "warning": 0, "info": 0, "total": 0},
  "findings": [{"code": "...", "severity": "...", "message": "...", "file": "...", "line": 0, "hint": "..."}],
  "data": {}
}
```

## Exit codes

| Code | Meaning |
| ---: | :--- |
| 0 | pass (or warnings without `--strict`) |
| 1 | warnings with `--strict` |
| 2 | at least one error or critical finding |
