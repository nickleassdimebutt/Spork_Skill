#!/usr/bin/env bash
# install.sh — copy SPORK files into ~/.claude/ on macOS / Linux / WSL.
# Functional equivalent of install.ps1; cross-platform portability.
# Re-run after every edit during Phase B iteration.

set -euo pipefail

# Locate this script's directory regardless of where it's invoked from.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
CLAUDE_ROOT="${HOME}/.claude"
SKILL_DEST="${CLAUDE_ROOT}/skills/spork"
COMMAND_DEST="${CLAUDE_ROOT}/commands/spork.md"

echo "SPORK install"
echo "  Source: ${SCRIPT_DIR}"
echo "  Skill  -> ${SKILL_DEST}"
echo "  Cmd    -> ${COMMAND_DEST}"

if [ ! -d "${CLAUDE_ROOT}" ]; then
    echo "ERROR: ~/.claude not found at ${CLAUDE_ROOT}. Run Claude Code at least once before installing." >&2
    exit 1
fi

# Ensure target parent dirs exist.
mkdir -p "$(dirname "${SKILL_DEST}")"
mkdir -p "$(dirname "${COMMAND_DEST}")"

# Copy skill (overwrite, preserving directory structure).
if [ -d "${SKILL_DEST}" ]; then
    rm -rf "${SKILL_DEST}"
fi
cp -R "${SCRIPT_DIR}/skills/spork" "${SKILL_DEST}"

# Copy command.
cp -f "${SCRIPT_DIR}/commands/spork.md" "${COMMAND_DEST}"

echo "Done."
echo "Invoke with: /spork  (or natural language: 'set up SPORK')"
