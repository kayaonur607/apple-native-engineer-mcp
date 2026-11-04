# Privacy, Security & Data Protection Engineering

On Apple platforms, privacy is treated as a fundamental human right and a core engineering requirement. Applications that fail to properly protect user data, neglect privacy manifests, or provide vague permission strings face immediate App Store rejection or regulatory liability.

> **Disclaimer**: This document provides technical and architectural engineering guidance based on Apple's published developer documentation. It does not constitute formal legal advice. Teams should consult qualified legal counsel for statutory compliance (such as GDPR, CCPA, or COPPA).

---

## 1. Privacy Manifests (`PrivacyInfo.xcprivacy`)

Starting in Spring 2024, Apple requires all apps and third-party SDKs to include a **Privacy Manifest** (`PrivacyInfo.xcprivacy`) declaring the types of data collected, tracking domains, and usage of **Required-Reason APIs**.

### A. Required-Reason API Categories
Apple audits binaries for calls to specific system APIs. If your app or any dependency calls these APIs, you must declare an approved reason code:

| API Category | Common Functions | Required Reason Key | Example Approved Reason |
| :--- | :--- | :--- | :--- |
| **User Defaults** | `UserDefaults.standard` | `NSPrivacyAccessedAPICategoryUserDefaults` | `CA92.1`: Access within app to store app-specific state. |
| **File Timestamps** | `URLResourceValues.contentModificationDate`, `stat` | `NSPrivacyAccessedAPICategoryFileTimestamp` | `C617.1`: Access within app to determine file freshness. |
| **System Boot Time** | `systemUptime`, `mach_absolute_time` | `NSPrivacyAccessedAPICategorySystemBootTime` | `35F9.1`: Measure time elapsed between app events. |
| **Disk Space** | `volumeAvailableCapacityKey`, `statfs` | `NSPrivacyAccessedAPICategoryDiskSpace` | `E174.1`: Check whether adequate space exists before downloading. |

### B. Sample `PrivacyInfo.xcprivacy` XML File
Place this file in your app's root bundle:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSPrivacyTracking</key>
    <false/>
    <key>NSPrivacyTrackingDomains</key>
    <array/>
    <key>NSPrivacyCollectedDataTypes</key>
    <array>
        <dict>
            <key>NSPrivacyCollectedDataType</key>
            <string>NSPrivacyCollectedDataTypeUserID</string>
            <key>NSPrivacyCollectedDataTypeLinked</key>
            <true/>
            <key>NSPrivacyCollectedDataTypeTracking</key>
            <false/>
            <key>NSPrivacyCollectedDataTypePurposes</key>
            <array>
                <string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string>
            </array>
        </dict>
    </array>
    <key>NSPrivacyAccessedAPITypes</key>
    <array>
        <dict>
            <key>NSPrivacyAccessedAPIType</key>
            <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
            <key>NSPrivacyAccessedAPITypeReasons</key>
            <array>
                <string>CA92.1</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
```

---

## 2. Permission Requests & `Info.plist` Usage Descriptions

Apple requires explicit purpose strings before accessing protected sensors or hardware (Camera, Microphone, Photo Library, Location, Bluetooth, Health, Contacts).

### Rules for Usage Descriptions:
1. **Explain the specific benefit to the user**: State *why* the access is needed for the user's workflow, not just what the technical component is.
2. **Never leave empty or generic strings**: Descriptions like "App needs camera access" or "Location required" result in immediate App Store rejection.
3. **Request Just-in-Time**: Never request permissions on app launch. Trigger the permission prompt only when the user taps an action that requires it (e.g., tapping "Scan Barcode").

```xml
<!-- ❌ REJECTED: Vague, lazy, unhelpful -->
<key>NSCameraUsageDescription</key>
<string>This app requires camera access.</string>

<!-- ✅ APPROVED: Clear, user-focused benefit -->
<key>NSCameraUsageDescription</key>
<string>We use your camera to scan physical invoice barcodes and upload receipts directly into your expense ledger.</string>
```

---

## 3. App Tracking Transparency (ATT)

If your app links user data collected from your app with third-party data for targeted advertising or shares data with a data broker, you **must** implement the App Tracking Transparency framework:

```swift
import AppTrackingTransparency
import AdSupport

func requestTrackingPermission() async {
    // Only prompt after explaining context to the user
    let status = await ATTrackingManager.requestTrackingAuthorization()
    switch status {
    case .authorized:
        let idfa = ASIdentifierManager.shared().advertisingIdentifier
        enableTargetedAnalytics(idfa)
    case .denied, .restricted, .notDetermined:
        disableThirdPartyTracking()
    @unknown default:
        disableThirdPartyTracking()
    }
}
```

*Note: If your app does not track users across other companies' apps and websites, set `NSPrivacyTracking` to `false` in your privacy manifest and do not prompt for ATT.*

---

## 4. Secure Storage: Keychain Services vs. UserDefaults

Never store passwords, authentication tokens, API keys, or personally identifiable information (PII) in `UserDefaults` or unencrypted SQLite databases. `UserDefaults` is stored in plaintext on disk and is included in unencrypted device backups.

### Secure Keychain Wrapper Implementation

```swift
import Foundation
import Security

public enum KeychainManager {
    
    public enum KeychainError: Error {
        case itemNotFound
        case duplicateItem
        case unexpectedStatus(OSStatus)
    }
    
    public static func save(token: String, forService service: String, account: String) throws {
        guard let data = token.data(using: .utf8) else { return }
        
        // Delete existing item if present
        let deleteQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account
        ]
        SecItemDelete(deleteQuery as CFDictionary)
        
        // Add new item with strict hardware security
        let addQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecValueData as String: data,
            // Accessible only after first device unlock, not migrated to other devices
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        ]
        
        let status = SecItemAdd(addQuery as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw KeychainError.unexpectedStatus(status)
        }
    }
    
    public static func read(service: String, account: String) throws -> String {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data, let token = String(data: data, encoding: .utf8) else {
            throw KeychainError.itemNotFound
        }
        return token
    }
}
```

---

## 5. Mandatory Account Deletion (Guideline 5.1.1(v))

If your application supports account creation, Apple **mandates** that users must also be able to initiate account deletion directly within the app:

- The deletion option must be easy to find (typically in Account / Privacy settings).
- Simply providing an email address to request deletion or linking to a generic website form is often rejected unless the website directly performs the deletion.
- It must delete all personal data associated with the account, or clearly explain what records must be legally retained (e.g., financial audit records).

```swift
Section("Account Management") {
    Button(role: .destructive) {
        showDeleteAccountConfirmation = true
    } label: {
        Label("Delete Account", systemImage: "person.crop.circle.badge.minus")
    }
}
.confirmationDialog(
    "Delete Account Permanently?",
    isPresented: $showDeleteAccountConfirmation,
    titleVisibility: .visible
) {
    Button("Permanently Delete Account & Data", role: .destructive) {
        Task {
            await accountViewModel.deleteAccount()
        }
    }
    Button("Cancel", role: .cancel) { }
} message: {
    Text("This will permanently remove your profile, purchase history, and all stored data. This action cannot be reversed.")
}
```

---

## 6. Official Apple References
- [Apple Developer - App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/)
- [Apple Developer - Describing Data Use in Privacy Manifests](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files)
- [Apple Developer - Keychain Services](https://developer.apple.com/documentation/security/keychain_services)
