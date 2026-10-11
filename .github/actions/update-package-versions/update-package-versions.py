#!/usr/bin/env python3
"""Sets the Version of the given packages' <PackageVersion> items in every tracked
Directory.Packages.props.

Env: PACKAGES (space-separated ids, matched case-insensitively), VERSION.
Writes changed, major and summary to $GITHUB_OUTPUT.
"""
import os
import re
import subprocess
import sys

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
PACKAGE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
ITEM = re.compile(r"<PackageVersion\b[^>]*>")
INCLUDE = re.compile(r'\bInclude\s*=\s*"([^"]*)"')
VERSION = re.compile(r'(\bVersion\s*=\s*")([^"]*)(")')


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def major(version):
    m = re.match(r"^(\d+)\.", version)
    return int(m.group(1)) if m else None


def main():
    version = os.environ.get("VERSION", "")
    ids = os.environ.get("PACKAGES", "").split()
    if not SEMVER.match(version):
        fail(f"invalid version: {version!r}")
    if not ids:
        fail("no packages given")
    for package in ids:
        if not PACKAGE_ID.match(package):
            fail(f"invalid package id: {package!r}")
    wanted = {package.lower() for package in ids}

    files = subprocess.run(["git", "ls-files", "-z", "--", "*Directory.Packages.props"],
                           check=True, capture_output=True, text=True).stdout.split("\0")
    bumps, any_major = [], False
    for path in filter(None, files):
        with open(path, "rb") as f:
            bom = f.read(3) == b"\xef\xbb\xbf"
        with open(path, encoding="utf-8-sig", newline="") as f:
            text = f.read()

        def replace(item):
            nonlocal any_major
            tag = item.group(0)
            include, current = INCLUDE.search(tag), VERSION.search(tag)
            if not include or not current or include.group(1).lower() not in wanted or current.group(2) == version:
                return tag
            old = current.group(2)
            if major(old) != major(version):
                any_major = True
            bumps.append(f"Bumps {include.group(1)} from {old} to {version}")
            return VERSION.sub(lambda m: m.group(1) + version + m.group(3), tag, count=1)

        updated = ITEM.sub(replace, text)
        if updated != text:
            with open(path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
                f.write(updated)
            print(f"updated {path}")

    summary = "\n".join(sorted(set(bumps)))
    print(summary or "nothing to update")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
        out.write(f"changed={'true' if bumps else 'false'}\n")
        out.write(f"major={'true' if any_major else 'false'}\n")
        out.write(f"summary<<EOF_SUMMARY\n{summary}\nEOF_SUMMARY\n")


if __name__ == "__main__":
    main()
