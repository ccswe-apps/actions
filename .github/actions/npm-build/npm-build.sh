#!/usr/bin/env bash
# npm ci, format:check, lint, test (if present) and build in WORKING_DIRECTORY. BUILD_ENV
# lines (KEY=value) are exported for the build. With COMMITTED_OUTPUT, fails unless the
# build leaves that path unchanged, and sets output stale=true so the composite uploads it as
# ARTIFACT_NAME.
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
  echo "stale=true" >> "$GITHUB_OUTPUT"
  path="${WORKING_DIRECTORY%/}/$COMMITTED_OUTPUT"
  path="${path#./}"
  rebuild="npm ci && npm run build"
  [ "${WORKING_DIRECTORY%/}" = . ] || rebuild="cd ${WORKING_DIRECTORY%/} && $rebuild"
  node="$(node --version)"
  download="rm -rf $path && gh run download $GITHUB_RUN_ID -R $GITHUB_REPOSITORY -n $ARTIFACT_NAME -D $path"
  echo "::error::$path is out of date. Rebuild it with Node $node (\`$rebuild\`) or download the expected build (\`$download\`), then commit $path."
  {
    echo "### \`$path\` is out of date"
    echo
    echo "Rebuild it with Node $node and commit it: \`$rebuild\`"
    echo
    echo "Or download the expected build (artifact \`$ARTIFACT_NAME\`) and commit it:"
    echo
    echo '```bash'
    echo "$download"
    echo '```'
  } >> "$GITHUB_STEP_SUMMARY"
  git status --short -- "$COMMITTED_OUTPUT"
  git diff --stat -- "$COMMITTED_OUTPUT"
  exit 1
fi
