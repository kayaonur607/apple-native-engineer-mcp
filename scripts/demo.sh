#!/usr/bin/env bash
# ==============================================================================
# demo.sh — what this toolkit does, in about thirty seconds.
#
# Runs the interesting checks against the deliberately broken fixture, then
# against the clean one, so the contrast is visible without reading the docs.
# ==============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

cyan() { printf '\n\033[1;36m%s\033[0m\n' "$1"; }
dim() { printf '\033[2m%s\033[0m\n' "$1"; }

cyan "1/4 · What is this project?"
dim "   python3 tools/project-inspector/inspect_project.py tests/fixtures/legacy-app"
python3 tools/project-inspector/inspect_project.py tests/fixtures/legacy-app --color never | head -14

cyan "2/4 · What is wrong with the SwiftUI?"
dim "   python3 tools/swiftui-linter/lint_swiftui.py tests/fixtures/legacy-app"
python3 tools/swiftui-linter/lint_swiftui.py tests/fixtures/legacy-app --color never | head -22

cyan "3/4 · Would the App Store accept the icon and the listing?"
dim "   python3 tools/asset-validator/validate_assets.py --icon … (512×512 with alpha)"
python3 tools/asset-validator/validate_assets.py tests/fixtures/legacy-app \
    --icon tests/fixtures/legacy-app/Assets.xcassets/AppIcon.appiconset/AppIcon-512.png --color never | head -12

cyan "4/4 · The verdict"
dim "   python3 tools/release-readiness/generate_report.py tests/fixtures/legacy-app --metadata … --icon …"
python3 tools/release-readiness/generate_report.py tests/fixtures/legacy-app \
    --metadata tests/fixtures/legacy-app/metadata.json \
    --icon tests/fixtures/legacy-app/Assets.xcassets/AppIcon.appiconset/AppIcon-512.png \
    --color never | tail -14

cyan "Now the same gate on a project that follows the rules"
dim "   tests/fixtures/clean-app"
python3 tools/release-readiness/generate_report.py tests/fixtures/clean-app \
    --metadata tests/fixtures/clean-app/metadata.json \
    --icon tests/fixtures/clean-app/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png \
    --screenshots tests/fixtures/clean-app/screenshots \
    --color never | sed -n '1,10p'

cyan "Next"
cat <<'EOF'
   make verify        run everything CI runs
   make doctor        check this machine
   node integrations/mcp-server/src/index.js --selftest   MCP inventory
EOF
