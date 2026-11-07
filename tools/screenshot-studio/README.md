# Screenshot Studio

Capture App Store screenshots in the Simulator, audit them against Apple's slots, and compose localized marketing frames rendered natively on macOS.

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
python3 tools/screenshot-studio/capture_batch.py plan.json --out shots --dry-run
python3 tools/screenshot-studio/capture_batch.py plan.json --out shots
python3 tools/screenshot-studio/screenshot_studio.py --screenshots ./shots --platforms ios,ipados
python3 tools/screenshot-studio/compose_marketing.py --screenshots ./shots --out ./frames --captions captions.json --render
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

- `capture_batch.py`: devices × locales × light/dark in the Simulator, 9:41 status bar, `-AppleLanguages`/`-AppleLocale`, per-screen launch arguments or deep links, `manifest.json` provenance
- Simulator PNGs carry alpha; captures are flattened to opaque RGB natively (App Store Connect rejects alpha)
- slot table from `data/app-store-specs.json` (Apple's published specification, dated): iPhone Duo, 6.9"–3.5", iPad 13"–9.7", Mac, Apple TV, Vision Pro, every Watch size
- per-locale sets: 1–10 per size, mixed orientations, one Watch size across locales, required sets per platform
- `compose_marketing.py`: localized captions, drawn device frame with Dynamic Island, right-to-left layout, SVG plus native CoreGraphics/San Francisco PNG at the exact slot size

## Findings

| Code | Meaning |
| :--- | :--- |
| `SHOT011` | dimensions match no slot |
| `SHOT013` | alpha channel (rejected) |
| `SHOT021` | more than 10 in a set |
| `SHOT022` | required set missing |
| `SHOT115` | locale fell back to other copy |
| `CAP032` | capture still has alpha |

## Output contract

`--json` prints one object and nothing else:

```json
{
  "schema_version": "2.0",
  "tool": "screenshot-studio",
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
