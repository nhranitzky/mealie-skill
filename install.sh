#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/mealie" && pwd)"
TARGET="${1:-}"

if [[ -z "$TARGET" ]]; then
    echo "Usage: $0 <target-directory>"
    echo "Example: $0 /home/pi/skills"
    exit 1
fi

TARGET="${TARGET%/}/mealie"

# If target exists and is non-empty, ask for confirmation before deleting
if [[ -d "$TARGET" ]] && [[ -n "$(ls -A "$TARGET" 2>/dev/null)" ]]; then
    echo "Target directory already exists and is not empty: $TARGET"
    read -r -p "Delete existing contents and reinstall? [y/N] " answer
    case "$answer" in
        [yY][eE][sS]|[yY])
            echo "Removing $TARGET ..."
            rm -rf "$TARGET"
            ;;
        *)
            echo "Aborted."
            exit 0
            ;;
    esac
fi

echo "Installing mealie skill to $TARGET ..."
cp -r "$SKILL_DIR" "$TARGET"
chmod +x "$TARGET/bin/mealie-cli"
echo "Done. Skill installed at $TARGET"
