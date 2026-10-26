#!/usr/bin/env bash
# Polls SOURCE's flat container or registration index until it lists VERSION for every id in
# PACKAGES (30s interval, 10-minute deadline). Writes indexed=true|false to GITHUB_OUTPUT.
set -euo pipefail

curl_args=(-sfL --compressed)
if [ -n "$FEED_USERNAME" ]; then
  curl_args+=(-u "${FEED_USERNAME}:${FEED_PASSWORD}")
fi

case "$INDEX" in
  flat-container) resource=PackageBaseAddress/3.0.0 ;;
  registration) resource=RegistrationsBaseUrl/3.6.0 ;;
  *) echo "::error::index must be flat-container or registration, got: $INDEX"; exit 1 ;;
esac
base="$(curl "${curl_args[@]}" "$SOURCE" | jq -r --arg t "$resource" '[.resources[] | select(."@type" == $t)][0]."@id" // empty')"
if [ -z "$base" ]; then
  echo "::error::no $resource in $SOURCE"
  exit 1
fi

served() {
  local id="${1,,}" wanted="${VERSION,,}"
  if [ "$INDEX" = flat-container ]; then
    curl "${curl_args[@]}" "${base%/}/${id}/index.json" | jq -e --arg v "$wanted" '.versions | index($v)' > /dev/null
  else
    # Paged indexes (128+ versions) don't inline their items; their `upper` bound still names the newest.
    curl "${curl_args[@]}" "${base%/}/${id}/index.json" |
      jq -e --arg v "$wanted" '[.items[] | (.upper, (.items[]?.catalogEntry.version))] | map(ascii_downcase) | index($v)' > /dev/null
  fi
}

deadline=$((SECONDS + 10 * 60))
for id in $(jq -r '.[]' <<< "$PACKAGES"); do
  until served "$id"; do
    if [ "$SECONDS" -ge "$deadline" ]; then
      echo "::warning::$id $VERSION not served by $SOURCE after 10 minutes"
      echo "indexed=false" >> "$GITHUB_OUTPUT"
      exit 0
    fi
    sleep 30
  done
  echo "$id $VERSION is served"
done
echo "indexed=true" >> "$GITHUB_OUTPUT"
