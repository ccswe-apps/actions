#!/usr/bin/env python3
"""Publishes a run's AABs to Google Play in one edit.

Each directory under ARTIFACT_DIR holding an AAB is a module (`app`, `feature/wear`); it
must hold exactly one `*.aab`, and its `mapping.txt` (optional) is uploaded as the
bundle's deobfuscation file. Modules in WEAR_MODULES (Gradle paths, space-separated)
go to `wear:<TRACK>`, the rest to TRACK. Each track gets one release with its version
codes and RELEASE_STATUS (completed or draft). Any error deletes the edit.

Env: PACKAGE_NAME, TRACK, RELEASE_STATUS, WEAR_MODULES, ARTIFACT_DIR,
     PLAY_ACCESS_TOKEN (androidpublisher scope; not needed with --dry-run).
--dry-run prints the plan and makes no requests.
Writes the version codes per track to $GITHUB_STEP_SUMMARY.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

API = "https://androidpublisher.googleapis.com/androidpublisher/v3/applications"
UPLOAD = "https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications"
STATUSES = ("completed", "draft")


class PlayError(Exception):
    pass


def fail(message):
    print(f"::error::{message}")
    sys.exit(1)


def module_dir(gradle_path):
    return gradle_path.strip(":").replace(":", "/")


def plan(artifact_dir, track, wear_modules):
    root = pathlib.Path(artifact_dir)
    if not root.is_dir():
        fail(f"Artifact directory {artifact_dir} not found")
    by_module = {}
    for aab in sorted(root.rglob("*.aab")):
        by_module.setdefault(aab.parent.relative_to(root).as_posix(), []).append(aab)
    if not by_module:
        fail(f"No AAB under {artifact_dir}")
    if "." in by_module:
        fail(f"AAB at the root of {artifact_dir}; expected <module>/<name>.aab")
    wear = {module_dir(m) for m in wear_modules.split()}
    missing = sorted(wear - by_module.keys())
    if missing:
        fail(f"Wear module(s) without an AAB: {', '.join(missing)}")
    modules = []
    for name, aabs in sorted(by_module.items()):
        if len(aabs) != 1:
            fail(f"Module {name} has {len(aabs)} AABs; expected one")
        mapping = aabs[0].parent / "mapping.txt"
        modules.append({
            "name": name,
            "aab": aabs[0],
            "mapping": mapping if mapping.is_file() else None,
            "track": f"wear:{track}" if name in wear else track,
        })
    return modules


def request(method, url, token, body=None, content_type="application/json", timeout=120):
    data = json.dumps(body).encode() if isinstance(body, dict) else body
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": content_type,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            message = json.loads(raw)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = raw[:500] or e.reason
        raise PlayError(f"{method} {url.split('?')[0]}: HTTP {e.code}: {message}") from None
    except urllib.error.URLError as e:
        raise PlayError(f"{method} {url.split('?')[0]}: {e.reason}") from None


def upload(url, token, path):
    return request("POST", f"{url}?uploadType=media", token, path.read_bytes(),
                   "application/octet-stream", timeout=900)


def publish(package, status, modules, token):
    edits = f"{API}/{package}/edits"
    uploads = f"{UPLOAD}/{package}/edits"
    edit = request("POST", edits, token)["id"]
    try:
        codes = {}
        for m in modules:
            bundle = upload(f"{uploads}/{edit}/bundles", token, m["aab"])
            if "versionCode" not in bundle:
                raise PlayError(f"{m['name']}: bundle upload returned no versionCode")
            code = str(bundle["versionCode"])
            print(f"{m['name']}: uploaded {m['aab'].name} as {code}")
            if m["mapping"]:
                upload(f"{uploads}/{edit}/apks/{code}/deobfuscationFiles/proguard", token, m["mapping"])
                print(f"{m['name']}: uploaded mapping.txt")
            codes.setdefault(m["track"], []).append(code)
        for track, track_codes in codes.items():
            request("PUT", f"{edits}/{edit}/tracks/{track}", token, {
                "track": track,
                "releases": [{"versionCodes": track_codes, "status": status}],
            })
            print(f"{track}: {', '.join(track_codes)} ({status})")
        request("POST", f"{edits}/{edit}:commit", token)
        print(f"Committed edit for {package}")
        return codes
    except BaseException:
        try:
            request("DELETE", f"{edits}/{edit}", token)
            print("Deleted the edit")
        except PlayError as e:
            print(f"::warning::Could not delete the edit: {e}")
        raise


def main():
    dry_run = "--dry-run" in sys.argv[1:]
    package = os.environ.get("PACKAGE_NAME", "").strip()
    track = os.environ.get("TRACK", "").strip() or "internal"
    status = os.environ.get("RELEASE_STATUS", "").strip() or "completed"
    if not package:
        fail("PACKAGE_NAME is required")
    if status not in STATUSES:
        fail(f"RELEASE_STATUS {status} is not one of {', '.join(STATUSES)}")
    modules = plan(os.environ.get("ARTIFACT_DIR", "."), track, os.environ.get("WEAR_MODULES", ""))

    print(f"package: {package}")
    for m in modules:
        mapping = f", {m['name']}/mapping.txt" if m["mapping"] else ""
        print(f"{m['name']}: {m['name']}/{m['aab'].name}{mapping} -> {m['track']}")
        if not m["mapping"]:
            print(f"::warning::No mapping.txt for {m['name']}; Play gets no deobfuscation file")
    print(f"status: {status}")
    if dry_run:
        print("dry run: no requests made")
        return

    token = os.environ.get("PLAY_ACCESS_TOKEN", "")
    if not token:
        fail("PLAY_ACCESS_TOKEN is required")
    try:
        codes = publish(package, status, modules, token)
    except PlayError as e:
        fail(str(e))

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(f"### Google Play: {package}\n\n| Track | Version codes | Status |\n|---|---|---|\n")
            for t, c in codes.items():
                f.write(f"| `{t}` | {', '.join(c)} | {status} |\n")


if __name__ == "__main__":
    main()
