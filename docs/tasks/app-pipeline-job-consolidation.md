# Fold update-behind and the library PR discovery preview into build

`dependabot / update-behind` (every build workflow's default-branch push) and the library PR `dependents` preview are separate jobs of a few seconds each, each billed a full minute. Re-evaluate folding them around 2026-11-24, after measuring billed minutes with opt-in dependent dispatch in place.

Blocker: both mint an andy token with `actions/create-github-app-token`, whose post step runs at job end and receives the same inputs, including `private-key`. Repo or dependency code that ran earlier in the job could replace the post script on the runner, so the token step can't share a job with that code, even as the first step.

## Options

- **A:** a composite that mints the token itself (RS256 JWT with openssl, installation token scoped to the repo, revoked on exit) in one step with no post step. Custom code; nanoFramework builds would run it on Windows (Git Bash).
- **C:** update-behind as the first step of `publish` in `dotnet-build-app.yml`, where dependency code runs only inside BuildKit containers. Covers .NET app pushes only.

## Steps

1. Measure per-job billed minutes on recent midworld app and library runs (jobs API).
2. Pick an option or drop the task; keep the required checks (`pipeline / build`) and never wrap a workflow (see `CLAUDE.md`).
3. Validate with a throwaway caller PR at `@<branch>`, then update `README.md` and the workflow headers.

Delete this file when done.
