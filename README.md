# actions

Reusable GitHub Actions workflows and composite actions shared across owners. The repo is public so any owner can call them.

Owner-specific steps (deploys, distribution) run as extra caller jobs from the owner's own repos. For example, Midworld apps run `midworld-apps/ci`'s `rollout-publish.yml` after `android-build-app.yml`, and `midworld-apps/manifests`' `bump-manifests.yml` after `dotnet-build-app.yml`.

## Workflows

| Workflow | Jobs |
|---|---|
| `android-build-app.yml` | `build` → `release` (signed APK as the `release-apk` artifact, on a version bump) · `dependabot` |
| `android-build-library.yml` | `build` → `publish` (GitHub Packages Maven, on a version bump) · `dependabot` |
| `dotnet-build-app.yml` | `build` → `publish` (GHCR image, opt-in, on a default-branch push) → `prune` · `dependabot` |
| `dotnet-build-library.yml` | `build` (optional `dotnet-validate`) → `publish` (nuget.org with `NUGET_API_KEY`, else GitHub Packages; when packable files changed; waits until the feed serves them) → `dependents` (dispatch `update-dependencies`) · `dependabot` |
| `dotnet-release-app.yml` | `release` (per-runtime archives as GitHub Release assets, on a version tag) |
| `dotnet-update-dependencies.yml` | `update` (consumer side of `dependents`: bump, PR, auto-merge unless major) |
| `dependabot.yml` | `merge` (non-major Dependabot PRs) · `update-behind` |

The caller shape, inputs and contract are in each workflow's header.

Callers:
- Keep the calling job id `pipeline`. The required check is `pipeline / build`.
- Set `permissions:` and `concurrency:` in the caller workflow. A called workflow can only lower permissions, and it sees the caller's `github.workflow`.
- Pass secrets by name. `secrets: inherit` doesn't cross orgs.
- Reference `@master` for now.

## Composite actions

- `dotnet-build`: nbgv version, restore, build, then the test projects matching `test-patterns`, with a test report and TRX artifact.
- `dotnet-pack`: packs every `IsPackable` project at the given version and checks each package exists.
- `discover-dependents`: an account's repos whose `update-dependencies` listener calls a given updater workflow.
- `update-package-versions`: sets package ids to one version in every tracked `Directory.Packages.props`.
- `gradle-build`: JDK (Temurin) and Gradle setup, CI `gradle.properties` lines (appended), the wrapper run, and an optional coverage artifact.
- `version-changed`: whether any watched file changed in the pushed range.

## Self-tests

`test.yml` runs on PRs and master pushes, and its job ids are required checks:
- `actionlint`
- `shellcheck` on the composite scripts
- `fixture-gradle` (`gradle-build` against `test/fixtures/gradle`)
- `fixture-dotnet-{pass,fail,no-tests,library,update}` (the .NET composites against `test/fixtures/dotnet`)
- `fixture-discover` (`discover-dependents --local` against `test/fixtures/listeners`)

Inside this repo, workflows reference the composites with `$/` (`uses: $/.github/actions/gradle-build`). That resolves to this repo at the running commit, even when the workflow is called from another owner.
