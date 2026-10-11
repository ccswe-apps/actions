#!/usr/bin/env bash
# Packs the solution in $SOLUTION_PATH (built with --configuration Release) to
# $RUNNER_TEMP/nupkg and fails unless every IsPackable project produced
# <PackageId>.$PACKAGE_VERSION.nupkg. Sets the step outputs directory and
# packages (JSON array of package ids).
set -euo pipefail

out="$RUNNER_TEMP/nupkg"
rm -rf "$out"
dotnet pack "$SOLUTION_PATH" --no-build --configuration Release --output "$out"

ids=()
missing=0
while IFS= read -r project; do
  project="${SOLUTION_PATH%/}/${project//\\//}"
  props="$(dotnet msbuild "$project" -getProperty:IsPackable -getProperty:PackageId)"
  [ "$(jq -r '.Properties.IsPackable' <<< "$props")" = true ] || continue
  id="$(jq -r '.Properties.PackageId' <<< "$props")"
  ids+=("$id")
  if [ ! -f "$out/$id.$PACKAGE_VERSION.nupkg" ]; then
    echo "::error::$project did not produce $id.$PACKAGE_VERSION.nupkg"
    missing=1
  fi
done < <(cd "$SOLUTION_PATH" && dotnet sln list | grep -E '\.(cs|fs|vb)proj$')

if [ ${#ids[@]} -eq 0 ]; then
  echo "::error::No packable projects under $SOLUTION_PATH"
  exit 1
fi
[ "$missing" -eq 0 ]

ls "$out"
echo "directory=$out" >> "$GITHUB_OUTPUT"
echo "packages=$(printf '%s\n' "${ids[@]}" | jq -R . | jq -sc 'sort')" >> "$GITHUB_OUTPUT"
