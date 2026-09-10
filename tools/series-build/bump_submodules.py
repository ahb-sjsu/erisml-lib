#!/usr/bin/env python3
"""
Re-pin every Geometric Series submodule in erisml-lib to the tip of the branch
declared in .gitmodules (normally `site`), verifying each tip actually contains
a root index.html before touching the index.

This exists because the July 2026 bump pinned the gitlinks to each repo's
default branch (source manuscripts), which deployed 11 empty volume directories
and 404s on erisml.org. Always bump with this script, never by hand.

Usage (from the erisml-lib root):
    python tools/series-build/bump_submodules.py            # stage updated gitlinks
    python tools/series-build/bump_submodules.py --commit   # ...and commit
    python tools/series-build/bump_submodules.py --only docs/geometric-law
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def sh(args, cwd, check=True):
    r = subprocess.run(args, cwd=str(cwd), text=True, encoding="utf-8", errors="replace", capture_output=True)
    if check and r.returncode != 0:
        print(f"ERROR: {' '.join(args)}\n{r.stderr}"); sys.exit(1)
    return r.stdout.strip()


def tip_has_index(url: str, sha: str) -> bool | None:
    """True/False via the GitHub API when `gh` is available, None if we cannot tell."""
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
    if not m:
        return None
    r = subprocess.run(["gh", "api", f"repos/{m.group(1)}/{m.group(2)}/contents/index.html?ref={sha}",
                        "--jq", ".name"], text=True, capture_output=True)
    if r.returncode == 0 and r.stdout.strip() == "index.html":
        return True
    if r.returncode != 0 and "Not Found" in (r.stdout + r.stderr):
        return False
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--only", action="append", default=[], help="submodule path(s) to bump; default all")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--allow-unverified", action="store_true",
                    help="stage a tip even when index.html presence could not be verified")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()

    raw = sh(["git", "config", "-f", ".gitmodules", "--list"], root)
    mods: dict[str, dict] = {}
    for line in raw.splitlines():
        m = re.match(r"submodule\.([^=]+?)\.(path|url|branch)=(.*)$", line)
        if m:
            mods.setdefault(m.group(1), {})[m.group(2)] = m.group(3)

    changed = []
    for name, cfg in mods.items():
        path, url, branch = cfg["path"], cfg["url"], cfg.get("branch", "site")
        if args.only and path not in args.only:
            continue
        current = sh(["git", "rev-parse", f":{path}"], root, check=False)
        ls = sh(["git", "ls-remote", url, f"refs/heads/{branch}"], root, check=False)
        if not ls:
            print(f"  {path:30s} SKIP: remote branch '{branch}' not found at {url}"); continue
        tip = ls.split()[0]
        verified = tip_has_index(url, tip)
        if verified is False:
            print(f"  {path:30s} REFUSED: {branch}@{tip[:8]} has no root index.html"); continue
        if verified is None and not args.allow_unverified:
            print(f"  {path:30s} SKIP: could not verify index.html (no gh?); use --allow-unverified"); continue
        if tip == current:
            print(f"  {path:30s} up to date ({tip[:8]})"); continue
        sh(["git", "update-index", "--cacheinfo", f"160000,{tip},{path}"], root)
        print(f"  {path:30s} {current[:8]} -> {tip[:8]}  [{branch}]")
        changed.append((path, current[:8], tip[:8]))

    if not changed:
        print("nothing to bump"); return
    if args.commit:
        body = "\n".join(f"- {p}: {a} -> {b}" for p, a, b in changed)
        msg = f"chore(portal): bump {len(changed)} Geometric Series submodule(s) to their site tips\n\n{body}\n"
        sh(["git", "commit", "-q", "-m", msg], root)
        print("committed:", sh(["git", "log", "--oneline", "-1"], root))
    else:
        print(f"{len(changed)} gitlink(s) staged; commit with: git commit -m 'chore(portal): bump submodules'")


if __name__ == "__main__":
    main()
