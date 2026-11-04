# Design Token Forge

Compiles design tokens into SwiftUI constants and `.xcassets` colour sets.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/design-token-forge/forge_tokens.py tokens.json --out Sources/Tokens.swift
python3 tools/design-token-forge/forge_tokens.py tokens.json --xcassets Assets.xcassets
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- token schema: colours need light and dark values, spacing/radius must be numeric
- typography against `Font.TextStyle`, `Font.Weight`, `Font.Design`
- declared contrast pairs against WCAG AA
- generates dynamic `Color` values plus optional asset catalog colour sets

## Findings

| Code | Meaning |
| :--- | :--- |
| `TOK003` | invalid hex colour |
| `TOK007` | unknown text style |
| `TOK011` | contrast pair below 4.5:1 |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "design-token-forge",
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
