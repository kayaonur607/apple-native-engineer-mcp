# App Store Connect (read-only)

Read-only App Store Connect inspection with explicit auth.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/app-store-connect/cli.py verify
python3 tools/app-store-connect/cli.py list-apps
python3 tools/app-store-connect/cli.py versions --app 1234567890
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- ES256 JWT signing via `cryptography` (no fake signatures)
- hard failure when credentials are missing — never a silent mock
- 429 rate-limit aware with backoff
- read-only: only GET requests are issued

## Findings

| Code | Meaning |
| :--- | :--- |
| `ASC001` | missing credentials |
| `ASC010` | explicit mock mode |
| `ASC013` | expired builds |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "app-store-connect",
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
