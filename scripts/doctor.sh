#!/usr/bin/env bash
# ==============================================================================
# doctor.sh — is this machine able to run everything in the repository?
#
# Checks the three toolchains the repo needs and reports what is missing, with
# the exact command that fixes it. Exit code 0 means `./scripts/verify.sh` can
# run to completion here.
# ==============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FAILED=0
WARNED=0

pass() { printf '  \033[32m✓\033[0m %-28s %s\n' "$1" "$2"; }
warn() { printf '  \033[33m!\033[0m %-28s %s\n' "$1" "$2"; WARNED=$((WARNED + 1)); }
fail() { printf '  \033[31m✗\033[0m %-28s %s\n' "$1" "$2"; FAILED=$((FAILED + 1)); }

printf '\n\033[1mapple-native-engineer-mcp · environment\033[0m\n\n'

# -- Python -------------------------------------------------------------------
if command -v python3 > /dev/null 2>&1; then
    PY_VERSION="$(python3 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
    PY_MAJOR="$(python3 -c 'import sys; print(sys.version_info[0])')"
    PY_MINOR="$(python3 -c 'import sys; print(sys.version_info[1])')"
    if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        pass "python3" "$PY_VERSION"
    else
        fail "python3" "$PY_VERSION is too old (need 3.10+): brew install python@3.12"
    fi
else
    fail "python3" "not found: install Python 3.10+"
fi

# -- Node ---------------------------------------------------------------------
if command -v node > /dev/null 2>&1; then
    NODE_VERSION="$(node --version)"
    NODE_MAJOR="${NODE_VERSION#v}"
    NODE_MAJOR="${NODE_MAJOR%%.*}"
    if [ "$NODE_MAJOR" -ge 20 ]; then
        pass "node" "$NODE_VERSION"
    else
        fail "node" "$NODE_VERSION is too old (need 20+)"
    fi
else
    fail "node" "not found: install Node 20+"
fi

if [ -d "integrations/mcp-server/node_modules" ]; then
    pass "mcp dependencies" "installed"
else
    warn "mcp dependencies" "missing: cd integrations/mcp-server && npm install"
fi

# -- Xcode --------------------------------------------------------------------
if command -v xcrun > /dev/null 2>&1; then
    SDK_VERSION="$(xcrun --sdk iphonesimulator --show-sdk-version 2>/dev/null || echo "0")"
    SDK_MAJOR="${SDK_VERSION%%.*}"
    if [ "${SDK_MAJOR:-0}" -ge 26 ]; then
        pass "iOS SDK" "$SDK_VERSION (full verification available)"
    elif [ "${SDK_MAJOR:-0}" -ge 18 ]; then
        warn "iOS SDK" "$SDK_VERSION — Liquid Glass snippets will be skipped; Xcode 26+ enables them"
    else
        warn "iOS SDK" "$SDK_VERSION — Swift checks will be skipped"
    fi
else
    warn "Xcode" "not installed — Python and MCP checks still work, Swift checks will be skipped"
fi

# -- Data and knowledge base ---------------------------------------------------
if [ -f "data/sf-symbols.json" ]; then
    SYMBOLS="$(python3 -c 'import json; print(json.load(open("data/sf-symbols.json"))["count"])')"
    pass "SF Symbols catalogue" "$SYMBOLS symbols"
else
    fail "SF Symbols catalogue" "data/sf-symbols.json is missing"
fi

REFERENCES="$(ls references/*.md 2>/dev/null | wc -l | tr -d ' ')"
pass "knowledge base" "$REFERENCES references, $(ls checklists/*.md | wc -l | tr -d ' ') checklists"

# -- MCP server ---------------------------------------------------------------
if [ -d "integrations/mcp-server/node_modules" ]; then
    if node integrations/mcp-server/src/index.js --selftest > /tmp/anm-selftest.json 2>/dev/null; then
        TOOLS_COUNT="$(python3 -c 'import json; print(len(json.load(open("/tmp/anm-selftest.json"))["tools"]))')"
        pass "mcp server" "$TOOLS_COUNT tools"
    else
        fail "mcp server" "selftest failed: node integrations/mcp-server/src/index.js --selftest"
    fi
fi

printf '\n'
if [ "$FAILED" -gt 0 ]; then
    printf '\033[31m%d blocking problem(s)\033[0m, %d warning(s)\n\n' "$FAILED" "$WARNED"
    exit 1
fi

printf '\033[32mReady\033[0m — %d warning(s). Run ./scripts/verify.sh to prove it.\n\n' "$WARNED"
