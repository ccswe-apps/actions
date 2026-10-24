# Limit automatic dependent updates on library publish

Every .NET library publish (`dotnet-build-library.yml` → `dispatch-dependents.yml`) sends `update-dependencies` to every discovered listener. Each listener then runs `dotnet-update-dependencies.yml`, opens a PR, runs its PR build, merges, and runs its master build, publish and deploy. That is convenient, but it costs a lot of Actions minutes, and most updates could wait.

Observed: the CCSWE.Blazor-only releases 10.0.155, 10.0.156 and 10.0.158 (ccswe-dotnet-core) produced update PRs, builds and deploys in rollout-api, shelver-api, videobrowser-api and iot-api. None of their `Directory.Packages.props` reference CCSWE.Blazor, but every package in the repo is republished at the shared version and the payload lists them all.

Not in scope: nanoFramework (`nanoframework-build-library.yml` / `nanoframework-update-dependencies.yml`); its dependents must stay in sync with the library.

## Steps

1. Research and measure first: the Actions minutes per library publish across dependents (PR build, master build, publish, deploy), which payload packages each dependent actually references, and how Dependabot already covers `CCSWE.*` (the repo-standards templates exclude `CCSWE.*` from cooldown; check the schedule and grouping).
2. Options to evaluate (ideas so far, not decisions):
   - Make the push-time dispatch opt-in: a library or caller input names the dependents to update now; everything else picks the version up from Dependabot on its schedule or a manual PR.
   - Skip dependents that reference none of the payload's changed packages (needs "changed" to mean more than "republished at the shared version"; e.g. publish only packages whose sources changed, or diff package contents).
   - Batch: let update PRs accumulate and merge on a schedule instead of on every publish.
3. Pick one with the user and implement it here (owner-agnostic). Owner-specific lists go in the callers or `midworld-apps/ci`. Keep `dispatch-dependents.yml`'s PR-log listing.
4. Update `README.md` / workflow headers, and the callers (ccswe-dotnet-core, CCSWE.Avalonia.*, ccswe-android-core if it uses the same dispatch). Validate with `actionlint` (ignore patterns from `.github/workflows/test.yml`).

Delete this file when done.
