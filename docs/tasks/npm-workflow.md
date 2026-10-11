# Reusable workflow for npm projects

**Initial thoughts only.** These steps are a starting point, not a plan. Review each step thoroughly and think it through, re-verifying every finding against the current repos and docs, before planning or executing.

Related: `~/src/repo-standards/docs/tasks/cross-org-shared-actions.md`. This repo is the public host it describes, so callers under any owner can use what's here.

The first caller is `ccswe-apps/ccswe.com`. Its `.github/workflows/ci.yml` does the following:
- `build`: checkout, `setup-node` (`.nvmrc`, npm cache), `npm ci`, `npx prettier --check .`, `npm run lint`, and `npm run build` with site env vars;
- `dependabot-merge` and `dependabot-update` jobs, which are copies of `repo-standards/dependabot/merge-job.yml`.

Steps:
1. **Repo setup:**
   - `README.md` with the caller contract;
   - `CLAUDE.md`;
   - `.github/dependabot.yml` from `repo-standards/dependabot/templates/actions.yml` (library: Monday; list every composite directory);
   - an entry in `repo-standards/rulesets/ccswe.json` with the self-test job ids as required checks.
2. **Composite `.github/actions/npm-build`:**
   - `setup-node` (node version from `.nvmrc`, npm cache), `npm ci`, then format check, lint, build and test, each run only when the matching `package.json` script exists.
   - A `prettier --check` fallback, since ccswe.com calls it directly.
   - Build env passed as `KEY=value` lines (written to `$GITHUB_ENV`), because inputs can't be maps.
3. **Reusable workflow `.github/workflows/npm-build.yml`** (`workflow_call`):
   - job `build` uses the composite via `$/`; the caller's check becomes `<caller job> / build`;
   - job `dependabot` calls a shared Dependabot workflow.
4. **Shared Dependabot workflow** (`merge` and `update-behind`): port `midworld-apps/ci/.github/workflows/dependabot.yml`.
   - Pass `AUTOMATION_APP_ID`/`AUTOMATION_APP_KEY` by name at every level, because `secrets: inherit` doesn't cross orgs.
   - Keep the `--auto || direct merge` fallback for private repos on Free, which can't enable auto-merge.
5. **Self-tests `test.yml`:**
   - actionlint (pinned, with the `$/` ignores from `midworld-apps/ci/.github/workflows/test.yml`) and shellcheck;
   - a fixture npm project under `test/fixtures/` run through the composite.
6. **Pinning:** decide `@master` vs a moving `@v1` with a tag ruleset (andy as bypass actor) before the first cross-org caller. See question 4 in the cross-org task.
7. **ccswe.com:** replace `build` and the Dependabot jobs with a call to `npm-build.yml`, keeping its build env. Remove the jobs that `repo-standards/audit.py` no longer needs to find (its `SHARED_DEPENDABOT` must accept this repo's workflows).

Delete this file when done.
