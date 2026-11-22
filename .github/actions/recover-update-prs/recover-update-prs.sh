#!/usr/bin/env bash
# Re-dispatches the oldest conflicting bot update PR in REPO (see action.yml). Env: GH_TOKEN, REPO, OWNER,
# DEFAULT_BRANCH; optional RETRY_DELAY (seconds between mergeable re-queries, default 5) and DRY_RUN=1
# (print instead of commenting, closing or dispatching).
set -euo pipefail

RETRY_DELAY="${RETRY_DELAY:-5}"
BOT="app/andy-the-messenger-robot"
MARKER_RE='<!-- update-dependencies (\{.*\}) -->'
RECOVERED='<!-- recovered -->'

run() {
  if [ "${DRY_RUN:-}" = 1 ]; then
    echo "dry run: $*"
  else
    "$@"
  fi
}

# Bot update PRs with auto-merge on, not yet recovered, oldest first.
candidates="$(gh pr list -R "$REPO" --state open --limit 100 \
  --json number,author,headRefName,title,body,mergeable,autoMergeRequest,comments |
  jq -c --arg bot "$BOT" --arg recovered "$RECOVERED" '
    [.[] | select(.author.login == $bot and .autoMergeRequest != null and
      ((.headRefName | startswith("bot/update-dependencies/")) or (.headRefName | startswith("nfbot/update-dependencies/"))) and
      ([.comments[].body | contains($recovered)] | any | not))] | sort_by(.number) | .[]')"

[ -n "$candidates" ] || { echo "no bot update PRs to check"; exit 0; }

while IFS= read -r pr; do
  number="$(jq -r .number <<< "$pr")"
  mergeable="$(jq -r .mergeable <<< "$pr")"
  # GitHub computes mergeability lazily; a query starts it.
  for _ in 1 2 3; do
    [ "$mergeable" = UNKNOWN ] || break
    sleep "$RETRY_DELAY"
    mergeable="$(gh pr view "$number" -R "$REPO" --json mergeable | jq -r .mergeable)"
  done
  if [ "$mergeable" != CONFLICTING ]; then
    echo "#$number: $mergeable"
    continue
  fi

  branch="$(jq -r .headRefName <<< "$pr")"
  if [[ "$branch" == nfbot/* ]]; then
    payload='{}'
    run gh pr close "$number" -R "$REPO" --delete-branch --comment "Closed for a fresh nanodu run (merge conflict)."
  else
    body="$(jq -r .body <<< "$pr")"
    if [[ "$body" =~ $MARKER_RE ]]; then
      payload="${BASH_REMATCH[1]}"
    else
      # PRs opened before the marker: source name from the branch, version from the title, ids from "Bumps".
      name="$(cut -d/ -f3 <<< "$branch")"
      title="$(jq -r .title <<< "$pr")"
      payload="$(jq -nc --arg source "$OWNER/$name" --arg version "${title##* to }" --arg body "$body" \
        '{source: $source, version: $version,
          packages: [$body | split("\n")[] | capture("^Bumps (?<id>\\S+) from ").id] | unique}')"
    fi
    if ! jq -e '(.source | test("^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$")) and
        (.version | test("^[0-9]+\\.[0-9]+\\.[0-9]+(-[0-9A-Za-z.-]+)?(\\+[0-9A-Za-z.-]+)?$")) and
        (.packages | type == "array" and length > 0 and all(.[]; test("^[A-Za-z0-9._:-]+$")))' <<< "$payload" > /dev/null 2>&1; then
      echo "::warning::#$number: no usable update payload; leaving it for a person"
      continue
    fi
    run gh pr comment "$number" -R "$REPO" \
      --body "Re-dispatching the update from ${DEFAULT_BRANCH} (merge conflict). $RECOVERED"
  fi

  echo "::notice::#$number conflicts; re-dispatching update-dependencies $payload"
  jq -nc --argjson p "$payload" '{event_type: "update-dependencies", client_payload: $p}' |
    run gh api "repos/$REPO/dispatches" --input -
  exit 0
done <<< "$candidates"
