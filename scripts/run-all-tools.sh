#!/usr/bin/env bash
# ==============================================================================
# run-all-tools.sh
# Runs the full Apple Native Engineer toolkit pipeline on a project.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${1:-.}"

echo "=========================================================="
echo "  Apple Native Engineer — Running Full Toolkit Pipeline   "
echo "=========================================================="
echo "Target directory: ${TARGET_DIR}"

echo -e "\n[1/6] Running Project Inspector..."
python3 "${REPO_ROOT}/tools/project-inspector/inspect_project.py" "${TARGET_DIR}"

echo -e "\n[2/6] Running Privacy & Required-Reason API Auditor..."
python3 "${REPO_ROOT}/tools/privacy-auditor/audit_privacy.py" "${TARGET_DIR}" || true

echo -e "\n[3/6] Running Localization & RTL Checker..."
python3 "${REPO_ROOT}/tools/localization-checker/check_localization.py" --project-dir "${TARGET_DIR}" || true

echo -e "\n[4/6] Running WidgetKit & Live Activity Validator..."
python3 "${REPO_ROOT}/tools/widget-validator/validate_widget.py" --project-dir "${TARGET_DIR}" || true

echo -e "\n[5/6] Validating Metadata Template..."
python3 "${REPO_ROOT}/tools/metadata-validator/validate_metadata.py" "${REPO_ROOT}/templates/metadata/app_metadata_template.json"

echo -e "\n[6/6] Generating Release Readiness Report..."
python3 "${REPO_ROOT}/tools/release-readiness/generate_report.py" "${TARGET_DIR}"

echo -e "\n✓ Toolkit pipeline completed."
