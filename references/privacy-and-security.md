# Privacy, Security & Data Protection Engineering

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.
> **Authority**: [Privacy manifest files](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files), [Describing use of required reason API](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api), [App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/)

Three separate jobs get conflated under "privacy": declaring what the binary touches (`PrivacyInfo.xcprivacy`), asking permission (ATT, usage strings), and protecting what you store (Keychain, CryptoKit, ATS). Each one has a mechanical check, and each check runs locally.

> **Not legal advice.** This is engineering guidance. GDPR, CCPA and COPPA obligations are for counsel.

---

## 1. Privacy manifest (`PrivacyInfo.xcprivacy`)

One file per target, plus one per bundled SDK. It declares tracking, tracking domains, collected data types, and required-reason API usage. The abridged manifest below is valid as written; add collected-data dictionaries under `NSPrivacyCollectedDataTypes` using keys of the form `NSPrivacyCollectedDataType<Type>`, `…DataTypeLinked`, `…DataTypeTracking`, `…DataTypePurposes`.

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
    <array/>
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

Generate it with **File ▸ New ▸ File ▸ Privacy Manifest** rather than typing XML. A malformed plist is `PRIV002` in the auditor and blocks upload.

Every linked third-party SDK ships its own manifest, and App Store Connect merges them with yours. So do not copy an SDK's codes into your own manifest (duplicates hide a missing file), and audit the merged result — an SDK declaring `CA92.1` while it actually writes shared defaults is a failure you inherit. Prefer SDK versions that ship a manifest over ones that need a justification in review notes.

---

## 2. Required-reason APIs and the codes that are valid

Apple rejects an upload when the binary calls a required-reason API and the manifest omits the category or names a code that does not exist. This table is the validity set enforced by `tools/privacy-auditor/audit_privacy.py`; it is the source of truth for this guide.

| Category | Detected calls | Valid reason codes |
| :--- | :--- | :--- |
| `NSPrivacyAccessedAPICategoryUserDefaults` | `UserDefaults`, `@AppStorage`, `NSUbiquitousKeyValueStore` | `CA92.1` app-only defaults · `1C8F.1` app group shared with extensions · `AC6B.1` managed configuration profile · `C56D.1` defaults written by a third-party SDK |
| `NSPrivacyAccessedAPICategoryFileTimestamp` | `attributesOfItem`, `creationDate`, `contentModificationDate`, `fileModificationDate`, `stat(` | `C617.1` files inside the container, app group or CloudKit container · `3B52.1` files the user explicitly granted · `0A2A.1` files outside the container (third-party SDK) |
| `NSPrivacyAccessedAPICategorySystemBootTime` | `systemUptime`, `mach_absolute_time`, `clock_gettime` | `35F9.1` elapsed time between events · `8FFB.1` absolute timestamps within one boot · `3D61.1` show boot time to the user |
| `NSPrivacyAccessedAPICategoryDiskSpace` | `volumeAvailableCapacityKey`, `volumeTotalCapacityKey`, `attributesOfFileSystem`, `NSFileSystemFreeSize` | `E174.1` free space before writing app-managed files · `85F4.1` show storage usage · `7D9E.1` write files the user asked to store · `B728.1` assess space for a user-requested feature |
| `NSPrivacyAccessedAPICategoryActiveKeyboards` | `activeInputModes` | `3EC4.1` adapt UI to the active keyboard language · `54BD.1` adapt custom text input |

Correction against the previous revision of this guide: it listed one code per category and omitted `ActiveKeyboards` entirely. Under-declaring fails the same way as declaring nothing, so the full sets above are now the only ones written down here.

The auditor's other findings: `PRIV001` no manifest · `PRIV002` unparseable manifest · `PRIV010` category used but not declared · `PRIV011` code that does not exist · `PRIV012` empty reason list · `PRIV013` unknown category (usually a typo) · `PRIV014` declared but unused · `PRIV020` tracking API while `NSPrivacyTracking` is `false` · `PRIV021` empty `NSPrivacyTrackingDomains` with tracking signals present · `PRIV022` data-collecting API with empty `NSPrivacyCollectedDataTypes`.

---

## 3. App Tracking Transparency

Tracking means linking your app's data with third-party data for advertising, or sharing it with a data broker. If you do either, `NSUserTrackingUsageDescription` is required and the prompt must run before any identifier is read.

```swift
import AdSupport
import AppTrackingTransparency

@MainActor
func trackingIdentifier() async -> String? {
    let status = await ATTrackingManager.requestTrackingAuthorization()
    guard status == .authorized else { return nil }
    return ASIdentifierManager.shared().advertisingIdentifier.uuidString
}
```

- The prompt shows **once**. To retest, delete the app or use Settings ▸ Privacy & Security ▸ Tracking.
- On iOS 27.2 in the EU, `ATTrackingManager.requestTrackingAuthorization(preferringExpandedInterface:additionalInformationAction:completionHandler:)` renders an expanded prompt and can use `NSUserTrackingMarkdownUsageDescription`. Guard with `if #available(iOS 27.2, *)` and keep the plain call as fallback.
- No tracking means `NSPrivacyTracking` stays `false` and the API is never called. Prompting for permission you do not need is a 5.1.2 problem, not a courtesy.

---

## 4. Keychain, not UserDefaults

`UserDefaults` is a plist in the app container: plaintext on disk, included in backups. Tokens, passwords and API keys belong in the Keychain.

