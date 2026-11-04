#!/usr/bin/env bash
# ==============================================================================
# verify.sh — the single source of truth for "does this repository work?"
#
# Runs, in order:
#   1. repository structure + link validation
#   2. Python unit and golden tests (tools + shared library)
#   3. MCP protocol tests against a real client/server pair
#   4. Swift compilation of the fixtures (macOS + Xcode only)
#
# Exit code is 0 only when every stage passes.
# ==============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PASS=0
FAIL=0
SKIP=0
START=$(date +%s)

section() {
    printf '\n\033[1m▸ %s\033[0m\n' "$1"
}

record() {
    case "$1" in
        pass) PASS=$((PASS + 1)) ;;
        fail) FAIL=$((FAIL + 1)) ;;
        skip) SKIP=$((SKIP + 1)) ;;
    esac
}

run_stage() {
    local name="$1"
    shift
    section "$name"
    if "$@"; then
        printf '\033[32m  ✓ %s\033[0m\n' "$name"
        record pass
    else
        printf '\033[31m  ✗ %s\033[0m\n' "$name"
        record fail
    fi
}

section "Repository structure and links"
if ./scripts/validate-skill.sh > /tmp/anm-validate.log 2>&1; then
    tail -3 /tmp/anm-validate.log | sed 's/^/  /'
    record pass
else
    cat /tmp/anm-validate.log | sed 's/^/  /'
    record fail
fi

section "Python tests (shared library + tools)"
if python3 -m unittest discover -s tests -t tests 2>&1 | tail -5; then
    record pass
else
    record fail
fi

section "MCP protocol tests"
if [ -d integrations/mcp-server/node_modules ]; then
    if (cd integrations/mcp-server && node --test test/ 2>&1 | tail -8); then
        record pass
    else
        record fail
    fi
else
    printf '  ! integrations/mcp-server/node_modules missing; run: cd integrations/mcp-server && npm install\n'
    record skip
fi

section "Swift compilation (fixtures + documentation snippets)"
if [ "$(uname -s)" = "Darwin" ] && command -v xcrun > /dev/null 2>&1; then
    if ./scripts/verify-swift.sh; then
        record pass
    else
        record fail
    fi
else
    printf '  ! requires macOS with Xcode; skipped\n'
    record skip
fi

ELAPSED=$(( $(date +%s) - START ))

printf '\n\033[1m────────────────────────────────────────────\033[0m\n'
printf '  passed: %d   failed: %d   skipped: %d   %ds\n' "$PASS" "$FAIL" "$SKIP" "$ELAPSED"
printf '\033[1m────────────────────────────────────────────\033[0m\n'

[ "$FAIL" -eq 0 ]
