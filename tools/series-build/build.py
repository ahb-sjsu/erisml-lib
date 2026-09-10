#!/usr/bin/env python3
"""
Canonical build script for the Geometric Series volumes (erisml.org).

Converts a volume's Markdown chapters into the unified Geometric Series
"modern brand-nav" HTML: shared CSS (../assets/css/style.css + ../book/book.css),
a #series-nav-list populated by ../assets/js/series.js from docs/books.json,
breadcrumb, prev/next chapter navigation, KaTeX auto-render, per-book footer.

This file is the SINGLE SOURCE OF TRUTH. Each volume repo carries a copy in
its `.build/` directory (build.py + template.html). Sync copies with:

    python tools/series-build/sync_kit.py            # from erisml-lib

Usage (from a volume repo root, or with --repo-root):
    python .build/build.py                       # build all chapters -> output/
    python .build/build.py chapters/ch01.md      # build one file
    python .build/build.py --output-dir out      # custom output directory
    python .build/build.py --no-manifest-check   # skip books.json identity check

Book identity (number / title / subtitle) is validated against docs/books.json
in a sibling erisml-lib checkout when one can be found; the manifest is the
single source of truth for series numbering (see series.js).
"""

from __future__ import annotations

import argparse
import html as htmllib
import re
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    import markdown
except ImportError:
    print("ERROR: 'markdown' package not installed. Run: pip install markdown")
    sys.exit(1)


SERIES_TAGLINE = "The geometry was always real. The scalars were always insufficient."

# ---------------------------------------------------------------------------
# Per-book configuration.
#
#   number        series number (must match docs/books.json)
#   title         book title (must match docs/books.json)
#   subtitle      book subtitle
#   source_dirs   directories (relative to repo root) searched for `glob`
#   glob          filename glob within each source dir
#   exclude       optional list of filename patterns to skip (fnmatch)
#   parts         optional list of (part_title, [file-stem, ...]) groups for the
#                 contents page. Stems not listed in any part fall into a final
#                 "Appendices" group if they start with "appendix", otherwise
#                 into an "Other" group (which is a build warning).
#   strip_zero_pad  if True, chapter-01-foo.md -> chapter-1-foo.html (keeps
#                 historical URLs for volumes that were published that way)
#   abstract_md   optional Markdown shown on the contents page under the hero
#   extra_head    optional raw HTML appended inside <head> on every page
#   extra_scripts optional raw HTML appended before </body> on every page
#   footer_note   optional per-book footer tagline (default SERIES_TAGLINE)
# ---------------------------------------------------------------------------

METHODS_EXTRA_HEAD = """
  <link rel="stylesheet" href="assets/demos.css">
  <script>
    // Legacy single-page URLs were index.html#chapter-02-... ; forward them to
    // the static per-chapter pages.
    (function () {
      var h = (location.hash || '').slice(1);
      if (/^(chapter-\\d{2}-|appendix-[a-z]-)[a-z0-9-]+$/.test(h)) {
        location.replace(h + '.html');
      }
    })();
  </script>"""

METHODS_EXTRA_SCRIPTS = """
  <script src="assets/demos.js"></script>
  <script>
    // Mount the interactive demos (assets/demos.js) for this chapter.
    document.addEventListener('DOMContentLoaded', function () {
      var id = document.body.getAttribute('data-chapter-id');
      var host = document.querySelector('.chapter-content');
      if (id && host && typeof window.injectDemos === 'function') {
        window.injectDemos(id, host);
      }
    });
  </script>"""

