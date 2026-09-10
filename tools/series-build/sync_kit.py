#!/usr/bin/env python3
"""
Copy the canonical build kit (build.py, template.html, publish_site.py,
series_check.py, katex_check.js) from erisml-lib/tools/series-build into the
`.build/` directory of one or more sibling volume repos, so the per-repo copies
never drift from the canonical one.

Usage (from erisml-lib root):
    python tools/series-build/sync_kit.py                 # all volumes in ../geometric-*
    python tools/series-build/sync_kit.py ../geometric-law ../geometric-methods
    python tools/series-build/sync_kit.py --check         # exit 1 if any copy differs
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = ["build.py", "template.html", "publish_site.py", "series_check.py", "katex_check.js"]
# Volumes that have their own bespoke pipeline and must NOT receive build.py/template.html:
OWN_PIPELINE = {"geometric-ethics"}   # docx -> pandoc (.build/build_ethics.py)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="*", help="volume repo roots (default: ../geometric-*)")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    erisml_root = HERE.parent.parent
    repos = [Path(r).resolve() for r in args.repos] or sorted(
        p for p in erisml_root.parent.glob("geometric-*") if (p / ".git").exists())
    stale = 0
    for repo in repos:
        files = KIT if repo.name not in OWN_PIPELINE else [f for f in KIT if f not in ("build.py", "template.html")]
        dst_dir = repo / ".build"
        dst_dir.mkdir(exist_ok=True)
        for f in files:
            src, dst = HERE / f, dst_dir / f
            same = dst.exists() and filecmp.cmp(src, dst, shallow=False)
            if args.check:
                if not same:
                    print(f"STALE  {dst}"); stale += 1
            elif not same:
                shutil.copy2(src, dst); print(f"synced {dst}")
    if args.check:
        print("all copies current" if not stale else f"{stale} stale copy(ies)")
        sys.exit(1 if stale else 0)


if __name__ == "__main__":
    main()
