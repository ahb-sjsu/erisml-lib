#!/usr/bin/env python3
"""
Build a Geometric Series volume and publish the HTML to the repo's `site` branch.

The erisml-lib portal consumes each volume as a git submodule pinned to the
volume repo's `site` branch (see erisml-lib/.gitmodules), so `site` must hold
ONLY the built HTML (+ the static assets the pages need) at the branch root.

Steps:
  1. build.py -> temp dir (fails if the build fails or books.json disagrees)
  2. fetch origin/site, check it out in a detached temporary worktree
  3. replace its contents with the fresh build (+ --keep paths copied from the
     working tree, e.g. assets/ images/)
  4. commit ("site: ...") and, with --push, push to origin site
  5. print the new site commit sha (feed it to erisml-lib's bump_submodules.py)

Usage (from the volume repo root):
    python .build/publish_site.py --message "site: rebuild after proofreading pass" --push
    python .build/publish_site.py --keep assets --push          # methods: demos.js/.css
    python .build/publish_site.py --dry-run                      # build + diff only
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sh(args: list[str], cwd: Path, check: bool = True, capture: bool = True) -> str:
    r = subprocess.run(args, cwd=str(cwd), text=True, encoding="utf-8", errors="replace",
                       capture_output=capture)
    if check and r.returncode != 0:
        print(f"ERROR: {' '.join(args)}\n{r.stdout}\n{r.stderr}")
        sys.exit(1)
    return (r.stdout or "").strip()


def main():
    ap = argparse.ArgumentParser(description="Build and publish a volume to its site branch")
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--branch", default="site")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--message", "-m", default=None, help="commit message (default: 'site: rebuild <date>')")
    ap.add_argument("--keep", action="append", default=[],
                    help="path (relative to repo root) to copy into the site tree as-is; repeatable")
    ap.add_argument("--push", action="store_true", help="push the new site commit to the remote")
    ap.add_argument("--dry-run", action="store_true", help="build and show the diff, do not commit")
    ap.add_argument("--build-arg", action="append", default=[], help="extra arg for build.py; repeatable")
    ap.add_argument("--source-dir", default=None,
                    help="skip build.py and publish the *.html files found in this directory instead "
                         "(for volumes with their own pipeline, e.g. geometric-ethics: --source-dir . --keep images --keep book.css)")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()
    if not (repo / ".git").exists():
        print(f"ERROR: {repo} is not a git repository root"); sys.exit(1)
    build_py = repo / ".build" / "build.py"
    if not build_py.exists():
        build_py = HERE / "build.py"

    tmp = Path(tempfile.mkdtemp(prefix="site-build-"))
    out = tmp / "out"
    wt = tmp / "wt"
    try:
        # 1. build (or collect pre-built pages)
        if args.source_dir:
            src_dir = (repo / args.source_dir).resolve()
            out.mkdir(parents=True)
            for p in sorted(src_dir.glob("*.html")):
                shutil.copy2(p, out / p.name)
        else:
            cmd = [sys.executable, str(build_py), "--repo-root", str(repo), "--output-dir", str(out), "--quiet"] + args.build_arg
            r = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", capture_output=True)
            if r.returncode != 0:
                print(r.stdout); print(r.stderr); print("ERROR: build failed; nothing published"); sys.exit(1)
        n_pages = len(list(out.glob("*.html")))
        if not (out / "index.html").exists() or n_pages < 2:
            print(f"ERROR: build produced {n_pages} page(s) and/or no index.html; refusing to publish"); sys.exit(1)
        print(f"built {n_pages} pages -> {out}")

        # 2. worktree on origin/<branch>
        sh(["git", "fetch", args.remote, args.branch], repo, check=False)
        has_remote = sh(["git", "rev-parse", "--verify", "--quiet", f"{args.remote}/{args.branch}"], repo, check=False)
        if has_remote:
            sh(["git", "worktree", "add", "--detach", str(wt), f"{args.remote}/{args.branch}"], repo)
        else:
            print(f"note: {args.remote}/{args.branch} does not exist; creating an orphan branch")
            sh(["git", "worktree", "add", "--detach", str(wt)], repo)
            sh(["git", "checkout", "--orphan", f"_publish_{args.branch}"], wt)
            sh(["git", "rm", "-rfq", "--cached", "."], wt, check=False)
            for p in wt.iterdir():
                if p.name != ".git":
                    shutil.rmtree(p) if p.is_dir() else p.unlink()

        # 3. replace contents
        for p in wt.iterdir():
            if p.name == ".git":
                continue
            shutil.rmtree(p) if p.is_dir() else p.unlink()
        for p in out.iterdir():
            shutil.copy2(p, wt / p.name)
        for rel in args.keep:
            src = repo / rel
            if not src.exists():
                print(f"WARNING: --keep {rel}: not found in working tree, skipped"); continue
            dst = wt / rel
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
        (wt / "README.md").write_text(
            f"# {repo.name} — built site\n\nGenerated by `.build/publish_site.py`; do not edit by hand. "
            f"Source lives on the default branch. Served at https://erisml.org/ via the erisml-lib submodule.\n",
            encoding="utf-8")

        sh(["git", "add", "-A"], wt)
        stat = sh(["git", "diff", "--cached", "--stat"], wt)
        if not stat:
            print("site branch already up to date; nothing to commit"); return
        print(stat.splitlines()[-1])
        if args.dry_run:
            print("(dry run) not committing"); return

        # 4. commit / push
        from datetime import date
        msg = args.message or f"site: rebuild {date.today().isoformat()}"
        src_sha = sh(["git", "rev-parse", "--short", "HEAD"], repo)
        sh(["git", "commit", "-q", "-m", f"{msg}\n\nBuilt from {repo.name}@{src_sha} with the Geometric Series build kit."], wt)
        new_sha = sh(["git", "rev-parse", "HEAD"], wt)
        if args.push:
            sh(["git", "push", args.remote, f"HEAD:refs/heads/{args.branch}"], wt)
            sh(["git", "branch", "-f", args.branch, new_sha], repo, check=False)
            print(f"pushed {args.remote}/{args.branch} = {new_sha}")
        else:
            sh(["git", "branch", "-f", args.branch, new_sha], repo)
            print(f"committed locally: {args.branch} = {new_sha} (re-run with --push to publish)")
        print(f"SITE_SHA={new_sha}")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=str(repo), capture_output=True)
        subprocess.run(["git", "worktree", "prune"], cwd=str(repo), capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
