# Geometric Series build kit

Canonical tooling for the thirteen Geometric Series volumes served at
https://erisml.org/. Each volume repo carries a copy of these files in its
`.build/` directory; **edit here, then run `sync_kit.py`** so the copies never
drift (drift is how the volumes ended up on three different page templates).

| file | purpose |
|---|---|
| `build.py` | Markdown → static HTML in the unified series look. Per-book config in `BOOK_CONFIGS` (number, title, source dirs, optional parts / abstract / extra head+scripts). Validates the book's number and title against `docs/books.json`, the single source of truth for series numbering. |
| `template.html` | Page shell: shared CSS (`../assets/css/style.css`, `../book/book.css`), manifest-driven series nav (`../assets/js/series.js`), breadcrumb, prev/next, KaTeX auto-render. |
| `series_check.py` | Mechanical proofreading and machine checks (encoding, structure, math balance, KaTeX parse of every formula, dangling cross-references, prose candidates, codespell, optional code-block execution and link checks, built-site link check). Writes `.build/reports/series_check.{md,json}`. Exit 1 on hard defects. |
| `katex_check.js` | Node helper used by `series_check.py` (needs `npm i katex@0.16.11` here). |
| `publish_site.py` | Build (or `--source-dir` for the docx-built Ethics volume) and commit the result to the repo's `site` branch, which the portal consumes as a submodule. `--keep <path>` carries static assets along. |
| `sync_kit.py` | Copy the kit into `../geometric-*/.build/` (`--check` for CI). |
| `bump_submodules.py` | Re-pin every `docs/<volume>` gitlink in erisml-lib to its `site` tip, refusing tips without a root `index.html`. |

## Publishing a volume end to end

```bash
cd ../geometric-law
python .build/series_check.py                       # fix hard defects first
python .build/publish_site.py -m "site: ..." --push # build + push site branch
cd ../erisml-lib
python tools/series-build/bump_submodules.py --commit && git push
```

The Pages workflow (`.github/workflows/pages.yml`) refuses to deploy if any
volume directory lacks `index.html`, so a wrong pin fails CI instead of
shipping 404s.

## Volumes with their own pipeline

`geometric-ethics` is built from a `.docx` by its own `.build/build_ethics.py`
(pandoc). It uses the same `template.html` look but not `build.py`; publish it
with `python .build/publish_site.py --source-dir . --keep images --keep book.css --push`.
