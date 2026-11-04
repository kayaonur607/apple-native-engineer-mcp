# Privacy Manifest Auditor

Validates `PrivacyInfo.xcprivacy` against actual Required-Reason API usage.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/privacy-auditor/audit_privacy.py [PATH]
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- manifest presence and parseability
- per-category detection: UserDefaults, file timestamp, boot time, disk space, keyboards
- declared reason codes against Apple's documented valid codes
- tracking domains vs detected tracking SDKs
- collected-data declarations vs detected data-collecting APIs

## Findings

| Code | Meaning |
| :--- | :--- |
| `PRIV001` | manifest missing |
| `PRIV010` | category used but undeclared |
| `PRIV011` | invalid reason code |
| `PRIV020` | tracking signals without NSPrivacyTracking |
| `PRIV022` | collected data undeclared |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "privacy-auditor",
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
