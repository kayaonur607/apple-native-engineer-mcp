---
description: "Ship a build: preflight, ExportOptions, archive, TestFlight or App Store upload, or Developer ID notarization — each account-changing step only with approval."
---

# Distribute a build

Uploading and notarizing change account state. Plan first, show the plan, then run one step at a time with the
developer's explicit approval.

## 1. Decide the method

Ask only if unclear: App Store / external TestFlight (`app-store`), internal TestFlight only
(`testflight-internal`), test devices (`release-testing`), enterprise, Mac App Store (`mac-app-store`) or macOS
outside the store (`developer-id`). Read `apple-native://references/distribution-and-release`.

## 2. Preflight

1. `plan_distribution method=<method>` (add `scheme` and `platform` when there are several).
2. Fix every error first: `DST040` Hardened Runtime, `DST041` App Sandbox, `DST060` wrong method for platform.
3. Resolve warnings or record the decision: `DST030` export compliance, `DST020/021` version and build number,
   `DST042` debug entitlements, `DST050` privacy manifest (`audit_privacy_manifest`), `DST051` icon.
4. For store submissions also run `generate_release_report`, `audit_app_store_review`, `validate_app_metadata`
   and `audit_screenshots`.

## 3. Execute with approval

1. Write ExportOptions: `plan_distribution … write_export_options=build/ExportOptions.plist`.
2. Run `archive` (local). Then ask before each step marked `requires_approval` (upload, notarize).
3. Credentials are environment variables (`ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_PRIVATE_KEY_PATH`). Never print,
   paste or commit key material.
4. After upload: `app_store_connect operation=builds` until processing completes. For Developer ID: staple, then
   `spctl --assess` must report a notarized Developer ID.

## Report

Answer in the user's language with: outcome · files changed · checks actually run (tool + finding codes, build
command and result, simulator/device runs) · Apple sources with URLs · what remains unverified · next action.
Static findings are not a build; a build is not a runtime check; neither is App Review approval.
