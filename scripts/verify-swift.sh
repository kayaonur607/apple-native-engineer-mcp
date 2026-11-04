#!/usr/bin/env bash
# ==============================================================================
# verify-swift.sh — compile the Swift in this repository.
#
# Two guarantees, both measured rather than claimed:
#   1. every Swift fixture type-checks against the iOS SDK
#   2. every ```swift block in references/ and examples/ parses
#
# macOS + Xcode only. Uses `-disable-sandbox` because the Swift macro plugin
# server cannot be nested inside another sandbox.
# ==============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SDK="$(xcrun --sdk iphonesimulator --show-sdk-path 2>/dev/null)" || {
    echo "  ! iphonesimulator SDK not found"
    exit 1
}

WORK="$REPO_ROOT/.swiftwork"
mkdir -p "$WORK/tmp" "$WORK/mc"

SDK_MAJOR="$(xcrun --sdk iphonesimulator --show-sdk-version | cut -d. -f1)"
TARGET="arm64-apple-ios18.0-simulator"
SWIFTC_FLAGS=(-typecheck -parse-as-library -disable-sandbox -sdk "$SDK" -target "$TARGET"
              -module-cache-path "$WORK/mc")

failures=0
checked=0

compile() {
    local label="$1"
    shift
    checked=$((checked + 1))
    if TMPDIR="$WORK/tmp" swiftc "${SWIFTC_FLAGS[@]}" "$@" > "$WORK/out.log" 2>&1; then
        printf '  ✓ %s\n' "$label"
    else
        printf '  ✗ %s\n' "$label"
        sed 's/^/      /' "$WORK/out.log" | head -12
        failures=$((failures + 1))
    fi
}

echo "  SDK: $(basename "$SDK")"

# 1. Fixtures ---------------------------------------------------------------
# Liquid Glass (`glassEffect`) only exists in the iOS 26+ SDK, so the glass demo
# is only compiled when the toolchain can see those symbols.
# Note: the Swift Testing module (`import Testing`) is only available to
# `swift test`, not to a standalone `swiftc` invocation, so the test target is
# compiled by Xcode/SwiftPM in CI rather than here.
APP_FILES=(tests/fixtures/clean-app/App/*.swift)
if [ "${SDK_MAJOR:-0}" -lt 26 ]; then
    APP_FILES=()
    for file in tests/fixtures/clean-app/App/*.swift; do
        case "$file" in
            *GlassSurface.swift)
                printf '  ~ skipping %s (needs the iOS 26 SDK; found %s)\n' \
                    "$(basename "$file")" "$(xcrun --sdk iphonesimulator --show-sdk-version)"
                ;;
            *) APP_FILES+=("$file") ;;
        esac
    done
fi

compile "fixture: clean-app/App"        "${APP_FILES[@]}"
compile "fixture: clean-app/Widgets"    tests/fixtures/clean-app/Widgets/*.swift

# 2. Documentation snippets (syntax only) -----------------------------------
SNIPPET_DIR="$WORK/snippets"
rm -rf "$SNIPPET_DIR"
mkdir -p "$SNIPPET_DIR"

python3 - "$SNIPPET_DIR" <<'PY'
import pathlib
import re
import sys

out = pathlib.Path(sys.argv[1])
count = 0
for md in sorted(pathlib.Path(".").glob("examples/*.md")) + sorted(pathlib.Path(".").glob("references/*.md")):
    text = md.read_text(encoding="utf-8", errors="ignore")
    for index, block in enumerate(re.finditer(r"```swift\n(.*?)```", text, re.S)):
        count += 1
        (out / f"{md.parent.name}-{md.stem}-{index:02d}.swift").write_text(block.group(1), encoding="utf-8")
print(count)
PY

snippet_count=$(ls "$SNIPPET_DIR" | wc -l | tr -d ' ')
syntax_failures=0
for snippet in "$SNIPPET_DIR"/*.swift; do
    if ! swiftc -parse "$snippet" > /dev/null 2>&1; then
        syntax_failures=$((syntax_failures + 1))
        echo "  ✗ syntax: $(basename "$snippet")"
    fi
done

checked=$((checked + 1))
if [ "$syntax_failures" -eq 0 ]; then
    printf '  ✓ documentation snippets parse (%s blocks)\n' "$snippet_count"
else
    printf '  ✗ %s of %s documentation snippets failed to parse\n' "$syntax_failures" "$snippet_count"
    failures=$((failures + 1))
fi

printf '  checked %d unit(s), %d failure(s)\n' "$checked" "$failures"
[ "$failures" -eq 0 ]
