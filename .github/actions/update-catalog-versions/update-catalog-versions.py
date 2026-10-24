#!/usr/bin/env python3
"""Sets the given Maven libraries to one version in a Gradle version catalog.

Env: PACKAGES (space-separated group:name, matched case-insensitively), VERSION, CATALOG.
A matched [libraries] entry with version.ref has that [versions] key set; one with an
inline version (or "group:name:version") has it set in place. Other entries sharing a
[versions] key move with it. Writes changed, breaking and summary to $GITHUB_OUTPUT.
"""
import os
import re
import sys
import tomllib

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
COORDINATE = re.compile(r"^[A-Za-z0-9._-]+:[A-Za-z0-9._-]+$")
HEADER = re.compile(r"^\s*\[\s*([^\[\]\s]+)\s*\]\s*(?:#.*)?$")


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def breaking(old, new):
    """A major change, or a minor change while the major is 0; unparsable counts too."""
    o, n = re.match(r"^(\d+)\.(\d+)", old), re.match(r"^(\d+)\.(\d+)", new)
    if not o or not n:
        return True
    return o.group(1) != n.group(1) or (o.group(1) == "0" and o.group(2) != n.group(2))


def coordinate(entry):
    """(group:name, version) of a [libraries] entry; version is a str, {"ref": key} or None."""
    if isinstance(entry, str):
        parts = entry.split(":")
        return ":".join(parts[:2]), (parts[2] if len(parts) > 2 else None)
    module = entry.get("module") or f"{entry.get('group', '')}:{entry.get('name', '')}"
    return module, entry.get("version")


def key_line(lines, section, key):
    """Index of `key = ...` inside [section], or None."""
    current, pattern = None, re.compile(r"^\s*(?:" + re.escape(key) + r"|\"" + re.escape(key) + r"\")\s*=")
    for i, line in enumerate(lines):
        header = HEADER.match(line)
        if header:
            current = header.group(1)
        elif current == section and pattern.match(line):
            return i
    return None


def main():
    version = os.environ.get("VERSION", "")
    packages = os.environ.get("PACKAGES", "").split()
    path = os.environ.get("CATALOG", "gradle/libs.versions.toml")
    if not SEMVER.match(version):
        fail(f"invalid version: {version!r}")
    if not packages:
        fail("no packages given")
    for package in packages:
        if not COORDINATE.match(package):
            fail(f"invalid coordinate: {package!r}")
    wanted = {package.lower() for package in packages}
    if not os.path.isfile(path):
        fail(f"no version catalog at {path}")

    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    catalog = tomllib.loads(text)
    lines = text.splitlines(keepends=True)
    versions = catalog.get("versions", {})

    bumps, any_breaking, refs = [], False, {}
    for alias, entry in catalog.get("libraries", {}).items():
        module, current = coordinate(entry)
        if module.lower() not in wanted:
            continue
        if isinstance(current, dict) and isinstance(current.get("ref"), str):
            refs.setdefault(current["ref"], []).append(module)
            continue
        if not isinstance(current, str):
            print(f"::warning::{alias} ({module}) has no plain version; not updated")
            continue
        if current == version:
            continue
        i = key_line(lines, "libraries", alias)
        pattern = (re.compile(r"(\bversion\s*=\s*\")([^\"]*)(\")") if isinstance(entry, dict)
                   else re.compile(r"(\"" + re.escape(module) + r":)([^\"]*)(\")"))
        if i is None or not pattern.search(lines[i]):
            print(f"::warning::{alias} ({module}) is not a one-line entry; not updated")
            continue
        lines[i] = pattern.sub(lambda m: m.group(1) + version + m.group(3), lines[i], count=1)
        bumps.append(f"Bumps {module} from {current} to {version}")
        any_breaking |= breaking(current, version)

    for key, modules in refs.items():
        current = versions.get(key)
        i = key_line(lines, "versions", key)
        pattern = re.compile(r"(=\s*\")([^\"]*)(\")")
        if not isinstance(current, str) or i is None or not pattern.search(lines[i]):
            print(f"::warning::[versions] {key} is not a plain version; not updated")
            continue
        if current == version:
            continue
        lines[i] = pattern.sub(lambda m: m.group(1) + version + m.group(3), lines[i], count=1)
        bumps.extend(f"Bumps {module} from {current} to {version}" for module in modules)
        any_breaking |= breaking(current, version)

    if bumps:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write("".join(lines))
        print(f"updated {path}")

    summary = "\n".join(sorted(set(bumps)))
    print(summary or "nothing to update")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
        out.write(f"changed={'true' if bumps else 'false'}\n")
        out.write(f"breaking={'true' if any_breaking else 'false'}\n")
        out.write(f"summary<<EOF_SUMMARY\n{summary}\nEOF_SUMMARY\n")


if __name__ == "__main__":
    main()
