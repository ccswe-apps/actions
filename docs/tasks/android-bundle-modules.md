# Android: `bundle-modules` input

`midworld-apps/smokinglog-android` ships a phone and a Wear app under one application ID, each as an AAB for Play. `android-build-app.yml` only produces one signed APK, in the `release-apk` artifact.

## Steps
1. `.github/workflows/android-build-app.yml`: add optional input `bundle-modules`, a space-separated list of Gradle modules. It's empty by default, and callers that don't set it keep today's behavior exactly.
2. When set, the release path runs `:<module>:bundleRelease` per module with the existing signing inputs, and fails if a module's `.aab` is missing.
3. Upload the AABs, plus each module's `mapping.txt`, as a `release-aab` artifact.
4. Document the input in the workflow header and README. Validate with `actionlint`, using the `-ignore` patterns from `test.yml`.

Design notes: `smokinglog-android/docs/rewrite/research/build-test-release.md`, "Proposed change in `ccswe-apps/actions`".

## Verification
`videobrowser-android`'s CI is unchanged. A test caller with two modules produces both AABs, signed with the upload key.
