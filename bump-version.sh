#!/bin/bash
# bump-version.sh — bump versi plugin
# Usage: ./bump-version.sh patch|minor|major
#   patch: 0.1.0 → 0.1.1
#   minor: 0.1.0 → 0.2.0
#   major: 0.1.0 → 1.0.0

set -e
cd "$(dirname "$0")"

METADATA="routing_plan/metadata.txt"
CURRENT=$(grep '^version=' "$METADATA" | head -1 | cut -d= -f2)
IFS='.' read -r MAJ MIN PAT <<< "$CURRENT"

case "${1:-patch}" in
    major) MAJ=$((MAJ + 1)); MIN=0; PAT=0 ;;
    minor) MIN=$((MIN + 1)); PAT=0 ;;
    patch) PAT=$((PAT + 1)) ;;
    *) echo "Usage: $0 patch|minor|major"; exit 1 ;;
esac

NEW="$MAJ.$MIN.$PAT"
sed -i '' "s/^version=.*/version=$NEW/" "$METADATA"
echo "$CURRENT → $NEW"
