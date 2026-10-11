# actions

Reusable GitHub Actions workflows and composite actions shared across owners. The repo is public so any owner can call them.

Owner-specific steps (deploys, distribution) stay in the owner's own CI repo and run as extra caller jobs. For example, `midworld-apps/ci`'s `rollout-publish.yml` runs after `android-build-app.yml`.

## Workflows

| Workflow | Jobs |
|---|---|
| `android-build-app.yml` | `build` → `release` (signed APK as the `release-apk` artifact, on a version bump) · `dependabot` |
| `android-build-library.yml` | `build` → `publish` (GitHub Packages Maven, on a version bump) · `dependabot` |
| `dependabot.yml` | `merge` (non-major Dependabot PRs) · `update-behind` |

The caller shape, inputs and contract are in each workflow's header.

Callers:
- Keep the calling job id `pipeline`. The required check is `pipeline / build`.
- Set `permissions:` and `concurrency:` in the caller workflow. A called workflow can only lower permissions, and it sees the caller's `github.workflow`.
- Pass secrets by name. `secrets: inherit` doesn't cross orgs.
- Reference `@master` for now.

## Composite actions

- `gradle-build`: JDK (Temurin) and Gradle setup, CI `gradle.properties` lines (appended), the wrapper run, and an optional coverage artifact.
- `version-changed`: whether any watched file changed in the pushed range.

## Self-tests

`test.yml` runs on PRs and master pushes, and its job ids are required checks:
- `actionlint`
- `shellcheck` on the composite scripts
- `fixture-gradle` (`gradle-build` against `test/fixtures/gradle`)

Inside this repo, workflows reference the composites with `$/` (`uses: $/.github/actions/gradle-build`). That resolves to this repo at the running commit, even when the workflow is called from another owner.
