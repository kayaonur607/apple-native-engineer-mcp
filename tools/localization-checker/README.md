# Localization Checker Tool

Scans Apple platform projects for hardcoded user-interface strings, non-adaptive layout padding (such as `.left` or `.right` which break Right-to-Left mirroring), and Xcode String Catalog (`.xcstrings`) completeness.

---

## Capabilities

1. **RTL Mirroring Check**: Detects hardcoded `.padding(.left)` and `.padding(.right)` and prompts for `.leading` / `.trailing`.
2. **Hardcoded UI Strings**: Scans SwiftUI views for raw string literals passed to `Text()`, `Button()`, `Label()`.
3. **String Catalog Inspection**: Parses `.xcstrings` catalogs to report untranslated keys (`new` or `needs_review` states).
4. **JSON Reporting**: Emits structured JSON for CI/CD pipelines and MCP tools.

---

## Usage

```bash
# Human-readable console audit
python3 tools/localization-checker/check_localization.py --project-dir /path/to/project

# JSON output
python3 tools/localization-checker/check_localization.py --project-dir /path/to/project --json
```
