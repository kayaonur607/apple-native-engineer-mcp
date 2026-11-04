# SF Symbols Catalog

Validates symbol names and OS availability against the real system catalogue.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/sf-symbols-catalog/check_symbols.py [PATH]
python3 tools/sf-symbols-catalog/check_symbols.py --name square.and.pencil --ios 17.0
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- 9,649 symbol names extracted from `CoreGlyphs.bundle`
- per-OS availability: does the symbol exist on the project's deployment target
- typo suggestions from the catalogue

## Findings

| Code | Meaning |
| :--- | :--- |
| `SFC010` | unknown symbol name |
| `SFC011` | symbol newer than deployment target |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "sf-symbols-catalog",
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
