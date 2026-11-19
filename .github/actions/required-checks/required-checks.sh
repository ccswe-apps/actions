#!/usr/bin/env bash
# Env: GH_TOKEN, REPO, BRANCH, SHA.
set -euo pipefail

required="$(gh api "repos/${REPO}/rules/branches/${BRANCH}" \
  --jq '[.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[]] | unique')"
if [[ "$(jq 'length' <<< "$required")" == 0 ]]; then
  echo "::error::${BRANCH} has no required checks"
  exit 1
fi

runs="$(gh api --paginate "repos/${REPO}/commits/${SHA}/check-runs?per_page=100" --jq '.check_runs[]' | jq -s '.')"

failures="$(jq -r --argjson runs "$runs" '
  .[] as $check
  | [$runs[] | select(.name == $check.context
      and ($check.integration_id == null or .app.id == $check.integration_id))]
  | max_by(.id) as $run
  | if $run == null then "\($check.context): no check run"
    elif $run.status != "completed" then "\($check.context): \($run.status)"
    elif ($run.conclusion | IN("success", "skipped", "neutral")) then empty
    else "\($check.context): \($run.conclusion)"
    end' <<< "$required")"

if [[ -n "$failures" ]]; then
  while IFS= read -r line; do
    echo "::error::${line} on ${SHA:0:7} (wait for ${BRANCH} CI or re-run it)"
  done <<< "$failures"
  exit 1
fi
echo "All $(jq 'length' <<< "$required") required checks passed on ${SHA:0:7}"
