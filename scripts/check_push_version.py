#!/usr/bin/env python3
"""Require a version increase before publishing this independent skill."""

from __future__ import annotations

import os
import subprocess
import sys

# Running this check must not create __pycache__ inside the shared toolbox.
sys.dont_write_bytecode = True
from check_update import REPO, VERSION_FILE, parse_version, remote_version


def _same_path(a: str, b: str) -> bool:
    """Compare filesystem paths cross-platform (separators, case, trailing slash)."""
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def git_state_error(local: str) -> str:
    root = VERSION_FILE.resolve().parent

    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        return result.stdout.strip()

    try:
        if not _same_path(git("rev-parse", "--show-toplevel"), str(root)):
            return "not-independent-repository"
        allowed_urls = {
            f"https://github.com/{REPO}",
            f"https://github.com/{REPO}.git",
            f"git@github.com:{REPO}.git",
            f"git@github.com:{REPO}",
        }
        push_urls = git("remote", "get-url", "--push", "--all", "origin").splitlines()
        if len(push_urls) != 1 or push_urls[0] not in allowed_urls:
            return "unexpected-push-remote"
        if git("branch", "--show-current") != "main":
            return "unexpected-branch"
        if git("rev-parse", "--is-shallow-repository") != "false":
            return "shallow-repository"
        if git("status", "--porcelain", "--untracked-files=all"):
            return "dirty-worktree"
        if git("show", "HEAD:VERSION") != local:
            return "uncommitted-version"
        files = git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        if "VERSION" not in files:
            return "version-not-in-latest-commit"
        try:
            git("rev-parse", "--verify", "HEAD^")
        except subprocess.CalledProcessError:
            return ""
        try:
            previous = parse_version(git("show", "HEAD^:VERSION"))
        except subprocess.CalledProcessError:
            return "parent-version-missing"
        current = parse_version(local)
        if previous is None or current is None:
            return "invalid-parent-version"
        if current <= previous:
            return "version-not-incremented"
    except (OSError, subprocess.SubprocessError):
        return "repository-unavailable"
    return ""


def empty_remote_repository() -> bool:
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{REPO}/branches?per_page=1", "--jq", "length"],
            capture_output=True,
            text=True,
            timeout=4,
            check=True,
        )
        return result.stdout.strip() == "0"
    except (OSError, subprocess.SubprocessError):
        return False


def main() -> int:
    try:
        local = VERSION_FILE.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        print("COULD_NOT_VERIFY missing-local-version")
        return 2
    current = parse_version(local)
    if current is None:
        print("COULD_NOT_VERIFY invalid-local-version")
        return 2
    git_error = git_state_error(local)
    if git_error:
        print(f"COULD_NOT_VERIFY {git_error}")
        return 2
    remote = remote_version()
    if not remote:
        if empty_remote_repository():
            print(f"VERSION_OK local={local} remote=none-first-release")
            return 0
        print("COULD_NOT_VERIFY remote-version-unavailable")
        return 2
    published = parse_version(remote)
    if published is None:
        print("COULD_NOT_VERIFY invalid-remote-version")
        return 2
    if current > published:
        print(f"VERSION_OK local={local} remote={remote}")
        return 0
    print(f"BUMP_REQUIRED local={local} remote={remote} https://github.com/{REPO}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
