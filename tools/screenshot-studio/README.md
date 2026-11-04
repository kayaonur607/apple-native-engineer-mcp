# Screenshot Studio Tool

Tool for capturing, validating, and organizing App Store screenshots:
- **Simulator Capture**: Directly captures screenshots from booted Xcode iOS/iPadOS simulators using `xcrun simctl`.
- **Set Validation**: Scans an entire directory of screenshots to verify compliance with required display dimensions (iPhone 6.7", 6.5", iPad 13").
- **Audit Breakdown**: Reports image count per device class and flags unsupported aspect ratios.

---

## Usage

```bash
# Capture screenshot from booted iOS Simulator
./tools/screenshot-studio/screenshot_studio.py --capture screenshots/ios/home_6_7.png

# Audit an existing directory of screenshots
./tools/screenshot-studio/screenshot_studio.py --audit /path/to/screenshots

# Output JSON report
./tools/screenshot-studio/screenshot_studio.py --audit /path/to/screenshots --json
```
