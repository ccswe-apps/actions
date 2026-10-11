#!/usr/bin/env bash
# npm ci, format:check, lint, test (if present) and build in WORKING_DIRECTORY. BUILD_ENV
# lines (KEY=value) are exported for the build. With COMMITTED_OUTPUT, fails unless the
# build leaves that path unchanged.
set -euo pipefail

cd "$WORKING_DIRECTORY"
npm ci
npm run format:check
npm run lint
npm run test --if-present

while IFS= read -r line; do
  [ -n "$line" ] || continue
  if [[ "$line" != *=* ]]; then
    echo "::error::build-env lines must be KEY=value: $line"
    exit 1
  fi
  export "${line?}"
done <<< "$BUILD_ENV"
npm run build

# Changed or new files under COMMITTED_OUTPUT relative to what's checked in.
if [ -n "$COMMITTED_OUTPUT" ] &&
  { ! git diff --quiet -- "$COMMITTED_OUTPUT" || [ -n "$(git ls-files --others --exclude-standard -- "$COMMITTED_OUTPUT")" ]; }; then
  echo "::error::$COMMITTED_OUTPUT is out of date: run \`npm run build\` and commit $COMMITTED_OUTPUT"
  git status --short -- "$COMMITTED_OUTPUT"
  git diff --stat -- "$COMMITTED_OUTPUT"
  exit 1
fi
