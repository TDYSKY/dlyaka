#!/usr/bin/env bash
# Install the DLYAKA Claude Code skill.
#
# Usage:
#   ./install.sh             # global (~/.claude/skills/)
#   ./install.sh --project   # current project (.claude/skills/)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/dlyaka"

if [[ "${1:-}" == "--project" ]]; then
    DEST=".claude/skills/dlyaka"
    echo "Installing skill into project: $DEST"
else
    DEST="$HOME/.claude/skills/dlyaka"
    echo "Installing skill globally: $DEST"
fi

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -r "$SKILL_SRC" "$DEST"

echo "Skill installed. Restart Claude Code (or open a new session) to pick it up."
