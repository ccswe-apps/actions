# CLAUDE.md

Public reusable workflows (`.github/workflows/`) and composite actions (`.github/actions/`) for any owner. See `README.md` for the list and caller rules.

## Placement

- **Here:** owner-agnostic pieces, such as build composites, app and library workflows, and Dependabot.
- **Owner CI repo:** deploys and distribution that only one owner uses (e.g. `midworld-apps/ci`: Rollout, GHCR/manifests). They run as extra caller jobs gated on this repo's workflow outputs. Never wrap these workflows in another reusable workflow: that renames the required check (`pipeline / build / build`).

## Conventions

- Workflow names: `<platform>-build-<app|library>.yml`. Publish and release are gated jobs inside them.
- Called jobs have no `name:`. The required check is `<caller job> / build`.
- Same-repo references use `$/` (no `@ref`). actionlint 1.7.12 rejects `$/`; pass the `-ignore` patterns from `test.yml`.
- Composite shell lives in `*.sh` next to `action.yml`, so the `shellcheck` self-test covers it. Inputs reach shell only through `env:`.
- Secrets are declared in `on.workflow_call.secrets` and passed by name to nested calls.
- Pin external actions to their latest major. Dependabot covers `/` and every composite directory that uses external actions.

## Validation

- Locally: `actionlint` with the `test.yml` ignores, and `shellcheck .github/actions/*/*.sh`.
- Callers use `@master`, so a merge reaches every caller on its next run. Before merging a workflow change, point a throwaway caller PR at the branch (`@<branch>`) and check `pipeline / build`. PR runs don't reach the publish/release jobs.
