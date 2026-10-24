#!/usr/bin/env python3
"""Groups explicit dependents and scanned accounts by owner.

Env: DEPENDENTS (owner/name lines), DISCOVER (account lines), ONLY (opted-in listeners).
Writes `owners` to $GITHUB_OUTPUT: a JSON array of {owner, discover, repos}.
"""
import json
import os
import re


def plan(dependents, discover, only):
    owners = {}

    def entry(owner):
        return owners.setdefault(owner.lower(), {"owner": owner, "discover": False, "repos": []})

    for line in filter(None, (l.strip() for l in dependents.splitlines())):
        if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+", line):
            raise SystemExit(f"::error::invalid dependents entry: {line}")
        entry(line.split("/")[0])["repos"].append(line)
    for line in filter(None, (l.strip() for l in discover.splitlines())):
        if not re.fullmatch(r"[A-Za-z0-9-]+", line):
            raise SystemExit(f"::error::invalid discover-dependents entry: {line}")
        entry(line)["discover"] = True
    print(f"only: {only or '(none)'}")
    for name in re.split(r"[\s,]+", only):
        if "/" in name and not owners.get(name.split("/")[0].lower(), {}).get("discover"):
            print(f"::warning::Update-Dependents: {name} is not in a scanned account")
    return list(owners.values())


def main():
    owners = json.dumps(plan(os.environ.get("DEPENDENTS", ""), os.environ.get("DISCOVER", ""),
                             os.environ.get("ONLY", "*")), separators=(",", ":"))
    print(f"owners={owners}")
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
            out.write(f"owners={owners}\n")


if __name__ == "__main__":
    main()
