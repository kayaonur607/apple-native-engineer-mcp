# Distribution Planner

Plan archive, export, App Store / TestFlight upload and Developer ID notarization, with preflight checks and a generated ExportOptions.plist.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/distribution/plan_distribution.py . --method app-store --scheme Planner
python3 tools/distribution/plan_distribution.py . --method testflight-internal --upload
python3 tools/distribution/plan_distribution.py . --method developer-id --write-export-options build/ExportOptions.plist
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- team, signing style, version and build number, shared schemes
- `ITSAppUsesNonExemptEncryption` (export compliance blocks every TestFlight build without it)
- Hardened Runtime for Developer ID, App Sandbox for the Mac App Store, `get-task-allow` in entitlements
- privacy manifest and app icon presence
- ExportOptions keys exactly as `xcodebuild -help` documents (method, destination, testFlightInternalTestingOnly, …)
- ordered commands: archive, export/upload, `altool` validate/upload, `notarytool`, `stapler`, `spctl`; nothing is executed

## Findings

| Code | Meaning |
| :--- | :--- |
| `DST030` | export compliance key missing |
| `DST040` | no Hardened Runtime for notarization |
| `DST041` | no App Sandbox for the Mac App Store |
| `DST060` | method does not fit the platform |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "distribution",
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
