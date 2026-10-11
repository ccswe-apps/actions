# Reusable workflow for npm projects

**Initial thoughts only.** These steps are a starting point, not a plan. Review each step thoroughly and think it through, re-verifying every finding against the current repos and docs, before planning or executing.

Related: `~/src/repo-standards/docs/tasks/cross-org-shared-actions.md`.

The repo setup, `dependabot.yml`, the lint self-tests and `@master` pinning already exist (see `README.md`, `CLAUDE.md`). Follow the Android workflows' shape.

The first caller is `ccswe-apps/ccswe.com`. Its `.github/workflows/ci.yml` `build` job does the following:
- checkout;
- `setup-node` (`.nvmrc`, npm cache);
- `npm ci`;
- `npx prettier --check .`;
- `npm run lint`;
- `npm run build` with site env vars.

Its Dependabot jobs are copies of `repo-standards/dependabot/merge-job.yml`.

Steps:
1. **Composite `.github/actions/npm-build`:**
   - `setup-node` (`.nvmrc`), `npm ci`, then format check, lint, build and test, each only when the matching `package.json` script exists;
   - a `prettier --check` fallback, since ccswe.com calls it directly;
   - build env as `KEY=value` lines written to `$GITHUB_ENV`;
   - shell in `npm-build.sh`.
   - Add the directory to `.github/dependabot.yml` if it uses external actions.
2. **Workflow `.github/workflows/npm-build-app.yml`** (naming: `<platform>-build-<app|library>.yml`):
   - job `build` uses the composite via `$/`;
   - job `dependabot` uses `$/.github/workflows/dependabot.yml`.
3. **Self-test `fixture-npm`:** a minimal npm project under `test/fixtures/npm`. Add the job id to `repo-standards/rulesets/ccswe.json` and `dependabot`'s `needs:`.
4. **ccswe.com:**
   - replace `build` and the Dependabot jobs with a `pipeline` job calling `npm-build-app.yml@master`, keeping its build env;
   - add the workflow path to `repo-standards/audit.py` `SHARED_DEPENDABOT`.

Delete this file when done.
