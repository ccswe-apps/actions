#!/usr/bin/env bash
# Runs every test project listed in $RUNNER_TEMP/test-projects (NUL-delimited),
# writing <project>.trx to $RUNNER_TEMP/TestResults, and fails after all have run if any failed.
set -uo pipefail

results="$RUNNER_TEMP/TestResults"
mkdir -p "$results"
failed=()
while IFS= read -r -d '' p; do
  echo "::group::test $p"
  if ! dotnet test "$p" --configuration Release --no-build --no-restore \
    --verbosity normal --logger "trx;LogFileName=$(basename "$p" .csproj).trx" \
    --results-directory "$results"; then
    failed+=("$p")
  fi
  echo "::endgroup::"
done < "$RUNNER_TEMP/test-projects"

for p in "${failed[@]}"; do
  echo "::error::Tests failed: $p"
done
[ ${#failed[@]} -eq 0 ]
