# Widget & Live Activity Validator

WidgetKit, Dynamic Island and ActivityKit completeness.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/widget-validator/validate_widget.py [PATH]
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- Live Activity: `NSSupportsLiveActivities`, `Activity.request`, push token handling
- Dynamic Island: compactLeading, compactTrailing, minimal, expanded regions
- `supportedFamilies` incl. Lock Screen accessory families
- timeline provider and App Intent configuration
- App Group shared container wiring

## Findings

| Code | Meaning |
| :--- | :--- |
| `WID010` | Live Activities flag missing |
| `WID020` | Dynamic Island region missing |
| `WID031` | no supportedFamilies |
| `WID032` | no timeline provider |
| `WID034` | no App Group |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "widget-validator",
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
