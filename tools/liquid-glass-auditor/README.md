# Liquid Glass Auditor

iOS 26 Liquid Glass adoption versus hand-rolled glassmorphism.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/liquid-glass-auditor/audit_liquid_glass.py [PATH]
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- glass APIs used below iOS 26 without an availability guard
- `GlassEffectContainer` / `glassEffectID` when several effects are adjacent
- imitation patterns: `.ultraThinMaterial` stacks, manual `.blur`, white-opacity overlays
- nested material layers that each sample the backdrop

## Findings

| Code | Meaning |
| :--- | :--- |
| `LG001` | iOS 26 API without availability guard |
| `LG010` | fake glass imitation |
| `LG022` | missing GlassEffectContainer |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "liquid-glass-auditor",
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
