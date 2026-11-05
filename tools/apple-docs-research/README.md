# Apple Documentation Research

Read Apple's official documentation with citations, from the JSON API the site itself uses.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/apple-docs-research/apple_docs.py search "navigation stack" --framework swiftui
python3 tools/apple-docs-research/apple_docs.py read swiftui/view/glassEffect(_:in:)
python3 tools/apple-docs-research/apple_docs.py availability swiftui/navigationstack
python3 tools/apple-docs-research/apple_docs.py guidelines buttons
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- refuses any host other than developer.apple.com, before a socket opens
- `search`: ranked symbol lookup across a framework index (8,000+ symbols for SwiftUI)
- `read`: page rendered as Markdown — declaration, overview, code listings, parameters
- `availability`: the per-platform table Apple publishes (introduced, deprecated, beta)
- `guidelines`: Human Interface Guidelines pages as Markdown
- every result carries `source_url` and `fetched_at`; cached seven days, `--refresh` to bypass, `--offline` to forbid the network

## Findings

| Code | Meaning |
| :--- | :--- |
| `DOC000` | document could not be retrieved (error, never a guess) |
| `DOC010` | served from cache |
| `DOC011` | API is deprecated on a platform |
| `DOC030` | no symbol matched |
| `DOC040` | HIG page rendered empty |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "apple-docs-research",
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
