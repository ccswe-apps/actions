# Version this repo

Callers reference `@master`, so every merge reaches every caller on its next run, and a breaking change can only be staged with a throwaway caller at `@<branch>`. Release semver tags with a moving major (`v1`), like the npm action repos (`vstest-nanoframework`), and move callers to `@v1`. Internal `$/` references resolve at the caller's commit, so a tagged ref gets matching composites and nested workflows without changes here.

## Decide first

- Release flow: tag `v1.x.y` on master by hand and run `move-major-tag.yml`, or a release workflow (like `npm-release-action.yml`'s `verify` → `publish` → `major`) on a `v*` tag push.
- Which changes are breaking (removed/renamed inputs, outputs, secrets, job ids, required permissions, changed caller contracts) and how `v2` coexists with `v1` (fixes backported or `v1` frozen).
- Dependabot: whether the repo-standards templates' `github-actions` entry should open PRs for new majors of these workflows (it does for tagged reusable workflows and composites).

## Steps

1. Tag ruleset for `v*` with andy as a bypass actor (`move-major-tag.yml` requires it); add it to `ccswe-apps/repo-standards` `rulesets/`.
2. Release workflow or documented manual steps; first release `v1.0.0` + `v1` at current master.
3. README "Callers": reference `@v1`; replace "stage a breaking change by pointing one caller at `@<branch>`" with the release process. CLAUDE.md "Validation": throwaway caller PRs still test `@<branch>` before a release; a merge reaches callers only when `v1` moves.
4. Update every caller example in the workflow and composite headers to `@v1`.
5. Verify `discover-dependents` still finds listeners: it matches `uses: <updater>@` with any ref (`discover-dependents.py`), so `@v1` should match; add a `test/fixtures/listeners` case with `@v1`.
6. Move callers from `@master` to `@v1`, one PR per repo (`.github/workflows/*.yml` and composite `uses:`). Enumerate them with `grep -rl 'ccswe-apps/actions/' ~/src/*/*/.github` plus external owners' repos (e.g. Emily.Clock); include templates. Midworld app repos deploy on merge: squash with `[skip ci]` in the title.
7. repo-standards: `audit.py` flags a caller on `@master` once all are moved.

## Verification

- A caller at `@v1` passes `pipeline / build`; a library publish dispatches to a `@v1` listener.
- After a release, moving `v1` reaches callers on their next run; rolling `v1` back to the previous tag (`move-major-tag.yml` with an older target) works.
