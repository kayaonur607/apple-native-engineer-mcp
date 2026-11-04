# Widget & Dynamic Island Validator

Audits WidgetKit bundles and ActivityKit Live Activities for missing Dynamic Island presentation states and required `Info.plist` entitlements.

---

## Capabilities

1. **Dynamic Island Completeness**: Confirms `compactLeading`, `compactTrailing`, and `minimal` presentations are defined.
2. **Entitlement Verification**: Verifies `NSSupportsLiveActivities` is configured in `Info.plist` when `ActivityAttributes` models are detected.
3. **Widget Protocol Detection**: Identifies widgets and live activity lifecycles across codebase.
4. **JSON Reporting**: Structured outputs ready for CI and agent consumption.

---

## Usage

```bash
# Terminal audit
python3 tools/widget-validator/validate_widget.py --project-dir /path/to/project

# JSON output
python3 tools/widget-validator/validate_widget.py --project-dir /path/to/project --json
```
