/*
 * sitebar.js: the one top bar of erisml.org, the same on every section.
 *
 * The site has sections built by different generators: the home page, the fourteen
 * volumes of the Geometric Series (each its own repository, sharing ../assets), the
 * Observation Theory Encyclopedia, the textbook Data Mining as Observation, and a few
 * single pages. Each used to carry its own top navigation. This script draws the same
 * bar on all of them:
 *
 *   [apple] ErisML / <where you are>     Geometric Series v   Textbook   Encyclopedia
 *                                        Math Primer   Community   [On this page v]
 *
 * A section keeps its own local navigation (a volume's breadcrumb and chapter links,
 * the encyclopedia's views, the textbook's chapter row) below the bar.
 *
 * Use: one tag anywhere in the page, with the path to the docs root:
 *   <script defer src="../assets/js/sitebar.js"></script>
 * Pages of the Geometric Series load series.js, which loads this file.
 *
 * Where the bar goes:
 *   - a page with <nav id="main-nav"> (home page, the volumes): the bar replaces that
 *     nav's contents, so the page's fixed-header offsets stay as they are. In-page links
 *     found in the old nav (href="#...") move into an "On this page" menu.
 *   - any other page: the bar is inserted at the top of <body>, sticky.
 *
 * The volume list comes from books.json at the docs root. If it cannot be loaded, the
 * Geometric Series item is a plain link to the home page's series section.
 * No build step, no dependencies.
 */
