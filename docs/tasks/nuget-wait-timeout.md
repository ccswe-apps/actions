# Set nuget-wait's timeout from measured publish latency

`nuget-wait` polls every 30s for up to 30 minutes (`.github/actions/nuget-wait/nuget-wait.sh`). The whole time is billed as runner minutes. On a timeout `indexed` is false and the library's `dependents` job sends nothing. That's acceptable: dependents can't restore an unserved version anyway, so the bump can be dispatched by hand or picked up by Dependabot.

## Measured (2026-10-26)

These are master publish jobs still in the Actions logs. The timing runs from the first "Your package was pushed" to the last package served, or to the timeout.

| Feed / index | Runs | Push → served |
|---|---|---|
| nuget.org flat-container (CCSWE.Avalonia.*, 2026-10-13 to 2026-10-26) | 7 served, 2 timed out | 601, 722, 753, 873, 1023, 1203, 1416 s; timeouts: Hosting 2026-10-13, Material 12.1.17 2026-10-26 (pushed around 19:09 UTC, in the flat container by 19:39) |
| nuget.org registration (CCSWE.nanoFramework, 15 packages, 2026-10-11) | 1 | 551 s |
| GitHub Packages flat-container (ccswe-dotnet-core, 2026-10-12 to 2026-10-26) | 45 | 5–10 s |

To re-measure, scan the `publish` / `pipeline / publish` job logs of the master "Build, test, and publish" runs (`gh run list`, `gh api repos/<repo>/actions/jobs/<id>/logs`).

## Steps

1. Re-measure with more nuget.org publishes, since the sample above is small.
2. Pick a timeout that covers the usual case. A shorter timeout costs a missed dispatch, not a failed build.
3. Change the deadline (and its comments in `nuget-wait.sh`, `action.yml` and the README) and validate as in `CLAUDE.md`.

Delete this file when done.
