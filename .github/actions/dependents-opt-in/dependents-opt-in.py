#!/usr/bin/env python3
"""Resolves `Update-Dependents:` lines from a PR body.

Env: EVENT_NAME, PR_BODY (pull_request), REPO, SHA, GH_TOKEN (push: the merged PR for SHA).
Writes `only` to $GITHUB_OUTPUT: space-separated owner/name or name entries, `*` for all,
or empty.
"""
import json
import os
import re
import subprocess

LINE = re.compile(r"^[ \t]*Update-Dependents[ \t]*:[ \t]*(.+?)[ \t]*$", re.I | re.M)
COMMENT = re.compile(r"<!--.*?(?:-->|$)", re.S)
ENTRY = re.compile(r"^(?:[A-Za-z0-9-]+/)?[A-Za-z0-9._-]+$")


def merged_pr_body(repo, sha):
    result = subprocess.run(["gh", "api", f"repos/{repo}/commits/{sha}/pulls"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"::warning::cannot list the pull requests for {sha}: {result.stderr.strip()}")
        return None
    pulls = [p for p in json.loads(result.stdout) if p.get("merged_at")]
    pull = next((p for p in pulls if p.get("merge_commit_sha") == sha), pulls[0] if pulls else None)
    if not pull:
        return None
    print(f"pull request: #{pull['number']}")
    return pull.get("body") or ""


def resolve(body):
    entries = []
    for line in LINE.findall(COMMENT.sub("", body.replace("\r\n", "\n"))):
        for token in filter(None, re.split(r"[\s,]+", line)):
            if token.lower() == "all":
                return ["*"]
            if ENTRY.match(token):
                if token.lower() not in (e.lower() for e in entries):
                    entries.append(token)
            else:
                print(f"::warning::invalid Update-Dependents entry: {token}")
    return entries


def main():
    if os.environ.get("EVENT_NAME") == "pull_request":
        body = os.environ.get("PR_BODY", "")
    else:
        body = merged_pr_body(os.environ["REPO"], os.environ["SHA"])
        if body is None:
            print("no merged pull request for this commit")
            body = ""
    only = " ".join(resolve(body))
    print(f"only={only}")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write(f"only={only}\n")


if __name__ == "__main__":
    main()