(function () {
  'use strict';
  if (window.__erismlSitebar) return;
  window.__erismlSitebar = true;

  // ---- where is the docs root, relative to this page?
  function basePrefix() {
    var scripts = document.getElementsByTagName('script');
    for (var i = 0; i < scripts.length; i++) {
      var src = scripts[i].getAttribute('src') || '';
      var m = src.match(/^(.*?)assets\/js\/(?:sitebar|series)\.js(?:\?.*)?$/);
      if (m) return m[1];
    }
    return '';
  }
  var BASE = basePrefix();

  var SECTIONS = [
    { id: 'textbook', label: 'Textbook', title: 'Data Mining as Observation', dir: 'data-mining-as-observation', href: 'data-mining-as-observation/index.html' },
    { id: 'encyclopedia', label: 'Encyclopedia', title: 'Observation Theory Encyclopedia', dir: 'encyclopedia', href: 'encyclopedia/index.html' },
    { id: 'primer', label: 'Math Primer', title: 'Math Primer', dir: 'guides', href: 'guides/math-primer.html' }
  ];

  var APPLE =
    '<svg class="esb-mark" viewBox="30 36 140 140" aria-hidden="true">' +
    '<circle cx="100" cy="115" r="58" fill="#f5c147"/>' +
    '<ellipse cx="84" cy="95" rx="14" ry="20" fill="#ffe8a8" opacity="0.5"/>' +
    '<path d="M 96 60 Q 100 46 112 50" fill="none" stroke="#6b3a00" stroke-width="3.5" stroke-linecap="round"/>' +
    '<path d="M 114 50 Q 135 42 140 62 Q 124 67 114 50 Z" fill="#4ade80"/>' +
    '</svg>';

  var CSS = [
    '.esb{font-family:Inter,"Segoe UI",Helvetica,Arial,sans-serif;font-size:14px;line-height:1.2;color:#c9d5e0;',
    'background:rgba(11,22,34,.96);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);',
    'border-bottom:1px solid rgba(102,194,165,.22);position:sticky;top:0;z-index:1000;text-align:left}',
    '.esb *{box-sizing:border-box}',
    '.esb-in{max-width:1200px;margin:0 auto;padding:0 clamp(14px,3vw,32px);height:60px;display:flex;align-items:center;gap:14px}',
    '.esb a{color:inherit;text-decoration:none}',
    '.esb-brand{display:flex;align-items:center;gap:9px;font-weight:650;font-size:16px;letter-spacing:.01em;color:#fff!important;flex:none}',
    '.esb-mark{width:26px;height:26px;display:block}',
    '.esb-here{display:flex;align-items:center;gap:12px;min-width:0;flex:0 1 auto;color:#8fd3bb!important;font-weight:500;',
    'white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.esb-here::before{content:"";flex:none;width:1px;height:20px;background:rgba(201,213,224,.28)}',
    '.esb-here small{font-size:12px;color:#7f97ab;font-weight:500;margin-right:-4px}',
    '.esb-nav{margin-left:auto;display:flex;align-items:center;gap:2px;flex:none}',
    '.esb-nav>a,.esb-nav>.esb-item>button{display:flex;align-items:center;gap:6px;height:36px;padding:0 11px;border-radius:8px;',
    'font:inherit;font-weight:500;color:#c9d5e0;background:none;border:0;cursor:pointer;white-space:nowrap}',
    '.esb-nav>a:hover,.esb-nav>.esb-item>button:hover,.esb-item.open>button{background:rgba(102,194,165,.13);color:#fff}',
    '.esb-nav>a.esb-cur,.esb-item.esb-cur>button{color:#8fd3bb}',
    '.esb-nav>a:focus-visible,.esb-nav button:focus-visible,.esb-menu a:focus-visible,.esb-brand:focus-visible{outline:2px solid #66c2a5;outline-offset:2px}',
    '.esb-caret{width:9px;height:9px;flex:none;transition:transform .15s}',
    '.esb-item.open .esb-caret{transform:rotate(180deg)}',
    '.esb-item{position:relative}',
    '.esb-menu{display:none;position:absolute;right:0;top:44px;background:#0f1f2e;border:1px solid rgba(102,194,165,.25);',
    'border-radius:12px;padding:8px;box-shadow:0 18px 40px rgba(0,0,0,.45);max-height:calc(100vh - 80px);overflow:auto}',
    '.esb-item.open>.esb-menu{display:grid}',
    '.esb-menu.esb-vols{grid-template-columns:1fr 1fr;width:min(560px,92vw);gap:2px 6px}',
    '.esb-menu.esb-page{grid-template-columns:1fr;min-width:210px}',
    '.esb-menu a{display:flex;align-items:baseline;gap:10px;padding:8px 10px;border-radius:8px;color:#c9d5e0;white-space:nowrap}',
    '.esb-menu a:hover{background:rgba(102,194,165,.13);color:#fff}',
    '.esb-menu a.esb-cur{color:#8fd3bb;background:rgba(102,194,165,.09)}',
    '.esb-menu .esb-n{font:500 11px ui-monospace,"JetBrains Mono",Consolas,monospace;color:#6f879b;width:1.6em;text-align:right;flex:none}',
    '.esb-menu .esb-all{grid-column:1/-1;border-top:1px solid rgba(102,194,165,.18);border-radius:0 0 8px 8px;margin-top:4px;color:#8fa4b8;font-size:13px}',
    '.esb-burger{display:none;margin-left:auto;width:40px;height:40px;border-radius:8px;border:0;background:none;cursor:pointer;',
    'align-items:center;justify-content:center;flex:none}',
    '.esb-burger:hover{background:rgba(102,194,165,.13)}',
    '.esb-burger span,.esb-burger span::before,.esb-burger span::after{display:block;width:20px;height:2px;background:#c9d5e0;border-radius:2px;content:"";position:relative}',
    '.esb-burger span::before{position:absolute;top:-6px}.esb-burger span::after{position:absolute;top:6px}',
    '@media (max-width:1020px){',
    '.esb-burger{display:flex}',
    '.esb-nav{display:none;position:absolute;left:0;right:0;top:60px;margin:0;flex-direction:column;align-items:stretch;gap:2px;',
    'background:#0b1622;border-bottom:1px solid rgba(102,194,165,.25);padding:10px clamp(14px,3vw,32px) 16px;max-height:calc(100vh - 60px);overflow:auto}',
    '.esb.esb-open .esb-nav{display:flex}',
    '.esb-nav>a,.esb-nav>.esb-item>button{width:100%;height:42px;justify-content:space-between}',
    '.esb-menu{position:static;box-shadow:none;border:0;background:none;padding:0 0 6px 8px;max-height:none}',
    '.esb-menu.esb-vols{width:auto}',
    '}',
    '@media (max-width:560px){.esb-menu.esb-vols{grid-template-columns:1fr}.esb-here small{display:none}}',
    /* a page whose own fixed nav now holds the bar */
    '#main-nav.esb-host{background:none;-webkit-backdrop-filter:none;backdrop-filter:none;border-bottom:0}',
    '#main-nav.esb-host .esb{position:static}',
    '@media print{.esb{display:none}}'
  ].join('');

  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return n;
  }
  var CARET = '<svg class="esb-caret" viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 3.5 5 7l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function menuItem(label, menu, current) {
    var btn = el('button', { type: 'button', 'aria-haspopup': 'true', 'aria-expanded': 'false', html: label + CARET });
    var item = el('div', { class: 'esb-item' + (current ? ' esb-cur' : '') }, [btn, menu]);
    btn.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var open = !item.classList.contains('open');
      closeMenus();
      item.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    return item;
  }
  function closeMenus() {
    var open = document.querySelectorAll('.esb-item.open');
    for (var i = 0; i < open.length; i++) {
      open[i].classList.remove('open');
      open[i].firstChild.setAttribute('aria-expanded', 'false');
    }
  }

  // ---- which section is this page in?
  function currentSection() {
    var slug = document.body.getAttribute('data-book-slug');
    if (slug) return { kind: 'volume', slug: slug };
    var path = location.pathname.replace(/\\/g, '/');
    for (var i = 0; i < SECTIONS.length; i++) {
      if (path.indexOf('/' + SECTIONS[i].dir + '/') >= 0) return { kind: 'section', section: SECTIONS[i] };
    }
    return { kind: BASE === '' ? 'home' : 'other' };
  }

  function build(volumes) {
    var cur = currentSection();
    var host = document.getElementById('main-nav');
    var pageLinks = [];
    if (host) {
      var old = host.querySelectorAll('.nav-links a[href^="#"]');
      for (var i = 0; i < old.length; i++) pageLinks.push({ href: old[i].getAttribute('href'), text: old[i].textContent.trim() });
    }

    var bar = el('header', { class: 'esb' });
    var inner = el('div', { class: 'esb-in' });
    bar.appendChild(inner);
    inner.appendChild(el('a', { class: 'esb-brand', href: BASE + 'index.html', title: 'erisml.org home', html: APPLE + '<span>ErisML</span>' }));

    // where you are
    var here = null;
    if (cur.kind === 'volume') {
      var v = null;
      (volumes || []).forEach(function (x) { if (x.slug === cur.slug) v = x; });
      if (v) here = el('a', { class: 'esb-here', href: BASE + v.href, title: v.title + ': contents', html: '<small>Book ' + v.number + '</small>' }, [el('span', null, [v.title])]);
    } else if (cur.kind === 'section') {
      here = el('a', { class: 'esb-here', href: BASE + cur.section.href }, [el('span', null, [cur.section.title])]);
    }
    if (here) inner.appendChild(here);

    var burger = el('button', { class: 'esb-burger', type: 'button', 'aria-label': 'Menu', 'aria-expanded': 'false', html: '<span></span>' });
    inner.appendChild(burger);
    var nav = el('nav', { class: 'esb-nav', 'aria-label': 'Site' });
    inner.appendChild(nav);

    // Geometric Series
    if (volumes && volumes.length) {
      var menu = el('div', { class: 'esb-menu esb-vols' });
      volumes.forEach(function (x) {
        menu.appendChild(el('a', { href: BASE + x.href, class: cur.kind === 'volume' && cur.slug === x.slug ? 'esb-cur' : '', title: x.subtitle || '' },
          [el('span', { class: 'esb-n' }, [String(x.number)]), el('span', null, [x.title])]));
      });
      menu.appendChild(el('a', { class: 'esb-all', href: BASE + 'index.html#geometric-series' }, ['About the series']));
      nav.appendChild(menuItem('Geometric Series', menu, cur.kind === 'volume'));
    } else {
      nav.appendChild(el('a', { href: BASE + 'index.html#geometric-series' }, ['Geometric Series']));
    }
    SECTIONS.forEach(function (s) {
      nav.appendChild(el('a', { href: BASE + s.href, title: s.title, class: cur.kind === 'section' && cur.section.id === s.id ? 'esb-cur' : '' }, [s.label]));
    });
    nav.appendChild(el('a', { href: BASE + 'index.html#community' }, ['Community']));
    if (pageLinks.length) {
      var pm = el('div', { class: 'esb-menu esb-page' });
      pageLinks.forEach(function (l) { pm.appendChild(el('a', { href: l.href }, [l.text])); });
      nav.appendChild(menuItem('On this page', pm, false));
    }

    burger.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var open = !bar.classList.contains('esb-open');
      bar.classList.toggle('esb-open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', function (ev) {
      if (!bar.contains(ev.target)) { closeMenus(); bar.classList.remove('esb-open'); }
      else if (ev.target.closest && ev.target.closest('.esb-menu a, .esb-nav > a')) { closeMenus(); bar.classList.remove('esb-open'); }
    });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { closeMenus(); bar.classList.remove('esb-open'); } });

    if (!document.getElementById('esb-style')) document.head.appendChild(el('style', { id: 'esb-style', html: CSS }));
    if (!document.querySelector('link[rel~="icon"]')) {
      document.head.appendChild(el('link', { rel: 'icon', type: 'image/svg+xml', href: BASE + 'brand/erisml_apple.svg' }));
    }
    var existing = document.querySelector('.esb');
    if (existing) existing.parentNode.removeChild(existing);
    if (host) {
      host.innerHTML = '';
      host.classList.add('esb-host');
      host.appendChild(bar);
    } else {
      document.body.insertBefore(bar, document.body.firstChild);
    }
  }

  function start() {
    var done = false;
    function go(volumes) { if (!done) { done = true; build(volumes); } }
    try {
      fetch(BASE + 'books.json', { cache: 'no-cache' })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (m) { go(m.volumes || []); })
        .catch(function () { go(null); });
    } catch (e) { go(null); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
