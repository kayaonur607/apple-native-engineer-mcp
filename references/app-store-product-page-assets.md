# App Store Product Page Assets: Screenshots, Previews and Icons

> **Authority**: [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications),
> [App preview specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/app-preview-specifications),
> [HIG — App icons](https://developer.apple.com/design/human-interface-guidelines/app-icons).
> Transcribed 2026-11-07 into `data/app-store-specs.json`, the single source the tools read. Call
> `get_app_store_specs` for the current table rather than copying numbers from memory.

The product page is the first screen of the app. Treat it as product design: real screens, one idea per frame,
copy that reads natively in every locale, and pixel-exact files App Store Connect accepts on the first upload.

---

## 1. Screenshot rules that cause rejected uploads

| Rule | Value | Checked by |
| :--- | :--- | :--- |
| Formats | PNG, JPEG | `audit_screenshots` |
| Alpha / transparency | **Not allowed** — Simulator PNGs include alpha; flatten them | `SHOT013`, `CAP032` (capture flattens automatically) |
| Per device size and locale | 1–10 | `SHOT021` |
| Exact pixel size | One of the slot sizes | `SHOT011` |
| Watch | One size used consistently in every localization | `SHOT023` |

## 2. Required sets

| Platform | Required | Capture on |
| :--- | :--- | :--- |
| iPhone | At least one **Dynamic Island (medium)** set — 1206×2622 or 1179×2556 — and a **6.9″ (1320×2868, 1290×2796, 1260×2736) or 6.5″ (1284×2778, 1242×2688)** set | iPhone 18 Pro, iPhone 18 Pro Max |
| iPhone Duo | Outer 1398×2034 and inner 2007×2853, from April 2027 for apps built with the iOS 27.1 SDK+ | iPhone Duo |
| iPad | **13″** — 2064×2752 or 2048×2732 — when the app runs on iPad | iPad Pro 13-inch (M5) |
| Mac | 16:10 — 2880×1800, 2560×1600, 1440×900 or 1280×800 | Mac (window capture) |
| Apple TV | 3840×2160 or 1920×1080 | Apple TV 4K |
| Apple Vision Pro | 3840×2160 | Apple Vision Pro |
| Apple Watch | One of 422×514, 410×502, 416×496, 396×484, 368×448, 312×390 | Apple Watch Ultra 3 / Series 11 |

When the UI is identical across sizes, App Store Connect scales the highest required resolution down; it still
shows which sets it requires — confirm there before submitting.

## 3. Previews (video)

15–30 seconds, up to 3 per size and locale, ≤500 MB, ≤30 fps, H.264 (10–12 Mbps, .mov/.m4v/.mp4) or ProRes 422 HQ
(.mov), stereo audio. iPhone Dynamic Island/Face ID sizes use **886×1920**; iPad uses 1200×1600; Mac and Apple TV
1920×1080 landscape; Vision Pro 3840×2160. Previews play before screenshots. Record with
`xcrun simctl io <device> recordVideo` and edit to length — never stage features the app does not have.

## 4. Icons

| Platform | Canvas | Shape after masking | Format |
| :--- | :--- | :--- | :--- |
| iOS, iPadOS, macOS | 1024×1024 | Rounded rectangle | Icon Composer `.icon` (layered, Liquid Glass; default, dark, clear, tinted) or flat PNG |
| watchOS | 1088×1088 | Circle | Icon Composer `.icon` or PNG |
| visionOS | 1024×1024 | Circle, 3D | Image stack: background + 1–2 layers |
| tvOS | 800×480 | Rounded rectangle | Parallax image stack, 2–5 layers |

Provide unmasked layers; never bake in highlights, shadows, bevels or blur. Keep content centred for circular
masks. A flat PNG is segmented by the system into two layers; supply an `.icon` to control which elements get
Liquid Glass. Alternate iOS icons need their own dark, clear and tinted variants.

---

## 5. The production pipeline

```text
get_app_store_specs ─▶ capture_screenshots ─▶ audit_screenshots ─▶ compose_marketing_screenshots ─▶ audit_screenshots
   (what is required)     (real Simulator)      (raw captures)        (localized frames, PNG)          (final upload set)
```

1. **Prepare the app for capture.** Add launch arguments that route to each screen (`-screen today`) and seed
   deterministic demo data behind a flag (`-UITestScreenshotMode YES`). Read locale from the system — the capture
   tool passes `-AppleLanguages` and `-AppleLocale`. Example: `examples/screenshot-pipeline/PlannerDemoApp.swift`.
2. **Plan** (`plan.json`):

```json
{
  "bundle_id": "com.example.planner",
  "app": "build/Build/Products/Debug-iphonesimulator/Planner.app",
  "devices": ["iphone-6.9", "iphone-6.3", "ipad-13"],
  "locales": ["en-US", "tr-TR", "de-DE", "ar-SA"],
  "appearances": ["light"],
  "launch_arguments": ["-UITestScreenshotMode", "YES"],
  "screens": [
    {"name": "01-today", "arguments": ["-screen", "today"]},
    {"name": "02-insights", "arguments": ["-screen", "insights"]}
  ]
}
```

3. **Dry run**, show the commands, then capture. Each file lands in `<out>/<locale>/<device>/<screen>.png` with a
   9:41 status bar, full battery and signal, flattened to opaque RGB, recorded in `manifest.json`.
4. **Write captions per locale** (`captions.json`). One benefit per frame, verb-first, ≤ ~30 characters for the
   headline. Translate meaning, not words; have a native speaker review. Arabic, Hebrew, Persian and Urdu frames are
   laid out right-to-left automatically.

```json
{
  "en-US": {"01-today": {"headline": "Plan your day in a minute", "subhead": "Focus, done and up next"}},
  "tr-TR": {"01-today": {"headline": "Gününü bir dakikada planla", "subhead": "Odak, tamamlananlar, sıradakiler"}},
  "*":     {"*": {"headline": "Made for focus"}}
}
```

5. **Compose** with `render: true`. On macOS the PNG is drawn natively (CoreGraphics, San Francisco, CoreText line
   breaking) at the exact slot size without alpha; SVGs stay editable for designers. `SHOT115` lists frames that fell
   back to another language; `SHOT119` lists captions that did not fit.
6. **Audit the final folder** with the platforms you ship: `audit_screenshots platforms=["iOS","iPadOS"]`.

## 6. Creative guidance

- **The first three frames carry the page**: lead with the core job, then the differentiator, then trust
  (privacy, widgets, Apple Watch, accessibility).
- Show the real app in its best real state: populated, not empty; no lorem ipsum; no placeholder names.
- Keep one visual system across frames: same theme, same caption position, consistent device framing.
- Light and dark sets are both valid — choose the one that best shows the content, and keep it consistent.
- Do not imitate Apple hardware marketing, use Apple trademarks as decoration, or show features you do not ship
  (Guideline 2.3). The drawn device frame here is a neutral generic bezel, not Apple product artwork.
- Custom Product Pages and In-App Events reuse these assets: keep the source plan and captions in the repository.
