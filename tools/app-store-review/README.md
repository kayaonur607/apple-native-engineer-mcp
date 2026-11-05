# App Store Review Risk

Finds the conditions that appear in rejection letters, each tied to a guideline section.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/app-store-review/review.py .
python3 tools/app-store-review/review.py . --metadata metadata.json --json
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- sensor use without a matching NS*UsageDescription (5.1.1)
- placeholder copy: TODO, FIXME, lorem ipsum, “coming soon” (2.1)
- account creation with no in-app deletion path (5.1.1(v))
- external payment providers where In-App Purchase is required (3.1.1)
- web-wrapper apps with no native navigation (4.2)
- private or deprecated API use: UIWebView, performSelector, reflective UIKit access (2.5.1)
- listing metadata: http:// links and unreplaced example.com URLs (2.3.1)

## Findings

| Code | Meaning |
| :--- | :--- |
| `RVW101` | usage description missing |
| `RVW201` | placeholder content |
| `RVW301` | no account deletion |
| `RVW401` | external payments |
| `RVW501` | web wrapper |
| `RVW601` | private API |
| `RVW803` | http:// URL in metadata |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "app-store-review",
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
