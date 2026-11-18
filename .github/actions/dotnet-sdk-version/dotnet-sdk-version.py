#!/usr/bin/env python3
"""Resolves the actions/setup-dotnet `dotnet-version` for a repo.

Env: DOTNET_VERSION (explicit version, passed through), ROOT (directory holding global.json).
Writes `sdk` to $GITHUB_OUTPUT: DOTNET_VERSION if set, else from ROOT/global.json, else FALLBACK.
"""
import json
import os
import re
import uuid

FALLBACK = "10.0.x"

# rollForward values whose accepted range spans feature bands (install the latest A.B.x).
MINOR_RANGE = {"feature", "latestfeature", "minor", "latestminor", "major", "latestmajor"}
# rollForward values limited to one feature band (install A.B.Cxx).
BAND_RANGE = {"patch", "latestpatch"}


def strip_json5(text):
    """Removes // and /* */ comments and trailing commas outside strings (global.json allows both)."""
    out = []
    i = 0
    in_string = False
    while i < len(text):
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\":
                out.append(text[i + 1 : i + 2])
                i += 1
            elif c == '"':
                in_string = False
        elif c == '"':
            in_string = True
            out.append(c)
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated comment")
            i = end + 2
            continue
        elif c == ",":
            rest = text[i + 1 :].lstrip()
            if rest[:1] not in ("}", "]"):
                out.append(c)
        else:
            out.append(c)
        i += 1
    return "".join(out)


def from_global_json(path):
    """The setup-dotnet version for a global.json, or None when it pins no SDK."""
    with open(path, encoding="utf-8-sig") as f:
        data = json.loads(strip_json5(f.read()))
    sdk = data.get("sdk") if isinstance(data, dict) else None
    version = sdk.get("version") if isinstance(sdk, dict) else None
    if not version:
        return None
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?", version)
    if not match:
        raise ValueError(f"unrecognized sdk.version {version!r}")
    major, minor, patch, prerelease = match.groups()
    roll_forward = str(sdk.get("rollForward") or "latestPatch").lower()
    if roll_forward not in MINOR_RANGE | BAND_RANGE | {"disable"}:
        raise ValueError(f"unrecognized sdk.rollForward {sdk.get('rollForward')!r}")
    if prerelease:
        return version
    if patch == "0":
        # A.B.0 is no real SDK; it means "any A.B SDK".
        return f"{major}.{minor}.x"
    if roll_forward == "disable":
        return version
    if roll_forward in BAND_RANGE:
        return f"{major}.{minor}.{int(patch) // 100}xx"
    return f"{major}.{minor}.x"


def resolve(explicit, root):
    if explicit.strip():
        return explicit.strip(), "dotnet-version input"
    path = os.path.join(root, "global.json")
    if os.path.isfile(path):
        try:
            version = from_global_json(path)
        except (ValueError, json.JSONDecodeError) as e:
            raise SystemExit(f"::error file=global.json::invalid global.json: {e}")
        if version:
            return version, "global.json"
    return FALLBACK, "fallback"


def main():
    sdk, source = resolve(os.environ.get("DOTNET_VERSION", ""), os.environ.get("ROOT") or ".")
    print(f"sdk ({source}): {sdk}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        delimiter = f"EOF_{uuid.uuid4().hex}"
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"sdk<<{delimiter}\n{sdk}\n{delimiter}\n")


if __name__ == "__main__":
    main()
