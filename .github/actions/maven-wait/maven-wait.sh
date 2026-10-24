#!/usr/bin/env bash
# Polls each group:name in PACKAGES under REPOSITORY_URL until its maven-metadata.xml lists
# VERSION (30s interval, 30-minute deadline). Writes served=true|false to GITHUB_OUTPUT.
set -euo pipefail

curl_args=(-sfL)
if [ -n "$MAVEN_USERNAME" ]; then
  curl_args+=(-u "${MAVEN_USERNAME}:${MAVEN_PASSWORD}")
fi

served() {
  local group="${1%%:*}" name="${1#*:}"
  curl "${curl_args[@]}" "${REPOSITORY_URL%/}/${group//.//}/${name}/maven-metadata.xml" |
    grep -F "<version>${VERSION}</version>" > /dev/null
}

deadline=$((SECONDS + 30 * 60))
for coordinate in $(jq -r '.[]' <<< "$PACKAGES"); do
  until served "$coordinate"; do
    if [ "$SECONDS" -ge "$deadline" ]; then
      echo "::warning::$coordinate $VERSION not served by $REPOSITORY_URL after 30 minutes"
      echo "served=false" >> "$GITHUB_OUTPUT"
      exit 0
    fi
    sleep 30
  done
  echo "$coordinate $VERSION is served"
done
echo "served=true" >> "$GITHUB_OUTPUT"
