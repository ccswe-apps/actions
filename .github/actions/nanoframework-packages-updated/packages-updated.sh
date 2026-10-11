#!/usr/bin/env bash
# Restores SOLUTION with lock files, runs `nuget update`, and fails if anything changed.
set -euo pipefail

nuget restore "$SOLUTION" -UseLockFile
nuget update "$SOLUTION"
if [ -n "$(git status --porcelain)" ]; then
  echo "::error::NuGet packages aren't on their latest versions; run the Update dependencies workflow"
  git status --short
  exit 1
fi
