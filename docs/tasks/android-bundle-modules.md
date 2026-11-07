# Android: `bundle-modules` input

`midworld-apps/smokinglog-android` ships a phone and a Wear app under one application ID, each as an AAB for Play. `android-build-app.yml` only produces one signed APK, in the `release-apk` artifact.

## Steps
1. `.github/workflows/android-build-app.yml`: add optional input `bundle-modules`, a space-separated list of Gradle modules. It's empty by default, and callers that don't set it keep today's behavior exactly.
2. When set, the release path runs exactly `:<module>:bundleRelease` for each module, in one Gradle invocation, with the existing signing setup. It skips `assembleRelease`, the `meta` step and the `release-apk` upload, and fails if a module's `.aab` is missing.
3. Upload the AABs, plus each module's `mapping.txt`, as a `release-aab` artifact.
4. In bundle mode, `app-module` stays required but unused, the `release` output is still `true`, and `version-name`, `version-code` and `file-name` are empty.
5. No keystore keeps today's behavior: build without release signing, no hard failure.
6. Document the input and the bundle-mode outputs in the workflow header and README. Validate with `actionlint`, using the `-ignore` patterns from `test.yml`.

Design notes: `smokinglog-android/docs/rewrite/research/build-test-release.md`, "Proposed change in `ccswe-apps/actions`".

## Verification
- `videobrowser-android`'s CI is unchanged.
- The first `Versions.kt` bump on `smokinglog-android` master, with its caller pinned to this branch, produces both AABs and their mappings in `release-aab`, signed with the upload key.