AESTHETICS_ABSTRACT = """
Aesthetic judgment, this book argues, is not a point on a line. It is a location
in a space &mdash; a space with dimensions, distances, directions, regimes, and
curvature. When we flatten that structure into a scalar (a four-star rating, a
Metacritic score, a number-one hit), we lose the information that matters most:
which qualities are present, where uncertainty concentrates, how judgment shifts
across genres, and where the rules discontinuously change.

The argument is empirical as well as philosophical. We present evidence from
**$n{=}4{,}998$ Gutenberg&#8596;Goodreads books** (discovery $R{=}0.241$,
$17\\sigma$) and **$n{=}24{,}801$ music tracks** from FMA-Medium ($28\\sigma$
after genre residualization), including a strong **cross-lingual invariance**
signal ($\\rho \\approx 0.70$ on Hellinger and Mahalanobis features across six
language families) and a **cross-modality sign flip**: the same geometric
feature that rewards continuity in books ($\\rho{=}{+}0.126$, $8.4\\sigma$)
punishes it in music ($\\rho{=}{-}0.076$, $p{=}5\\times10^{-33}$). Books reward
coherence; music rewards contrast. The aesthetic geometry has directionality
that is modality-specific, and that directionality is measurable.
"""

BOOK_CONFIGS: dict[str, dict] = {
    "geometric-methods": {
        "number": 1, "title": "Geometric Methods",
        "subtitle": "Computational Modeling",
        "source_dirs": ["chapters"], "glob": "*.md",
        "parts": [
            ("Part I: Foundations", [
                "chapter-01-why-geometry", "chapter-02-mahalanobis-distance",
                "chapter-03-hyperbolic-geometry", "chapter-04-spd-manifolds",
                "chapter-05-topological-data-analysis"]),
            ("Part II: Algorithms on Manifolds", [
                "chapter-06-pathfinding-on-manifolds", "chapter-07-equilibrium-on-manifolds",
                "chapter-08-pareto-optimization", "chapter-09-adversarial-robustness",
                "chapter-10-adversarial-probing"]),
            ("Part III: Design Patterns", [
                "chapter-11-subset-enumeration", "chapter-12-compositional-testing",
                "chapter-13-group-theoretic-augmentation", "chapter-14-gradient-reversal",
                "chapter-15-cholesky-parameterization"]),
            ("Part IV: Systems & Integration", [
                "chapter-16-geometric-pipelines", "chapter-17-scaling",
                "chapter-18-production-deployment", "chapter-19-case-study-defect-prediction",
                "chapter-20-case-study-bioacoustics"]),
        ],
        "extra_head": METHODS_EXTRA_HEAD,
        "extra_scripts": METHODS_EXTRA_SCRIPTS,
        "footer_note": "Geometry first. Scalars, if ever, last.",
    },
    "geometric-reasoning": {
        "number": 3, "title": "Geometric Reasoning",
        "subtitle": "From Search to Manifolds",
        "source_dirs": ["chapters"], "glob": "*.md",
    },
    "geometric-economics": {
        "number": 4, "title": "Geometric Economics",
        "subtitle": "Decision Manifolds, Equilibria, and the Geometry of Markets",
        "source_dirs": ["chapters"], "glob": "*.md",
    },
    "geometric-law": {
        "number": 5, "title": "Geometric Law",
        "subtitle": "Symmetry, Invariance, and the Structure of Legal Reasoning",
        "source_dirs": ["chapters"], "glob": "*.md",
    },
    "geometric-cognition": {
        "number": 6, "title": "Geometric Cognition",
        "subtitle": "The Mathematical Structure of Human and Artificial Thought",
        "source_dirs": ["chapters"], "glob": "*.md",
    },
    "geometric-communication": {
        "number": 7, "title": "Geometric Communication",
        "subtitle": "Language, Signal, and the Topology of Meaning",
        "source_dirs": ["manuscript/part_i", "manuscript/part_ii",
                        "manuscript/part_iii", "manuscript/part_iv",
                        "manuscript/part_v", "manuscript/appendices"],
        "glob": "*.md",
    },
    "geometric-medicine": {
        "number": 8, "title": "Geometric Medicine",
        "subtitle": "Clinical Reasoning, Triage, and the Ethics of Allocation",
        "source_dirs": ["manuscript/part_i", "manuscript/part_ii",
                        "manuscript/part_iii", "manuscript/part_iv",
                        "manuscript/appendices"],
        "glob": "*.md",
    },
    "geometric-education": {
        "number": 9, "title": "Geometric Education",
        "subtitle": "Learning, Assessment, and the Topology of Understanding",
        "source_dirs": ["manuscript/part_i", "manuscript/part_ii",
                        "manuscript/part_iii", "manuscript/appendices"],
        "glob": "*.md",
    },
    "geometric-politics": {
        "number": 10, "title": "Geometric Politics",
        "subtitle": "Representation, Polarization, and the Topology of Democratic Choice",
        "source_dirs": ["manuscript/part_i", "manuscript/part_ii",
                        "manuscript/part_iii", "manuscript/appendices"],
        "glob": "*.md",
    },
    "geometric-ai": {
        "number": 11, "title": "Geometric AI",
        "subtitle": "Alignment, Safety, and the Structure-Preserving Path to Superintelligence",
        "source_dirs": ["manuscript", "manuscript/part_i", "manuscript/part_ii",
                        "manuscript/part_iii", "manuscript/part_iv", "manuscript/part_v",
                        "manuscript/part_vi", "manuscript/appendices", "manuscript/backmatter"],
        "glob": "*.md",
    },
    "geometric-gastronomy": {
        "number": 12, "title": "Geometric Gastronomy",
        "subtitle": "The Mathematical Structure of Flavor, Pairing, and Culinary Harmony",
        "source_dirs": ["chapters"], "glob": "*.md",
    },
    "geometric-aesthetics": {
        "number": 13, "title": "Geometric Aesthetics",
        "subtitle": "The Mathematical Structure of Judgment",
        "source_dirs": ["book/src", "book/src/appendices"], "glob": "*.md",
        "exclude": ["_*.md"],
        "strip_zero_pad": True,
        "abstract_md": AESTHETICS_ABSTRACT,
        "footer_note": "Beauty is not a number. It is a geometry.",
        "parts": [
            ("Part I: The Problem", ["chapter-01-*", "chapter-02-*", "chapter-03-*"]),
            ("Part II: Foundations", ["chapter-04-*", "chapter-05-*", "chapter-06-*",
                                      "chapter-07-*", "chapter-08-*", "chapter-09-*"]),
            ("Part III: Dynamics", ["chapter-10-*", "chapter-11-*", "chapter-12-*",
                                    "chapter-13-*", "chapter-14-*", "chapter-15-*"]),
            ("Part IV: Meta", ["chapter-16-*", "chapter-17-*", "chapter-18-*", "chapter-19-*"]),
            ("Part V: Applications", ["chapter-20-*", "chapter-21-*", "chapter-22-*",
                                      "chapter-23-*", "chapter-24-*", "chapter-25-*",
                                      "chapter-26-*", "chapter-27-*", "chapter-28-*"]),
            ("Part VI: Conclusion", ["chapter-29-*", "chapter-30-*"]),
        ],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_repo_name(repo_root: Path) -> str:
    name = repo_root.name.lower()
    if name in BOOK_CONFIGS:
        return name
    for key in BOOK_CONFIGS:
        if key in name:
            return key
    return name


def find_manifest(repo_root: Path, explicit: str | None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates += [
        repo_root.parent / "erisml-lib" / "docs" / "books.json",
        repo_root.parent.parent / "books.json",          # when repo is docs/<book>/
        repo_root / ".build" / "books.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def check_manifest(config: dict, manifest_path: Path) -> list[str]:
    """Return a list of problems (empty if identity matches books.json)."""
    problems = []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    slug = config["slug"]
    vol = next((v for v in data.get("volumes", []) if v.get("slug") == slug), None)
    if vol is None:
        return [f"slug '{slug}' not found in {manifest_path}"]
    if vol.get("number") != config["number"]:
        problems.append(f"number mismatch: build={config['number']} manifest={vol.get('number')}")
    if vol.get("title") != config["title"]:
        problems.append(f"title mismatch: build='{config['title']}' manifest='{vol.get('title')}'")
    return problems


def protect_math(text: str) -> tuple[str, dict[str, str]]:
    """Replace LaTeX math with placeholders before Markdown processing.

    Fenced code blocks are left untouched so `$` inside code is not treated as math.
    """
    placeholders: dict[str, str] = {}
    counter = 0

    def _replace(match: re.Match) -> str:
        nonlocal counter
        key = f"\x00MATH{counter}\x00"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    def _protect_segment(seg: str) -> str:
        seg = re.sub(r'\$\$(.+?)\$\$', _replace, seg, flags=re.DOTALL)
        seg = re.sub(r'(?<![\$\\])\$(?!\$)(?!\s)(.+?)(?<![\s\\])\$(?!\$)', _replace, seg)
        seg = re.sub(r'\\\[(.+?)\\\]', _replace, seg, flags=re.DOTALL)
        seg = re.sub(r'\\\((.+?)\\\)', _replace, seg)
        return seg

    parts = re.split(r'(^```.*?^```[ \t]*$|^~~~.*?^~~~[ \t]*$)', text, flags=re.DOTALL | re.MULTILINE)
    out = []
    for i, seg in enumerate(parts):
        out.append(seg if i % 2 == 1 else _protect_segment(seg))
    return "".join(out), placeholders


def restore_math(html: str, placeholders: dict[str, str]) -> str:
    for key, value in placeholders.items():
        html = html.replace(key, value)
    return html


def extract_title(md_text: str) -> str:
    match = re.search(r'^#\s+(.+?)\s*(?:\{#[^}]*\})?\s*$', md_text, re.MULTILINE)
    if match:
        title = match.group(1).strip()
        title = re.sub(r'\*+(.+?)\*+', r'\1', title)
        return title
    return "Untitled"


def _make_converter() -> "markdown.Markdown":
    return markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "smarty", "attr_list", "footnotes"],
        extension_configs={
            "toc": {"permalink": False, "toc_depth": "2-4"},
            "smarty": {"smart_quotes": True, "smart_dashes": True},
        },
    )


def md_to_html(md_text: str) -> str:
    protected, placeholders = protect_math(md_text)
    body = _make_converter().convert(protected)
    return restore_math(body, placeholders)


def output_name(md_path: Path, config: dict) -> str:
    stem = md_path.stem
    if config.get("strip_zero_pad"):
        m = re.match(r"^(chapter)-0*(\d+)-(.+)$", stem)
        if m:
            stem = f"{m.group(1)}-{int(m.group(2))}-{m.group(3)}"
    return f"{stem}.html"


def find_source_files(repo_root: Path, config: dict) -> list[Path]:
    import fnmatch
    files: list[Path] = []
    seen: set[Path] = set()
    excludes = config.get("exclude", [])
    for src_dir in config["source_dirs"]:
        search_dir = repo_root / src_dir
        if not search_dir.exists():
            continue
        for f in sorted(search_dir.glob(config["glob"])):
            if not f.is_file() or f.suffix != ".md":
                continue
            if any(fnmatch.fnmatch(f.name, pat) for pat in excludes):
                continue
            if f.resolve() in seen:
                continue
            seen.add(f.resolve())
            files.append(f)
    return files


def _fill(template: str, *, title: str, body: str, config: dict, build_date: str,
          chapter_id: str, nav_top: str, nav_bottom: str) -> str:
    rep = {
        "{{content}}": body,
        "{{title}}": htmllib.escape(title, quote=False),
        "{{book_title}}": config["title"],
        "{{book_subtitle}}": config["subtitle"],
        "{{book_slug}}": config["slug"],
        "{{book_number}}": str(config["number"]),
        "{{chapter_id}}": chapter_id,
        "{{nav_top}}": nav_top,
        "{{nav_bottom}}": nav_bottom,
        "{{footer_note}}": config.get("footer_note") or SERIES_TAGLINE,
        "{{extra_head}}": config.get("extra_head", ""),
        "{{extra_scripts}}": config.get("extra_scripts", ""),
        "{{build_date}}": build_date,
    }
    out = template
    for k, v in rep.items():
        out = out.replace(k, v)
    return out


def _short(title: str, n: int = 64) -> str:
    return title if len(title) < n else title[: n - 4].rstrip() + "…"


def nav_html(prev: tuple[str, str] | None, nxt: tuple[str, str] | None, cls: str) -> str:
    p = (f'<a href="{prev[1]}" class="nav-prev">&larr; {htmllib.escape(_short(prev[0]))}</a>'
         if prev else '<span class="nav-prev"></span>')
    n = (f'<a href="{nxt[1]}" class="nav-next">{htmllib.escape(_short(nxt[0]))} &rarr;</a>'
         if nxt else '<span class="nav-next"></span>')
    return (f'<div class="{cls}">\n        {p}\n        '
            f'<a href="index.html" class="nav-toc">Contents</a>\n        {n}\n      </div>')


def group_parts(chapters: list[tuple[str, str, str]], config: dict) -> list[tuple[str, list]]:
    """Return [(part_title, [(stem, title, html_name), ...]), ...] honoring config['parts']."""
    import fnmatch
    parts_cfg = config.get("parts")
    if not parts_cfg:
        return [("", chapters)]
    remaining = list(chapters)
    groups: list[tuple[str, list]] = []
    for part_title, patterns in parts_cfg:
        members = []
        for ch in list(remaining):
            if any(fnmatch.fnmatch(ch[0], pat) for pat in patterns):
                members.append(ch)
                remaining.remove(ch)
        if members:
            groups.append((part_title, members))
        else:
            print(f"  WARNING: part '{part_title}' matched no chapters")
    appendices = [c for c in remaining if c[0].lower().startswith("appendix")]
    other = [c for c in remaining if c not in appendices]
    if appendices:
        groups.append(("Appendices", appendices))
    if other:
        print(f"  WARNING: {len(other)} file(s) not assigned to any part: "
              + ", ".join(c[0] for c in other))
        groups.append(("Other", other))
    return groups


def generate_index(chapters: list[tuple[str, str, str]], template: str,
                   config: dict, build_date: str) -> str:
    """Generate index.html: hero + (optional abstract) + contents (flat or by part)."""
    body = [
        '<header class="book-hero">',
        f'  <p class="book-number">Book {config["number"]} of the Geometric Series</p>',
        f'  <h1>{config["title"]}</h1>',
        f'  <p class="book-subtitle">{config["subtitle"]}</p>',
        '  <p class="book-byline">A volume in the <em>Geometric Series</em> by Andrew H. Bond.</p>',
        '</header>',
    ]
    if config.get("abstract_md"):
        body.append('<div class="book-abstract">')
        body.append(md_to_html(config["abstract_md"].strip()))
        body.append('</div>')
    body.append('<h2>Contents</h2>')
    for part_title, members in group_parts(chapters, config):
        items = [f'    <li><a href="{h}">{htmllib.escape(t, quote=False)}</a></li>'
                 for _, t, h in members]
        if part_title:
            body.append(f'<div class="toc-part">\n  <h3>{htmllib.escape(part_title)}</h3>')
            body.append('  <ol class="toc-chapters">\n' + "\n".join(items) + '\n  </ol>\n</div>')
        else:
            body.append('<ol class="toc-chapters">\n' + "\n".join(items) + '\n</ol>')
    return _fill(template, title="Contents", body="\n".join(body), config=config,
                 build_date=build_date, chapter_id="index", nav_top="", nav_bottom="")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build(repo_root: Path, output_dir: Path, files: list[str] | None = None,
          manifest: str | None = None, manifest_check: bool = True,
          quiet: bool = False) -> list[tuple[str, str, str]]:
    def log(*a):
        if not quiet:
            print(*a)

    repo_name = detect_repo_name(repo_root)
    base = BOOK_CONFIGS.get(repo_name)
    if base is None:
        print(f"ERROR: Unknown repo '{repo_name}'. Add it to BOOK_CONFIGS.")
        sys.exit(1)
    config = {**base, "slug": repo_name}

    if manifest_check:
        mpath = find_manifest(repo_root, manifest)
        if mpath is None:
            log("  note: books.json not found; skipping manifest identity check")
        else:
            problems = check_manifest(config, mpath)
            if problems:
                print(f"ERROR: build config disagrees with {mpath}:")
                for p in problems:
                    print("   -", p)
                print("Fix BOOK_CONFIGS (or books.json) so the series numbering has one source of truth.")
                sys.exit(2)
            log(f"  manifest ok: Book {config['number']} '{config['title']}' ({mpath})")

    template_path = repo_root / ".build" / "template.html"
    if not template_path.exists():
        template_path = Path(__file__).resolve().parent / "template.html"
    if not template_path.exists():
        print(f"ERROR: Template not found at {template_path}")
        sys.exit(1)
    template = template_path.read_text(encoding="utf-8")
    build_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    output_dir.mkdir(parents=True, exist_ok=True)
    all_sources = find_source_files(repo_root, config)
    if not all_sources:
        print("No source Markdown files found.")
        sys.exit(0)
    selected = ([Path(f).resolve() for f in files] if files else all_sources)

    # Chapter order for prev/next is always the full ordered source list.
    ordered = [(p.stem, extract_title(p.read_text(encoding="utf-8")), output_name(p, config))
               for p in all_sources]
    idx_of = {stem: i for i, (stem, _, _) in enumerate(ordered)}

    log(f"Building {config['title']} (Book {config['number']})")
    log(f"  Source files: {len(all_sources)}  Output: {output_dir}\n")

    for md_path in selected:
        i = idx_of.get(md_path.stem)
        stem, title, html_name = ordered[i] if i is not None else (
            md_path.stem, extract_title(md_path.read_text(encoding="utf-8")), output_name(md_path, config))
        prev = (ordered[i - 1][1], ordered[i - 1][2]) if i not in (None, 0) else None
        nxt = (ordered[i + 1][1], ordered[i + 1][2]) if i is not None and i + 1 < len(ordered) else None
        body = md_to_html(md_path.read_text(encoding="utf-8"))
        page = _fill(template, title=title, body=body, config=config, build_date=build_date,
                     chapter_id=stem,
                     nav_top=nav_html(prev, nxt, "chapter-nav-top"),
                     nav_bottom=nav_html(prev, nxt, "chapter-nav-bottom"))
        (output_dir / html_name).write_text(page, encoding="utf-8")
        log(f"  {md_path.name} -> {html_name}  [{title}]")

    (output_dir / "index.html").write_text(
        generate_index(ordered, template, config, build_date), encoding="utf-8")
    log(f"\n  index.html  [Contents]\nDone. {len(selected)} page(s) built -> {output_dir}")
    return ordered


def main():
    ap = argparse.ArgumentParser(description="Build a Geometric Series volume from Markdown")
    ap.add_argument("files", nargs="*", help="Specific .md files (default: all)")
    ap.add_argument("--output-dir", "-o", default="output", help="Output directory (default: output/)")
    ap.add_argument("--repo-root", default=None, help="Repo root (default: cwd)")
    ap.add_argument("--manifest", default=None, help="Path to docs/books.json")
    ap.add_argument("--no-manifest-check", action="store_true")
    ap.add_argument("--quiet", "-q", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd()
    out = Path(args.output_dir)
    if not out.is_absolute():
        out = repo_root / out
    build(repo_root, out, args.files or None, args.manifest,
          manifest_check=not args.no_manifest_check, quiet=args.quiet)


if __name__ == "__main__":
    main()