```swift
import Foundation
import Security

enum KeychainError: Error {
    case encodingFailed
    case unexpectedStatus(OSStatus)
}

struct KeychainStore {
    let service: String

    func save(_ token: String, account: String) throws {
        guard let data = token.data(using: .utf8) else { throw KeychainError.encodingFailed }
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(query as CFDictionary)

        var attributes = query
        attributes[kSecValueData as String] = data
        attributes[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly

        let status = SecItemAdd(attributes as CFDictionary, nil)
        guard status == errSecSuccess else { throw KeychainError.unexpectedStatus(status) }
    }
}
```

Reading is the same query plus `kSecReturnData: true` and `kSecMatchLimit: kSecMatchLimitOne`, then `SecItemCopyMatching(query, &item)` and a cast to `Data`.

- `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` survives a background relaunch but never migrates to a new device through a backup. `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` is stricter — use it when the secret is only needed while the user is present.
- Delete-then-add is not atomic. For concurrent writers, call `SecItemUpdate` first and `SecItemAdd` only on `errSecItemNotFound`.

---

## 5. CryptoKit and the Secure Enclave

Encrypt payloads with `AES.GCM`; keep the key where the app cannot read it.

```swift
import CryptoKit
import Foundation
import Security

func seal(_ plaintext: Data, using key: SymmetricKey) throws -> Data {
    let box = try AES.GCM.seal(plaintext, using: key)
    guard let combined = box.combined else { throw KeychainError.encodingFailed }
    return combined
}

func makeDeviceSigningKey() throws -> SecureEnclave.P256.Signing.PrivateKey {
    let access = SecAccessControlCreateWithFlags(
        nil, kSecAttrAccessibleWhenUnlockedThisDeviceOnly, [.privateKeyUsage, .userPresence], nil
    )!
    return try SecureEnclave.P256.Signing.PrivateKey(accessControl: access)
}
```

The Secure Enclave key never leaves the device: signing happens in hardware, and `.userPresence` forces Face ID, Touch ID or the passcode before each use. `combined` is nonce + ciphertext + tag — store that, not the parts.

---

## 6. Face ID and Touch ID with `LAContext`

```swift
import LocalAuthentication

func authenticateForVault() async throws -> Bool {
    let context = LAContext()
    var error: NSError?
    guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
        return false        // no biometry enrolled — fall back to a passcode policy if the feature allows it
    }
    return try await context.evaluatePolicy(
        .deviceOwnerAuthenticationWithBiometrics,
        localizedReason: "Unlock your saved expense reports."
    )
}
```

`NSFaceIDUsageDescription` is required for the biometric prompt. Use `.deviceOwnerAuthentication` when the feature must also work on a device with no enrolled biometry, and `context.localizedCancelTitle` when the system's cancel label is wrong for your UI.

---

## 7. App Transport Security and certificate pinning

ATS blocks cleartext HTTP by default; keep it that way and add exceptions per domain (`NSExceptionDomains` → `NSExceptionMinimumTLSVersion`, `NSIncludesSubdomains`), never globally. `NSAllowsArbitraryLoads` is both a review flag and an attack surface: if a host cannot do TLS 1.2, replace the host.

Pinning is worth its maintenance cost only for high-value endpoints. Pin the leaf certificate's SHA-256 and ship at least two hashes so a rotation does not brick the app.

```swift
import CryptoKit
import Foundation
import Security

final class PinnedSessionDelegate: NSObject, URLSessionDelegate {
    private let pinnedHashes: Set<String>

    init(pinnedHashes: Set<String>) { self.pinnedHashes = pinnedHashes }

    func urlSession(_ session: URLSession,
                    didReceive challenge: URLAuthenticationChallenge) async
    -> (URLSession.AuthChallengeDisposition, URLCredential?) {
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let trust = challenge.protectionSpace.serverTrust else {
            return (.performDefaultHandling, nil)
        }

        var error: CFError?
        guard SecTrustEvaluateWithError(trust, &error),
              let chain = SecTrustCopyCertificateChain(trust) as? [SecCertificate],
              let leaf = chain.first else {
            return (.cancelAuthenticationChallenge, nil)
        }

        let der = SecCertificateCopyData(leaf) as Data
        let hash = Data(SHA256.hash(data: der)).base64EncodedString()
        return pinnedHashes.contains(hash)
            ? (.useCredential, URLCredential(trust: trust))
            : (.cancelAuthenticationChallenge, nil)
    }
}
```

`SecTrustEvaluateWithError` must run before you read the chain, or you are trusting an unvalidated chain. Subject-public-key pinning survives certificate renewal but requires DER-wrapping the key yourself.

---

## 8. Account deletion (5.1.1(v))

If users can create an account they must be able to delete it in the app — not by email, not through a marketing page. Delete the account, not just the device copy, and say in the confirmation what is retained for legal reasons (invoices, tax records) instead of keeping it silently. The pattern is a destructive `Button` in account settings, a `confirmationDialog` that names the consequence, and an `async` call that deletes server-side state before the local purge. [app-store-readiness.md](app-store-readiness.md) lists it in the pre-upload checklist.

---

## 9. Evidence

`python3 tools/privacy-auditor/audit_privacy.py .` enforces the manifest rules: it fails with `PRIV001`/`PRIV010`/`PRIV011` and warns `PRIV020`–`PRIV022`. The privacy-policy URL in metadata is checked by `validate_metadata.py` (`META004`, `META005`).

Full documentation index: [official-resources.md](official-resources.md). Key pages: [privacy manifests](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files), [required-reason API](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api), [Keychain Services](https://developer.apple.com/documentation/security/keychain_services), [Certificate, Key, and Trust Services](https://developer.apple.com/documentation/security/certificate_key_and_trust_services).
