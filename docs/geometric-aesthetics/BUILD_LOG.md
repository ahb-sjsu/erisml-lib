# Geometric Aesthetics — Build Log

**Built:** 2026-04-11
**Source:** `docs/book/src/aesthetics/` (+ `appendices/`)
**Target:** `docs/geometric-aesthetics/`
**Build tool:** pandoc 3.8.3 (via `_build.py`, invoked from the `geometric-aesthetics/` directory)
**Math:** pandoc `--katex`, rendered client-side by KaTeX 0.16.11

## What was built

- `index.html` — book landing page (Book 12 hero, abstract with headline empirical numbers, TOC grouped by Part I–VI + Appendices A–F)
- 30 chapter pages: `chapter-1-introduction-why-geometry.html` through `chapter-30-conclusion-the-geometry-of-beauty.html` (no zero-padding, per Book 3 Ethics naming convention)
- 6 appendix pages: `appendix-a-*` through `appendix-f-*`

Total: **37 HTML files** + `book.css` shared via `../book/book.css` (no duplicate CSS written).

## Source fix-ups applied

- **Chapter 17** source file was at `docs/book/src/chapter-31-geometric-aesthetics.md` with heading `# Chapter 31: Geometric Aesthetics — Beauty, Judgment, and the Content Manifold` and section numbering `31.1`…`31.11`. As part of the build:
  - Moved file to `docs/book/src/aesthetics/chapter-17-empirical-evidence-for-geometric-aesthetics.md`
  - Retitled heading to `# Chapter 17: Empirical Evidence for Geometric Aesthetics {#chapter-17-empirical-evidence-for-geometric-aesthetics}`
  - Renumbered all `## 31.X` → `## 17.X` and `### 31.X.Y` → `### 17.X.Y`

No other chapter sources required manual fix-ups. Title lines across chapters vary between em-dash and colon separators (`Chapter 5 — The Aesthetic Manifold` vs `Chapter 7: One Work — Five Levels`); the build script normalizes to `Chapter N: <rest>` in display but preserves the body heading from pandoc, so chapter bodies retain the author's original punctuation.

## Main site integration

Edits applied to `docs/index.html`:

1. Line 1456: "Ten volumes" → "Twelve volumes" in the series section subtitle.
2. Lines 1531–1535: inserted new Book 12 card after Book 11 (Geometric AI), matching the existing card styling.

## Volume-number cross-refs

Searched all aesthetics markdown for `Volume N` / `Book N` references. The only remaining "Volume 7" self-reference is in `_BOOK_REFERENCE.md` (per instructions, already corrected; not further modified). No chapter body incorrectly cites the aesthetics book as "Volume 7" or similar.

## TODO items carried forward (for author review)

**Citation TODOs (flagged `TODO-cite` in source):** present in `appendix-a-related-work-and-differentiation.md` (7 instances — Spotify/Echonest paper refs, McAuley group review-data work, Jacobsen/Höfel EEG symmetry, Van de Cruys predictive-processing, and a book-rating ML reference) and in `appendix-f-mathematical-ledger-status-of-formal-claims.md` (row F5.3, Riemannian-metric positive-definiteness). These render into the HTML verbatim as `**TODO-cite**` — they will show up as bold text in the published pages until the author completes the citation pass. If it is preferable to suppress them from the public build, we can add a pandoc filter or sed-pass that hides `**TODO-cite**` behind a CSS `.editorial-note` span.

**Non-citation TODO:** `chapter-26-geometric-ai-curation.md` contains a line of narrative that quotes a fictional `# TODO:` code comment inside a character beat (Priya's predecessor). That is intentional prose, not a build artifact — left as-is.

**Figure placeholders:** none present in source. No images are referenced from aesthetics chapters (grep for `![` in src returned no matches in chapter bodies).

## Known cosmetic quirks

- Each chapter body opens with a pandoc-generated `<section class="level1">` wrapping the `<h1>` — same pattern as `geometric-politics/`. The ethics book (`docs/book/`) uses custom classes (`chapter-title`, `section-heading`) instead. We chose the pandoc pattern because it matches the politics template referenced for sub-book pages; visual styling from `../book/book.css` handles both.
- Chapter 17 appendix-E filename is `appendix-e-skeptic-s-appendix-objections-alternatives-failure-modes.html` (apostrophe in "Skeptic's" splits into `skeptic-s`). The task spec allowed any reasonable descriptive slug; this matches the source markdown filename pattern.

## Re-running the build

From a shell with pandoc 3.x on PATH:

```bash
cd C:/source/erisml-lib/docs/geometric-aesthetics
python _build.py
```

The script is idempotent: it overwrites HTML files in place. No intermediate state is kept.
