# Resolve the .NET SDK from global.json

The .NET workflows install `dotnet-version` (default `'10.0.x'`) and never read `global.json`; no caller passes the input. Moving a repo to .NET 11 (`midworld-apps/ccswe-dotnet-core` `docs/tasks/net11-upgrade.md`) should only need its root `global.json` changed, while repos that stay on 10 (CCSWE.Avalonia.*, Remote.Adb, DeviceOwner: root `global.json` `10.0.0` / `latestMinor`) and outside callers keep working unchanged.

## Resolution order (first match wins)

1. `dotnet-version` input, passed through unchanged (multi-line, `latest`, `A.x` still work).
2. Repo-root `global.json` only: `dotnet` runs from the root, so a `src/global.json` is never honored.
3. Fallback `10.0.x` (current LTS; bump only on LTS releases).

Always emit a value or fail. Never hand setup-dotnet an empty `dotnet-version`: it then reads `global.json` itself and throws on `10.0.0` with `rollForward` (it requires `A.B.Cxx`).

`global.json` → setup-dotnet version:

| global.json | install |
|---|---|
| prerelease `version`, or `rollForward: disable` | exact version |
| `patch`, `latestPatch`, or no `rollForward` | `A.B.Cxx` (feature band) |
| `feature`, `latestFeature`, `minor`, `latestMinor`, `major`, `latestMajor` | `A.B.x` |

`allowPrerelease: false` → consider `dotnet-quality: ga`.

## Steps

1. Add `.github/actions/dotnet-sdk-version/` (`action.yml` + `resolve.py`). The name avoids Dependabot's `dotnet-sdk` ecosystem name. Inputs via `env:` only: `DOTNET_VERSION`, `ROOT` (default `$GITHUB_WORKSPACE`). Output `sdk`.
   - Parse with comments (`//`, `/* */`) and trailing commas stripped, opened `utf-8-sig` (CRLF files exist, e.g. ccswe-dotnet-core). `jq` and Python `json` reject comments.
   - No `sdk` or `sdk.version` (e.g. only `msbuild-sdks` or `test`) = no pin. Malformed file = `::error::`, not a silent fallback.
2. Wire it in front of each `actions/setup-dotnet@v6`:
   - `.github/actions/dotnet-build/action.yml`: run `"$GITHUB_ACTION_PATH/../dotnet-sdk-version/resolve.py"` directly; `$/` inside a composite is unproven here (see how `nuget-org-publish` reaches `nuget-wait`).
   - `dotnet-update-dependencies.yml`: `uses: $/.github/actions/dotnet-sdk-version`.
   - `dotnet-build-library.yml` publish job: delete its setup-dotnet step (no checkout there; `dotnet nuget push` uses the preinstalled SDK, as `nuget-org-publish/push.sh` already does).
   - Log `dotnet --version` from the repo root after setup.
3. `dotnet-version` default → `''` in `dotnet-build/action.yml`, `dotnet-build-app.yml`, `dotnet-build-library.yml`, `dotnet-release-app.yml`, `dotnet-update-dependencies.yml`; update descriptions. The input stays only for public compatibility (an undeclared input fails a reusable-workflow call).
4. Unchanged (same job as `dotnet-build`, or no SDK install): `dotnet-pack`, `dotnet tool restore` in the library build, the release RID publish, `nuget-org-publish`, nanoFramework workflows. No Docker build-arg: each Dockerfile's `ARG DOTNET_VERSION` plus its copied root `global.json` decide the image.
5. Add `.github/actions/dotnet-sdk-version` to the github-actions `directories` in `.github/dependabot.yml` (`repo-standards/audit.py` checks it).
6. `test.yml`: a `fixture-dotnet-sdk-version` job running `resolve.py` against fixture dirs via `ROOT` (like `fixture-discover`; no SDK installs). Cases: input single and multi-line; `10.0.0`/`latestMinor` → `10.0.x`; `11.0.100`/`latestMinor` → `11.0.x`; `latestPatch` → `A.B.Cxx`; `disable` and prerelease → exact; comments + BOM + CRLF; `msbuild-sdks` only and no file → `10.0.x`; malformed → fails. Add it to `dependabot.needs`, the README Self-tests list, and the ruleset's required checks.
7. Docs: README "Composite actions" entry, resolution order, behavior changes (non-root `global.json` ignored; malformed `global.json` now fails). Update the header contracts in `dotnet-build-app.yml`, `dotnet-build-library.yml`, `dotnet-update-dependencies.yml`.

## Verification

- actionlint with the `$/` ignore patterns from `test.yml`; `test.yml` green.
- Throwaway caller PRs at `@<branch>`, checking the logged `dotnet --version` (not the resolver output):
  - a Midworld app (no root `global.json` yet) → 10.0.x;
  - ccswe-dotnet-core and one CCSWE.Avalonia library → 10.0.x;
  - Remote.Adb → `dotnet-build-app` only. Release-app is covered through the shared composite; a test tag would create a real release.
- Out-of-scope callers need no edits.
