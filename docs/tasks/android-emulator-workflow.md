# Android: emulator test workflow

`videobrowser-android` has a smoke test task (`docs/tasks/instrumented-smoke-tests.md`, if still present) and `midworld-apps/smokinglog-android` needs upgrade and R8 smoke tests. Both need instrumented tests on an emulator in CI, and no shared workflow exists.

## Steps
1. Add a separate reusable workflow in `.github/workflows/`. Don't add a job to the Android build workflows, and don't wrap an existing workflow.
2. Inputs: `script` (the commands to run on the emulator), `api-level` and `gradle-properties`. Secret: `PACKAGES_PAT`. Expose `GH_TOKEN` to the script. Fixtures and test code stay in the consumer.
3. Use `reactivecircus/android-emulator-runner` at its latest major, with KVM on hosted runners and a cached AVD. Confirm `adb` works inside `script`.
4. Upload test reports on failure.
5. Validate with `actionlint`, and add a self-test in `test.yml` if the repo's pattern calls for it.

Caller shape: `workflow_dispatch`, plus `pull_request` with `paths` on the version file (`Versions.kt`). Not a required check.

## Guardrails
- Nothing a CI emulator job runs may reach a real Firebase project. Run the emulator with no network, and consumers disable mapping upload for every minified test build type. Smoke and upgrade tests decline consent.
- Local note: on blaine, `adb` on port 5037 reaches Remote.Adb, so a local emulator needs `ANDROID_ADB_SERVER_PORT=5038`.

## Consumers
- `smokinglog-android`: R8 smoke and upgrade tests.
- `videobrowser-android`: its smoke test task gets a `Depends on:` link to this file.

## Verification
A consumer's smoke test passes on a PR, and a deliberately failing test fails the job and uploads its report.
