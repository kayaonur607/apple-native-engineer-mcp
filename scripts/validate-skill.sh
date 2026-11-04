#!/usr/bin/env bash
# ==============================================================================
# validate-skill.sh
# Validates SKILL.md YAML frontmatter, directory layout, and link integrity
# according to the Agent Skills open standard (agentskills.io).
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

echo "=========================================================="
echo "  Apple Native Engineer - Skill Validation Tool    "
echo "=========================================================="
log_info "Repository root: ${REPO_ROOT}"

# ------------------------------------------------------------------------------
# 1. Verify Canonical SKILL.md Existence
# ------------------------------------------------------------------------------
SKILL_FILE="${REPO_ROOT}/SKILL.md"
if [[ ! -f "${SKILL_FILE}" ]]; then
    log_fail "SKILL.md does not exist at repository root!"
    exit 1
else
    log_pass "SKILL.md exists at repository root."
fi

# ------------------------------------------------------------------------------
# 2. Validate YAML Frontmatter
# ------------------------------------------------------------------------------
FIRST_LINE=$(head -n 1 "${SKILL_FILE}")
if [[ "${FIRST_LINE}" != "---" ]]; then
    log_fail "SKILL.md must start with '---' YAML frontmatter delimiter."
else
    log_pass "SKILL.md starts with frontmatter delimiter."
fi

# Extract frontmatter block
FRONTMATTER=$(awk 'NR>1 {if ($0 ~ /^---$/) exit; print}' "${SKILL_FILE}")

# Extract name field
SKILL_NAME=$(echo "${FRONTMATTER}" | grep -E '^name:' | sed -E 's/^name:[[:space:]]*//' | tr -d '"'"'" || true)
if [[ -z "${SKILL_NAME}" ]]; then
    log_fail "Frontmatter missing required 'name' field."
else
    # Validate name rules: <= 64 chars, lowercase a-z, 0-9, and hyphens, no leading/trailing hyphen
    NAME_LEN=${#SKILL_NAME}
    if (( NAME_LEN > 64 )); then
        log_fail "Skill name '${SKILL_NAME}' exceeds 64 characters (current: ${NAME_LEN})."
    elif [[ ! "${SKILL_NAME}" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
        log_fail "Skill name '${SKILL_NAME}' contains invalid characters or bad hyphens."
    else
        log_pass "Skill name '${SKILL_NAME}' is valid (${NAME_LEN}/64 chars)."
    fi
fi

# Extract description field
SKILL_DESC=$(echo "${FRONTMATTER}" | grep -E '^description:' | sed -E 's/^description:[[:space:]]*//' | tr -d '"'"'" || true)
if [[ -z "${SKILL_DESC}" ]]; then
    log_fail "Frontmatter missing required 'description' field."
else
    DESC_LEN=${#SKILL_DESC}
    if (( DESC_LEN > 1024 )); then
        log_fail "Skill description exceeds 1024 characters (current: ${DESC_LEN})."
    else
        log_pass "Skill description is valid (${DESC_LEN}/1024 chars)."
    fi
fi

# ------------------------------------------------------------------------------
# 3. Check Required Directory Structure & Files
# ------------------------------------------------------------------------------
EXPECTED_FILES=(
    "README.md"
    "SOURCES.md"
    "COMMANDS.md"
    "LICENSE"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
    "CODE_OF_CONDUCT.md"
    "SECURITY.md"
    ".gitignore"
    "assets/hero.svg"
    "references/apple-hig-foundations.md"
    "references/design-principles.md"
    "references/typography-and-color.md"
    "references/liquid-glass.md"
    "references/native-components.md"
    "references/navigation-patterns.md"
    "references/iphone-design.md"
    "references/ipad-design.md"
    "references/macos-design.md"
    "references/architecture-and-clean-code.md"
    "references/privacy-and-security.md"
    "references/app-store-readiness.md"
    "references/accessibility.md"
    "references/performance-optimization.md"
    "references/swiftui-engineering.md"
    "references/animation-principles.md"
    "references/design-systems.md"
    "references/visual-quality.md"
    "references/official-resources.md"
    "references/community-resources.md"
    "checklists/apple-hig-audit.md"
    "checklists/app-store-guidelines-review.md"
    "checklists/privacy-security-review.md"
    "checklists/performance-review.md"
    "checklists/iphone-review.md"
    "checklists/ipad-review.md"
    "checklists/accessibility-review.md"
    "checklists/visual-design-review.md"
    "checklists/release-review.md"
    "examples/navigation-examples.md"
    "examples/adaptive-layout-examples.md"
    "examples/native-components.md"
    "examples/animation-examples.md"
    "examples/design-system-example.md"
    "integrations/claude-code.md"
    "integrations/codex.md"
    "integrations/cursor.md"
    "integrations/github-copilot.md"
    "integrations/gemini-cli.md"
    "integrations/opencode.md"
    "integrations/vercel-skills.md"
)

log_info "Verifying core repository files..."
MISSING_FILES=0
for rel_path in "${EXPECTED_FILES[@]}"; do
    full_path="${REPO_ROOT}/${rel_path}"
    if [[ ! -f "${full_path}" ]]; then
        log_fail "Missing required file: ${rel_path}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if (( MISSING_FILES == 0 )); then
    log_pass "All ${#EXPECTED_FILES[@]} core structural files present and accounted for."
fi

# ------------------------------------------------------------------------------
# 4. Run Relative Link Integrity Check
# ------------------------------------------------------------------------------
log_info "Running cross-reference link validation..."
bash "${SCRIPT_DIR}/check-references.sh"

# ------------------------------------------------------------------------------
# 5. Summary & Exit Code
# ------------------------------------------------------------------------------
echo "----------------------------------------------------------"
if (( ERRORS == 0 )); then
    echo -e "${GREEN}✓ ALL VALIDATION CHECKS PASSED.${NC} (Warnings: ${WARNINGS})"
    exit 0
else
    echo -e "${RED}[FAIL] VALIDATION FAILED WITH ${ERRORS} ERROR(S).${NC} (Warnings: ${WARNINGS})"
    exit 1
fi
