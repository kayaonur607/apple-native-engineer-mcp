# Screenshot pipeline example

A controlled demo app and the exact inputs used for the recorded run in
[`assets/evidence`](../../assets/evidence/README.md).

```bash
# 1. Build the demo app for the iOS Simulator (Xcode required)
mkdir -p .swiftwork/PlannerDemo.app
xcrun swiftc -parse-as-library -sdk "$(xcrun --sdk iphonesimulator --show-sdk-path)" \
  -target arm64-apple-ios18.0-simulator examples/screenshot-pipeline/PlannerDemoApp.swift \
  -o .swiftwork/PlannerDemo.app/PlannerDemo
# …plus an Info.plist with CFBundleIdentifier dev.applenative.plannerdemo (see scripts/capture-runtime-proof.py)

# 2. Capture: 3 device sizes × 2 locales × light/dark × 2 screens = 24 real captures
python3 tools/screenshot-studio/capture_batch.py examples/screenshot-pipeline/plan.json --out .swiftwork/shots

# 3. Compose localized frames and render App Store-ready PNGs natively
python3 tools/screenshot-studio/compose_marketing.py --screenshots .swiftwork/shots --out .swiftwork/frames \
  --captions examples/screenshot-pipeline/captions.json --theme blue --render

# 4. Audit the upload set
python3 tools/screenshot-studio/screenshot_studio.py --screenshots .swiftwork/frames --platforms ios,ipados
```

The app reads `-screen <name>` to open a screen directly and takes its language from the
`-AppleLanguages`/`-AppleLocale` arguments the capture tool passes — the two hooks any real app needs for
automated App Store captures.
