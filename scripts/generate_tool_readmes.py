#!/usr/bin/env python3
"""Generate the per-tool README files from a single source of truth.

Fourteen hand-maintained READMEs drift: one gets a flag that no longer exists,
another keeps a finding code that was renamed. The tool metadata lives here and
`./scripts/verify.sh` fails if a generated README is stale.

Usage::

    python3 scripts/generate_tool_readmes.py           # write
    python3 scripts/generate_tool_readmes.py --check   # verify up to date
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parents[1]

TOOLS: Dict[str, dict] = {
    "project-inspector": {
        "script": "inspect_project.py",
        "title": "Project Inspector",
        "summary": "Structural analysis of an Xcode project or Swift package.",
        "usage": ["python3 tools/project-inspector/inspect_project.py [PATH]"],
        "checks": [
            "project kind: `.xcodeproj`, `.xcworkspace`, `Package.swift`",
            "targets, deployment targets per platform, Swift language version",
            "frameworks in use (SwiftUI, SwiftData, StoreKit, WidgetKit, …)",
            "architecture signals: `@Observable`, structured concurrency, TCA, SwiftData",
            "structural debt: legacy OS floor, missing tests, `NavigationView`, missing manifest",
        ],
        "codes": {"PROJ001": "no project file found", "PROJ003": "iOS floor below 17.0",
                  "PROJ005": "Swift < 6 language mode", "PROJ006": "no test target",
                  "PROJ007": "ObservableObject without @Observable", "PROJ008": "NavigationView"},
    },
    "privacy-auditor": {
        "script": "audit_privacy.py",
        "title": "Privacy Manifest Auditor",
        "summary": "Validates `PrivacyInfo.xcprivacy` against actual Required-Reason API usage.",
        "usage": ["python3 tools/privacy-auditor/audit_privacy.py [PATH]"],
        "checks": [
            "manifest presence and parseability",
            "per-category detection: UserDefaults, file timestamp, boot time, disk space, keyboards",
            "declared reason codes against Apple's documented valid codes",
            "tracking domains vs detected tracking SDKs",
            "collected-data declarations vs detected data-collecting APIs",
        ],
        "codes": {"PRIV001": "manifest missing", "PRIV010": "category used but undeclared",
                  "PRIV011": "invalid reason code", "PRIV020": "tracking signals without NSPrivacyTracking",
                  "PRIV022": "collected data undeclared"},
    },
    "asset-validator": {
        "script": "validate_assets.py",
        "title": "Asset Validator",
        "summary": "App Store icon and screenshot compliance, parsed from image headers.",
        "usage": [
            "python3 tools/asset-validator/validate_assets.py [PATH]",
            "python3 tools/asset-validator/validate_assets.py --icon AppIcon-1024.png",
            "python3 tools/asset-validator/validate_assets.py --screenshots ./shots",
        ],
        "checks": [
            "marketing icon: exactly 1024×1024, PNG, no alpha channel",
            "`.appiconset` Contents.json: declared slots exist with matching dimensions",
            "screenshots: accepted App Store slot per device and orientation",
        ],
        "codes": {"ASSET002": "not a PNG", "ASSET003": "wrong dimensions",
                  "ASSET004": "alpha channel present", "ASSET022": "screenshot slot unknown"},
    },
    "metadata-validator": {
        "script": "validate_metadata.py",
        "title": "Metadata Validator",
        "summary": "App Store listing copy and URLs against App Store Connect limits.",
        "usage": ["python3 tools/metadata-validator/validate_metadata.py metadata.json"],
        "checks": [
            "character limits: name 30, subtitle 30, keywords 100, promotional text 170, description 4000",
            "required `https://` URLs (support, privacy) and optional marketing URL",
            "keyword duplicates and wasted budget",
            "screenshot count (3–10) and http links in the description",
        ],
        "codes": {"META001": "over character limit", "META004": "required URL missing",
                  "META005": "invalid https URL", "META007": "duplicate keywords",
                  "META012": "fewer than 3 screenshots"},
    },
    "localization-checker": {
        "script": "check_localization.py",
        "title": "Localization Checker",
        "summary": "Strings that can never be translated, plus RTL mirroring defects.",
        "usage": ["python3 tools/localization-checker/check_localization.py [PATH]"],
        "checks": [
            "`Text(verbatim:)` and other explicit localisation bypasses",
            "UIKit string assignments that are never looked up in a catalog",
            "`Text(resolvedString)` where interpolation is required",
            "`.left` / `.right` padding and alignment that do not mirror in RTL",
            "String Catalog keys with missing translations or `needs_review` state",
        ],
        "codes": {"L10N001": "verbatim string", "L10N002": "UIKit string assignment",
                  "L10N003": "Text(String) not localisable", "L10N010": "RTL-hostile layout",
                  "L10N021": "missing translations"},
    },
    "widget-validator": {
        "script": "validate_widget.py",
        "title": "Widget & Live Activity Validator",
        "summary": "WidgetKit, Dynamic Island and ActivityKit completeness.",
        "usage": ["python3 tools/widget-validator/validate_widget.py [PATH]"],
        "checks": [
            "Live Activity: `NSSupportsLiveActivities`, `Activity.request`, push token handling",
            "Dynamic Island: compactLeading, compactTrailing, minimal, expanded regions",
            "`supportedFamilies` incl. Lock Screen accessory families",
            "timeline provider and App Intent configuration",
            "App Group shared container wiring",
        ],
        "codes": {"WID010": "Live Activities flag missing", "WID020": "Dynamic Island region missing",
                  "WID031": "no supportedFamilies", "WID032": "no timeline provider",
                  "WID034": "no App Group"},
    },
    "swiftui-linter": {
        "script": "lint_swiftui.py",
        "title": "SwiftUI Linter",
        "summary": "20 opinionated static rules for native-quality SwiftUI.",
        "usage": ["python3 tools/swiftui-linter/lint_swiftui.py [PATH]", "python3 tools/swiftui-linter/lint_swiftui.py --rules"],
        "checks": [
            "deprecated API: `foregroundColor`, `NavigationView`, `onChange(of:perform:)`, `animation(_:)`",
            "hardcoded styling: hex colours, fixed font sizes, white/black backgrounds",
            "view identity churn: `AnyView`, `id(UUID())`, `ForEach(0..<n)`",
            "robustness: `try!`, `UIScreen.main.bounds`, body-side effects",
            "motion: `scaleEffect(0)`, oversized shadows",
        ],
        "codes": {"SWU001": "hardcoded hex colour", "SWU002": "foregroundColor deprecated",
                  "SWU003": "NavigationView", "SWU006": "UIScreen.main.bounds",
                  "SWU009": "scaleEffect(0)", "SWU011": "ObservableObject", "SWU014": "try!"},
    },
    "accessibility-auditor": {
        "script": "audit_accessibility.py",
        "title": "Accessibility Auditor",
        "summary": "WCAG contrast maths, Dynamic Type, touch targets and VoiceOver labels.",
        "usage": ["python3 tools/accessibility-auditor/audit_accessibility.py [PATH]"],
        "checks": [
            "contrast ratio for detected text colours against light and dark backgrounds",
            "fixed point sizes and single-line limits that break Dynamic Type",
            "interactive elements smaller than 44×44pt",
            "icon-only buttons without an accessibility label",
            "controls hidden from assistive technologies",
        ],
        "codes": {"A11Y001": "contrast below 3:1", "A11Y002": "contrast below 4.5:1",
                  "A11Y010": "fixed font size", "A11Y020": "tap target under 44pt",
                  "A11Y030": "unlabelled icon button"},
    },
    "liquid-glass-auditor": {
        "script": "audit_liquid_glass.py",
        "title": "Liquid Glass Auditor",
        "summary": "iOS 26 Liquid Glass adoption versus hand-rolled glassmorphism.",
        "usage": ["python3 tools/liquid-glass-auditor/audit_liquid_glass.py [PATH]"],
        "checks": [
            "glass APIs used below iOS 26 without an availability guard",
            "`GlassEffectContainer` / `glassEffectID` when several effects are adjacent",
            "imitation patterns: `.ultraThinMaterial` stacks, manual `.blur`, white-opacity overlays",
            "nested material layers that each sample the backdrop",
        ],
        "codes": {"LG001": "iOS 26 API without availability guard",
                  "LG010": "fake glass imitation", "LG022": "missing GlassEffectContainer"},
    },
    "sf-symbols-catalog": {
        "script": "check_symbols.py",
        "title": "SF Symbols Catalog",
        "summary": "Validates symbol names and OS availability against the real system catalogue.",
        "usage": [
            "python3 tools/sf-symbols-catalog/check_symbols.py [PATH]",
            "python3 tools/sf-symbols-catalog/check_symbols.py --name square.and.pencil --ios 17.0",
        ],
        "checks": [
            "9,649 symbol names extracted from `CoreGlyphs.bundle`",
            "per-OS availability: does the symbol exist on the project's deployment target",
            "typo suggestions from the catalogue",
        ],
        "codes": {"SFC010": "unknown symbol name", "SFC011": "symbol newer than deployment target"},
    },
    "design-token-forge": {
        "script": "forge_tokens.py",
        "title": "Design Token Forge",
        "summary": "Compiles design tokens into SwiftUI constants and `.xcassets` colour sets.",
        "usage": [
            "python3 tools/design-token-forge/forge_tokens.py tokens.json --out Sources/Tokens.swift",
            "python3 tools/design-token-forge/forge_tokens.py tokens.json --xcassets Assets.xcassets",
        ],
        "checks": [
            "token schema: colours need light and dark values, spacing/radius must be numeric",
            "typography against `Font.TextStyle`, `Font.Weight`, `Font.Design`",
            "declared contrast pairs against WCAG AA",
            "generates dynamic `Color` values plus optional asset catalog colour sets",
        ],
        "codes": {"TOK003": "invalid hex colour", "TOK007": "unknown text style",
                  "TOK011": "contrast pair below 4.5:1"},
    },
    "screenshot-studio": {
        "script": "screenshot_studio.py",
        "title": "Screenshot Studio",
        "summary": "Capture from a booted simulator and validate App Store slots.",
        "usage": [
            "python3 tools/screenshot-studio/screenshot_studio.py --out shot.png",
            "python3 tools/screenshot-studio/screenshot_studio.py --screenshots ./shots",
        ],
        "checks": [
            "booted simulator discovery via `xcrun simctl`",
            "capture and immediate dimension validation",
            "slot matching for iPhone 6.9\"/6.7\"/6.5\", iPad 13\", Watch, Vision Pro",
        ],
        "codes": {"SHOT002": "no booted simulator", "SHOT004": "capture failed",
                  "SHOT011": "dimensions match no slot"},
    },
    "app-store-connect": {
        "script": "cli.py",
        "title": "App Store Connect (read-only)",
        "summary": "Read-only App Store Connect inspection with explicit auth.",
        "usage": [
            "python3 tools/app-store-connect/cli.py verify",
            "python3 tools/app-store-connect/cli.py list-apps",
            "python3 tools/app-store-connect/cli.py versions --app 1234567890",
        ],
        "checks": [
            "ES256 JWT signing via `cryptography` (no fake signatures)",
            "hard failure when credentials are missing — never a silent mock",
            "429 rate-limit aware with backoff",
            "read-only: only GET requests are issued",
        ],
        "codes": {"ASC001": "missing credentials", "ASC010": "explicit mock mode",
                  "ASC013": "expired builds"},
    },
    "apple-docs-research": {
        "script": "apple_docs.py",
        "title": "Apple Documentation Research",
        "summary": "Read Apple's official documentation with citations, from the JSON API the site itself uses.",
        "usage": [
            "python3 tools/apple-docs-research/apple_docs.py search \"navigation stack\" --framework swiftui",
            "python3 tools/apple-docs-research/apple_docs.py read swiftui/view/glassEffect(_:in:)",
            "python3 tools/apple-docs-research/apple_docs.py availability swiftui/navigationstack",
            "python3 tools/apple-docs-research/apple_docs.py guidelines buttons",
        ],
        "checks": [
            "refuses any host other than developer.apple.com, before a socket opens",
            "`search`: ranked symbol lookup across a framework index (8,000+ symbols for SwiftUI)",
            "`read`: page rendered as Markdown — declaration, overview, code listings, parameters",
            "`availability`: the per-platform table Apple publishes (introduced, deprecated, beta)",
            "`guidelines`: Human Interface Guidelines pages as Markdown",
            "every result carries `source_url` and `fetched_at`; cached seven days, `--refresh` to bypass, `--offline` to forbid the network",
        ],
        "codes": {"DOC000": "document could not be retrieved (error, never a guess)",
                  "DOC010": "served from cache", "DOC011": "API is deprecated on a platform",
                  "DOC030": "no symbol matched", "DOC040": "HIG page rendered empty"},
    },
    "aso-engine": {
        "script": "aso.py",
        "title": "ASO Engine",
        "summary": "Deterministic App Store Optimization analysis: no invented search volume, no invented competitors.",
        "usage": [
            "python3 tools/aso-engine/aso.py metadata.json",
            "python3 tools/aso-engine/aso.py metadata.json --locale tr-TR --json",
        ],
        "checks": [
            "character budgets per field against App Store Connect limits",
            "duplicate keywords, single-character keywords, budget spent on words already in the name",
            "keywords that never appear in the name, subtitle or description (coverage hint)",
            "unverifiable claims: “best”, “#1”, “world's”, “guaranteed”, “100%”",
            "description structure: opening paragraph length, bullet list, tappable link",
            "candidate keywords extracted from the developer's own description, with the arithmetic shown",
        ],
        "codes": {"ASO001": "field over its limit", "ASO002": "budget left unused",
                  "ASO010": "duplicate keywords", "ASO012": "keywords absent from visible copy",
                  "ASO020": "unverifiable claim", "ASO031": "keyword candidates that fit the budget"},
    },
    "icon-studio": {
        "script": "icon_studio.py",
        "title": "Icon Studio",
        "summary": "Turn one 1024×1024 master into a complete, valid AppIcon set — no image SDK required.",
        "usage": [
            "python3 tools/icon-studio/icon_studio.py prepare AppIcon-1024.png --out Assets.xcassets/AppIcon.appiconset",
            "python3 tools/icon-studio/icon_studio.py verify Assets.xcassets/AppIcon.appiconset",
            "python3 tools/icon-studio/icon_studio.py preview AppIcon-1024.png --at 120 --out preview.png",
        ],
        "checks": [
            "master validation: 1024×1024, PNG, no alpha channel",
            "18 slots generated by box-filter downscale (iPhone, iPad, marketing)",
            "Contents.json written in the shape Xcode expects",
            "`verify` re-reads every slot and checks its pixel size",
            "`preview` renders the icon at a small size for legibility review",
        ],
        "codes": {"ICON001": "master unreadable", "ICON003": "master not 1024×1024",
                  "ICON004": "master has alpha", "ICON021": "referenced file missing",
                  "ICON022": "slot has the wrong pixel size"},
    },
    "release-readiness": {
        "script": "generate_report.py",
        "title": "Release Readiness Gate",
        "summary": "Weighted, evidence-based pre-submission verdict across every gate.",
        "usage": ["python3 tools/release-readiness/generate_report.py . --metadata metadata.json --icon AppIcon.png --output RELEASE_REPORT.md"],
        "checks": [
            "seven weighted gates: privacy 25, assets 15, metadata 15, project 15, localisation 10, widgets 10, accessibility 10",
            "a gate with no input is NOT INSPECTED, scores zero and forces BLOCKED",
            "any error or critical finding zeroes its gate",
            "`READY` requires every applicable gate passing AND a score of at least 90",
        ],
        "codes": {"REL001": "gate not inspected", "REL002": "gate failed",
                  "REL003": "gate has warnings", "REL010": "all gates passed"},
    },
}


def render(name: str, spec: dict) -> str:
    checks = "\n".join(f"- {item}" for item in spec["checks"])
    usage = "\n".join(spec["usage"])
    codes = "\n".join(f"| `{code}` | {message} |" for code, message in spec["codes"].items())
    return f"""# {spec['title']}

