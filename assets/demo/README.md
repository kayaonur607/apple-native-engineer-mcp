# Demonstration provenance

These assets were generated from an actual Apple Native Engineer v2.2.0 stdio MCP client/server session using only public repository fixtures.

| Asset | What it establishes |
| --- | --- |
| `session.json` | Raw requests/responses, per-call durations, timestamp, version and produced icon file names |
| `audit-comparison.png` | Legacy fixture: 14 SwiftUI violations; clean fixture: zero violations and one informational finding |
| `icon-pipeline.png` | One opaque 1024-pixel fixture master generated 18 icon slots; separate verification reported no missing/wrong-size files |
| `usage-demo.mp4` | 64-second 1600×900 / 24fps animated walkthrough based on eight real MCP responses; captions, no audio |
| `usage-preview.gif` | Animated preview of the same eight-chapter walkthrough |
| `usage-demo.vtt` | Chapter captions |
| `SHA256SUMS` | Integrity hashes for the recording and rendered artifacts |

The video is an evidence-based motion graphic with animated signal flow, finding cards, icon fan-out and verification indicators. It is not a desktop, AI-chat or simulator screen capture. Each animated chapter lasts eight seconds; actual tool durations are shown separately. Animation timing and counter reveals are illustrative and do not measure execution progress. No voice or AI conversation is synthesized. Legacy and clean are separate fixtures, not an automated source rewrite. The source master icon is deliberately a solid-colour fixture.

Regenerate from the repository root:

```bash
node integrations/mcp-server/scripts/record-demo.mjs
python3 scripts/render-demo-media.py
```

Install Pillow and ffmpeg separately for media authoring. On non-macOS systems, supply `DEMO_FONT`, `DEMO_BOLD_FONT` and `DEMO_MONO_FONT` paths. Fonts influence rendering, so generated pixels need not be identical across machines. The JSON report is the primary execution evidence. No customer projects, accounts or source code are used.

Before publishing customer-facing screenshots of an actual app, separately capture real simulator/device output and document the OS, appearance, locale and accessibility settings. Do not relabel these fixture cards as UI runtime evidence.
