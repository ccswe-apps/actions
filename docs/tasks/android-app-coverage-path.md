# Coverage upload for Android apps

`android-build-library.yml` passes a `coverage-path` input to the `gradle-build` composite, which uploads it as `coverage-report`. `android-build-app.yml` has no such input, so app callers can only print coverage in the log. `midworld-apps/videobrowser-android` runs Kover through a `tasks` override (`testReleaseUnitTest lintRelease koverXmlReportRelease koverHtmlReportRelease koverLogRelease`) as the dogfood.

## Steps
1. In `.github/workflows/android-build-app.yml`, add a `coverage-path` input (string, default `''`, description as in `android-build-library.yml`) and pass `coverage-path: ${{ inputs.coverage-path }}` to the build job's `gradle-build` step. Update the header comment. Empty keeps today's behavior for every caller.
2. Validate: `actionlint` with the `test.yml` ignores; a throwaway videobrowser-android caller PR at `@<branch>` with `coverage-path: videobrowser-app/build/reports/kover/` shows `pipeline / build` passing and a `coverage-report` artifact.
3. Merge, then do `~/src/midworld-apps/videobrowser-android/docs/tasks/coverage-artifact.md`; delete this file.

Notes: Kover class filters match fully qualified names, so `Hilt_*` alone misses `com.example.Hilt_Foo`; videobrowser also excludes `*.Hilt_*`. Check `ccswe-android-core/buildSrc/src/main/kotlin/CoverageExclusions.kt` for the same gap.
