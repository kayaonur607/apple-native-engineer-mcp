# SwiftUI Linter

20 opinionated static rules for native-quality SwiftUI.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/swiftui-linter/lint_swiftui.py [PATH]
python3 tools/swiftui-linter/lint_swiftui.py --rules
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- deprecated API: `foregroundColor`, `NavigationView`, `onChange(of:perform:)`, `animation(_:)`
- hardcoded styling: hex colours, fixed font sizes, white/black backgrounds
- view identity churn: `AnyView`, `id(UUID())`, `ForEach(0..<n)`
- robustness: `try!`, `UIScreen.main.bounds`, body-side effects
- motion: `scaleEffect(0)`, oversized shadows

## Findings

| Code | Meaning |
| :--- | :--- |
| `SWU001` | hardcoded hex colour |
| `SWU002` | foregroundColor deprecated |
| `SWU003` | NavigationView |
| `SWU006` | UIScreen.main.bounds |
| `SWU009` | scaleEffect(0) |
| `SWU011` | ObservableObject |
| `SWU014` | try! |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "swiftui-linter",
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
