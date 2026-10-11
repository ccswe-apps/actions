# CLAUDE.md

Public reusable workflows (`.github/workflows/`) and composite actions (`.github/actions/`) for any owner. See `README.md` for the list and caller rules.

## Placement

- **Here:** owner-agnostic pieces, such as build composites, app and library workflows, and Dependabot.
- **Owner repos:** deploys and distribution that only one owner uses (e.g. Midworld: `midworld-apps/ci` Rollout, `midworld-apps/manifests` bump). They run as extra caller jobs gated on this repo's workflow outputs. Never wrap these workflows in another reusable workflow: that renames the required check (`pipeline / build / build`).

## Conventions

- Workflow names: `<platform>-build-<app|library>.yml`. Publish and release are gated jobs inside them. Separate triggers get their own workflow (`dotnet-release-app.yml` on tags, `dotnet-update-dependencies.yml` on dispatch).
- nanoFramework jobs that need nanobuild, MSBuild, the NuGet CLI or nanodu run on `windows-latest`; everything else on ubuntu. There's no nanoFramework fixture: validate changes with a throwaway CCSWE.nanoFramework or Emily.Clock caller PR at `@<branch>`.
- npm callers follow the README's script contract (`format:check`, `lint`, `test`, `build`); change the contract and every caller together.
- The library workflows share `dispatch-dependents.yml` (nested; its check names gain a segment, none required) and the `nuget-wait` composite.
- `dotnet-build-library.yml`'s discovery matches listeners by the literal string `ccswe-apps/actions/.github/workflows/dotnet-update-dependencies.yml` (`nanoframework-build-library.yml`: `.../nanoframework-update-dependencies.yml`); renaming either file breaks every dependent until their listeners change.
- Called jobs have no `name:`. The required check is `<caller job> / build`.
- Same-repo references use `$/` (no `@ref`). actionlint 1.7.12 rejects `$/`; pass the `-ignore` patterns from `test.yml`.
- Composite shell lives in `*.sh` (or `*.py`) next to `action.yml`, so the `shellcheck` self-test covers it. Inputs reach shell only through `env:`.
- Secrets are declared in `on.workflow_call.secrets` and passed by name to nested calls.
- Pin external actions to their latest major. Dependabot covers `/` and every composite directory that uses external actions.

## Validation

- Locally: `actionlint` with the `test.yml` ignores, and `shellcheck .github/actions/*/*.sh`.
- Callers use `@master`, so a merge reaches every caller on its next run. Before merging a workflow change, point a throwaway caller PR at the branch (`@<branch>`) and check `pipeline / build`. PR runs don't reach the publish/release jobs.
