# ASO Engine

Deterministic App Store Optimization analysis: no invented search volume, no invented competitors.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/aso-engine/aso.py metadata.json
python3 tools/aso-engine/aso.py metadata.json --locale tr-TR --json
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- character budgets per field against App Store Connect limits
- duplicate keywords, single-character keywords, budget spent on words already in the name
- keywords that never appear in the name, subtitle or description (coverage hint)
- unverifiable claims: “best”, “#1”, “world's”, “guaranteed”, “100%”
- description structure: opening paragraph length, bullet list, tappable link
- candidate keywords extracted from the developer's own description, with the arithmetic shown

## Findings

| Code | Meaning |
| :--- | :--- |
| `ASO001` | field over its limit |
| `ASO002` | budget left unused |
| `ASO010` | duplicate keywords |
| `ASO012` | keywords absent from visible copy |
| `ASO020` | unverifiable claim |
| `ASO031` | keyword candidates that fit the budget |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "aso-engine",
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
