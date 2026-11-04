# Privacy & Required-Reason API Auditor Tool

Audits an Apple platform project for compliance with Apple's privacy mandates:
- Scans Swift and Objective-C codebases for calls to **Required-Reason APIs** (`UserDefaults`, `stat`, `mach_absolute_time`, `statfs`).
- Parses `PrivacyInfo.xcprivacy` and cross-references detected APIs against declared reasons.
- Inspects `Info.plist` sensor permission strings (`NSCameraUsageDescription`, `NSLocationWhenInUseUsageDescription`, etc.) to flag vague, generic phrasing.

---

## Usage

```bash
# Audit the current project workspace
./tools/privacy-auditor/audit_privacy.py

# Audit a specific target repository
./tools/privacy-auditor/audit_privacy.py /path/to/my-ios-app

# JSON output for CI pipelines or MCP agents
./tools/privacy-auditor/audit_privacy.py /path/to/my-ios-app --json
```
