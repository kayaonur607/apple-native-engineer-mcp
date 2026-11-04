# Project Inspector Tool

Executable CLI tool that analyzes an Apple platform repository, Xcode project, or Swift Package.

---

## Capabilities
- Discovers project type (`.xcodeproj`, `Package.swift`, `Podfile`).
- Analyzes Swift source files to detect frameworks (`SwiftUI`, `UIKit`, `AppKit`, `StoreKit 2`, `Observation`).
- Detects architectural patterns (`@Observable`, `@MainActor`, legacy `ObservableObject`, `TCA`).
- Verifies presence of `PrivacyInfo.xcprivacy` and `Info.plist`.
- Generates human-readable summaries or machine-readable JSON.

---

## Usage

```bash
# Human-readable report of current workspace
./tools/project-inspector/inspect_project.py

# Inspect a specific project folder
./tools/project-inspector/inspect_project.py /path/to/my-ios-app

# JSON output for automated scripting or MCP integration
./tools/project-inspector/inspect_project.py /path/to/my-ios-app --json
```
