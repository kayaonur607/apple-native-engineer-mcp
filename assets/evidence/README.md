# Screenshot pipeline evidence

Recorded 2026-11-07 on macOS with Xcode 27.2 and the iOS 27.2 Simulator.

| File | What it is |
| --- | --- |
| `pipeline-run.json` | Summaries of the four tool envelopes (capture, audit of captures, composition, audit of frames), every executed `simctl` command, and each capture's size and alpha state. Local paths are replaced with `<run>` / `<repository>`. |
| `screenshot-frames.jpg` | One raw capture and four composed frames, downscaled for the README. |
| `SHA256SUMS` | Checksums of the two files above. |

Inputs: [`examples/screenshot-pipeline`](../../examples/screenshot-pipeline/README.md) (`PlannerDemoApp.swift`,
`plan.json`, `captions.json`). Regenerate with the commands in that README, then
`python3 scripts/render_evidence_gallery.py`.

Scope: a controlled demo app, not a customer project. The frames are marketing compositions of real captures.
No build was uploaded to App Store Connect. Full-size captures and frames are not committed.
