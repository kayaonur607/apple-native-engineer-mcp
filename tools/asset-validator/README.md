# Asset Validator

App Store icon and screenshot compliance, parsed from image headers.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/asset-validator/validate_assets.py [PATH]
python3 tools/asset-validator/validate_assets.py --icon AppIcon-1024.png
python3 tools/asset-validator/validate_assets.py --screenshots ./shots
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- marketing icon: exactly 1024×1024, PNG, no alpha channel
- `.appiconset` Contents.json: declared slots exist with matching dimensions
- screenshots: accepted App Store slot per device and orientation

## Findings

| Code | Meaning |
| :--- | :--- |
| `ASSET002` | not a PNG |
| `ASSET003` | wrong dimensions |
| `ASSET004` | alpha channel present |
| `ASSET022` | screenshot slot unknown |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "asset-validator",
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
