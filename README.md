# actions

Reusable GitHub Actions workflows and composite actions shared across owners. The repo is public so any owner can call them.

Owner-specific steps (deploys, distribution) run as extra caller jobs from the owner's own repos. For example, Midworld apps run `midworld-apps/ci`'s `rollout-publish.yml` after `android-build-app.yml`, and `midworld-apps/manifests`' `bump-manifests.yml` after `dotnet-build-app.yml`.

## Workflows

| Workflow | Jobs |
|---|---|
| `android-build-app.yml` | `build` (on a version-bump push, only the signed APK as the `release-apk` artifact, or with `bundle-modules` each module's AAB and R8 mapping as `release-aab`, kept 14 days; tests ran on the PR) · `dependabot` |
| `android-build-library.yml` | `build` (on a version-bump push, only `publish` to GitHub Packages Maven and wait until it serves them; tests ran on the PR) → `dependents` · `dependabot` |
| `android-update-dependencies.yml` | `update` (consumer side of `dependents`: bump `gradle/libs.versions.toml`, PR, auto-merge unless breaking; see [Update PRs](#update-prs)) |
| `gradle-dependency-submission.yml` | `submit` (resolves every Gradle configuration, including `buildSrc` and plugin classpaths, and submits the dependency graph for Dependabot alerts; for a weekly `schedule` caller with `contents: write`; see the header) |
| `dotnet-build-app.yml` | `build` → `publish` (GHCR image, opt-in, on a default-branch push; then prunes old image versions) · `dependabot` |
| `dotnet-build-library.yml` | `build` (optional `dotnet-validate`) → `publish` (GitHub Packages; when packable files changed; waits until the feed serves them) → `dependents` (dispatch `update-dependencies`) · `dependabot`. With `nuget-org: true`, `publish` (`nuget-org-publish`) and `dependents` are caller jobs; see the header |
| `dotnet-release-app.yml` | `release` (per-runtime archives as GitHub Release assets, on a version tag) |
| `dotnet-update-dependencies.yml` | `update` (consumer side of `dependents`: bump, PR, auto-merge unless major; see [Update PRs](#update-prs)) |
| `nanoframework-build-app.yml` | `build` (Windows) · `package-lock` · `packages-updated` (PRs) · `dependabot` |
| `nanoframework-build-library.yml` | `build` (Windows, nuspec pack; outputs `publish` when packable files changed) · `package-lock` · `packages-updated` (PRs) · `dependabot`. The caller adds `publish` (`nuget-org-publish`) and `dependents` (`dispatch-dependents.yml`) jobs; see the header |
| `nanoframework-update-dependencies.yml` | nanodu update PR (cron/dispatch) → `manage-prs` (close superseded, auto-merge unless major) |
| `npm-build-app.yml` | `build` (npm ci, format:check, lint, test, build with build env) · `dependabot` |
| `npm-build-action.yml` | `build` (the same, then fails unless the committed `dist/` matches the build, uploading the expected `dist/` as artifact `committed-output`) · `dependabot` |
| `release-tag.yml` | on dispatch: `verify` (default branch, every required check passed on the commit, next version) → `release` (tag and GitHub Release) → `major` (move the major tag); see [Releases](#releases) |
| `move-major-tag.yml` | moves a major tag (e.g. `v2`) with the andy App token; also a manual rollback |
| `dispatch-dependents.yml` | nested in the GitHub Packages library workflows, a caller job for nuget.org libraries: find dependents, send `update-dependencies` (see [Dependents](#dependents)) |
| `dependabot.yml` | `merge` (non-major Dependabot PRs) · `update-behind` (updates behind auto-merge bot PRs; re-dispatches the oldest conflicting bot update PR, `recover-update-prs`) |

The caller shape, inputs and contract are in each workflow's header.

Callers:
- Keep the calling job id `pipeline`. The required check is `pipeline / build`.
- Set `permissions:` and `concurrency:` in the caller workflow. A called workflow can only lower permissions, and it sees the caller's `github.workflow`.
- Pass secrets by name. `secrets: inherit` doesn't cross orgs.
- Reference the major tag (`@v1`). It moves only when a release is cut ([Releases](#releases)).

## Releases

This repo and callers using `release-tag.yml` release by dispatch from the default branch:

```bash
gh workflow run release.yml -f bump=<patch|minor|major>
```

The run tags the next `vX.Y.Z` (from the highest existing one), creates the GitHub Release with generated notes and moves the major tag. The semver rules are in the `release-tag.yml` header. `rollback.yml` points the major tag at an earlier release (`-f target=v1.2.3 -f major=v1`). `v*` tags are created and moved only by andy-the-messenger-robot and org admins (repo-standards `rulesets/release-tags.json`).

After a new major, callers move by hand. Their Dependabot `github-actions` entries also open a PR to the new major in the `actions-major` group; it closes once the reference is updated.

## Dependents

After a publish, the library workflows (or, for a nuget.org library, its `dependents` caller job) send `repository_dispatch: update-dependencies` to the repos in `dependents` and the listeners found in the `discover-dependents` accounts. A listener is a workflow that takes `update-dependencies` and calls the platform's updater (`dotnet-`, `android-` or `nanoframework-update-dependencies.yml`), which opens the bump PR.

### Opt-in dispatch

`dotnet-build-library.yml` and `android-build-library.yml` take `dispatch`:
- `all` (default): every discovered listener. nanoFramework always dispatches to all.
- `opt-in`: only the discovered listeners the library PR names in `Update-Dependents:` lines. Explicit `dependents` are always sent.

```
Update-Dependents: rollout-web, midworld-apps/shelver-web
Update-Dependents: videobrowser-web
```

- A line starts with `Update-Dependents:` (case-insensitive); a PR body can have several.
- Entries are a bare `name` (matched in every `discover-dependents` account) or `owner/name`, separated by commas or spaces.
- `all` anywhere in a line opts in every listener.
- Lines inside HTML comments (`<!-- ... -->`) are ignored, so a PR template can carry a commented hint.

When it's read:
- **Push to the default branch:** the current body of the merged PR for the pushed commit. These dependents get the dispatch after the publish.
- **`pull_request`:** the PR body in the event (with the default `pull_request` types, editing the body alone doesn't start a run; push a commit). This is a preview: the dependents job logs each discovered listener as kept or `(not opted in)`, and never sends. Fork PRs get no secrets, so they skip discovery and log only the explicit repos.

With no line (or no merged PR, e.g. a direct push), nothing is dispatched and the push skips the dependents job. Dependents pick the version up from their Dependabot schedule (weekly with the `repo-standards` templates) or a manual PR.

A name that matches no listener in its account logs `::warning::Update-Dependents: <owner/name> is not an update-dependencies listener`; an `owner/name` outside the scanned accounts logs `... is not in a scanned account`. Invalid entries are warnings too; none of these fail the build.

### Android updater

`android-build-library.yml` reads the published coordinates from each `build/publications/*/pom-default.xml` and, once GitHub Packages serves `maven-metadata.xml` with the new version, sends `packages` as `group:name`. A listener calls `android-update-dependencies.yml`, which sets the matching `[libraries]` entries in `gradle/libs.versions.toml` (their `version.ref` key, or an inline version) and opens a `bot/update-dependencies/<source>/...` PR. It auto-merges unless the bump is breaking: a major change, or a minor change of a 0.x version.

### Update PRs

The .NET and Android updaters never lower a SemVer version (a re-dispatched older update is a no-op). With nothing to change, they close that source's open update PRs for the same version ("Already up to date"). Each PR body ends with an `<!-- update-dependencies {...} -->` marker holding the dispatch payload. When a merge leaves a bot update PR conflicting (two library updates editing adjacent lines), `dependabot.yml`'s `update-behind` runs `recover-update-prs`: for the oldest such PR with auto-merge on, it comments (marking it recovered) and re-sends `update-dependencies` with the marker's payload (or one parsed from the title, branch and `Bumps` lines), so the updater opens a fresh PR from base and supersedes it. One per push, since the updaters' concurrency group keeps a single pending run. A conflicting `nfbot/update-dependencies/*` PR is closed and nanodu re-dispatched.

## Composite actions

- `dotnet-build`: SDK (`dotnet-sdk-version`), nbgv version, restore, build, then the test projects matching `test-patterns` (excluding tests tagged `[Category("LocalOnly")]`, for those that need an internal network or external sites; VSTest runner), with a test report and TRX artifact. `dotnet-build-app` runs `*.UnitTests.csproj` and `*.IntegrationTests.csproj` (Docker is available for Testcontainers).
- `setup-tailwind`: the Tailwind CSS standalone CLI pinned by the root Dockerfile's `ARG TAILWIND_VERSION=<version>` (release checksum and version verified), on PATH for later steps; skipped without a Dockerfile or a pinned version. `dotnet-build-app` runs it before the build, so CSS compiled during `dotnet build` (CCSWE.Blazor's `TailwindBuild`) matches the image.
- `dotnet-sdk-version`: the `actions/setup-dotnet` version, first match wins: an explicit `dotnet-version` (passed through), the repo-root `global.json` (`sdk.version` and `rollForward`; see the header), else `10.0.x`. A `global.json` below the root is ignored (`dotnet` runs from the root and never sees it); a malformed one fails. The .NET workflows use it, so a repo changes SDK by editing its root `global.json`.
- `dotnet-pack`: packs every `IsPackable` project at the given version and checks each package exists.
- `discover-dependents`: an account's repos whose `update-dependencies` listener calls a given updater workflow, optionally limited to an opt-in list.
- `dependents-opt-in`: the `Update-Dependents:` names from the PR body.
- `dependents-plan`: groups `dependents` and `discover-dependents` by account into the `owners` matrix `dispatch-dependents.yml` takes.
- `update-package-versions`: sets package ids to one version in every tracked `Directory.Packages.props`.
- `setup-nanoframework`, `build-nanoframework`: nanobuild, MSBuild and NuGet CLI (Windows); locked restore and Release build stamped with nbgv.
- `nanoframework-package-lock`, `nanoframework-packages-updated`: the nanoFramework PR checks.
- `nuget-org-publish`: pushes the run's `nuget-packages` artifact to nuget.org with Trusted Publishing (`NuGet/login`), then `nuget-wait`. Use it from a job in the caller's own workflow file: nuget.org matches the policy against that file.
- `android-play-publish`: publishes the run's `release-aab` artifact to a Google Play track in one edit (Wear modules to `wear:<track>`), with an optional in-app update priority, with an access token from workload identity federation (`google-github-actions/auth`). Use it from a caller job with `id-token: write`; see the header.
- `nuget-wait`: waits until a feed's flat container (exact restore) or registration index ("latest") lists every package version.
- `maven-wait`: waits until a Maven repository's `maven-metadata.xml` lists the version for every artifact.
- `update-catalog-versions`: sets Maven libraries to one version in a Gradle version catalog.
- `recover-update-prs`: re-dispatches the oldest conflicting bot update PR (see [Update PRs](#update-prs)).
- `npm-build`: Node from `.nvmrc`, `npm ci`, then `npm run format:check`, `lint`, `test` (if present) and `build`; optional build env and committed-output check (on failure: rebuild and download commands in the error and step summary, and the built output uploaded as an artifact, so fork contributors can commit it).
- `gradle-build`: JDK (Temurin) and Gradle setup, CI `gradle.properties` lines (appended), the wrapper run, and an optional coverage artifact (kept 7 days). On GitHub-hosted Linux runners it removes preinstalled toolchains Gradle builds don't use (.NET, GHC, Swift, CodeQL), and before the build it removes restored caches and distributions of other Gradle versions. `cache-read-only: true` forces a read-only Gradle cache; otherwise setup-gradle's default applies (read-only off the default branch). `android-build-app` and `android-build-library` release builds don't save the cache; non-release default-branch pushes refresh it.
- `version-changed`: whether any watched file changed in the pushed range.
- `next-release-version`, `required-checks`: the next `vX.Y.Z` tag, and the gate that every required check passed on a commit (`release-tag.yml`).

## Self-tests

`test.yml` runs on PRs, master pushes and dispatch (`gh workflow run test.yml` re-runs master's checks for a release), and its job ids are required checks:
- `actionlint`
- `shellcheck` on the composite scripts
- `fixture-gradle` (`gradle-build` against `test/fixtures/gradle`)
- `fixture-dotnet-{pass,fail,no-tests,library,update}` (the .NET composites against `test/fixtures/dotnet`)
- `fixture-dotnet-sdk-version` (`dotnet-sdk-version` against generated `global.json` files)
- `fixture-tailwind` (`setup-tailwind` against generated Dockerfiles)
- `fixture-discover` (`discover-dependents --local` against `test/fixtures/listeners`, `dependents-plan`, and `dependents-opt-in` parsing)
- `fixture-android-update` (`update-catalog-versions` against `test/fixtures/catalog`)
- `fixture-android-play` (`android-play-publish --dry-run` on a generated phone and Wear tree)
- `fixture-npm-app`, `fixture-npm-action`, `fixture-npm-action-stale` (`npm-build` against `test/fixtures/npm`; the stale one also checks the uploaded artifact)
- `fixture-recover-update-prs` (`recover-update-prs` against a stubbed `gh`)
- `fixture-release` (`next-release-version` against a generated repo, `required-checks` against a stubbed `gh`)

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

- The library workflow takes no nuget.org key: the caller's `publish` job uses Trusted Publishing (a nuget.org policy for the caller repo and workflow file). It publishes only when `src`, `version.json`, `Directory.Build.props` or `nuget.config` change, and adds `discover-dependents` next to `dependents`.
- Dependents are found by a listener calling `ccswe-apps/actions/.github/workflows/nanoframework-update-dependencies.yml`; update the listener when the library switches.
- Check names stay `pipeline / build`, `pipeline / package-lock`, `pipeline / packages-updated`.
