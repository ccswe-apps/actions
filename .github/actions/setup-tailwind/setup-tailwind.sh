#!/usr/bin/env bash
# Installs the Tailwind CSS standalone CLI pinned by `ARG TAILWIND_VERSION=<v>` in $ROOT/Dockerfile (the first
# such line with a value), so CI builds the same CSS as the image. Skips when there's no Dockerfile or no pinned
# version. Verifies the release's sha256sums.txt and the CLI's version banner, then puts it on $GITHUB_PATH.
set -euo pipefail

dockerfile="$ROOT/Dockerfile"
if [ ! -f "$dockerfile" ]; then
  echo "No Dockerfile at $dockerfile; skipping Tailwind"
  exit 0
fi

line="$(tr -d '\r' < "$dockerfile" | grep -m1 -E '^[[:space:]]*ARG[[:space:]]+TAILWIND_VERSION=' || true)"
if [ -z "$line" ]; then
  echo "No ARG TAILWIND_VERSION=<version> in $dockerfile; skipping Tailwind"
  exit 0
fi

version="${line#*=}"
version="$(printf '%s' "$version" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g; s/^"(.*)"$/\1/; s/^'"'"'(.*)'"'"'$/\1/')"
if ! [[ "$version" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+([-.][0-9A-Za-z.]+)?$ ]]; then
  echo "::error file=Dockerfile::ARG TAILWIND_VERSION must be a release version (e.g. v4.3.3), got '$version'"
  exit 1
fi
version="v${version#v}"

case "${RUNNER_ARCH:-X64}" in
  X64) arch=x64 ;;
  ARM64) arch=arm64 ;;
  *) echo "::error::Unsupported runner architecture ${RUNNER_ARCH}"; exit 1 ;;
esac

asset="tailwindcss-linux-$arch"
dir="$RUNNER_TEMP/tailwindcss"
rm -rf "$dir"
mkdir -p "$dir/bin"
base="https://github.com/tailwindlabs/tailwindcss/releases/download/$version"
curl -fsSL --retry 3 -o "$dir/$asset" "$base/$asset"
curl -fsSL --retry 3 -o "$dir/sha256sums.txt" "$base/sha256sums.txt"
(cd "$dir" && sha256sum -c --ignore-missing sha256sums.txt)

install -m 0755 "$dir/$asset" "$dir/bin/tailwindcss"
# The banner is colored on CI runners; strip ANSI escapes before comparing.
banner="$(NO_COLOR=1 "$dir/bin/tailwindcss" --help 2>&1 | sed -E $'s/\x1b\\[[0-9;]*m//g' || true)"
banner="${banner%%$'\n'*}"
if [[ "$banner" != *"tailwindcss $version"* ]]; then
  echo "::error::tailwindcss --help reported '$banner', expected tailwindcss $version"
  exit 1
fi

echo "$dir/bin" >> "$GITHUB_PATH"
echo "Installed $banner"
