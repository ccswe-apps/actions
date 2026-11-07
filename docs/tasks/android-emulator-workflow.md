# Android: emulator test workflow

`videobrowser-android` has a smoke test task (`docs/tasks/instrumented-smoke-tests*.md`, if still present) and `midworld-apps/smokinglog-android` needs upgrade and R8 smoke tests. Both need instrumented tests on an emulator in CI, and no shared workflow exists.

## Steps
1. Add a reusable workflow in `.github/workflows/`, or a job in the Android build workflows, whichever keeps the required check name stable. Don't wrap an existing workflow.
2. Inputs only for what varies between callers: Gradle task, API level.
3. Use KVM on hosted runners and cache the AVD. Pick the emulator action at its latest major.
4. Upload test reports on failure.
5. Validate with `actionlint`, and add a self-test in `test.yml` if the repo's pattern calls for it.

## Guardrails
- Debug builds of apps with Firebase must not report to real projects from CI: run with collection off or no network.
- Local note: on blaine, `adb` on port 5037 reaches Remote.Adb, so a local emulator needs `ANDROID_ADB_SERVER_PORT=5038`.

## Verification
A consumer's smoke test passes on a PR, and a deliberately failing test fails the job and uploads its report.
