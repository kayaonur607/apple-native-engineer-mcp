# Privacy & Security Review Checklist

Use this checklist to perform a comprehensive audit of privacy practices, permission usage, required-reason APIs, secure storage, and regulatory compliance.

---

## 1. Privacy Manifests & Required-Reason APIs
- [ ] **`PrivacyInfo.xcprivacy` Included**: A valid Privacy Manifest exists in the main app target bundle.
- [ ] **Required-Reason APIs Declared**: If the app or any third-party SDK accesses User Defaults, File Timestamps, System Boot Time, or Disk Space, an approved reason code is declared.
- [ ] **No Undisclosed Tracking**: If `NSPrivacyTracking` is set to `true`, tracking domains and purposes are accurately declared.
- [ ] **Third-Party SDK Manifests**: All embedded binary frameworks and SPM packages provide their own valid privacy manifests.

---

## 2. Sensor & Data Permissions (`Info.plist`)
- [ ] **User-Centric Purpose Strings**: Every requested capability (Camera, Location, Photos, Microphone, Contacts) provides a detailed, clear, and user-focused reason string in `Info.plist`.
- [ ] **No Generic Strings**: Generic phrases ("Required for app", "Needs access") are eliminated.
- [ ] **Just-In-Time Prompts**: Permission dialogs appear only when the user initiates a related action, never immediately on app launch.

---

## 3. Secure Storage & Credential Handling
- [ ] **Keychain for Secrets**: User authentication tokens, passwords, and sensitive keys are stored in the Keychain (`kSecClassGenericPassword`), never in `UserDefaults` or plaintext files.
- [ ] **Proper Keychain Accessibility**: Secrets use `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` to prevent unencrypted export during iCloud or device backups.
- [ ] **No Hardcoded API Secrets**: Production private keys and API tokens are loaded dynamically from environment configurations or secure servers.

---

## 4. Account Deletion & User Rights
- [ ] **In-App Account Deletion**: If the app supports user registration, users can initiate permanent account deletion directly within the app (Guideline 5.1.1(v)).
- [ ] **Complete Data Erasure**: Deletion removes all personal data and user-generated content from backend servers (or explains legal retention policies).

---

## 5. Network & Transport Security
- [ ] **App Transport Security (ATS)**: All network endpoints use HTTPS with TLS 1.3 or 1.2; arbitrary HTTP loads are disabled (`NSAllowsArbitraryLoads = false`).
- [ ] **No Sensitive Data in Logs**: Passwords, tokens, credit card numbers, and PII are scrubbed before logging with `os.Logger`.
