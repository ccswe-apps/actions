# actions

Reusable GitHub Actions workflows and composite actions shared across owners. The repo is public so any owner can call them.

Owner-specific steps (deploys, distribution) run as extra caller jobs from the owner's own repos. For example, Midworld apps run `midworld-apps/ci`'s `rollout-publish.yml` after `android-build-app.yml`, and `midworld-apps/manifests`' `bump-manifests.yml` after `dotnet-build-app.yml`.

## Workflows

| Workflow | Jobs |
|---|---|
| `android-build-app.yml` | `build` (on a version-bump push, only the signed APK as the `release-apk` artifact; tests ran on the PR) · `dependabot` |
| `android-build-library.yml` | `build` (on a version-bump push, only `publish` to GitHub Packages Maven; tests ran on the PR) · `dependabot` |
| `dotnet-build-app.yml` | `build` → `publish` (GHCR image, opt-in, on a default-branch push) → `prune` · `dependabot` |
| `dotnet-build-library.yml` | `build` (optional `dotnet-validate`) → `publish` (nuget.org with `NUGET_API_KEY`, else GitHub Packages; when packable files changed; waits until the feed serves them) → `dependents` (dispatch `update-dependencies`) · `dependabot` |
| `dotnet-release-app.yml` | `release` (per-runtime archives as GitHub Release assets, on a version tag) |
| `dotnet-update-dependencies.yml` | `update` (consumer side of `dependents`: bump, PR, auto-merge unless major) |
| `nanoframework-build-app.yml` | `build` (Windows) · `package-lock` · `packages-updated` (PRs) · `dependabot` |
| `nanoframework-build-library.yml` | `build` (Windows, nuspec pack) → `publish` (nuget.org, when packable files changed; waits for the registration index) → `dependents` · `package-lock` · `packages-updated` (PRs) · `dependabot` |
| `nanoframework-update-dependencies.yml` | nanodu update PR (cron/dispatch) → `manage-prs` (close superseded, auto-merge unless major) |
| `npm-build-app.yml` | `build` (npm ci, format:check, lint, test, build with build env) · `dependabot` |
| `npm-build-action.yml` | `build` (the same, then fails unless the committed `dist/` matches the build) · `dependabot` |
| `npm-release-action.yml` | on a version tag: `verify` (tag on the default branch, `npm-build` with the `dist/` check) → `publish` (GitHub Release) → `major` (move the major tag) |
| `move-major-tag.yml` | moves a major tag (e.g. `v2`) with the andy App token; also a manual rollback |
| `dispatch-dependents.yml` | nested in the library workflows: find dependents, send `update-dependencies` |
| `dependabot.yml` | `merge` (non-major Dependabot PRs) · `update-behind` |

The caller shape, inputs and contract are in each workflow's header.

Callers:
- Keep the calling job id `pipeline`. The required check is `pipeline / build`.
- Set `permissions:` and `concurrency:` in the caller workflow. A called workflow can only lower permissions, and it sees the caller's `github.workflow`.
- Pass secrets by name. `secrets: inherit` doesn't cross orgs.
- Reference `@master`: there are no release tags, so stage a breaking change by pointing one caller at `@<branch>` first.

## Composite actions

- `dotnet-build`: nbgv version, restore, build, then the test projects matching `test-patterns`, with a test report and TRX artifact.
- `dotnet-pack`: packs every `IsPackable` project at the given version and checks each package exists.
- `discover-dependents`: an account's repos whose `update-dependencies` listener calls a given updater workflow.
- `update-package-versions`: sets package ids to one version in every tracked `Directory.Packages.props`.
- `setup-nanoframework`, `build-nanoframework`: nanobuild, MSBuild and NuGet CLI (Windows); locked restore and Release build stamped with nbgv.
- `nanoframework-package-lock`, `nanoframework-packages-updated`: the nanoFramework PR checks.
- `nuget-wait`: waits until a feed's flat container (exact restore) or registration index ("latest") lists every package version.
- `npm-build`: Node from `.nvmrc`, `npm ci`, then `npm run format:check`, `lint`, `test` (if present) and `build`; optional build env and committed-output check.
- `gradle-build`: JDK (Temurin) and Gradle setup, CI `gradle.properties` lines (appended), the wrapper run, and an optional coverage artifact.
- `version-changed`: whether any watched file changed in the pushed range.

## Self-tests

`test.yml` runs on PRs and master pushes, and its job ids are required checks:
- `actionlint`
- `shellcheck` on the composite scripts
- `fixture-gradle` (`gradle-build` against `test/fixtures/gradle`)
- `fixture-dotnet-{pass,fail,no-tests,library,update}` (the .NET composites against `test/fixtures/dotnet`)
- `fixture-discover` (`discover-dependents --local` against `test/fixtures/listeners`)
- `fixture-npm-app`, `fixture-npm-action`, `fixture-npm-action-stale` (`npm-build` against `test/fixtures/npm`)

Inside this repo, workflows reference the composites with `$/` (`uses: $/.github/actions/gradle-build`). That resolves to this repo at the running commit, even when the workflow is called from another owner.

## npm script contract

npm callers provide these `package.json` scripts: `format` (write), `format:check`, `lint`, `test` (single run; optional), `test:coverage`, `build`. CI runs `format:check`, `lint`, `test` and `build`.

## Migrating from `ccswe-nanoframework/actions-nanoframework`

That repo is archived; its workflows live here now.

| Old | New |
|---|---|
| `nanoframework-build-publish.yml` with `publish-nuget: true` | `nanoframework-build-library.yml` |
| `nanoframework-build-publish.yml` without `publish-nuget` | `nanoframework-build-app.yml` |
| `nanoframework-update-dependencies.yml` | `nanoframework-update-dependencies.yml` (same inputs) |
| `.github/actions/setup-nanoframework`, `build-nanoframework` | `ccswe-apps/actions/.github/actions/setup-nanoframework`, `build-nanoframework` |

- The library workflow takes `NUGET_API_KEY` (was `NUGET_ORG_API_KEY`), publishes only when `src`, `version.json`, `Directory.Build.props` or `nuget.config` change, and adds `discover-dependents` next to `dependents`.
- Dependents are found by a listener calling `ccswe-apps/actions/.github/workflows/nanoframework-update-dependencies.yml`; update the listener when the library switches.
- Check names stay `pipeline / build`, `pipeline / package-lock`, `pipeline / packages-updated`.
