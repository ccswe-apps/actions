#!/usr/bin/env python3
"""Lists the repos under one account that listen for `update-dependencies` and
hand it to a given reusable updater workflow.

A repo is kept when one of its workflows has a `types:` list (or scalar) naming
`update-dependencies` under `repository_dispatch` and a `uses: <updater>@<ref>`.
Archived repos, template repos and EXCLUDE are skipped.

ONLY (default `*`, all) keeps just the listeners it names (owner/name or name, separated
by commas or whitespace; empty keeps none); a name matching no listener is a warning.

Live:  env OWNER, UPDATER, EXCLUDE (owner/name), ONLY, GH_TOKEN (an installation
       token for OWNER; `gh api installation/repositories` lists its repos).
Local: --local DIR, where each DIR/<name>/.github/workflows/*.yml is a repo
       named OWNER/<name> (for tests).
Prints only the listeners, kept or not opted in (callers may be public; scanned names
may be private), and a skipped count, then writes `repos` (JSON array of owner/name) to $GITHUB_OUTPUT.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

EVENT = "update-dependencies"


def dispatch_types(text):
    """Event types named by `types:` keys (flow list, scalar or block list)."""
    found = set()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)types\s*:\s*(.*?)\s*(?:#.*)?$", line)
        if not m:
            continue
        indent, rest = len(m.group(1)), m.group(2)
        if rest.startswith("["):
            items = rest.strip("[]").split(",")
        elif rest:
            items = [rest]
        else:
            items = []
            for follow in lines[i + 1:]:
                item = re.match(r"^(\s*)-\s*(.*?)\s*(?:#.*)?$", follow)
                if not item or len(item.group(1)) < indent:
                    break
                items.append(item.group(2))
        found.update(x.strip().strip("'\"") for x in items if x.strip())
    return found


def listens(text, updater):
    return (re.search(r"^\s*repository_dispatch\s*:", text, re.M) is not None
            and EVENT in dispatch_types(text)
            and re.search(r"^\s*(?:-\s*)?uses\s*:\s*['\"]?" + re.escape(updater) + "@", text, re.M) is not None)


def gh(*args):
    result = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    return result.returncode, result.stdout


def live_repos(owner):
    code, out = gh("--paginate", "installation/repositories",
                   "--jq", ".repositories[] | [.full_name, .archived, .is_template] | @tsv")
    if code != 0:
        sys.exit(f"::error::cannot list installation repositories for {owner}")
    for line in filter(None, out.splitlines()):
        full_name, archived, is_template = line.split("\t")
        yield full_name, archived == "true", is_template == "true"


def live_workflows(full_name):
    code, out = gh(f"repos/{full_name}/contents/.github/workflows",
                   "--jq", '.[] | select(.type == "file") | .path')
    if code != 0:
        return
    for path in out.splitlines():
        if path.endswith((".yml", ".yaml")):
            code, text = gh(f"repos/{full_name}/contents/{path}", "-H", "Accept: application/vnd.github.raw")
            if code == 0:
                yield path, text


def local_repos(root, owner):
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        yield f"{owner}/{d.name}", False, False


def local_workflows(root, full_name):
    workflows = root / full_name.split("/", 1)[1] / ".github" / "workflows"
    for p in sorted(workflows.glob("*.y*ml")) if workflows.is_dir() else []:
        yield str(p.relative_to(root)), p.read_text()


def opted_in(owner, only):
    """Lowercase owner/name entries for OWNER, or None for all."""
    entries = [e.lower() for e in re.split(r"[\s,]+", only) if e]
    if "*" in entries:
        return None
    return {e if "/" in e else f"{owner.lower()}/{e}" for e in entries
            if "/" not in e or e.split("/", 1)[0] == owner.lower()}


def main():
    owner, updater = os.environ["OWNER"], os.environ["UPDATER"]
    exclude = os.environ.get("EXCLUDE", "").lower()
    only = opted_in(owner, os.environ.get("ONLY", "*"))
    local = pathlib.Path(sys.argv[2]) if sys.argv[1:2] == ["--local"] else None
    repos = local_repos(local, owner) if local else live_repos(owner)
    workflows = (lambda r: local_workflows(local, r)) if local else live_workflows

    kept, listeners, skipped = [], set(), 0
    for full_name, archived, is_template in repos:
        candidate = (full_name.split("/", 1)[0].lower() == owner.lower() and not archived
                     and not is_template and full_name.lower() != exclude)
        listener = candidate and next((path for path, text in workflows(full_name) if listens(text, updater)), None)
        if not listener:
            skipped += 1
            continue
        listeners.add(full_name.lower())
        if only is None or full_name.lower() in only:
            kept.append(full_name)
            print(f"+ {full_name}: listener {listener}")
        else:
            print(f"- {full_name}: listener {listener} (not opted in)")

    print(f"skipped: {skipped}")
    for name in sorted((only or set()) - listeners):
        print(f"::warning::Update-Dependents: {name} is not an update-dependencies listener")

    result = json.dumps(sorted(kept))
    print(f"repos={result}")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write(f"repos={result}\n")


if __name__ == "__main__":
    main()
