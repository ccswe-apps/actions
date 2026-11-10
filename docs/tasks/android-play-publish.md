# Android: publish AABs to a Google Play track

`midworld-apps/smokinglog-android` builds signed phone and Wear AABs into the `release-aab` artifact (`android-build-app.yml`, `bundle-modules`). It needs them on a Play track with no manual upload. Any Android app on Play can use this, so it belongs here as a reusable workflow that callers run as a job after `pipeline`, like `nuget-org-publish`.

## Steps
1. Add `.github/workflows/android-play-publish.yml` (`workflow_call`):
   - Inputs: `package-name`, `track` (default `internal`), `release-status` (`completed` or `draft`, default `completed`), `artifact` (default `release-aab`).
   - Secret: `PLAY_SERVICE_ACCOUNT_JSON` (a service account invited in Play Console with release permission for that track).
   - Downloads the artifact; for each `<module>/*.aab`, uploads it to one Play Developer API edit (`edits.insert` → `edits.bundles.upload` → `edits.deobfuscationfiles.upload` with the module's `mapping.txt` when present → `edits.tracks.update` with all version codes in one release → `edits.commit`). Fails the job on any API error and deletes the edit.
   - Writes the uploaded version codes to the job summary.
2. Decide the client before building: a short script calling the API with a token from the service account (no third-party action holds the key) versus a marketplace action. Recommended: the script; the owner confirms.
3. Header and README row: inputs, secret, and the caller job shape (`needs: pipeline`, `if: needs.pipeline.outputs.release == 'true'`).
4. Validate with `actionlint` (`-ignore` patterns from `test.yml`).

## Verification
- A `smokinglog-android` release with the caller pinned to the branch publishes 1002/1003 to `internal` as `completed`, and Play Console shows both version codes with their mapping files.
