# Project Inspector

Structural analysis of an Xcode project or Swift package.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/project-inspector/inspect_project.py [PATH]
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- project kind: `.xcodeproj`, `.xcworkspace`, `Package.swift`
- targets, deployment targets per platform, Swift language version
- frameworks in use (SwiftUI, SwiftData, StoreKit, WidgetKit, …)
- architecture signals: `@Observable`, structured concurrency, TCA, SwiftData
- structural debt: legacy OS floor, missing tests, `NavigationView`, missing manifest

## Findings

| Code | Meaning |
| :--- | :--- |
| `PROJ001` | no project file found |
| `PROJ003` | iOS floor below 17.0 |
| `PROJ005` | Swift < 6 language mode |
| `PROJ006` | no test target |
| `PROJ007` | ObservableObject without @Observable |
| `PROJ008` | NavigationView |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "project-inspector",
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
