---
description: "Produce App Store screenshots from the real app: plan, capture in the Simulator across devices, locales and appearances, compose localized frames, and audit the upload set."
---

# `/apple-native-screenshots` — App Store screenshot production

Real screens only. Compositions are labelled as marketing frames; captures are never edited to show features the
app does not have (Guideline 2.3).

## 1. What is required

`get_app_store_specs` with the app's platforms. Read `apple-native://references/app-store-product-page-assets`.
Choose the minimum device set (e.g. `iphone-6.9`, `iphone-6.3`, `ipad-13`), the locales the listing ships in, and
whether light or dark shows the content best.

## 2. Prepare the app (with the developer's approval)

- A launch argument per screen (`-screen today`) that routes directly to it.
- Deterministic, realistic demo data behind a flag (`-UITestScreenshotMode YES`); no lorem ipsum, no real
  personal data.
- Locale read from the system (the tool passes `-AppleLanguages` and `-AppleLocale`).
- Build for the Simulator: `xcodebuild -scheme <App> -destination 'generic/platform=iOS Simulator'
  -derivedDataPath build build`.

## 3. Capture

1. Write `plan.json` (bundle_id, app, devices, locales, appearances, screens).
2. `capture_screenshots dry_run=true`; show the commands.
3. `capture_screenshots`; then open several images and check them visually (content, clipping, translations).
4. `audit_screenshots platforms=[…]` on the capture folder.

## 4. Compose and finish

1. Write `captions.json`: one benefit per frame, verb-first, short; translated by meaning, reviewed by a native
   speaker. Right-to-left locales are laid out automatically.
2. `compose_marketing_screenshots captions=… frame="auto" render=true` (theme to match the brand).
3. Fix `SHOT115` (fallback copy) and `SHOT119` (copy too long); look at the PNGs.
4. `audit_screenshots` on the final folder; the upload set must have no errors.

## Report

Answer in the user's language with: outcome · files changed · checks actually run (tool + finding codes, build
command and result, simulator/device runs) · Apple sources with URLs · what remains unverified · next action.
Static findings are not a build; a build is not a runtime check; neither is App Review approval.
