# Adding a New Book to the Series

The series navigation on the GitHub Pages site (`docs/`) is **manifest-driven**
via `docs/books.json` + `docs/assets/js/series.js`. When you add a new volume,
edit one file (`books.json`) and the rest of the site updates itself at load
time — no hand-patching of every other book's top-nav or the main index grid.

## To add Volume N+1

1. **Edit `docs/books.json`.** Append a new entry to `volumes`:

   ```json
   {
     "number": 13,
     "slug": "geometric-your-topic",
     "title": "Geometric Your Topic",
     "subtitle": "…",
     "href": "geometric-your-topic/index.html",
     "short": "Your Topic"
   }
   ```

   The `slug` must match the directory name under `docs/`.
   The `short` string is what appears in the top-nav list.

2. **Create `docs/geometric-your-topic/`** with at minimum an `index.html`.
   Copy from `docs/geometric-politics/index.html` as a template and replace
   the content. Ensure the new page has:

   - `<body data-book-slug="geometric-your-topic">` — used by `series.js` to
     highlight the current book in the nav and drive prev/next.
   - `<ul class="nav-links" id="series-nav-list">` — placeholder the injector
     will overwrite with the live series list.
   - `<script src="../assets/js/series.js"></script>` before `</body>`.

3. **Commit and push.** On the next page load, `series.js` will:

   - Update the main site book grid at `docs/index.html`
     (`<div id="series-card-grid">` container).
   - Update every other book's `#series-nav-list` top-nav.
   - Update the volume-count text (`<span id="series-volume-count">`) from
     "Twelve" to "Thirteen", etc.
   - Highlight the active book via `class="active"` on the matching `<a>`.

## How it works

- **Single source of truth:** `docs/books.json`. Machine-readable manifest of
  the series. Adding a volume = appending one object.
- **Runtime injection:** `docs/assets/js/series.js` fetches the manifest at
  page load and replaces the contents of well-known placeholder elements:
  - `#series-card-grid` — 12-book landing-page card grid
  - `#series-nav-list` — top-nav `<ul>` on each book page
  - `#series-volume-count` — "Twelve" / "Thirteen" etc.
  - `#book-prev-next` — prev/next links on a book page (opt-in)
- **Path resolution:** the script auto-detects whether it was loaded from the
  docs root or a subfolder (by inspecting its own `src`), so `books.json`
  resolves correctly whether you are on `docs/index.html` or
  `docs/geometric-politics/index.html`.
- **Fallback safety:** if `books.json` fails to load (network error, 404),
  whatever hand-coded HTML is inside each placeholder is left untouched. The
  site still works — it just shows the last-known-good state.
- **No build step.** Pure static HTML + one vanilla-JS file. Ships as-is
  through GitHub Pages.

## Testing locally

```bash
cd C:/source/erisml-lib
python -m http.server -d docs 8000
```

Then open:

- `http://localhost:8000/` — main site; verify the book grid and volume
  count update.
- `http://localhost:8000/geometric-politics/index.html` — verify the top-nav
  shows *all* books (including the newest one).
- Browser DevTools console — should be free of `[series.js]` warnings.

If you see a warning like `[series.js] Could not load manifest`, check that
`books.json` is valid JSON and that the path resolves.

## What the script does NOT do

- It does not touch chapter pages. Each chapter's breadcrumb and internal
  top-nav are still hand-maintained. (They rarely go stale; only book-level
  indices do.)
- It does not modify the three non-standard book indices whose top-nav is
  not a series list: `book/` (Ethics — uses a custom nav), `geometric-methods/`
  (links to PyPI/GitHub), and `geometric-communication/` (uses a breadcrumb,
  not a nav-links list). Those pages still include `series.js` for the
  `data-book-slug` attribute / future placeholders, but the injector simply
  no-ops when the placeholder IDs are absent.
