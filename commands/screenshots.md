# `/apple-native-screenshots` — App Store Screenshot Studio & Validation

Captures, composes, and validates App Store screenshots from actual running applications.

---

## Agent Execution Steps

1. **Feature Identification**:
   Inspect the application to identify the 3 to 5 strongest user flows and screens.

2. **Actual Screenshot Capture**:
   Capture unscaled screenshots directly from booted iOS Simulators using `xcrun simctl`:
   ```bash
   python3 tools/screenshot-studio/screenshot_studio.py --capture screenshots/ios/01_dashboard.png
   ```

3. **Display Specification Validation**:
   Validate that captured assets match Apple's required dimensions (6.7" iPhone, 6.5" iPhone, 13" iPad):
   ```bash
   python3 tools/screenshot-studio/screenshot_studio.py --audit screenshots/
   ```

4. **Marketing Composition**:
   Apply clean typography, consistent margins, and short benefit-driven headlines aligned with `templates/screenshot-layouts/spec.json`.