{spec['summary']}

Part of [apple-native-engineer-mcp](../../README.md). Exposed over MCP as a matching tool.

## Usage

```bash
{usage}
```

Every tool accepts `--json` (stable envelope, see below), `--strict` (warnings become failures) and
`--color auto|always|never`.

## What it checks

{checks}

## Findings

| Code | Meaning |
| :--- | :--- |
{codes}

## Output contract

`--json` prints one object and nothing else:

```json
{{
  "schema_version": "2.0",
  "tool": "{name}",
  "tool_version": "2.0.0",
  "target": "/absolute/path",
  "status": "pass | warn | fail",
  "summary": {{"critical": 0, "error": 0, "warning": 0, "info": 0, "total": 0}},
  "findings": [{{"code": "...", "severity": "...", "message": "...", "file": "...", "line": 0, "hint": "..."}}],
  "data": {{}}
}}
```

## Exit codes

| Code | Meaning |
| ---: | :--- |
| 0 | pass (or warnings without `--strict`) |
| 1 | warnings with `--strict` |
| 2 | at least one error or critical finding |
"""


def main(argv: List[str]) -> int:
    stale: List[str] = []
    for name, spec in TOOLS.items():
        target = REPO / "tools" / name / "README.md"
        content = render(name, spec)
        if "--check" in argv:
            if not target.exists() or target.read_text() != content:
                stale.append(name)
        else:
            target.write_text(content)
            print(f"wrote tools/{name}/README.md")
    if "--check" in argv:
        if stale:
            print("stale tool READMEs: " + ", ".join(stale))
            return 1
        print(f"{len(TOOLS)} tool READMEs are up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
