#!/usr/bin/env bash
# Install global skills to ~/.claude/skills/
# Run once per machine after cloning to ~/agent-scaffold/

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DST="$HOME/.claude/skills"

mkdir -p "$SKILLS_DST"

for skill_dir in "$REPO_DIR/global/skills"/*/; do
    name=$(basename "$skill_dir")
    if [ -d "$SKILLS_DST/$name" ]; then
        echo "Updating skill: $name"
        rm -rf "$SKILLS_DST/$name"
    else
        echo "Installing skill: $name"
    fi
    cp -r "$skill_dir" "$SKILLS_DST/$name"
done

echo "Done. Skills installed to $SKILLS_DST"
echo "Tools are called directly from $REPO_DIR/global/tools/ — no install needed."
