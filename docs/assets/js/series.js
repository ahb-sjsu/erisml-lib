/*
 * series.js — manifest-driven series navigation injector
 *
 * Single source of truth: /books.json (at the docs/ root).
 * This script finds well-known placeholder IDs on the current page and
 * fills them with fresh content derived from the manifest, so that
 * adding a new volume requires editing ONLY books.json.
 *
 * Placeholders handled:
 *   #series-card-grid   → 13-book card grid (used on main site index)
 *   #series-nav-list    → <ul> of short-name series links (top-nav submenu)
 *   #series-volume-count → auto-updated text "Thirteen volumes" etc.
 *   #book-prev-next     → prev/next book links for a book landing page
 *
 * Current-book highlighting: set <body data-book-slug="..."> on book pages.
 *
 * Fallback safety: if the fetch or parse fails, the existing hand-coded
 * HTML inside each placeholder is left untouched.
 *
 * No build step. Vanilla ES2017+. Include via:
 *   <script src="assets/js/series.js"></script>   (main site)
 *   <script src="../assets/js/series.js"></script> (book subfolder)
 */
(function () {
  'use strict';

  // --- Resolve the path to books.json and the path prefix to apply to
  //     each volume.href. We want this to work whether we are at the
  //     docs root (index.html) or one subfolder deep (book/index.html).
  //     Approach: look at where THIS script tag was loaded from. Its src
  //     is something like "assets/js/series.js" or "../assets/js/series.js".
  //     The directory that contains "assets/" is the docs root.
  function computeBasePrefix() {
    const scripts = document.getElementsByTagName('script');
    for (const s of scripts) {
      const src = s.getAttribute('src') || '';
      const m = src.match(/^(.*?)assets\/js\/series\.js(?:\?.*)?$/);
      if (m) return m[1]; // "", "../", "../../", etc.
    }
    return ''; // assume root
  }
  const BASE = computeBasePrefix();
  const MANIFEST_URL = BASE + 'books.json';

  // --- English word-form for small counts (≤ 20), numeric otherwise. ---
  const WORDS = ['Zero','One','Two','Three','Four','Five','Six','Seven','Eight',
                 'Nine','Ten','Eleven','Twelve','Thirteen','Fourteen','Fifteen',
                 'Sixteen','Seventeen','Eighteen','Nineteen','Twenty'];
  function countWord(n) {
    return (n >= 0 && n <= 20) ? WORDS[n] : String(n);
  }

  // --- DOM helpers ---
  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      if (k === 'style') node.setAttribute('style', attrs[k]);
      else if (k === 'class') node.className = attrs[k];
      else node.setAttribute(k, attrs[k]);
    }
    if (children) for (const c of [].concat(children)) {
      node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return node;
  }

  // --- Renderers ------------------------------------------------------

  function renderCardGrid(container, volumes, currentSlug) {
    // Reuse the same inline styles as the hand-coded fallback so visual
    // output is identical. Cards are simple <a> blocks.
    const cardStyle = "background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 20px 24px; text-decoration: none; transition: all 0.25s; display: block;";
    const numStyle  = "font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 6px;";
    const titleStyle= "font-family: 'Crimson Pro', serif; font-size: 1.15rem; font-weight: 600; color: var(--accent-light); margin-bottom: 4px;";
    const subStyle  = "font-family: 'Crimson Pro', serif; font-size: 0.9rem; color: var(--text-secondary); font-style: italic;";

    const frag = document.createDocumentFragment();
    for (const v of volumes) {
      const a = el('a', {
        href: BASE + v.href,
        style: cardStyle,
        'data-book-slug': v.slug,
      }, [
        el('div', { style: numStyle }, 'Book ' + v.number),
        el('div', { style: titleStyle }, v.title),
        el('div', { style: subStyle }, v.subtitle),
      ]);
      if (v.slug === currentSlug) a.classList.add('current');
      frag.appendChild(a);
    }
    container.innerHTML = '';
    container.appendChild(frag);
  }

  function renderNavList(container, volumes, currentSlug) {
    // container is expected to be a <ul>. We rebuild its <li> children.
    // Preserve any trailing "Home" link if the original markup had one
    // pointing to ../index.html or index.html (heuristic).
    const frag = document.createDocumentFragment();
    for (const v of volumes) {
      const a = el('a', { href: BASE + v.href }, v.short);
      if (v.slug === currentSlug) a.className = 'active';
      frag.appendChild(el('li', null, a));
    }
    // Append a Home link pointing back to the docs root.
    const home = el('a', { href: BASE + 'index.html' }, 'Home');
    frag.appendChild(el('li', null, home));

    container.innerHTML = '';
    container.appendChild(frag);
  }

  function renderVolumeCount(container, n) {
    container.textContent = countWord(n);
  }

  function renderPrevNext(container, volumes, currentSlug) {
    const idx = volumes.findIndex(v => v.slug === currentSlug);
    if (idx < 0) return;
    const prev = idx > 0 ? volumes[idx - 1] : null;
    const next = idx < volumes.length - 1 ? volumes[idx + 1] : null;
    container.innerHTML = '';
    if (prev) container.appendChild(el('a', { href: BASE + prev.href, class: 'prev' }, '← Book ' + prev.number + ': ' + prev.title));
    if (next) container.appendChild(el('a', { href: BASE + next.href, class: 'next' }, 'Book ' + next.number + ': ' + next.title + ' →'));
  }

  // --- Main injection driver ----------------------------------------

  async function inject() {
    let manifest;
    try {
      const res = await fetch(MANIFEST_URL, { cache: 'no-cache' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      manifest = await res.json();
    } catch (err) {
      // Fail silent: hand-coded fallback remains on the page.
      console.warn('[series.js] Could not load manifest; keeping hand-coded fallback.', err);
      return;
    }
    const volumes = manifest.volumes || [];
    const currentSlug = document.body.getAttribute('data-book-slug') || null;

    const grid = document.getElementById('series-card-grid');
    if (grid) renderCardGrid(grid, volumes, currentSlug);

    const navList = document.getElementById('series-nav-list');
    if (navList) renderNavList(navList, volumes, currentSlug);

    const count = document.getElementById('series-volume-count');
    if (count) renderVolumeCount(count, volumes.length);

    const prevNext = document.getElementById('book-prev-next');
    if (prevNext) renderPrevNext(prevNext, volumes, currentSlug);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
