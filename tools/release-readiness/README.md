# Release Readiness Generator Tool

Consolidates all project inspection, asset verification, metadata checking, and privacy compliance tools into a unified App Store release readiness report.

---

## Capabilities
- Computes an **App Store Readiness Score (0-100)**.
- Identifies critical App Store Review risks (missing Required-Reason APIs, bad icon dimensions, metadata errors).
- Generates formatted Markdown reports suitable for PRs or release audits, and machine-readable JSON.

---

## Usage

```bash
# Generate report for current workspace
./tools/release-readiness/generate_report.py

# Evaluate a specific project with custom metadata
./tools/release-readiness/generate_report.py /path/to/my-ios-app --metadata /path/to/metadata.json

# Export report directly to Markdown file
./tools/release-readiness/generate_report.py --output RELEASE_AUDIT.md
```
