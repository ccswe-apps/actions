#!/usr/bin/env bash
# Writes the tracked files under $SOLUTION_PATH matching any of $TEST_PATTERNS
# (space-separated globs), NUL-delimited, to $RUNNER_TEMP/test-projects and sets
# the step output found=true|false.
set -euo pipefail

list="$RUNNER_TEMP/test-projects"
: > "$list"
read -ra patterns <<< "$TEST_PATTERNS"
for pattern in "${patterns[@]}"; do
  git -C "$SOLUTION_PATH" ls-files -z -- ":(glob)**/$pattern" |
    while IFS= read -r -d '' p; do
      printf '%s/%s\0' "${SOLUTION_PATH%/}" "$p"
    done >> "$list"
done
sort -zu -o "$list" "$list"

if [ -s "$list" ]; then
  tr '\0' '\n' < "$list"
  echo "found=true" >> "$GITHUB_OUTPUT"
else
  echo "::warning::No test projects matching '$TEST_PATTERNS' under $SOLUTION_PATH; skipping tests"
  echo "found=false" >> "$GITHUB_OUTPUT"
fi
