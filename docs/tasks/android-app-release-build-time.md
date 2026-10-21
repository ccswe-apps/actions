# Android app workflow: release job rebuilds from scratch

In `.github/workflows/android-build-app.yml`, a release push runs `build` (the caller's `tasks`, e.g. `testReleaseUnitTest lintRelease`) and then a separate `release` job (`assembleRelease`) on a fresh runner. The release job recompiles everything the build job just compiled, then runs R8.

Measured on videobrowser-android 1.2.38 (run 39657460650):
- build job: 5m24s
- release job: 8m32s, of which Gradle took 7m37s with "65 actionable tasks: 65 executed" (nothing from the build cache)
  - start to `kspReleaseKotlin`: about 2 min
  - KSP/Hilt plus `compileReleaseKotlin`: about 1m40s
  - `minifyReleaseWithR8` to the end: about 4m20s

`org.gradle.caching=true` is set in the app, but the build cache is local to each runner.

## Options to investigate
- Build the APK in the build job on release pushes. This keeps the warm daemon and the compiled classes.
  - `version-changed` runs after the build step today (`:113-117`), so it would have to move first.
  - Signing would move into the build job.
  - Keep `release` as a thin job that only reads metadata and uploads, or drop it. Check that the `release`/`version-*` workflow outputs and the callers' `publish` jobs still line up.
- Share the Gradle build cache between the jobs, via `setup-gradle` cache settings or a remote cache. This only skips the recompile; R8 still runs.
- R8 itself, the largest share: a larger runner, or the R8/Gradle memory settings. Keep `proguard-android-optimize.txt` unless measurements show it's the cost.

## Steps
1. Decide from a timing comparison, using a throwaway videobrowser-android caller PR pointed at the branch.
2. Change the workflow and validate with `actionlint` (ignore patterns in `.github/workflows/test.yml`).
3. Record the before and after release times in the PR; delete this file.
