#!/usr/bin/env bash
# Fails unless each .nfproj listed in SOLUTION has a packages.lock.json next to it.
set -euo pipefail

sln="${SOLUTION//\\//}"
if [ ! -f "$sln" ]; then
  echo "::error::Solution not found: $sln"
  exit 1
fi
root="$(dirname "$sln")"
mapfile -t projects < <(grep -oE '[^"]+\.nfproj' "$sln")
projects=("${projects[@]//\\//}")
if [ ${#projects[@]} -eq 0 ]; then
  echo "::error::No .nfproj projects found in $sln"
  exit 1
fi
missing=0
for project in "${projects[@]}"; do
  lock="$(dirname "$root/$project")/packages.lock.json"
  if [ ! -f "$lock" ]; then
    echo "::error::Missing $lock (run 'nuget restore -UseLockFile')"
    missing=1
  fi
done
exit "$missing"
