#!/usr/bin/env python3
"""Compare installed and published versions without changing any files."""

from __future__ import annotations

import base64
import re
import subprocess
import urllib.request
from pathlib import Path

REPO = "Lzjin426/lzj-law-md"
RAW_URL = f"https://raw.githubusercontent.com/{REPO}/main/VERSION"
VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


def parse_version(value: str) -> tuple[int, int, int] | None:
    value = value.strip()
    if not re.fullmatch(r"[vV]?\d+(?:\.\d+){0,2}", value):
        return None
    parts = [int(part) for part in value.lstrip("vV").split(".")]
    return tuple((parts + [0, 0])[:3])


def fetch_gh() -> str:
    result = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/VERSION?ref=main", "--jq", ".content"],
        capture_output=True,
        text=True,
        timeout=3,
        check=True,
    )
    return base64.b64decode(result.stdout.strip(), validate=False).decode("utf-8").strip()


def fetch_raw() -> str:
    request = urllib.request.Request(RAW_URL, headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(request, timeout=2) as response:
        return response.read(128).decode("utf-8").strip()


def remote_version() -> str:
    for fetch in (fetch_gh, fetch_raw):
        try:
            result = fetch()
            if result:
                return result
        except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
            continue
    return ""


def main() -> int:
    try:
        local = VERSION_FILE.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        print("CHECK_SKIPPED missing-local-version")
        return 0
    local_version = parse_version(local)
    if local_version is None:
        print("CHECK_SKIPPED invalid-local-version")
        return 0
    remote = remote_version()
    if not remote:
        print("CHECK_SKIPPED network-unavailable")
        return 0
    published = parse_version(remote)
    if published is None:
        print("CHECK_SKIPPED invalid-remote-version")
    elif published > local_version:
        print(f"UPDATE_AVAILABLE local={local} remote={remote} https://github.com/{REPO}")
    else:
        print(f"UP_TO_DATE local={local} remote={remote}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
