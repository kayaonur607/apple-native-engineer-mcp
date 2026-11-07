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
VERIFY_LOG_DIR=$(mktemp -d)
trap 'rm -rf "$VERIFY_LOG_DIR"' EXIT

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
if python3 -m unittest discover -s tests -t tests > "$VERIFY_LOG_DIR/python.log" 2>&1; then
    tail -5 "$VERIFY_LOG_DIR/python.log"
    record pass
else
    cat "$VERIFY_LOG_DIR/python.log"
    record fail
fi

section "MCP protocol tests"
if [ -d integrations/mcp-server/node_modules ]; then
    if (cd integrations/mcp-server && npm test) > "$VERIFY_LOG_DIR/mcp.log" 2>&1; then
        tail -8 "$VERIFY_LOG_DIR/mcp.log"
        record pass
    else
        cat "$VERIFY_LOG_DIR/mcp.log"
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

section "Documentation API claims"
if [ "$(uname -s)" = "Darwin" ] && command -v xcrun > /dev/null 2>&1; then
    if python3 scripts/check_api_claims.py; then
        record pass
    else
        record fail
    fi
else
    printf '  ! requires an Apple SDK; skipped\n'
    record skip
fi

ELAPSED=$(( $(date +%s) - START ))

printf '\n\033[1m────────────────────────────────────────────\033[0m\n'
printf '  passed: %d   failed: %d   skipped: %d   %ds\n' "$PASS" "$FAIL" "$SKIP" "$ELAPSED"
printf '\033[1m────────────────────────────────────────────\033[0m\n'

[ "$FAIL" -eq 0 ]
