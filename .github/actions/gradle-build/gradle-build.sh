#!/usr/bin/env bash
# Appends GRADLE_PROPERTIES to the user-level gradle.properties (setup-gradle may
# already have written it), then runs TASKS with the wrapper in WORKING_DIRECTORY.
set -euo pipefail

if [ -n "$GRADLE_PROPERTIES" ]; then
  mkdir -p "$HOME/.gradle"
  printf '%s\n' "$GRADLE_PROPERTIES" >> "$HOME/.gradle/gradle.properties"
fi

cd "$WORKING_DIRECTORY"
chmod +x gradlew
read -ra task_list <<< "$TASKS"
./gradlew "${task_list[@]}"
