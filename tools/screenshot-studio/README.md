# Screenshot Studio

Capture from a booted simulator and validate App Store slots.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/screenshot-studio/screenshot_studio.py --out shot.png
python3 tools/screenshot-studio/screenshot_studio.py --screenshots ./shots
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- booted simulator discovery via `xcrun simctl`
- capture and immediate dimension validation
- slot matching for iPhone 6.9"/6.7"/6.5", iPad 13", Watch, Vision Pro

## Findings

| Code | Meaning |
| :--- | :--- |
| `SHOT002` | no booted simulator |
| `SHOT004` | capture failed |
| `SHOT011` | dimensions match no slot |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "screenshot-studio",
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
