# Metadata Validator

App Store listing copy and URLs against App Store Connect limits.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/metadata-validator/validate_metadata.py metadata.json
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- character limits: name 30, subtitle 30, keywords 100, promotional text 170, description 4000
- required `https://` URLs (support, privacy) and optional marketing URL
- keyword duplicates and wasted budget
- screenshot count (3–10) and http links in the description

## Findings

| Code | Meaning |
| :--- | :--- |
| `META001` | over character limit |
| `META004` | required URL missing |
| `META005` | invalid https URL |
| `META007` | duplicate keywords |
| `META012` | fewer than 3 screenshots |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "metadata-validator",
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
