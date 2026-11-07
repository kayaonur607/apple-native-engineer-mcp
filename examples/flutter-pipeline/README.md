# Flutter pipeline example

The Flutter app behind the recorded run in [`assets/evidence/flutter-run.json`](../../assets/evidence/flutter-run.json):
`main.dart` (the whole app), `plan.json` (capture plan) and `captions.json` (localized marketing copy).

```bash
# 1. Create the host project and add the app
flutter create --org dev.applenative --project-name habits_demo --platforms ios .swiftwork/flutter-demo
cp examples/flutter-pipeline/main.dart .swiftwork/flutter-demo/lib/main.dart
cd .swiftwork/flutter-demo
flutter pub add flutter_localizations --sdk=flutter
flutter pub add shared_preferences
cd -

# 2. Audit: on Flutter 3.44.8 + Xcode 27.2 the fresh template reports XPL020 (deployment target 13.0 < 15.0)
#    and FLT009 (Turkish missing from knownRegions)
python3 tools/cross-platform-auditor/audit_cross_platform.py .swiftwork/flutter-demo

# 3. Fix both in ios/Runner.xcodeproj (IPHONEOS_DEPLOYMENT_TARGET = 15.0; Runner › Info › Localizations › + Turkish)
#    then build for the Simulator
(cd .swiftwork/flutter-demo && flutter build ios --simulator)

# 4. Capture, compose, audit
python3 tools/screenshot-studio/capture_batch.py examples/flutter-pipeline/plan.json --out .swiftwork/evidence-flutter/shots
python3 tools/screenshot-studio/compose_marketing.py --screenshots .swiftwork/evidence-flutter/shots \
  --out .swiftwork/evidence-flutter/frames --captions examples/flutter-pipeline/captions.json --theme graphite --render
python3 tools/screenshot-studio/screenshot_studio.py --screenshots .swiftwork/evidence-flutter/frames --platforms ios
```

Screens are selected with the `-screen` launch argument, read by `SharedPreferencesAsync` from the NSUserDefaults
argument domain. Environment variables and custom-scheme deep links were tried and rejected; see
[references/flutter-apple-native.md](../../references/flutter-apple-native.md#4-screenshots).
