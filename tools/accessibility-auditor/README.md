# Accessibility Auditor

WCAG contrast maths, Dynamic Type, touch targets and VoiceOver labels.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/accessibility-auditor/audit_accessibility.py [PATH]
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- contrast ratio for detected text colours against light and dark backgrounds
- fixed point sizes and single-line limits that break Dynamic Type
- interactive elements smaller than 44×44pt
- icon-only buttons without an accessibility label
- controls hidden from assistive technologies

## Findings

| Code | Meaning |
| :--- | :--- |
| `A11Y001` | contrast below 3:1 |
| `A11Y002` | contrast below 4.5:1 |
| `A11Y010` | fixed font size |
| `A11Y020` | tap target under 44pt |
| `A11Y030` | unlabelled icon button |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "accessibility-auditor",
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
