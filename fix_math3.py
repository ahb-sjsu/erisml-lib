#!/usr/bin/env python3
"""
Fix Type 3 missing math: single-space gaps before punctuation where
math variables were stripped. E.g., "If , the space" should be "If R=0, the space".

Uses a completely different strategy: for each HTML paragraph, reconstruct
the full text by interleaving text and math from the docx, then replace
the entire paragraph content.
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
        if tag == 't': parts.append(el.text or '')
        elif tag in ('r', 'e', 'sub', 'sup', 'num', 'den', 'deg'):
            for child in el: process(child)
        elif tag.endswith('Pr'): pass
        else:
            for child in el: process(child)
    process(elem)
    return ''.join(parts).strip()


def omath_to_html(elem):
    parts = []
    mns = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
    def process(el):
        tag = el.tag.split('}')[-1] if '}' in el.tag else el.tag
        if tag == 't': parts.append(html_mod.escape(el.text or ''))
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
        elif tag.endswith('Pr'): pass
        else:
            for child in el: process(child)
    process(elem)
    return ''.join(parts).strip()


def get_fragments(para_element):
    """Get ordered list of (type, text, formatting) from a docx paragraph."""
    fragments = []
    for child in para_element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'r':
            rPr = child.find('w:rPr', ns)
            is_bold = rPr is not None and rPr.find('w:b', ns) is not None if rPr is not None else False
            is_italic = rPr is not None and rPr.find('w:i', ns) is not None if rPr is not None else False
            t_el = child.find('w:t', ns)
            if t_el is not None and t_el.text:
                fragments.append(('text', t_el.text, is_bold, is_italic))
        elif tag == 'oMath':
            math_html = omath_to_html(child)
            if math_html:
                fragments.append(('math', math_html, False, True))
        elif tag == 'hyperlink':
            for r in child.findall('w:r', ns):
                t_el = r.find('w:t', ns)
                if t_el is not None and t_el.text:
                    fragments.append(('text', t_el.text, False, False))
    return fragments


def rebuild_from_fragments(fragments):
    """Build HTML paragraph content from docx fragments."""
    parts = []
    in_bold = False
    in_italic = False

    for frag in fragments:
        ftype, text = frag[0], frag[1]
        is_bold = frag[2] if len(frag) > 2 else False
        is_italic = frag[3] if len(frag) > 3 else False

        if ftype == 'math':
            # Close any open tags
            if in_italic:
                parts.append('</em>')
                in_italic = False
            if in_bold:
                parts.append('</strong>')
                in_bold = False
            parts.append(f'<em class="math">{text}</em>')
        else:
            # Handle bold/italic transitions
            if is_bold and not in_bold:
                if in_italic:
                    parts.append('</em>')
                    in_italic = False
                parts.append('<strong>')
                in_bold = True
            elif not is_bold and in_bold:
                parts.append('</strong>')
                in_bold = False

            if is_italic and not in_italic:
                parts.append('<em>')
                in_italic = True
            elif not is_italic and in_italic:
                parts.append('</em>')
                in_italic = False

            parts.append(html_mod.escape(text))

    # Close any remaining tags
    if in_italic:
        parts.append('</em>')
    if in_bold:
        parts.append('</strong>')

    return ''.join(parts)


def normalize(text):
    t = re.sub(r'\s+', ' ', text).strip()
    t = t.replace('\u2013', '-').replace('\u2014', '-')
    t = t.replace('\u2019', "'").replace('\u2018', "'")
    t = t.replace('\u201c', '"').replace('\u201d', '"')
    t = t.replace('\xa0', ' ')
    return t.lower()


def build_docx_db(doc):
    """Build a database of all docx paragraphs with math."""
    db = []
    for p in doc.paragraphs:
        omath_elems = p._element.findall('.//m:oMath', ns)
        if not omath_elems:
            continue
        plain = normalize(p.text)
        if len(plain) < 10:
            continue
        fragments = get_fragments(p._element)
        db.append((plain, fragments))
    return db


def find_match(html_text, db):
    """Find best matching docx paragraph."""
    h = normalize(html_text)
    if len(h) < 10:
        return None

    best_score = 0
    best_match = None

    for plain, fragments in db:
        # Quick prefix check
        if h[:30] == plain[:30]:
            return (plain, fragments)

        # Word overlap
        h_words = set(h.split())
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
            best_match = (plain, fragments)

    if best_score > 0.6:
        return best_match
    return None


def has_missing_math(text_only):
    """Check if a text line has suspicious patterns indicating missing math."""
    # Double spaces
    if '  ' in text_only:
        return True
    # "If ," "across ." "either  or" etc.
    if re.search(r'\bIf [,.]', text_only):
        return True
    if re.search(r'across [,.]', text_only):
        return True
    if re.search(r'(?:over|on|in|of|from|by|with) [,.]', text_only):
        return True
    if re.search(r'\bthen [,.]', text_only):
        return True
    if re.search(r'\bwhere [,.]', text_only):
        return True
    if re.search(r'\bthat [,.]', text_only):
        return True
    # Standalone period/comma after space suggesting missing var
    if re.search(r'[a-z] [,.;:] [A-Z]', text_only):
        return True
    return False


def process_file(filepath, db):
    """Process a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    total_fixes = 0
    new_lines = []

    for line in lines:
        if '<p ' not in line:
            new_lines.append(line)
            continue

        text_only = re.sub(r'<[^>]+>', '', line)

        if not has_missing_math(text_only):
            new_lines.append(line)
            continue

        # Skip lines that already have class="math" (already fixed)
        if 'class="math"' in line:
            new_lines.append(line)
            continue

        match = find_match(text_only, db)
        if not match:
            new_lines.append(line)
            continue

        plain, fragments = match

        # Extract the opening tag and class
        tag_match = re.match(r'(<p[^>]*>)', line)
        if not tag_match:
            new_lines.append(line)
            continue

        open_tag = tag_match.group(1)
        rebuilt_content = rebuild_from_fragments(fragments)
        new_line = f'{open_tag}{rebuilt_content}</p>'

        # Verify the rebuild has actual math
        if 'class="math"' in new_line:
            new_lines.append(new_line)
            total_fixes += 1
        else:
            new_lines.append(line)

    if total_fixes > 0:
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(new_lines))

    return total_fixes


def main():
    print("Loading source docx...")
    doc = Document(DOCX_PATH)
    print("Building paragraph database...")
    db = build_docx_db(doc)
    print(f"  {len(db)} paragraphs with math\n")

    total_all = 0
    for fname in sorted(os.listdir(BOOK_DIR)):
        if not fname.endswith('.html'):
            continue
        filepath = os.path.join(BOOK_DIR, fname)
        fixes = process_file(filepath, db)
        if fixes > 0:
            print(f"  {fname}: {fixes} paragraphs rebuilt with math")
            total_all += fixes

    print(f"\nTotal: {total_all} paragraphs rebuilt")


if __name__ == '__main__':
    main()
