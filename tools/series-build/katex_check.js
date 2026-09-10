#!/usr/bin/env node
/*
 * katex_check.js — parse a batch of TeX math snippets with KaTeX and report
 * the ones KaTeX cannot render (these show up as red error text on the site).
 *
 * stdin:  JSON array of {id, tex, display}
 * stdout: JSON array of {id, error} for failures only
 *
 * Needs the `katex` package resolvable from this file's directory or from
 * KATEX_NODE_PATH. Install once with:  npm i katex@0.16.11
 */
'use strict';
const path = require('path');
let katex;
try {
  katex = require('katex');
} catch (e) {
  const extra = process.env.KATEX_NODE_PATH;
  if (extra) katex = require(path.join(extra, 'node_modules', 'katex'));
  else { console.error('katex not installed: npm i katex@0.16.11 (or set KATEX_NODE_PATH)'); process.exit(2); }
}
let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => buf += d);
process.stdin.on('end', () => {
  const items = JSON.parse(buf || '[]');
  const out = [];
  for (const it of items) {
    try {
      katex.renderToString(it.tex, { displayMode: !!it.display, throwOnError: true, strict: 'ignore' });
    } catch (e) {
      out.push({ id: it.id, error: String(e.message || e).replace(/^KaTeX parse error: /, '') });
    }
  }
  process.stdout.write(JSON.stringify(out));
});
