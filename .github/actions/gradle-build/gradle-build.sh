#!/usr/bin/env bash
# Appends GRADLE_PROPERTIES to the user-level gradle.properties (setup-gradle may
# already have written it), drops caches and distributions of other Gradle
# versions, then runs TASKS with the wrapper in WORKING_DIRECTORY.
set -euo pipefail

if [ -n "$GRADLE_PROPERTIES" ]; then
  mkdir -p "$HOME/.gradle"
  printf '%s\n' "$GRADLE_PROPERTIES" >> "$HOME/.gradle/gradle.properties"
fi

cd "$WORKING_DIRECTORY"

# A cache saved before a wrapper upgrade restores the old version's caches/<version>
# (transforms, Kotlin DSL); the build never reads them.
version=$(sed -nE 's#^distributionUrl=.*/gradle-(.+)-(bin|all)\.zip$#\1#p' gradle/wrapper/gradle-wrapper.properties 2>/dev/null || true)
if [ -n "$version" ]; then
  for dir in "$HOME"/.gradle/caches/[0-9]*/ "$HOME"/.gradle/wrapper/dists/gradle-*/; do
    [ -d "$dir" ] || continue
    case "$(basename "$dir")" in
      "$version" | "gradle-$version-"*) ;;
      *) echo "Removing $dir"; rm -rf "$dir" ;;
    esac
  done
fi
df -h /

chmod +x gradlew
read -ra task_list <<< "$TASKS"
./gradlew "${task_list[@]}"
