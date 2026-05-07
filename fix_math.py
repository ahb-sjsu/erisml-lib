#!/usr/bin/env python3
"""
Fix missing math variables in HTML book chapters.

The HTML was generated from a Word document containing Office MathML (m:oMath)
elements. During conversion, these math elements were stripped, leaving blank
gaps between <em> tags. This script extracts the math from the source .docx
and re-inserts it into the HTML files.

Strategy:
- For each HTML file with missing math (</em>  <em> pattern),
  find the matching paragraph in the docx by text similarity.
- Extract the m:oMath elements and convert to HTML with <em class="math">.
- Insert them into the gaps in the HTML.
"""

import html
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from docx import Document  # noqa: E402

BOOK_DIR = r"C:\source\erisml-lib\docs\book"
DOCX_PATH = r"C:\source\erisml-lib\docs\papers\foundations\Geometric Ethics - The Mathematical Structure of Moral Reasoning - Bond - v1.14 - Mar 2026.docx"

ns = {
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def omath_to_unicode_inner(elem):
    parts = []

    def process(el):
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "t":
            parts.append(el.text or "")
        elif tag in ("r", "e", "sub", "sup", "num", "den", "deg"):
            for child in el:
                process(child)
        elif tag.endswith("Pr"):
            pass
        else:
            for child in el:
                process(child)

    process(elem)
    return "".join(parts).strip()


def omath_to_html(elem):
    """Convert Office MathML to inline HTML math notation."""
    parts = []
    mns = "http://schemas.openxmlformats.org/officeDocument/2006/math"

    def process(el):
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "t":
            t = el.text or ""
            parts.append(html.escape(t))
        elif tag == "sSub":
            base = el.find("m:e", ns)
            sub = el.find("m:sub", ns)
            if base is not None:
                process(base)
            if sub is not None:
                sub_t = omath_to_unicode_inner(sub)
                parts.append(f"<sub>{html.escape(sub_t)}</sub>")
        elif tag == "sSup":
            base = el.find("m:e", ns)
            sup = el.find("m:sup", ns)
            if base is not None:
                process(base)
            if sup is not None:
                sup_t = omath_to_unicode_inner(sup)
                parts.append(f"<sup>{html.escape(sup_t)}</sup>")
        elif tag == "sSubSup":
            base = el.find("m:e", ns)
            sub = el.find("m:sub", ns)
            sup = el.find("m:sup", ns)
            if base is not None:
                process(base)
            if sub is not None:
                sub_t = omath_to_unicode_inner(sub)
                parts.append(f"<sub>{html.escape(sub_t)}</sub>")
            if sup is not None:
                sup_t = omath_to_unicode_inner(sup)
                parts.append(f"<sup>{html.escape(sup_t)}</sup>")
        elif tag == "f":
            num = el.find("m:num", ns)
            den = el.find("m:den", ns)
            num_t = omath_to_unicode_inner(num) if num is not None else ""
            den_t = omath_to_unicode_inner(den) if den is not None else ""
            parts.append(f"({html.escape(num_t)})/({html.escape(den_t)})")
        elif tag == "rad":
            base = el.find("m:e", ns)
            parts.append("\u221a(")
            if base is not None:
                process(base)
            parts.append(")")
        elif tag == "nary":
            chr_el = el.find("m:naryPr/m:chr", ns)
            op = (
                chr_el.get(f"{{{mns}}}val", "\u2211")
                if chr_el is not None
                else "\u2211"
            )
            sub = el.find("m:sub", ns)
            sup = el.find("m:sup", ns)
            base = el.find("m:e", ns)
            parts.append(op)
            if sub is not None:
                st = omath_to_unicode_inner(sub)
                if st.strip():
                    parts.append(f"<sub>{html.escape(st)}</sub>")
            if sup is not None:
                st = omath_to_unicode_inner(sup)
                if st.strip():
                    parts.append(f"<sup>{html.escape(st)}</sup>")
            parts.append(" ")
            if base is not None:
                process(base)
        elif tag == "d":
            dPr = el.find("m:dPr", ns)
            beg, end = "(", ")"
            if dPr is not None:
                b = dPr.find("m:begChr", ns)
                e = dPr.find("m:endChr", ns)
                if b is not None:
                    beg = b.get(f"{{{mns}}}val", "(")
                if e is not None:
                    end = e.get(f"{{{mns}}}val", ")")
            parts.append(html.escape(beg))
            e_els = el.findall("m:e", ns)
            for idx, ee in enumerate(e_els):
                if idx > 0:
                    parts.append(", ")
                process(ee)
            parts.append(html.escape(end))
        elif tag == "acc":
            base = el.find("m:e", ns)
            if base is not None:
                process(base)
        elif tag == "bar":
            base = el.find("m:e", ns)
            if base is not None:
                process(base)
        elif tag in ("r", "e", "sub", "sup", "num", "den", "deg", "oMath", "oMathPara"):
            for child in el:
                process(child)
        elif tag.endswith("Pr"):
            pass
        else:
            for child in el:
                process(child)

    process(elem)
    return "".join(parts).strip()


def normalize_text(text):
    """Normalize text for fuzzy matching."""
    t = re.sub(r"\s+", " ", text).strip()
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("\xa0", " ")
    return t


def extract_docx_math():
    """Extract all paragraphs with math from the source docx."""
    doc = Document(DOCX_PATH)
    result = []  # list of (plain_text, [math_html_strings])

    for p in doc.paragraphs:
        omath_elems = p._element.findall(".//m:oMath", ns)
        if not omath_elems:
            continue

        plain = normalize_text(p.text)
        if len(plain) < 5:
            continue

        math_list = []
        for om in omath_elems:
            math_html = omath_to_html(om)
            if math_html:
                math_list.append(math_html)

        if math_list:
            result.append((plain, math_list))

    return result


def find_best_match(html_text, docx_paragraphs):
    """Find the docx paragraph that best matches the HTML text."""
    html_norm = normalize_text(html_text)
    if len(html_norm) < 10:
        return None

    best_score = 0
    best_match = None

    for plain, math_list in docx_paragraphs:
        # Count matching words
        h_words = set(html_norm.lower().split())
        p_words = set(plain.lower().split())
        if not h_words or not p_words:
            continue

        common = h_words & p_words
        score = len(common) / max(len(h_words), len(p_words))

        # Boost score for matching definition/proposition numbers
        def_match = re.search(
            r"(Definition|Proposition|Theorem|Lemma)\s+\d+\.\d+", html_norm
        )
        if def_match and def_match.group() in plain:
            score += 0.5

        if score > best_score:
            best_score = score
            best_match = (plain, math_list)

    if best_score > 0.5:
        return best_match
    return None


def fix_html_line(line, docx_paragraphs):
    """Fix a single HTML line by inserting missing math."""
    # Check if this line has the empty-math pattern
    if "</em>" not in line or "<em>" not in line:
        return line, 0

    # Count the gaps (</em>  <em> with no content between)
    gaps = list(re.finditer(r"</em>\s*<em(?:\s[^>]*)?>|</em>\s*<em>", line))
    if not gaps:
        return line, 0

    # Extract the text content (strip HTML tags) for matching
    text_only = re.sub(r"<[^>]+>", "", line)
    text_only = re.sub(r"\s+", " ", text_only).strip()

    match = find_best_match(text_only, docx_paragraphs)
    if not match:
        return line, 0

    plain, math_list = match

    # Now insert math into the gaps
    # Strategy: replace each </em>  <em> gap with </em> <em class="math">MATH</em> <em>
    result = line
    math_idx = 0
    new_parts = []
    pos = 0

    for gap in gaps:
        if math_idx >= len(math_list):
            break
        # Add everything before this gap
        new_parts.append(result[pos : gap.start()])
        # Insert the math
        math_html = math_list[math_idx]
        new_parts.append(f'</em> <em class="math">{math_html}</em> <em>')
        pos = gap.end()
        math_idx += 1

    # Add remaining
    new_parts.append(result[pos:])
    fixed = "".join(new_parts)

    fixes = min(len(gaps), len(math_list))
    return fixed, fixes


def process_file(filepath, docx_paragraphs):
    """Process a single HTML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total_fixes = 0
    new_lines = []

    for line in lines:
        fixed_line, fixes = fix_html_line(line, docx_paragraphs)
        new_lines.append(fixed_line)
        total_fixes += fixes

    if total_fixes > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    return total_fixes


def main():
    print("Extracting math from source docx...")
    docx_paragraphs = extract_docx_math()
    print(f"  Found {len(docx_paragraphs)} paragraphs with math\n")

    # Also add a CSS rule for math styling
    css_path = os.path.join(BOOK_DIR, "book.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    if ".math" not in css:
        css += '\n\n/* Restored math variables */\nem.math { font-style: italic; font-family: "Cambria Math", "STIX Two Math", serif; }\n'
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(css)
        print("Added .math CSS rule to book.css")

    # Process all HTML files
    total_all = 0
    for fname in sorted(os.listdir(BOOK_DIR)):
        if not fname.endswith(".html"):
            continue
        filepath = os.path.join(BOOK_DIR, fname)
        fixes = process_file(filepath, docx_paragraphs)
        if fixes > 0:
            print(f"  {fname}: {fixes} math expressions restored")
            total_all += fixes

    print(f"\nTotal: {total_all} math expressions restored across all files")


if __name__ == "__main__":
    main()
