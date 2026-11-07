# Platform coverage and developer workflow

Reviewed 2026-11-06. Shared source checks are heuristics, not a platform certification.

| Platform | Current evidence | Required human/device checks |
| --- | --- | --- |
| iOS | Clean/legacy source fixtures, SDK type-checks, icon and screenshot rules | VoiceOver, Dynamic Type, contrast over real content, permissions, offline and purchase flows |
| iPadOS | Shared iOS checks and adaptive-layout guidance | Multitasking, resizing, keyboard, pointer, orientation and presentation behavior |
| macOS | Shared Swift scanning, AppKit/SwiftUI reference guidance | Windows, menus, keyboard, sandbox, signing and notarization |
| watchOS | Shared Swift scanning and platform references | Crown, complications, wrist interaction, constrained layout and connectivity |
| visionOS | Selected documentation snippets type-checked for visionOS | Focus, gaze/pinch, comfort, windows/volumes, immersion and accessibility |
| tvOS | Shared source inspection only; no dedicated fixture or complete asset rules | Focus engine, Siri Remote, viewing distance, media and platform-specific assets |

Do not apply the iPhone 44-point target heuristic or the 1024 PNG icon workflow as universal rules across all platforms.
Confirm framework and symbol availability for each deployment target. A watch, TV or spatial app needs a dedicated
build/test destination and platform-specific asset review.

## First contribution or first app audit

1. Install Node 20+ and Python 3.10+. Xcode is optional for static checks and required for SDK verification or simulator work.
2. In `integrations/mcp-server`, run `npm ci`, then `node src/index.js --doctor` and `node src/index.js --selftest`.
3. Start with `APPLE_NATIVE_MODULES=core,swift-engineering,privacy-security-audit`. This is tool exposure control,
   not OS-level isolation. The default remains all twelve modules for compatibility; ASC reads credentials only when called.
4. Inspect the project and run `review_diff` while editing. Preserve minimum OS support and stable view identity.
5. Run the complete static suite, then build and test with the project's own scheme and destination. Enable Swift
   concurrency diagnostics appropriate to the project's language mode; do not silence them with unchecked annotations.
6. Preserve a result bundle with `xcodebuild test -scheme YOUR_SCHEME -destination YOUR_DESTINATION -resultBundlePath TestResults.xcresult`.
   Supply your real scheme and destination; build scripts in an unfamiliar project should be reviewed before execution.
7. Read recorded tests with `python3 scripts/collect_xcode_evidence.py TestResults.xcresult` (Xcode required).
   This optional utility uses the local `xcresulttool get test-results summary` schema. A zero-test run fails,
   skipped/expected-failure tests require review, and an unsupported schema fails closed. It does not certify freshness:
   associate the bundle with the tested commit and retain your exact build command.
8. Verify actual screens on relevant devices: Light/Dark, accessibility sizes, VoiceOver order, RTL, reduced motion,
   slow network, errors, account deletion, purchases and restoration. Capture real screenshots before composition.
9. Run the static release report with metadata/icon inputs. Its success string is now `CONFIGURED STATIC CHECKS PASSED`;
   consumers matching the previous `READY FOR SUBMISSION` literal must update. JSON `status` and exit-code semantics remain.
10. Review App Store Connect separately. This project reads listings and builds; it does not submit or upload them.

## Apple sources to check at release time

- [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines): platform interaction and accessibility.
- [Swift concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/): isolation and structured tasks.
- [Swift Testing](https://developer.apple.com/documentation/testing): test design; UI tests may still use XCTest.
- [Required-reason APIs](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api): choose reasons matching actual use; inspect SDK manifests too.
- [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications): verify current target slots rather than treating this repository's table as exhaustive.
- [App icons](https://developer.apple.com/design/human-interface-guidelines/app-icons): the current icon studio prepares raster slots, not generative artwork or every platform's icon format.
- [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/): review metadata, privacy, commerce and account behavior in context.
- [App Store Connect API](https://developer.apple.com/documentation/appstoreconnectapi): use least-privilege keys outside the checkout.

ASO results are copy analysis, not market research. No keyword-volume, ranking lift or acceptance probability is measured.
