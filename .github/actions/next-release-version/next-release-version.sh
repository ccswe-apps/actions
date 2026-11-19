#!/usr/bin/env bash
# Writes version, major and previous to $GITHUB_OUTPUT. Env: BUMP (patch|minor|major).
set -euo pipefail

stable='^v[0-9]+\.[0-9]+\.[0-9]+$'

case "$BUMP" in
  patch | minor | major) ;;
  *) echo "::error::bump must be patch, minor or major, not '${BUMP}'"; exit 1 ;;
esac

released="$(git tag --points-at HEAD | grep -E "$stable" || true)"
if [[ -n "$released" ]]; then
  echo "::error::$(git rev-parse --short HEAD) is already released as ${released//$'\n'/, }"
  exit 1
fi

previous="$(git tag -l 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname | grep -E "$stable" | awk 'NR==1' || true)"
IFS=. read -r major minor patch <<< "${previous:-v0.0.0}"
major="${major#v}"
case "$BUMP" in
  patch) patch=$((patch + 1)) ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  major) major=$((major + 1)); minor=0; patch=0 ;;
esac

version="v${major}.${minor}.${patch}"
echo "Next release: ${version} (previous: ${previous:-none})"
{
  echo "version=${version}"
  echo "major=v${major}"
  echo "previous=${previous}"
} >> "$GITHUB_OUTPUT"
