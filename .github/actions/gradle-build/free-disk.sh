#!/usr/bin/env bash
# Removes preinstalled toolchains no Gradle build uses. Runs in the background,
# overlapping the JDK setup and the Gradle cache restore.
set -euo pipefail

df -h /
sudo -n rm -rf \
  /usr/share/dotnet \
  /usr/local/.ghcup \
  /opt/ghc \
  /usr/share/swift \
  /opt/hostedtoolcache/CodeQL \
  >/dev/null 2>&1 &
