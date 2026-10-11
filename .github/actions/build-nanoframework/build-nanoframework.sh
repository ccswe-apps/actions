#!/usr/bin/env bash
# Locked restore (when lock files are tracked) and a Release MSBuild of SOLUTION, stamped
# with the nbgv versions when HAS_VERSION_JSON is true.
set -euo pipefail

if [ "$HAS_VERSION_JSON" = true ] && [ -z "${NBGV_NuGetPackageVersion:-}" ]; then
  echo "::error::nbgv produced an empty NuGetPackageVersion"
  exit 1
fi

restore_args=()
if [ -n "$(git ls-files '*packages.lock.json')" ]; then
  restore_args+=(-LockedMode)
fi
nuget restore "$SOLUTION" "${restore_args[@]}"

build_args=(-p:Configuration=Release)
if [ -n "${NBGV_AssemblyVersion:-}" ]; then
  build_args+=(
    "-p:AssemblyVersion=$NBGV_AssemblyVersion"
    "-p:FileVersion=${NBGV_AssemblyFileVersion:-}"
    "-p:InformationalVersion=${NBGV_AssemblyInformationalVersion:-}"
  )
fi
MSBuild.exe "$SOLUTION" "${build_args[@]}"
