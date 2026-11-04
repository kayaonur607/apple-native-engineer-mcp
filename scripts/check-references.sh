#!/usr/bin/env bash
# ==============================================================================
# check-references.sh
# Scans markdown files for local link validity and reference consistency.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
CHECKED=0

echo -e "${BLUE}[INFO]${NC} Scanning markdown documents for link integrity..."

# Find all markdown files in repo root, references, checklists, examples, integrations
while IFS= read -r md_file; do
    file_dir="$(dirname "${md_file}")"
    
    # Extract markdown links of format [label](target)
    # Exclude external http/https/mailto links, anchors starting with #
    links=$(grep -o -E '\[[^]]+\]\(([^)]+)\)' "${md_file}" | sed -E 's/\[[^]]+\]\(([^)]+)\)/\1/' || true)
    
    while IFS= read -r link; do
        [[ -z "${link}" ]] && continue
        
        # Skip web links and internal page anchors
        if [[ "${link}" =~ ^https?:// ]] || [[ "${link}" =~ ^mailto: ]] || [[ "${link}" =~ ^# ]]; then
            continue
        fi
        
        # Clean file:/// prefix if present
        clean_target="${link#file:///}"
        # Strip URL query or anchor
        clean_target="${clean_target%%#*}"
        [[ -z "${clean_target}" ]] && continue
        
        # Resolve target path
        if [[ "${clean_target}" = /* ]]; then
            # Absolute from repo root
            resolved_target="${REPO_ROOT}/${clean_target#/}"
        else
            # Relative to containing document or repo root
            if [[ -e "${file_dir}/${clean_target}" ]]; then
                resolved_target="${file_dir}/${clean_target}"
            elif [[ -e "${REPO_ROOT}/${clean_target}" ]]; then
                resolved_target="${REPO_ROOT}/${clean_target}"
            else
                resolved_target="${file_dir}/${clean_target}"
            fi
        fi
        
        CHECKED=$((CHECKED + 1))
        if [[ ! -e "${resolved_target}" ]]; then
            echo -e "${RED}[BROKEN LINK]${NC} In ${md_file#"${REPO_ROOT}/"}: '${link}' -> target not found (${resolved_target#"${REPO_ROOT}/"})"
            ERRORS=$((ERRORS + 1))
        fi
    done <<< "${links}"
    
done < <(find "${REPO_ROOT}" -type f -name "*.md" -not -path "*/.*/*")

echo -e "${BLUE}[INFO]${NC} Checked ${CHECKED} internal link references."

if (( ERRORS == 0 )); then
    echo -e "${GREEN}[PASS]${NC} All local markdown links resolve successfully."
    exit 0
else
    echo -e "${RED}[FAIL]${NC} Found ${ERRORS} broken link reference(s)."
    exit 1
fi
