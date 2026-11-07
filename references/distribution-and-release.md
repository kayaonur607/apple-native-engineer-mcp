# Distribution: Signing, TestFlight, App Store and Notarization

> **Authority**: `xcodebuild -help` (Xcode 27.2, the source of every ExportOptions key below),
> [Distributing your app for beta testing and releases](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases),
> [Notarizing macOS software before distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution),
> [Complying with encryption export regulations](https://developer.apple.com/documentation/security/complying-with-encryption-export-regulations).
> Verified 2026-11-07 against Xcode 27.2 (`xcodebuild`, `altool` 27.10.4, `notarytool`, `stapler`).

Distribution is where engineering meets account state. Building and archiving are local and reversible; uploading,
notarizing and submitting are not. This server therefore **plans** distribution (`plan_distribution`) and the host
AI runs each step only with the developer's approval.

---

## 1. Choose the method

| Goal | `plan_distribution method` | ExportOptions `method` | Notes |
| :--- | :--- | :--- | :--- |
| App Store and external TestFlight | `app-store` | `app-store-connect` | Default. `destination` `export` or `upload` |
| Internal TestFlight only (PRs, branches) | `testflight-internal` | `app-store-connect` + `testFlightInternalTestingOnly` | Build can never reach external testers or the store |
| Registered test devices | `release-testing` | `release-testing` | Formerly `ad-hoc` |
| In-house (Enterprise Program) | `enterprise` | `enterprise` | Not for public distribution |
| Development build | `debugging` | `debugging` | Formerly `development` |
| macOS outside the Mac App Store | `developer-id` | `developer-id` | Requires Hardened Runtime and notarization |
| Mac App Store | `mac-app-store` | `app-store-connect` | Requires App Sandbox |

Deprecated spellings `app-store`, `ad-hoc` and `development` still parse in `xcodebuild` but should not be written
into new ExportOptions files.

---

## 2. Preflight — what actually stops uploads

| Check | Finding | Fix |
| :--- | :--- | :--- |
| Team set | `DST010` / `DST013` | One `DEVELOPMENT_TEAM` for every target in the upload |
| Version and build | `DST020` / `DST021` | `MARKETING_VERSION` (customer-visible) and a strictly increasing `CURRENT_PROJECT_VERSION` per version |
| Export compliance | `DST030` | Declare `ITSAppUsesNonExemptEncryption` (`NO` when only exempt encryption such as HTTPS is used). Otherwise every TestFlight build waits for a manual answer |
| Hardened Runtime | `DST040` | `ENABLE_HARDENED_RUNTIME = YES` — the notary service rejects apps without it |
| App Sandbox | `DST041` | `com.apple.security.app-sandbox` for the Mac App Store |
| Debug entitlements | `DST042` | Remove `get-task-allow` from distribution entitlements |
| Privacy manifest | `DST050` | `PrivacyInfo.xcprivacy` covering required-reason APIs (`audit_privacy_manifest`) |
| App icon | `DST051` | A 1024 px App Store icon (`prepare_icon_assets`) or Icon Composer `.icon` |
| Shared scheme | `DST012` | Share the scheme so CI can archive |

---

## 3. The command sequence

Credentials come from the environment — the same variables `app_store_connect` reads:
`ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_PRIVATE_KEY_PATH` (an App Store Connect API key, `.p8`). Never paste key
material into chat or commit it.

```bash
# 1. Archive (local; -allowProvisioningUpdates may create or refresh signing assets)
xcodebuild archive -project App.xcodeproj -scheme App -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/App.xcarchive \
  -allowProvisioningUpdates -authenticationKeyPath "$ASC_PRIVATE_KEY_PATH" \
  -authenticationKeyID "$ASC_KEY_ID" -authenticationKeyIssuerID "$ASC_ISSUER_ID"

# 2a. Export and upload in one step (ExportOptions destination = upload)  ← changes account state
xcodebuild -exportArchive -archivePath build/App.xcarchive -exportPath build/export \
  -exportOptionsPlist ExportOptions.plist -allowProvisioningUpdates \
  -authenticationKeyPath "$ASC_PRIVATE_KEY_PATH" -authenticationKeyID "$ASC_KEY_ID" \
  -authenticationKeyIssuerID "$ASC_ISSUER_ID"

# 2b. …or export, validate, then upload with altool
xcrun altool --validate-app build/export/App.ipa --api-key "$ASC_KEY_ID" --api-issuer "$ASC_ISSUER_ID"
xcrun altool --upload-package build/export/App.ipa --api-key "$ASC_KEY_ID" --api-issuer "$ASC_ISSUER_ID" --wait
```

`altool --api-key` looks for `AuthKey_<KEY_ID>.p8` in `./private_keys`, `~/private_keys`, `~/.private_keys`,
`~/.appstoreconnect/private_keys` or `$API_PRIVATE_KEYS_DIR`.

After upload, confirm processing with `app_store_connect operation=builds` (read-only). Processing usually takes
minutes; a build is not testable until it finishes.

### Developer ID (macOS outside the store)

```bash
ditto -c -k --keepParent build/export/App.app build/export/App.zip
xcrun notarytool submit build/export/App.zip --key "$ASC_PRIVATE_KEY_PATH" \
  --key-id "$ASC_KEY_ID" --issuer "$ASC_ISSUER_ID" --wait      # ← uploads to Apple
xcrun stapler staple build/export/App.app                      # ticket for offline Gatekeeper
spctl --assess --type execute -vv build/export/App.app         # must say: accepted, Notarized Developer ID
```

On rejection, read the log: `xcrun notarytool log <submission-id> --key … --key-id … --issuer …`. Ship a DMG by
creating it with `hdiutil create … -format UDZO`, then notarize and staple the DMG as well.

---

## 4. ExportOptions.plist keys (Xcode 27.2)

| Key | Use |
| :--- | :--- |
| `method` | `app-store-connect`, `release-testing`, `enterprise`, `debugging`, `developer-id`, `mac-application`, `validation` |
| `destination` | `export` (default) or `upload` |
| `teamID` | Team for the export |
| `signingStyle` | `automatic` or `manual` |
| `signingCertificate`, `installerSigningCertificate`, `provisioningProfiles` | Manual signing only |
| `testFlightInternalTestingOnly` | Lock the build to internal testing |
| `manageAppVersionAndBuildNumber` | Let Xcode bump the build number on upload (default YES; the planner writes NO so the repository stays the source of truth) |
| `uploadSymbols`, `stripSwiftSymbols` | Crash symbolication; smaller IPA |
| `thinning` | Non-App Store exports: `<none>`, `<thin-for-all-variants>` or a model identifier |
| `iCloudContainerEnvironment` | `Development` or `Production` for CloudKit |
| `manifest` | Over-the-air install manifest for non-App Store exports |
| `distributionBundleIdentifier` | Export one eligible target from the archive |

---

## 5. TestFlight and release

- **Internal testers** (team members) get builds as soon as processing finishes.
- **External testers** need Beta App Review for the first build of a version; supply What to Test notes.
- Increase the build number for every upload; the version only when customers should see a new number.
- Phased release, manual release and expedited review are App Store Connect decisions — present them to the
  developer; do not choose silently.
- Before submission: `generate_release_report`, `audit_app_store_review`, `audit_screenshots`, `validate_app_metadata`.

---

## 6. CI pattern

Archive with a shared scheme, export with `method app-store-connect` + `testFlightInternalTestingOnly` for pull
requests, and a separate tagged job with `destination upload` for releases. Store the `.p8` in the CI secret store,
write it to a temporary path at runtime, and delete it after the job. Xcode Cloud is the zero-script alternative.
