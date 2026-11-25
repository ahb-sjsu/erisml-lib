# How the website is put together

[erisml.org](https://erisml.org) is the `docs/` directory of this repository. The workflow
`.github/workflows/pages.yml` deploys it on every push to `main`. There is no build step: the site is static
HTML with two small scripts that draw the shared navigation.

## Sections

| Section | Where it comes from |
|---|---|
| Home page | `docs/index.html`, with `docs/assets/css/style.css` and the scripts in `docs/assets/js/` |
| The Geometric Series, 14 volumes | git submodules under `docs/` (`docs/book` and `docs/geometric-*`). Each tracks the built `site` branch of its volume's own repository |
| OT textbook, *Data Mining as Observation* | `docs/data-mining-as-observation/`, written by `tools/publish_site.py` of the book's repository |
| Observation Theory Encyclopedia | `docs/encyclopedia/`, written by `encyclopedia/publish_site.py` of `observation-theory-campaigns` |
| Math primer | `docs/guides/math-primer.html` |

## The shared top bar

Every section shows the same bar: the ErisML mark, where you are, the Geometric Series menu, OT Textbook,
OT Encyclopedia, Math Primer, Community.

- **`docs/assets/js/sitebar.js`** draws it. It is self-contained (its styles are inside it) and builds the
  volume menu from `docs/books.json`.
- **A page gets the bar by loading the script**: `<script defer src="../assets/js/sitebar.js"></script>`,
  with the path to the docs root.
- **The volumes need no change.** They already load `../assets/js/series.js`, which loads `sitebar.js`.
- **Where the bar goes.** On a page with `<nav id="main-nav">` (the home page, the volumes) the bar replaces
  that nav's contents, and the nav's in-page links (`href="#..."`) move into an "On this page" menu. On any
  other page the bar is inserted at the top of `<body>`.
- **To add a section to the bar**, add it to `SECTIONS` in `sitebar.js`.

## To add a volume to the series

1. **Publish the volume's site.** In the volume's own repository, build the HTML onto a `site` branch with an
   `index.html` at its root. The page needs:
   - `<body data-book-slug="geometric-your-topic">`, which tells the bar which volume this is;
   - `<nav id="main-nav">…</nav>`, which the bar fills;
   - `<script src="../assets/js/series.js"></script>` before `</body>`.

   Use an existing volume's `site` branch as the template.

2. **Add it here as a submodule** tracking that branch:

   ```bash
   git submodule add -b site https://github.com/ahb-sjsu/geometric-your-topic docs/geometric-your-topic
   ```

   The Pages workflow refuses to deploy if a submodule has no `index.html` at its root, which is what
   happens when the submodule points at the source branch instead of `site`.

3. **Add it to `docs/books.json`**, appending to `volumes`:

   ```json
   {
     "number": 15,
     "slug": "geometric-your-topic",
     "title": "Geometric Your Topic",
     "subtitle": "…",
     "href": "geometric-your-topic/index.html",
     "short": "Your Topic"
   }
   ```

   The `slug` must match the directory name under `docs/`.

4. **Commit and push.** On the next page load the Geometric Series menu of the bar, the card grid of the home
   page (`#series-card-grid`) and the volume count (`#series-volume-count`) all include the new volume.

To update a volume that is already listed, move its submodule to the new commit of the `site` branch and
commit the changed gitlink.

## How the manifest is used

- **Single source of truth:** `docs/books.json`.
- **`sitebar.js`** builds the Geometric Series menu from it and marks the current volume.
- **`series.js`** fills these placeholders when a page has them:
  - `#series-card-grid`: the card grid on the home page
  - `#series-volume-count`: the count in words ("Fourteen")
  - `#book-prev-next`: previous and next volume links on a volume's landing page (opt-in)
- **Path resolution:** both scripts find the docs root from their own `src`, so the same files work from the
  root and from a subfolder.
- **If `books.json` cannot be loaded**, the hand-written HTML inside each placeholder stays, and the bar's
  series item becomes a plain link to the home page's series section.

## Testing locally

```bash
git submodule update --init docs/book   # the volumes' stylesheet, book.css, lives in this submodule
python -m http.server -d docs 8000
```

Then open:

- `http://localhost:8000/`: the home page; check the bar, the card grid and the volume count.
- `http://localhost:8000/geometric-observation/index.html`: a volume; check the bar names the volume and its
  menu lists all volumes. A volume whose submodule is not initialised is an empty directory locally.
- `http://localhost:8000/encyclopedia/index.html` and
  `http://localhost:8000/data-mining-as-observation/index.html`.
- The browser console should show no `[series.js]` warning.

## What the scripts do not do

- They do not touch a volume's chapter pages beyond the top bar. Breadcrumbs and previous/next chapter links
  come from each volume's own build.
- They do not rebuild the textbook or the encyclopedia. Those are republished from their repositories.
