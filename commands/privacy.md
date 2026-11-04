# `/apple-native-privacy` — Privacy, Manifests & Permissions Audit

Audits privacy manifests, Required-Reason APIs, `Info.plist` permission descriptions, and Keychain security.

---

## Agent Execution Steps

1. **Automated Audit**:
   Execute the privacy auditor tool:
   ```bash
   python3 tools/privacy-auditor/audit_privacy.py . --json
   ```

2. **Required-Reason APIs**:
   Cross-reference detected calls (User Defaults, File Timestamps, System Boot Time, Disk Space) against declared reasons in `PrivacyInfo.xcprivacy`.

3. **Sensor Permissions**:
   Audit `Info.plist` usage descriptions (`NSCameraUsageDescription`, `NSLocationWhenInUseUsageDescription`) to ensure clear, user-focused explanations.

4. **Secure Storage**:
   Verify sensitive authentication tokens and passwords are saved in Keychain Services (`kSecClassGenericPassword`), never in `UserDefaults`.
