# Screenshot pipeline evidence

Recorded 2026-11-07 on macOS with Xcode 27.2 and the iOS 27.2 Simulator.

| File | What it is |
| --- | --- |
| `pipeline-run.json` | Summaries of the four tool envelopes (capture, audit of captures, composition, audit of frames), every executed `simctl` command, and each capture's size and alpha state. Local paths are replaced with `<run>` / `<repository>`. |
| `screenshot-frames.jpg` | One raw capture and four composed frames, downscaled for the README. |
| `flutter-run.json` | The Flutter run: cross-platform audit before and after the fixes, capture, composition and final audit. |
| `flutter-frames.jpg` | One raw Flutter capture and three composed frames. |
| `SHA256SUMS` | Checksums of the files above. |

Inputs: [`examples/flutter-pipeline`](../../examples/flutter-pipeline/README.md) for the Flutter run and
[`examples/screenshot-pipeline`](../../examples/screenshot-pipeline/README.md) (`PlannerDemoApp.swift`,
`plan.json`, `captions.json`). Regenerate with the commands in that README, then
`python3 scripts/render_evidence_gallery.py`.

Scope: a controlled demo app, not a customer project. The frames are marketing compositions of real captures.
No build was uploaded to App Store Connect. Full-size captures and frames are not committed.
