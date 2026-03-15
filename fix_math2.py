#!/usr/bin/env python3
"""
Fix Type 2 missing math: bare double-spaces in non-italic text where
Office MathML variables were stripped during docx-to-HTML conversion.

Strategy: For each HTML paragraph with suspicious double-spaces,
find the matching docx paragraph, extract m:oMath elements in order,
and replace each double-space gap with the corresponding math HTML.
"""

import sys, io, re, os, html as html_mod
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from docx import Document
import lxml.etree as ET

BOOK_DIR = r'C:\source\erisml-lib\docs\book'
DOCX_PATH = r'C:\source\erisml-lib\docs\papers\foundations\Geometric Ethics - The Mathematical Structure of Moral Reasoning - Bond - v1.14 - Mar 2026.docx'

ns = {'m': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
      'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def omath_to_unicode_inner(elem):
    parts = []
    def process(el):
        tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
        if tag == 't':
            parts.append(el.text or '')
        elif tag in ('r', 'e', 'sub', 'sup', 'num', 'den', 'deg'):
            for child in el: process(child)
        elif tag.endswith('Pr'):
            pass
        else:
            for child in el: process(child)
    process(elem)
    return ''.join(parts).strip()


def omath_to_html(elem):
    """Convert Office MathML to inline HTML."""
    parts = []
    mns = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

    def process(el):
        tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
        if tag == 't':
            parts.append(html_mod.escape(el.text or ''))
        elif tag == 'sSub':
            base = el.find('m:e', ns); sub = el.find('m:sub', ns)
            if base is not None: process(base)
            if sub is not None:
                parts.append(f'<sub>{html_mod.escape(omath_to_unicode_inner(sub))}</sub>')
        elif tag == 'sSup':
            base = el.find('m:e', ns); sup = el.find('m:sup', ns)
            if base is not None: process(base)
            if sup is not None:
                parts.append(f'<sup>{html_mod.escape(omath_to_unicode_inner(sup))}</sup>')
        elif tag == 'sSubSup':
            base = el.find('m:e', ns); sub = el.find('m:sub', ns); sup = el.find('m:sup', ns)
            if base is not None: process(base)
            if sub is not None:
                parts.append(f'<sub>{html_mod.escape(omath_to_unicode_inner(sub))}</sub>')
            if sup is not None:
                parts.append(f'<sup>{html_mod.escape(omath_to_unicode_inner(sup))}</sup>')
        elif tag == 'f':
            num = el.find('m:num', ns); den = el.find('m:den', ns)
            n = html_mod.escape(omath_to_unicode_inner(num)) if num is not None else ''
            d = html_mod.escape(omath_to_unicode_inner(den)) if den is not None else ''
            parts.append(f'({n})/({d})')
        elif tag == 'rad':
            base = el.find('m:e', ns)
            parts.append('\u221a(')
            if base is not None: process(base)
            parts.append(')')
        elif tag == 'nary':
            chr_el = el.find('m:naryPr/m:chr', ns)
            op = chr_el.get(f'{{{mns}}}val', '\u2211') if chr_el is not None else '\u2211'
            sub = el.find('m:sub', ns); sup = el.find('m:sup', ns); base = el.find('m:e', ns)
            parts.append(op)
            if sub is not None:
                st = omath_to_unicode_inner(sub)
                if st.strip(): parts.append(f'<sub>{html_mod.escape(st)}</sub>')
            if sup is not None:
                st = omath_to_unicode_inner(sup)
                if st.strip(): parts.append(f'<sup>{html_mod.escape(st)}</sup>')
            parts.append(' ')
            if base is not None: process(base)
        elif tag == 'd':
            dPr = el.find('m:dPr', ns); beg, end = '(', ')'
            if dPr is not None:
                b = dPr.find('m:begChr', ns); e = dPr.find('m:endChr', ns)
                if b is not None: beg = b.get(f'{{{mns}}}val', '(')
                if e is not None: end = e.get(f'{{{mns}}}val', ')')
            parts.append(html_mod.escape(beg))
            e_els = el.findall('m:e', ns)
            for idx, ee in enumerate(e_els):
                if idx > 0: parts.append(', ')
                process(ee)
            parts.append(html_mod.escape(end))
        elif tag == 'acc':
            base = el.find('m:e', ns)
            if base is not None: process(base)
        elif tag == 'bar':
            base = el.find('m:e', ns)
            if base is not None: process(base)
        elif tag in ('r', 'e', 'sub', 'sup', 'num', 'den', 'deg', 'oMath', 'oMathPara'):
            for child in el: process(child)
        elif tag.endswith('Pr'):
            pass
        else:
            for child in el: process(child)

    process(elem)
    return ''.join(parts).strip()


def normalize(text):
    t = re.sub(r'\s+', ' ', text).strip()
    t = t.replace('\u2013', '-').replace('\u2014', '-')
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    t = t.replace('\u201c', '"').replace('\u201d', '"')
    t = t.replace('\xa0', ' ')
    return t.lower()


def get_text_fragments(para_element):
    """Get ordered list of (type, text) from a docx paragraph element.
    type is 'text' for regular runs, 'math' for m:oMath elements."""
    fragments = []
    for child in para_element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'r':
            t_el = child.find('w:t', ns)
            if t_el is not None and t_el.text:
                fragments.append(('text', t_el.text))
        elif tag == 'oMath':
            math_html = omath_to_html(child)
            if math_html:
                fragments.append(('math', math_html))
        elif tag == 'hyperlink':
            # Extract text from hyperlink runs
            for r in child.findall('w:r', ns):
                t_el = r.find('w:t', ns)
                if t_el is not None and t_el.text:
                    fragments.append(('text', t_el.text))
    return fragments


def build_docx_index(doc):
    """Build an index of docx paragraphs with math, keyed by text fingerprint."""
    index = {}
    for p in doc.paragraphs:
        omath_elems = p._element.findall('.//m:oMath', ns)
        if not omath_elems:
            continue

        plain = normalize(p.text)
        if len(plain) < 10:
            continue

        fragments = get_text_fragments(p._element)
        math_list = [f[1] for f in fragments if f[0] == 'math']

        if not math_list:
            continue

        # Use multiple key lengths for matching
        for keylen in [40, 60, 80, 100]:
            key = plain[:keylen]
            if key not in index:
                index[key] = (plain, math_list, fragments)

    return index


def find_match(html_text, docx_index):
    """Find the best matching docx paragraph for an HTML text."""
    h = normalize(html_text)
    if len(h) < 10:
        return None

    # Try exact prefix matches at various lengths
    for keylen in [100, 80, 60, 40]:
        key = h[:keylen]
        if key in docx_index:
            return docx_index[key]

    # Fuzzy match: find best word overlap
    h_words = set(h.split())
    best_score = 0
    best_match = None

    for key, val in docx_index.items():
        plain = val[0]
        p_words = set(plain.split())
        if not p_words:
            continue
        common = h_words & p_words
        score = len(common) / max(len(h_words), len(p_words))

        # Boost for definition/proposition matches
        def_m = re.search(r'(definition|proposition|theorem|lemma)\s+\d+\.\d+', h)
        if def_m and def_m.group() in plain:
            score += 0.5

        if score > best_score:
            best_score = score
            best_match = val

    if best_score > 0.55:
        return best_match
    return None


def rebuild_paragraph(html_line, fragments):
    """Rebuild an HTML paragraph by inserting math from docx fragments
    into the double-space gaps in the HTML."""

    # Extract the tag wrapper
    tag_match = re.match(r'(<p[^>]*>)(.*?)(</p>)', html_line, re.DOTALL)
    if not tag_match:
        return html_line, 0

    open_tag = tag_match.group(1)
    inner = tag_match.group(2)
    close_tag = tag_match.group(3)

    # Get the math elements in order
    math_items = [f[1] for f in fragments if f[0] == 'math']
    if not math_items:
        return html_line, 0

    # Find all double-space positions in the stripped text
    # But we need to work with the HTML, preserving tags

    # Strategy: find positions in the HTML where there are double-spaces
    # (in text content, not inside tags) and replace with math

    math_idx = 0
    result = []
    i = 0
    fixes = 0

    while i < len(inner):
        if inner[i] == '<':
            # Skip HTML tag
            end = inner.find('>', i)
            if end == -1:
                result.append(inner[i:])
                break
            result.append(inner[i:end + 1])
            i = end + 1
        elif inner[i] == ' ' and i + 1 < len(inner) and inner[i + 1] == ' ':
            # Double space found - this is likely a missing math variable
            # Consume all spaces
            j = i
            while j < len(inner) and inner[j] == ' ':
                j += 1

            if math_idx < len(math_items):
                math_html = math_items[math_idx]
                result.append(f' <em class="math">{math_html}</em> ')
                math_idx += 1
                fixes += 1
            else:
                result.append(inner[i:j])

            i = j
        else:
            result.append(inner[i])
            i += 1

    rebuilt = open_tag + ''.join(result) + close_tag
    return rebuilt, fixes


def process_file(filepath, docx_index):
    """Process a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    total_fixes = 0
    new_lines = []

    for line in lines:
        # Check if this line is a paragraph with double-spaces
        if '<p ' not in line or '  ' not in line:
            new_lines.append(line)
            continue

        # Strip tags to get text
        text_only = re.sub(r'<[^>]+>', '', line)

        # Check for double-spaces indicating missing math
        if not re.search(r'(?<=[a-zA-Z)}\]]) {2}(?=[a-zA-Z(,.\[{])', text_only):
            # Also check for patterns like "If , " or "across . "
            if not re.search(r' {2}', text_only):
                new_lines.append(line)
                continue

        # Find matching docx paragraph
        match = find_match(text_only, docx_index)
        if not match:
            new_lines.append(line)
            continue

        plain, math_list, fragments = match

        # Rebuild the paragraph with math inserted
        fixed_line, fixes = rebuild_paragraph(line, fragments)
        new_lines.append(fixed_line)
        total_fixes += fixes

    if total_fixes > 0:
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(new_lines))

    return total_fixes


def main():
    print("Loading source docx...")
    doc = Document(DOCX_PATH)
    print("Building paragraph index...")
    docx_index = build_docx_index(doc)
    print(f"  Indexed {len(docx_index)} keys from paragraphs with math\n")

    total_all = 0
    for fname in sorted(os.listdir(BOOK_DIR)):
        if not fname.endswith('.html'):
            continue
        filepath = os.path.join(BOOK_DIR, fname)
        fixes = process_file(filepath, docx_index)
        if fixes > 0:
            print(f"  {fname}: {fixes} math expressions restored")
            total_all += fixes

    print(f"\nTotal: {total_all} math expressions restored")


if __name__ == '__main__':
    main()
