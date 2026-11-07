# Cross-Platform Auditor

Apple-native quality for Flutter, React Native, Expo, Capacitor, .NET MAUI and Kotlin/Compose Multiplatform apps, checked through their native iOS host.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/cross-platform-auditor/audit_cross_platform.py path/to/flutter-app
python3 tools/cross-platform-auditor/audit_cross_platform.py path/to/expo-app --json
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- framework and native host detection (`ios/Runner`, `ios/<App>.xcworkspace`, `ios/App`, `Platforms/iOS`, `iosApp`)
- Dynamic Type overrides, VoiceOver labels on icon-only controls, Dark Mode (Flutter `darkTheme`, Expo `userInterfaceStyle` defaulting to light)
- Flutter `.adaptive()` controls and Cupertino tab bars; React Native deprecated `SafeAreaView`, `Dimensions.get`, start/end layout
- usage descriptions for permission plugins, Flutter languages missing from Xcode `knownRegions`, deployment target below the installed SDK's minimum
- Expo bundle identifier, export compliance, privacy manifests, build number, icon appearances; Capacitor remote `server.url`

## Findings

| Code | Meaning |
| :--- | :--- |
| `FLT001` | Flutter text scaling disabled |
| `FLT009` | language missing from knownRegions |
| `RNA001` | React Native font scaling disabled |
| `EXP003` | Expo Dark Mode off |
| `XPL010` | usage description missing |
| `XPL020` | deployment target below SDK minimum |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "cross-platform-auditor",
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
