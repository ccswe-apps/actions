#!/usr/bin/env bash
# Writes changed=true|false to GITHUB_OUTPUT: whether any of FILES changed in BEFORE..SHA.
# On an empty or zero BEFORE, diffs against the tip commit's first parent.
set -euo pipefail

base="$BEFORE"
if [ -z "$base" ] || [ "$base" = "0000000000000000000000000000000000000000" ]; then
  base="$(git rev-parse HEAD^ 2>/dev/null || true)"
fi
read -ra paths <<< "$FILES"
changed=false
if [ -n "$base" ] && git diff --name-only "$base" "$SHA" -- "${paths[@]}" | grep -q .; then
  changed=true
fi
echo "changed=$changed" >> "$GITHUB_OUTPUT"
