# Consolidate short jobs in the app master pipeline

On a midworld .NET app's master push (`dotnet-build-app.yml` plus the caller's `deploy` job), three jobs run for seconds but each bills a full minute: `dependabot` (update-behind), `prune`, and the caller's `deploy` (`midworld-apps/manifests` `bump-manifests.yml`). Together they are about 3 of the roughly 7.7 billed minutes per dependent update.

## Steps

1. Measure the current per-job billed minutes on a recent master run of a midworld app.
2. Evaluate folding `prune` and the `dependabot` update-behind step into an existing job (e.g. the end of `publish`), and whether the caller's `deploy` can share a job with anything.
3. Keep the required check names (`pipeline / build`) unchanged; never wrap a workflow (see `CLAUDE.md`).
4. Validate with a throwaway caller PR at `@<branch>`, then update `README.md` and the workflow headers.

Delete this file when done.
