#!/usr/bin/env python3
"""
Build pipeline for Geometric Series book chapters.

Converts Markdown chapters to HTML using Pandoc with KaTeX math rendering.
Replaces the previous regex-based approach that broke on:
  - * in math (A*, gamma*) conflicting with markdown italic
  - _ in subscripts conflicting with markdown bold/italic
  - Display math blocks
  - Nested formatting

Pandoc handles math delimiters natively, producing clean <span class="math inline">
and <span class="math display"> elements that KaTeX renders client-side.

Usage:
    python build_books.py                  # Build all books
    python build_books.py --book medicine  # Build one book
    python build_books.py --test           # Test on medicine ch13 only
    python build_books.py --dry-run        # Show what would be built
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ── Configuration ──────────────────────────────────────────────────────────

ERISML_ROOT = Path(__file__).parent.resolve()
DOCS_DIR = ERISML_ROOT / "docs"
TEMPLATE = ERISML_ROOT / "templates" / "chapter.html"

AUTHOR = "Andrew H. Bond"


@dataclass
class ChapterSource:
    """A single markdown chapter source file."""

    md_path: Path
    chapter_num: int  # 0 for front matter


@dataclass
class BookConfig:
    """Configuration for one book in the series."""

    key: str  # e.g. "medicine"
    dir_name: str  # e.g. "geometric-medicine" (output dir in docs/)
    title: str  # e.g. "Geometric Medicine"
    subtitle: str  # e.g. "Clinical Reasoning, Triage, and the Ethics of Allocation"
    source_repo: Path  # root of source repo
    chapter_sources: list  # list of (part_dir_or_chapters_dir, pattern) tuples
    nav_key: str  # e.g. "nav-medicine" — for active nav highlighting
    book_number: int  # e.g. 8

    def get_output_dir(self) -> Path:
        return DOCS_DIR / self.dir_name


def get_book_configs() -> dict[str, BookConfig]:
    """Define all six books and their chapter source locations."""
    source = Path("C:/source")

    return {
        "reasoning": BookConfig(
            key="reasoning",
            dir_name="geometric-reasoning",
            title="Geometric Reasoning",
            subtitle="From Search to Manifolds",
            source_repo=source / "geometric-reasoning",
            chapter_sources=[("chapters", "ch*.md")],
            nav_key="nav-reasoning",
            book_number=2,
        ),
        "economics": BookConfig(
            key="economics",
            dir_name="geometric-economics",
            title="Geometric Economics",
            subtitle="Decision Manifolds, Equilibria, and the Geometry of Markets",
            source_repo=source / "geometric-economics",
            chapter_sources=[("chapters", "ch*.md")],
            nav_key="nav-economics",
            book_number=4,
        ),
        "law": BookConfig(
            key="law",
            dir_name="geometric-law",
            title="Geometric Law",
            subtitle="Symmetry, Invariance, and the Structure of Legal Reasoning",
            source_repo=source / "geometric-law",
            chapter_sources=[("chapters", "ch*.md")],
            nav_key="nav-law",
            book_number=5,
        ),
        "cognition": BookConfig(
            key="cognition",
            dir_name="geometric-cognition",
            title="Geometric Cognition",
            subtitle="The Mathematical Structure of Human and Artificial Thought",
            source_repo=source / "geometric-cognition",
            chapter_sources=[("chapters", "ch*.md")],
            nav_key="nav-cognition",
            book_number=6,
        ),
        "communication": BookConfig(
            key="communication",
            dir_name="geometric-communication",
            title="Geometric Communication",
            subtitle="Language, Signal, and the Topology of Meaning",
            source_repo=source / "geometric-communication",
            chapter_sources=[
                ("manuscript/part_i", "ch*.md"),
                ("manuscript/part_ii", "ch*.md"),
                ("manuscript/part_iii", "ch*.md"),
                ("manuscript/part_iv", "ch*.md"),
                ("manuscript/part_v", "ch*.md"),
                ("manuscript/part_vi", "ch*.md"),
                ("manuscript/part_vii", "ch*.md"),
            ],
            nav_key="nav-communication",
            book_number=7,
        ),
        "medicine": BookConfig(
            key="medicine",
            dir_name="geometric-medicine",
            title="Geometric Medicine",
            subtitle="Clinical Reasoning, Triage, and the Ethics of Allocation",
            source_repo=source / "geometric-medicine",
            chapter_sources=[
                ("manuscript/part_i", "ch*.md"),
                ("manuscript/part_ii", "ch*.md"),
                ("manuscript/part_iii", "ch*.md"),
                ("manuscript/part_iv", "ch*.md"),
                ("manuscript/part_v", "ch*.md"),
                ("manuscript/part_vi", "ch*.md"),
            ],
            nav_key="nav-medicine",
            book_number=8,
        ),
        "education": BookConfig(
            key="education",
            dir_name="geometric-education",
            title="Geometric Education",
            subtitle="Learning, Assessment, and the Topology of Human Development",
            source_repo=source / "geometric-education",
            chapter_sources=[
                ("manuscript/part_i", "ch*.md"),
                ("manuscript/part_ii", "ch*.md"),
                ("manuscript/part_iii", "ch*.md"),
                ("manuscript/part_iv", "ch*.md"),
                ("manuscript/part_v", "ch*.md"),
            ],
            nav_key="nav-education",
            book_number=9,
        ),
        "politics": BookConfig(
            key="politics",
            dir_name="geometric-politics",
            title="Geometric Politics",
            subtitle="Representation, Polarization, and the Topology of Democratic Choice",
            source_repo=source / "geometric-politics",
            chapter_sources=[
                ("manuscript/part_i", "ch*.md"),
                ("manuscript/part_ii", "ch*.md"),
                ("manuscript/part_iii", "ch*.md"),
                ("manuscript/part_iv", "ch*.md"),
                ("manuscript/part_v", "ch*.md"),
            ],
            nav_key="nav-politics",
            book_number=10,
        ),
        "ai": BookConfig(
            key="ai",
            dir_name="geometric-ai",
            title="Geometric AI",
            subtitle="Alignment, Safety, and the Structure-Preserving Path to Superintelligence",
            source_repo=source / "geometric-ai",
            chapter_sources=[
                ("manuscript/part_i", "ch*.md"),
                ("manuscript/part_ii", "ch*.md"),
                ("manuscript/part_iii", "ch*.md"),
                ("manuscript/part_iv", "ch*.md"),
                ("manuscript/part_v", "ch*.md"),
                ("manuscript/part_vi", "ch*.md"),
            ],
            nav_key="nav-ai",
            book_number=11,
        ),
    }


# ── Chapter Discovery ──────────────────────────────────────────────────────


def discover_chapters(book: BookConfig) -> list[ChapterSource]:
    """Find all chapter markdown files for a book, sorted by chapter number."""
    chapters = []

    for subdir, pattern in book.chapter_sources:
        search_dir = book.source_repo / subdir
        if not search_dir.exists():
            print(f"  WARNING: Source directory not found: {search_dir}")
            continue

        for md_file in sorted(search_dir.glob(pattern)):
            # Extract chapter number from filename like ch01_xxx.md or ch00_front_matter.md
            match = re.match(r"ch(\d+)", md_file.name)
            if match:
                ch_num = int(match.group(1))
                chapters.append(ChapterSource(md_path=md_file, chapter_num=ch_num))

    # Also check for manuscript/front_matter.md at repo root
    front_matter = book.source_repo / "manuscript" / "front_matter.md"
    if front_matter.exists() and not any(c.chapter_num == 0 for c in chapters):
        # Only add if we don't already have a ch00 from chapters/
        pass  # front matter is usually ch00

    # Sort by chapter number
    chapters.sort(key=lambda c: c.chapter_num)
    return chapters


def extract_title_from_md(md_path: Path) -> str:
    """Extract the chapter title from the first # heading in the markdown."""
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
    # Fallback: derive from filename
    stem = md_path.stem
    # ch01_reasoning_as_search -> Reasoning as Search
    parts = stem.split("_")
    if parts[0].startswith("ch"):
        parts = parts[1:]
    return " ".join(p.capitalize() for p in parts)


