# Localization Checker

Strings that can never be translated, plus RTL mirroring defects.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/localization-checker/check_localization.py [PATH]
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- `Text(verbatim:)` and other explicit localisation bypasses
- UIKit string assignments that are never looked up in a catalog
- `Text(resolvedString)` where interpolation is required
- `.left` / `.right` padding and alignment that do not mirror in RTL
- String Catalog keys with missing translations or `needs_review` state

## Findings

| Code | Meaning |
| :--- | :--- |
| `L10N001` | verbatim string |
| `L10N002` | UIKit string assignment |
| `L10N003` | Text(String) not localisable |
| `L10N010` | RTL-hostile layout |
| `L10N021` | missing translations |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "localization-checker",
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
