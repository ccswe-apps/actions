# Switch create-github-app-token to client-id

`actions/create-github-app-token@v3` deprecates `app-id` in favor of `client-id` and logs a warning on every run that passes `app-id` (seen in the dispatch, update-dependencies and dependabot jobs).

Blocked: actionlint 1.7.12, the latest release, still has the old input metadata. It reports `input "client-id" is not defined` and `missing input "app-id"`, which fails the required `actionlint` check.

## Steps

1. Wait for an actionlint release that knows `client-id` (check `gh release list -R rhysd/actionlint`); update the pinned actionlint here and in `~/.claude/TOOLS.md`.
2. Replace `app-id:` with `client-id:` in every workflow and composite that mints the andy token, and switch the secret from `AUTOMATION_APP_ID` to the App's client ID (add a new secret; check the owner orgs' Actions and Dependabot secrets and the callers that pass it).
3. Validate with actionlint (ignore patterns in `.github/workflows/test.yml`) and a throwaway caller PR at `@<branch>`.

Delete this file when done.
