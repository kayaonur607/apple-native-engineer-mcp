#!/usr/bin/env bash
# ==============================================================================
# install-skill.sh
# Cross-agent local installer for apple-native-engineer
# Installs or links the skill into Claude Code, Codex, Cursor, Gemini/Antigravity
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SKILL_NAME="apple-native-engineer"
SCOPE="project" # project or global
TARGET_AGENT="all"

print_usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -g, --global       Install globally to user home directory (default: current project)
  -p, --project      Install locally into current workspace
  -a, --agent AGENT  Target specific agent: claude, codex, cursor, gemini, opencode, all (default: all)
  -h, --help         Show this help message

Examples:
  ./scripts/install-skill.sh -p -a claude      # Install into current project for Claude Code
  ./scripts/install-skill.sh -g -a all         # Install globally for all supported agents
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -g|--global)
            SCOPE="global"
            shift
            ;;
        -p|--project)
            SCOPE="project"
            shift
            ;;
        -a|--agent)
            TARGET_AGENT="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            print_usage
            exit 1
            ;;
    esac
done

echo "Installing '${SKILL_NAME}' (Scope: ${SCOPE}, Agent: ${TARGET_AGENT})..."

install_for_agent() {
    local agent="$1"
    local target_dir=""
    
    case "${agent}" in
        claude)
            if [[ "${SCOPE}" == "global" ]]; then
                target_dir="${HOME}/.claude/skills/${SKILL_NAME}"
            else
                target_dir="$(pwd)/.claude/skills/${SKILL_NAME}"
            fi
            ;;
        codex)
            if [[ "${SCOPE}" == "global" ]]; then
                target_dir="${HOME}/.agents/skills/${SKILL_NAME}"
            else
                target_dir="$(pwd)/.agents/skills/${SKILL_NAME}"
            fi
            ;;
        cursor)
            if [[ "${SCOPE}" == "global" ]]; then
                target_dir="${HOME}/.cursor/skills/${SKILL_NAME}"
            else
                target_dir="$(pwd)/.cursor/skills/${SKILL_NAME}"
            fi
            ;;
        gemini)
            if [[ "${SCOPE}" == "global" ]]; then
                target_dir="${HOME}/.gemini/antigravity/skills/${SKILL_NAME}"
            else
                target_dir="$(pwd)/.gemini/skills/${SKILL_NAME}"
            fi
            ;;
        opencode)
            if [[ "${SCOPE}" == "global" ]]; then
                target_dir="${HOME}/.config/opencode/skills/${SKILL_NAME}"
            else
                target_dir="$(pwd)/.agents/skills/${SKILL_NAME}"
            fi
            ;;
        *)
            echo "Unrecognized agent: ${agent}"
            return 1
            ;;
    esac
    
    mkdir -p "$(dirname "${target_dir}")"
    
    if [[ -L "${target_dir}" ]] || [[ -e "${target_dir}" ]]; then
        echo "Removing existing installation at ${target_dir}..."
        rm -rf "${target_dir}"
    fi
    
    echo "Creating symlink to ${REPO_ROOT} at ${target_dir}..."
    ln -s "${REPO_ROOT}" "${target_dir}"
    echo "✓ Successfully installed for ${agent}."
}

if [[ "${TARGET_AGENT}" == "all" ]]; then
    for ag in claude codex cursor gemini opencode; do
        install_for_agent "${ag}"
    done
else
    install_for_agent "${TARGET_AGENT}"
fi

echo "All requested installations completed successfully."