def slugify(title: str) -> str:
    """Convert a chapter title to a URL-friendly slug."""
    # Remove LaTeX math
    slug = re.sub(r"\$[^$]+\$", "", title)
    slug = slug.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug


def make_output_filename(chapter: ChapterSource, title: str) -> str:
    """Generate the output HTML filename for a chapter."""
    if chapter.chapter_num == 0:
        return "front-matter.html"
    # Strip "Chapter N:" prefix before slugifying to avoid double numbering
    clean_title = re.sub(r"^Chapter\s+\d+\s*:\s*", "", title)
    slug = slugify(clean_title)
    return f"chapter-{chapter.chapter_num}-{slug}.html"


# ── Pandoc Conversion ─────────────────────────────────────────────────────


def check_pandoc() -> bool:
    """Check if Pandoc is installed and return True if available."""
    try:
        result = subprocess.run(
            ["pandoc", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            print(f"Found {version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print("ERROR: Pandoc is not installed.")
    print("Install it from: https://pandoc.org/installing.html")
    print("  Windows: winget install --id JohnMacFarlane.Pandoc")
    print("  macOS:   brew install pandoc")
    print("  Ubuntu:  sudo apt install pandoc")
    return False


def convert_chapter_pandoc(
    md_path: Path,
    output_path: Path,
    book: BookConfig,
    title: str,
    prev_url: Optional[str],
    prev_title: Optional[str],
    next_url: Optional[str],
    next_title: Optional[str],
    dry_run: bool = False,
) -> bool:
    """Convert a single markdown chapter to HTML using Pandoc."""
    if dry_run:
        print(f"  [dry-run] Would convert: {md_path.name} -> {output_path.name}")
        return True

    # Build Pandoc metadata as YAML
    metadata = {
        "title": title,
        "book-title": book.title,
        "book-subtitle": book.subtitle,
        "author": AUTHOR,
        book.nav_key: True,
    }
    if prev_url:
        metadata["prev-url"] = prev_url
        metadata["prev-title"] = prev_title
    if next_url:
        metadata["next-url"] = next_url
        metadata["next-title"] = next_title

    # Build pandoc command
    cmd = [
        "pandoc",
        str(md_path),
        "--from",
        "markdown+tex_math_dollars+tex_math_single_backslash",
        "--to",
        "html5",
        "--katex",
        "--template",
        str(TEMPLATE),
        "--output",
        str(output_path),
        "--wrap=none",
        "--section-divs",
    ]

    # Add metadata via -V flags
    for key, value in metadata.items():
        if isinstance(value, bool):
            if value:
                cmd.extend(["-V", f"{key}=true"])
        else:
            cmd.extend(["-V", f"{key}={value}"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(md_path.parent),  # so relative image paths work
        )
        if result.returncode != 0:
            print(f"  ERROR converting {md_path.name}:")
            print(f"    {result.stderr.strip()}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  ERROR: Pandoc timed out on {md_path.name}")
        return False


# ── Post-processing ───────────────────────────────────────────────────────


def get_existing_output_filename(book: BookConfig, chapter_num: int) -> Optional[str]:
    """Look up the existing HTML filename for a chapter in the current docs.

    This preserves backward compatibility with existing URLs/links in the
    index.html files that were hand-crafted. Checks both the index.html
    links and actual files on disk, handling both zero-padded (chapter-01)
    and non-padded (chapter-1) numbering.
    """
    output_dir = book.get_output_dir()

    if chapter_num == 0:
        if (output_dir / "front-matter.html").exists():
            return "front-matter.html"
        return None

    # First try: check index.html for links (most authoritative)
    index_path = output_dir / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Match both chapter-1- and chapter-01- patterns
        for num_str in [str(chapter_num), f"{chapter_num:02d}"]:
            pattern = rf'href="(chapter-{num_str}-[^"]+\.html)"'
            match = re.search(pattern, content)
            if match:
                return match.group(1)

    # Second try: check actual files on disk
    if output_dir.exists():
        for num_str in [str(chapter_num), f"{chapter_num:02d}"]:
            matches = list(output_dir.glob(f"chapter-{num_str}-*.html"))
            if matches:
                return matches[0].name

    return None


def build_chapter_list(
    book: BookConfig,
    chapters: list[ChapterSource],
) -> list[dict]:
    """Build the ordered list of chapters with titles and filenames."""
    chapter_list = []

    for ch in chapters:
        title = extract_title_from_md(ch.md_path)

        # Try to use existing filename for URL compatibility
        existing = get_existing_output_filename(book, ch.chapter_num)
        if existing:
            filename = existing
        else:
            filename = make_output_filename(ch, title)

        chapter_list.append(
            {
                "source": ch,
                "title": title,
                "filename": filename,
            }
        )

    return chapter_list


# ── Main Build Logic ──────────────────────────────────────────────────────


def build_book(book: BookConfig, dry_run: bool = False) -> tuple[int, int]:
    """Build all chapters for one book. Returns (success_count, fail_count)."""
    print(f"\n{'='*60}")
    print(f"Building: {book.title}")
    print(f"  Source: {book.source_repo}")
    print(f"  Output: {book.get_output_dir()}")
    print(f"{'='*60}")

    # Discover chapters
    chapters = discover_chapters(book)
    if not chapters:
        print("  No chapters found!")
        return 0, 0

    print(f"  Found {len(chapters)} chapters")

    # Build chapter list with titles and filenames
    chapter_list = build_chapter_list(book, chapters)

    # Ensure output directory exists
    output_dir = book.get_output_dir()
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    fail = 0

    for i, ch_info in enumerate(chapter_list):
        title = ch_info["title"]
        filename = ch_info["filename"]
        output_path = output_dir / filename

        # Determine prev/next
        prev_url = chapter_list[i - 1]["filename"] if i > 0 else None
        prev_title = chapter_list[i - 1]["title"] if i > 0 else None
        next_url = (
            chapter_list[i + 1]["filename"] if i < len(chapter_list) - 1 else None
        )
        next_title = chapter_list[i + 1]["title"] if i < len(chapter_list) - 1 else None

        ok = convert_chapter_pandoc(
            md_path=ch_info["source"].md_path,
            output_path=output_path,
            book=book,
            title=title,
            prev_url=prev_url,
            prev_title=prev_title,
            next_url=next_url,
            next_title=next_title,
            dry_run=dry_run,
        )

        if ok:
            success += 1
            status = "[ok]" if not dry_run else "[dry-run]"
        else:
            fail += 1
            status = "[FAIL]"

        print(f"  {status} Ch.{ch_info['source'].chapter_num:02d}: {title[:50]}...")

    return success, fail


def build_single_chapter(
    book: BookConfig,
    chapter_num: int,
    dry_run: bool = False,
) -> bool:
    """Build a single chapter from a book. Used for testing."""
    chapters = discover_chapters(book)
    chapter_list = build_chapter_list(book, chapters)

    target = None
    target_idx = None
    for i, ch_info in enumerate(chapter_list):
        if ch_info["source"].chapter_num == chapter_num:
            target = ch_info
            target_idx = i
            break

    if target is None:
        print(f"  Chapter {chapter_num} not found in {book.title}")
        return False

    output_dir = book.get_output_dir()
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    prev_url = chapter_list[target_idx - 1]["filename"] if target_idx > 0 else None
    prev_title = chapter_list[target_idx - 1]["title"] if target_idx > 0 else None
    next_url = (
        chapter_list[target_idx + 1]["filename"]
        if target_idx < len(chapter_list) - 1
        else None
    )
    next_title = (
        chapter_list[target_idx + 1]["title"]
        if target_idx < len(chapter_list) - 1
        else None
    )

    output_path = output_dir / target["filename"]

    print(f"\nBuilding: {target['title']}")
    print(f"  Source: {target['source'].md_path}")
    print(f"  Output: {output_path}")

    ok = convert_chapter_pandoc(
        md_path=target["source"].md_path,
        output_path=output_path,
        book=book,
        title=target["title"],
        prev_url=prev_url,
        prev_title=prev_title,
        next_url=next_url,
        next_title=next_title,
        dry_run=dry_run,
    )

    return ok


def validate_output(html_path: Path) -> dict:
    """Validate an HTML output file for common rendering issues."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    issues = []

    # Check for unclosed <em> tags (the old bug)
    em_opens = len(re.findall(r"<em\b", content))
    em_closes = len(re.findall(r"</em>", content))
    if em_opens != em_closes:
        issues.append(f"Unclosed <em> tags: {em_opens} opens vs {em_closes} closes")

    # Check for the old triple-render pattern: <em class="math">
    old_math_em = len(re.findall(r'<em class="math">', content))
    if old_math_em > 0:
        issues.append(f"Old-style <em class='math'> tags found: {old_math_em}")

    # Check for proper Pandoc math spans
    math_inline = len(re.findall(r'<span class="math inline">', content))
    math_display = len(re.findall(r'<span class="math display">', content))

    # Check for unrendered dollar signs that suggest math wasn't processed
    # (exclude those inside <span class="math"> elements, and currency like $200,000)
    stripped = re.sub(
        r'<span class="math[^"]*">.*?</span>', "", content, flags=re.DOTALL
    )
    # Match $...$ but exclude currency amounts ($123, $4.2B, $200K, etc.)
    stray_dollar_matches = re.findall(r"(?<![\\])\$[^$]+\$", stripped)
    stray_dollars = sum(
        1
        for m in stray_dollar_matches
        if not re.match(r"^\$[\d,.]+[KMBkmb]?\$?", m)  # not currency
    )

    # Check for KaTeX CSS/JS references
    has_katex_css = "katex.min.css" in content
    has_katex_js = "katex.min.js" in content

    return {
        "path": str(html_path),
        "file_size": html_path.stat().st_size,
        "math_inline_spans": math_inline,
        "math_display_spans": math_display,
        "unclosed_em_tags": em_opens != em_closes,
        "old_math_em_tags": old_math_em,
        "stray_dollar_math": stray_dollars,
        "has_katex_css": has_katex_css,
        "has_katex_js": has_katex_js,
        "issues": issues,
    }


# ── CLI ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Build Geometric Series book chapters from Markdown to HTML via Pandoc."
    )
    parser.add_argument(
        "--book",
        choices=[
            "reasoning",
            "economics",
            "law",
            "cognition",
            "communication",
            "medicine",
            "education",
            "politics",
            "ai",
            "all",
        ],
        default="all",
        help="Which book to build (default: all)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: build only Medicine chapter 13 and validate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be built without actually converting",
    )
    parser.add_argument(
        "--validate",
        type=str,
        help="Validate an existing HTML file (path)",
    )
    parser.add_argument(
        "--chapter",
        type=int,
        help="Build only this chapter number (requires --book)",
    )

    args = parser.parse_args()

    # Validate mode
    if args.validate:
        path = Path(args.validate)
        if not path.exists():
            print(f"File not found: {path}")
            sys.exit(1)
        result = validate_output(path)
        print(json.dumps(result, indent=2))
        sys.exit(0 if not result["issues"] else 1)

    # Check Pandoc
    if not check_pandoc():
        sys.exit(1)

    # Check template
    if not TEMPLATE.exists():
        print(f"ERROR: Template not found: {TEMPLATE}")
        sys.exit(1)

    configs = get_book_configs()

    # Test mode: medicine ch13
    if args.test:
        print("\n--- TEST MODE: Medicine Chapter 13 ---")
        book = configs["medicine"]
        ok = build_single_chapter(book, chapter_num=13, dry_run=args.dry_run)

        if ok and not args.dry_run:
            # Validate
            output_dir = book.get_output_dir()
            ch13_file = get_existing_output_filename(book, 13)
            if ch13_file:
                output_path = output_dir / ch13_file
            else:
                output_path = (
                    output_dir
                    / "chapter-13-the-mathematical-theory-of-moral-injury.html"
                )

            if output_path.exists():
                print("\n--- Validation ---")
                result = validate_output(output_path)
                print(f"  File size: {result['file_size']:,} bytes")
                print(f"  Math inline spans: {result['math_inline_spans']}")
                print(f"  Math display spans: {result['math_display_spans']}")
                print(f"  KaTeX CSS: {'yes' if result['has_katex_css'] else 'NO'}")
                print(f"  KaTeX JS: {'yes' if result['has_katex_js'] else 'NO'}")
                print(f"  Old <em class='math'> tags: {result['old_math_em_tags']}")
                print(
                    f"  Unclosed <em> tags: {'YES - BUG!' if result['unclosed_em_tags'] else 'none'}"
                )
                print(f"  Stray $ math: {result['stray_dollar_math']}")
                if result["issues"]:
                    print("\n  ISSUES:")
                    for issue in result["issues"]:
                        print(f"    - {issue}")
                else:
                    print("\n  All checks passed.")
            else:
                print(f"  Output file not found for validation: {output_path}")

        sys.exit(0 if ok else 1)

    # Single chapter mode
    if args.chapter is not None:
        if args.book == "all":
            print("ERROR: --chapter requires --book to specify which book")
            sys.exit(1)
        book = configs[args.book]
        ok = build_single_chapter(book, chapter_num=args.chapter, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    # Build books
    if args.book == "all":
        books_to_build = list(configs.values())
    else:
        books_to_build = [configs[args.book]]

    total_success = 0
    total_fail = 0

    for book in books_to_build:
        s, f = build_book(book, dry_run=args.dry_run)
        total_success += s
        total_fail += f

    print(f"\n{'='*60}")
    print(f"DONE: {total_success} chapters built, {total_fail} failures")
    if total_fail > 0:
        print("Review errors above.")
        sys.exit(1)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
