# Switch create-github-app-token to client-id

`actions/create-github-app-token@v3` deprecates `app-id` in favor of `client-id` and logs a warning on every run that passes `app-id` (seen in the dispatch, update-dependencies and dependabot jobs).

Blocked: actionlint 1.7.12, the latest release, still has the old input metadata. It reports `input "client-id" is not defined` and `missing input "app-id"`, which fails the required `actionlint` check.

## Steps

1. Wait for an actionlint release that knows `client-id` (check `gh release list -R rhysd/actionlint`); update the pinned actionlint here and in `~/.claude/TOOLS.md`.
2. In every workflow and composite that mints the andy token, add an optional `AUTOMATION_APP_CLIENT_ID` secret (the App's client ID) and pass `client-id:` when it's set, else `app-id:`. That's a minor release. Add the org secrets (Actions and Dependabot) and switch callers to pass it; removing `AUTOMATION_APP_ID` is a breaking change for the next major.
3. Validate with actionlint (ignore patterns in `.github/workflows/test.yml`) and a throwaway caller PR at `@<branch>`.

Delete this file when done.
