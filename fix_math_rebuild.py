#!/usr/bin/env python3
"""
Comprehensive math rebuild for Geometric Ethics HTML chapters.

Fixes ALL three categories of missing math:
1. Display equations (m:oMathPara) - 290 equation paragraphs missing from HTML
2. Inline math (m:oMath) - variables stripped leaving blank gaps
3. Misplaced equations - display equations in wrong positions from prior fixes

Algorithm:
- Parse docx into chapter sequences with ordered paragraphs
- For each HTML chapter: remove old display-math, then walk docx/HTML in tandem
  using headings as anchor points, inserting display eqs and rebuilding inline math
- Print verification report

Chapters 20-28 HTML were generated separately (not from docx) - skip those.
HTML chapters 1-19 = docx chapters 1-19
HTML chapter 29 = docx chapter 20
HTML chapter 30 = docx chapter 21
"""

import html as html_mod
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

MNS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

# ─── omath converter ─────────────────────────────────────────────────


def omath_to_unicode_inner(elem):
    """Extract plain-text content from an Office MathML element."""
    parts = []

    def process(el):
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "t":
            parts.append(el.text or "")
        elif tag.endswith("Pr"):
            pass
        else:
            for child in el:
                process(child)

    process(elem)
    return "".join(parts).strip()


def omath_to_html(elem):
    """Convert Office MathML element to HTML with sub/sup tags."""
    parts = []

    def process(el):
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "t":
            parts.append(html_mod.escape(el.text or ""))
        elif tag == "sSub":
            base = el.find("m:e", ns)
            sub = el.find("m:sub", ns)
            if base is not None:
                process(base)
            if sub is not None:
                parts.append(
                    f"<sub>{html_mod.escape(omath_to_unicode_inner(sub))}</sub>"
                )
        elif tag == "sSup":
            base = el.find("m:e", ns)
            sup = el.find("m:sup", ns)
            if base is not None:
                process(base)
            if sup is not None:
                parts.append(
                    f"<sup>{html_mod.escape(omath_to_unicode_inner(sup))}</sup>"
                )
        elif tag == "sSubSup":
            base = el.find("m:e", ns)
            sub = el.find("m:sub", ns)
            sup = el.find("m:sup", ns)
            if base is not None:
                process(base)
            if sub is not None:
                parts.append(
                    f"<sub>{html_mod.escape(omath_to_unicode_inner(sub))}</sub>"
                )
            if sup is not None:
                parts.append(
                    f"<sup>{html_mod.escape(omath_to_unicode_inner(sup))}</sup>"
                )
        elif tag == "f":
            num = el.find("m:num", ns)
            den = el.find("m:den", ns)
            n = html_mod.escape(omath_to_unicode_inner(num)) if num is not None else ""
            d = html_mod.escape(omath_to_unicode_inner(den)) if den is not None else ""
            parts.append(f"({n})/({d})")
        elif tag == "rad":
            base = el.find("m:e", ns)
            parts.append("\u221a(")
            if base is not None:
                process(base)
            parts.append(")")
        elif tag == "nary":
            chr_el = el.find("m:naryPr/m:chr", ns)
            op = (
                chr_el.get(f"{{{MNS}}}val", "\u2211")
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
                    parts.append(f"<sub>{html_mod.escape(st)}</sub>")
            if sup is not None:
                st = omath_to_unicode_inner(sup)
                if st.strip():
                    parts.append(f"<sup>{html_mod.escape(st)}</sup>")
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
                    beg = b.get(f"{{{MNS}}}val", "(")
                if e is not None:
                    end = e.get(f"{{{MNS}}}val", ")")
            parts.append(html_mod.escape(beg))
            e_els = el.findall("m:e", ns)
            for idx, ee in enumerate(e_els):
                if idx > 0:
                    parts.append(", ")
                process(ee)
            parts.append(html_mod.escape(end))
        elif tag == "acc":
            base = el.find("m:e", ns)
            if base is not None:
                process(base)
        elif tag == "bar":
            base = el.find("m:e", ns)
            if base is not None:
                process(base)
        elif tag == "eqArr":
            for idx, ee in enumerate(el.findall("m:e", ns)):
                if idx > 0:
                    parts.append("<br>")
                process(ee)
        elif tag == "limLow":
            base = el.find("m:e", ns)
            lim = el.find("m:lim", ns)
            if base is not None:
                process(base)
            if lim is not None:
                parts.append(
                    f"<sub>{html_mod.escape(omath_to_unicode_inner(lim))}</sub>"
                )
        elif tag == "limUpp":
            base = el.find("m:e", ns)
            lim = el.find("m:lim", ns)
            if base is not None:
                process(base)
            if lim is not None:
                parts.append(
                    f"<sup>{html_mod.escape(omath_to_unicode_inner(lim))}</sup>"
                )
        elif tag == "func":
            fname = el.find("m:fName", ns)
            base = el.find("m:e", ns)
            if fname is not None:
                process(fname)
            if base is not None:
                parts.append(" ")
                process(base)
        elif tag == "m":
            # Matrix
            rows = el.findall("m:mr", ns)
            parts.append("[")
            for ri, row in enumerate(rows):
                if ri > 0:
                    parts.append("; ")
                e_els = row.findall("m:e", ns)
                for ci, ce in enumerate(e_els):
                    if ci > 0:
                        parts.append(", ")
                    process(ce)
            parts.append("]")
        elif tag == "box":
            base = el.find("m:e", ns)
            if base is not None:
                process(base)
        elif tag == "borderBox":
            base = el.find("m:e", ns)
            if base is not None:
                process(base)
        elif tag == "groupChr":
            base = el.find("m:e", ns)
            if base is not None:
                process(base)
        elif tag == "phant":
            base = el.find("m:e", ns)
            if base is not None:
                process(base)
        elif tag in (
            "r",
            "e",
            "sub",
            "sup",
            "num",
            "den",
            "deg",
            "oMath",
            "oMathPara",
            "lim",
            "fName",
        ):
            for child in el:
                process(child)
        elif tag.endswith("Pr"):
            pass
        else:
            for child in el:
                process(child)

    process(elem)
    return "".join(parts).strip()


# ─── text normalization ───────────────────────────────────────────────


def normalize(text):
    """Normalize text for matching: collapse whitespace, replace special chars."""
    t = re.sub(r"\s+", " ", text).strip().lower()
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def strip_html_tags(html_text):
    """Remove all HTML tags and return plain text."""
    return re.sub(r"<[^>]+>", "", html_text)


# ─── docx paragraph parsing ──────────────────────────────────────────


def get_fragments(para_element):
    """Get ordered (type, content, is_bold, is_italic) fragments from a docx paragraph XML."""
    fragments = []
    for child in para_element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "r":
            rPr = child.find("w:rPr", ns)
            is_bold = rPr is not None and rPr.find("w:b", ns) is not None
            is_italic = rPr is not None and rPr.find("w:i", ns) is not None
            t_el = child.find("w:t", ns)
            if t_el is not None and t_el.text:
                fragments.append(("text", t_el.text, is_bold, is_italic))
        elif tag == "oMath":
            math_html = omath_to_html(child)
            if math_html:
                fragments.append(("math", math_html, False, True))
        elif tag == "oMathPara":
            math_html = omath_to_html(child)
            if math_html:
                fragments.append(("displaymath", math_html, False, False))
        elif tag == "hyperlink":
            for r in child.findall("w:r", ns):
                rPr = r.find("w:rPr", ns)
                is_bold = rPr is not None and rPr.find("w:b", ns) is not None
                is_italic = rPr is not None and rPr.find("w:i", ns) is not None
                t_el = r.find("w:t", ns)
                if t_el is not None and t_el.text:
                    fragments.append(("text", t_el.text, is_bold, is_italic))
    return fragments


def get_para_text(para_element):
    """Get plain text from a paragraph element including math text."""
    parts = []
    for child in para_element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "r":
            t_el = child.find("w:t", ns)
            if t_el is not None and t_el.text:
                parts.append(t_el.text)
        elif tag in ("oMath", "oMathPara"):
            parts.append(omath_to_unicode_inner(child))
        elif tag == "hyperlink":
            for r in child.findall("w:r", ns):
                t_el = r.find("w:t", ns)
                if t_el is not None and t_el.text:
                    parts.append(t_el.text)
    return "".join(parts).strip()


def rebuild_from_fragments(fragments):
    """Build HTML paragraph content from docx fragments, interleaving text and math."""
    parts = []
    in_bold = False
    in_italic = False

    for fi, frag in enumerate(fragments):
        ftype, text = frag[0], frag[1]
        is_bold = frag[2] if len(frag) > 2 else False
        is_italic = frag[3] if len(frag) > 3 else False

        if ftype in ("math", "displaymath"):
            # Close any open formatting tags before math
            if in_italic:
                parts.append("</em>")
                in_italic = False
            if in_bold:
                parts.append("</strong>")
                in_bold = False
            # Add space before math only if needed (previous part doesn't end with space)
            prev = "".join(parts)
            if prev and not prev.endswith(" ") and not prev.endswith(">"):
                parts.append(" ")
            parts.append(f'<em class="math">{text}</em>')
            # Add space after math only if next fragment doesn't start with space/punctuation
            if fi + 1 < len(fragments):
                next_frag = fragments[fi + 1]
                next_text = next_frag[1]
                if next_frag[0] in ("math", "displaymath"):
                    parts.append(" ")
                elif next_text and next_text[0] not in (
                    " ",
                    ",",
                    ".",
                    ":",
                    ";",
                    ")",
                    "]",
                    "!",
                    "?",
                    "\u2019",
                    "\u201d",
                ):
                    parts.append(" ")
            # Don't add trailing space at end of content
        else:
            # Handle bold transitions
            if is_bold and not in_bold:
                if in_italic:
                    parts.append("</em>")
                    in_italic = False
                parts.append("<strong>")
                in_bold = True
            elif not is_bold and in_bold:
                parts.append("</strong>")
                in_bold = False
            # Handle italic transitions
            if is_italic and not in_italic:
                parts.append("<em>")
                in_italic = True
            elif not is_italic and in_italic:
                parts.append("</em>")
                in_italic = False
            parts.append(html_mod.escape(text))

    if in_italic:
        parts.append("</em>")
    if in_bold:
        parts.append("</strong>")
    result = "".join(parts)
    # Clean up any remaining double spaces
    result = re.sub(r"  +", " ", result)
    return result


# ─── docx chapter building ───────────────────────────────────────────


def build_docx_chapters(doc):
    """
    Parse entire docx into per-chapter sequences.
    Returns dict: chapter_num -> list of paragraph entries.
    """
    all_paras = []
    for p in doc.paragraphs:
        el = p._element
        text = p.text.strip()

        has_math = bool(el.findall(".//m:oMath", ns))
        has_display = bool(el.findall(".//m:oMathPara", ns))

        # A display-only paragraph: m:oMathPara present, and no text outside math
        text_without_math = get_text_without_math(el)
        is_display_only = has_display and len(text_without_math.strip()) == 0

        fragments = get_fragments(el) if (has_math or has_display) else None

        # Get display HTML directly from XML for display-only paragraphs
        display_html = None
        if is_display_only:
            omath_els = el.findall(".//m:oMath", ns)
            if omath_els:
                display_html = " ".join(omath_to_html(om) for om in omath_els)
            else:
                omathpara_els = el.findall(".//m:oMathPara", ns)
                if omathpara_els:
                    display_html = " ".join(omath_to_html(om) for om in omathpara_els)

        # Determine if this is a heading
        style_el = el.find("w:pPr/w:pStyle", ns)
        style_name = (
            style_el.get(f'{{{ns["w"]}}}val', "") if style_el is not None else ""
        )
        is_heading = "Heading" in style_name or style_name.startswith("heading")

        all_paras.append(
            {
                "text": text,
                "text_full": get_para_text(el),  # includes math text
                "normalized": normalize(text) if text else "",
                "norm_full": normalize(get_para_text(el)),
                "has_math": has_math,
                "has_display": has_display,
                "is_display_only": is_display_only,
                "display_html": display_html,
                "fragments": fragments,
                "is_heading": is_heading,
                "style": style_name,
            }
        )

    # Find chapter boundaries
    chapters = {}
    current_chapter = None
    for i, entry in enumerate(all_paras):
        text = entry["text"]
        if text.startswith("Chapter ") and ":" in text[:30]:
            ch_match = re.match(r"Chapter (\d+)", text)
            if ch_match:
                ch_num = int(ch_match.group(1))
                if current_chapter is not None:
                    chapters[current_chapter] = all_paras[chapters[current_chapter] : i]
                chapters[ch_num] = i  # temporarily store start index
                current_chapter = ch_num
        elif text.startswith("Appendix ") and ":" in text[:30]:
            if current_chapter is not None:
                chapters[current_chapter] = all_paras[chapters[current_chapter] : i]
                current_chapter = None

    # Close last chapter
    if current_chapter is not None:
        chapters[current_chapter] = all_paras[chapters[current_chapter] :]

    return chapters


def get_text_without_math(para_element):
    """Get text content from paragraph excluding math elements."""
    parts = []
    for child in para_element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "r":
            t_el = child.find("w:t", ns)
            if t_el is not None and t_el.text:
                parts.append(t_el.text)
        elif tag == "hyperlink":
            for r in child.findall("w:r", ns):
                t_el = r.find("w:t", ns)
                if t_el is not None and t_el.text:
                    parts.append(t_el.text)
    return "".join(parts)


# ─── HTML paragraph matching ─────────────────────────────────────────


def html_line_text(line):
    """Extract plain text from an HTML line, stripping tags."""
    return strip_html_tags(line).strip()


def is_heading_line(line):
    """Check if an HTML line is a heading."""
    return bool(re.match(r"<h[1-6]", line.strip()))


def get_heading_text(line):
    """Extract text from an HTML heading line."""
    return normalize(strip_html_tags(line))


def match_score(docx_norm, html_norm):
    """
    Score how well a docx paragraph matches an HTML line.
    Returns 0-100. Higher = better match.
    """
    if not docx_norm or not html_norm:
        return 0

    # Exact match
    if docx_norm == html_norm:
        return 100

    # Prefix match (first N chars) - accounts for math being stripped
    match_len = min(40, len(docx_norm), len(html_norm))
    if match_len < 5:
        return 0

    prefix_d = docx_norm[:match_len]
    prefix_h = html_norm[:match_len]
    if prefix_d == prefix_h:
        return 90

    # Shorter prefix
    match_len = min(25, len(docx_norm), len(html_norm))
    if match_len >= 10:
        prefix_d = docx_norm[:match_len]
        prefix_h = html_norm[:match_len]
        if prefix_d == prefix_h:
            return 80

    # Word overlap
    d_words = set(docx_norm.split())
    h_words = set(html_norm.split())
    if d_words and h_words:
        overlap = len(d_words & h_words) / max(len(d_words), len(h_words))
        if overlap > 0.7:
            return int(70 * overlap)

    return 0


def find_html_match(lines, docx_norm, start_from=0, max_ahead=80):
    """
    Find the best matching HTML line for a docx paragraph.
    Returns (line_index, score) or (-1, 0) if not found.
    """
    if not docx_norm or len(docx_norm) < 5:
        return -1, 0

    best_idx = -1
    best_score = 0

    end = min(start_from + max_ahead, len(lines))
    for i in range(start_from, end):
        line = lines[i].strip()
        # Only match against paragraph/list lines, not headings or structural elements
        if not (line.startswith("<p ") or line.startswith("<li")):
            continue

        html_norm = normalize(strip_html_tags(line))
        if not html_norm:
            continue

        score = match_score(docx_norm, html_norm)
        if score > best_score:
            best_score = score
            best_idx = i

        # Perfect or near-perfect match - take it immediately
        if score >= 90:
            return best_idx, best_score

    if best_score >= 50:
        return best_idx, best_score
    return -1, 0


def find_heading_match(lines, heading_norm, start_from=0, max_ahead=100):
    """Find matching heading in HTML lines."""
    if not heading_norm or len(heading_norm) < 5:
        return -1

    end = min(start_from + max_ahead, len(lines))
    for i in range(start_from, end):
        line = lines[i].strip()
        if not is_heading_line(line):
            continue
        h_norm = normalize(strip_html_tags(line))
        if not h_norm:
            continue
        # Headings should match closely
        if h_norm == heading_norm:
            return i
        # Prefix match for long headings
        match_len = min(40, len(heading_norm), len(h_norm))
        if match_len >= 10 and heading_norm[:match_len] == h_norm[:match_len]:
            return i
    return -1


# ─── main processing ─────────────────────────────────────────────────


def process_chapter(html_path, docx_paras, html_chapter_num, docx_chapter_num):
    """
    Process a single chapter HTML file using the docx paragraph sequence.

    Steps:
    1. Remove ALL existing display-math lines (clean slate)
    2. Walk docx paragraphs and HTML lines in tandem using headings as anchors
    3. Insert display equations at correct positions
    4. Rebuild inline math paragraphs from docx fragments
    """
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Step 1: Remove all existing display-math lines
    removed_display = 0
    clean_lines = []
    for line in lines:
        if 'class="display-math"' in line:
            removed_display += 1
        else:
            clean_lines.append(line)

    lines = clean_lines

    # Find the chapter-content div boundaries
    content_start = 0
    len(lines)
    for i, line in enumerate(lines):
        if 'class="chapter-content"' in line:
            content_start = i + 1
            break
    for i in range(len(lines) - 1, content_start, -1):
        if "</div>" in lines[i] and i > content_start:
            # Look for the chapter-nav-bottom that marks end of content
            pass
        if 'class="chapter-nav-bottom"' in lines[i]:
            break

    # Step 2: Walk docx and HTML in tandem
    html_cursor = content_start  # current position in HTML lines
    insertions = []  # (line_index, html_to_insert)
    rebuilds = {}  # line_index -> new_line_content
    inline_count = 0
    display_count = 0
    skipped_display = 0

    # Process docx paragraphs in order
    for di, entry in enumerate(docx_paras):
        # Skip entries before the chapter title
        if di == 0:
            # First entry is the chapter heading itself; find it in HTML
            heading_idx = find_heading_match(
                lines, entry["normalized"], content_start, 50
            )
            if heading_idx >= 0:
                html_cursor = heading_idx + 1
            continue

        if entry["is_display_only"]:
            # This is a standalone display equation - insert it at current position
            if not entry.get("display_html"):
                skipped_display += 1
                continue

            eq_html = entry["display_html"]
            eq_line = f'<p class="display-math"><em class="math">{eq_html}</em></p>'

            # Find the best insertion point: after the preceding text paragraph
            # Look backward in docx for the nearest non-display paragraph
            prev_text = None
            for pi in range(di - 1, max(0, di - 10), -1):
                if not docx_paras[pi]["is_display_only"] and docx_paras[pi]["text"]:
                    prev_text = docx_paras[pi]
                    break

            # Also look forward for the next non-display paragraph
            next_text = None
            for ni in range(di + 1, min(len(docx_paras), di + 10)):
                if not docx_paras[ni]["is_display_only"] and docx_paras[ni]["text"]:
                    next_text = docx_paras[ni]
                    break

            insert_after = -1

            if prev_text:
                if prev_text["is_heading"]:
                    # Preceding element is a heading
                    h_idx = find_heading_match(
                        lines, prev_text["normalized"], html_cursor - 5, 100
                    )
                    if h_idx >= 0:
                        insert_after = h_idx
                        html_cursor = max(html_cursor, h_idx + 1)
                else:
                    # Preceding element is a text paragraph
                    h_idx, score = find_html_match(
                        lines,
                        prev_text["norm_full"],
                        max(content_start, html_cursor - 5),
                        100,
                    )
                    if h_idx >= 0:
                        insert_after = h_idx
                        html_cursor = max(html_cursor, h_idx + 1)

            if insert_after < 0:
                # Couldn't find preceding paragraph; try next paragraph and insert before it
                if next_text:
                    if next_text["is_heading"]:
                        h_idx = find_heading_match(
                            lines, next_text["normalized"], html_cursor, 100
                        )
                        if h_idx >= 0:
                            insert_after = h_idx - 1
                    else:
                        h_idx, score = find_html_match(
                            lines, next_text["norm_full"], html_cursor, 100
                        )
                        if h_idx >= 0:
                            insert_after = h_idx - 1

            if insert_after >= content_start:
                insertions.append((insert_after, eq_line))
                display_count += 1
            else:
                skipped_display += 1

        elif entry["is_heading"]:
            # Use headings as anchor points to keep cursors aligned
            h_idx = find_heading_match(
                lines, entry["normalized"], max(content_start, html_cursor - 5), 150
            )
            if h_idx >= 0:
                html_cursor = h_idx + 1

        elif entry["has_math"] and entry["fragments"] and entry["text"]:
            # Paragraph with inline math - find matching HTML and rebuild if needed
            h_idx, score = find_html_match(
                lines, entry["norm_full"], max(content_start, html_cursor - 5), 100
            )
            if h_idx < 0:
                # Also try matching against the text without math
                h_idx, score = find_html_match(
                    lines, entry["normalized"], max(content_start, html_cursor - 5), 100
                )

            if h_idx >= 0:
                html_cursor = h_idx + 1
                html_line = lines[h_idx]

                # Check if this line needs rebuilding
                needs_rebuild = False

                # Count math elements in docx vs HTML
                docx_math_count = sum(
                    1 for f in entry["fragments"] if f[0] in ("math", "displaymath")
                )
                html_math_count = html_line.count('class="math"')

                # Check 1: Line has no math but docx does
                if 'class="math"' not in html_line:
                    needs_rebuild = True

                # Check 2: Fewer math elements in HTML than docx
                if html_math_count < docx_math_count:
                    needs_rebuild = True

                # Check 3: Line has gaps (double spaces, "If ,", "and .")
                text_only = strip_html_tags(html_line)
                if "  " in text_only:
                    needs_rebuild = True
                if re.search(r"(?<=[A-Za-z])\s+[,.:;)]", text_only):
                    needs_rebuild = True
                if re.search(r"At\s*:", text_only) and 'class="math"' not in html_line:
                    needs_rebuild = True

                # Check 4: Empty parentheses () suggesting stripped math
                if re.search(r"\(\)", text_only):
                    needs_rebuild = True

                # Check 5: Comma-space after word with no preceding math: "component ,"
                if (
                    re.search(r"\w\s+,", text_only)
                    and docx_math_count > html_math_count
                ):
                    needs_rebuild = True

                if needs_rebuild:
                    # Extract the opening tag from the current HTML line
                    tag_match = re.match(r"(<(?:p|li)[^>]*>)", html_line)
                    if tag_match:
                        open_tag = tag_match.group(1)
                        # Determine closing tag
                        if open_tag.startswith("<li"):
                            close_tag = "</li>"
                        else:
                            close_tag = "</p>"

                        rebuilt = rebuild_from_fragments(entry["fragments"])
                        if rebuilt.strip():
                            rebuilds[h_idx] = f"{open_tag}{rebuilt}{close_tag}"
                            inline_count += 1

        else:
            # Non-math paragraph - use for cursor tracking only
            if entry["text"] and len(entry["normalized"]) >= 15:
                h_idx, score = find_html_match(
                    lines, entry["normalized"], max(content_start, html_cursor - 3), 60
                )
                if h_idx >= 0 and score >= 70:
                    html_cursor = h_idx + 1

    # Step 3: Apply changes
    # First apply rebuilds (these don't change line numbers)
    for idx, new_line in rebuilds.items():
        lines[idx] = new_line

    # Then apply insertions (in reverse order to preserve indices)
    # Sort insertions by position, then reverse to insert from bottom up
    insertions.sort(key=lambda x: x[0], reverse=True)
    for insert_after, eq_line in insertions:
        lines.insert(insert_after + 1, eq_line)

    # Step 4: Post-process - clean up double spaces around math tags in all lines
    for i in range(len(lines)):
        line = lines[i]
        if 'class="math"' in line and ("  " in strip_html_tags(line)):
            # Clean double spaces between text and math tags
            line = re.sub(r'\s+((<em class="math">))', r" \1", line)
            line = re.sub(r"(</em>)\s+", r"\1 ", line)
            # Clean double spaces within text
            # But be careful not to break HTML attributes
            # Only clean text segments (outside tags)
            parts = re.split(r"(<[^>]+>)", line)
            cleaned_parts = []
            for part in parts:
                if part.startswith("<"):
                    cleaned_parts.append(part)
                else:
                    cleaned_parts.append(re.sub(r"  +", " ", part))
            lines[i] = "".join(cleaned_parts)

    # Write back
    with open(html_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    return {
        "removed": removed_display,
        "display_inserted": display_count,
        "display_skipped": skipped_display,
        "inline_rebuilt": inline_count,
    }


def verify_chapter(html_path):
    """Verify a chapter HTML file for remaining issues."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    display_count = 0
    inline_count = 0
    remaining_gaps = 0
    remaining_patterns = 0

    # Find chapter-content boundaries
    in_content = False
    for line in lines:
        if 'class="chapter-content"' in line:
            in_content = True
            continue
        if in_content and 'class="chapter-nav-bottom"' in line:
            in_content = False

        if 'class="display-math"' in line:
            display_count += 1
        if 'class="math"' in line:
            inline_count += line.count('class="math"')

        if not in_content:
            continue

        if "<p " in line or "<li" in line:
            text = strip_html_tags(line).strip()
            if "display-math" in line:
                continue
            if not text:
                continue
            # Check for real double-space gaps in content text
            if "  " in text:
                remaining_gaps += 1
            # Check for "word ," / "word ." patterns suggesting missing inline math
            if re.search(r"(?<=[A-Za-z])\s{2,}[,.:;)]", text):
                remaining_patterns += 1

    return {
        "display_math": display_count,
        "inline_math": inline_count,
        "remaining_gaps": remaining_gaps,
        "remaining_patterns": remaining_patterns,
    }


# ─── chapter file mapping ────────────────────────────────────────────


def get_chapter_files():
    """Map HTML chapter numbers to filenames."""
    chapter_files = {}
    for fname in os.listdir(BOOK_DIR):
        m = re.match(r"chapter-(\d+)-", fname)
        if m:
            chapter_files[int(m.group(1))] = fname
    return chapter_files


# HTML chapter -> docx chapter mapping
# Chapters 1-19: same
# Chapters 20-28: skip (generated separately)
# Chapter 29 HTML = docx chapter 20
# Chapter 30 HTML = docx chapter 21


def html_to_docx_chapter(html_ch):
    """Map HTML chapter number to docx chapter number. Returns None for skip."""
    if 1 <= html_ch <= 19:
        return html_ch
    if 20 <= html_ch <= 28:
        return None  # skip
    if html_ch == 29:
        return 20
    if html_ch == 30:
        return 21
    return None


# ─── main ─────────────────────────────────────────────────────────────


def main():
    print("=" * 70)
    print("COMPREHENSIVE MATH REBUILD")
    print("=" * 70)
    print()

    print("Loading source docx...")
    doc = Document(DOCX_PATH)
    print("Building chapter sequences from docx...")
    docx_chapters = build_docx_chapters(doc)
    print(f"  Found {len(docx_chapters)} chapters in docx")

    # Stats
    total_display = 0
    total_inline_math = 0
    for ch_num, paras in docx_chapters.items():
        for p in paras:
            if p["is_display_only"]:
                total_display += 1
            if p["has_math"] and not p["is_display_only"]:
                total_inline_math += 1
    print(f"  {total_display} display equation paragraphs")
    print(f"  {total_inline_math} paragraphs with inline math")
    print()

    chapter_files = get_chapter_files()

    total_stats = {
        "display_inserted": 0,
        "inline_rebuilt": 0,
        "display_skipped": 0,
        "removed": 0,
    }

    # Process each chapter
    for html_ch in sorted(chapter_files.keys()):
        docx_ch = html_to_docx_chapter(html_ch)
        if docx_ch is None:
            continue
        if docx_ch not in docx_chapters:
            print(
                f"  WARNING: docx chapter {docx_ch} not found for HTML chapter {html_ch}"
            )
            continue

        fname = chapter_files[html_ch]
        filepath = os.path.join(BOOK_DIR, fname)
        docx_paras = docx_chapters[docx_ch]

        print(f"Processing Chapter {html_ch} (docx ch {docx_ch}): {fname}")
        stats = process_chapter(filepath, docx_paras, html_ch, docx_ch)
        print(
            f"  Removed {stats['removed']} old display-math, inserted {stats['display_inserted']} new, rebuilt {stats['inline_rebuilt']} inline"
        )
        if stats["display_skipped"] > 0:
            print(
                f"  ({stats['display_skipped']} display equations could not be placed)"
            )

        for k in total_stats:
            total_stats[k] += stats[k]

    print()
    print("=" * 70)
    print("VERIFICATION REPORT")
    print("=" * 70)
    print()
    print(f"{'Chapter':<12} {'Display':>8} {'Inline':>8} {'Gaps':>8} {'Patterns':>10}")
    print("-" * 50)

    grand_display = 0
    grand_inline = 0
    grand_gaps = 0
    grand_patterns = 0

    for html_ch in sorted(chapter_files.keys()):
        docx_ch = html_to_docx_chapter(html_ch)
        if docx_ch is None:
            continue

        fname = chapter_files[html_ch]
        filepath = os.path.join(BOOK_DIR, fname)
        v = verify_chapter(filepath)

        print(
            f"Ch {html_ch:<8} {v['display_math']:>8} {v['inline_math']:>8} {v['remaining_gaps']:>8} {v['remaining_patterns']:>10}"
        )
        grand_display += v["display_math"]
        grand_inline += v["inline_math"]
        grand_gaps += v["remaining_gaps"]
        grand_patterns += v["remaining_patterns"]

    print("-" * 50)
    print(
        f"{'TOTAL':<12} {grand_display:>8} {grand_inline:>8} {grand_gaps:>8} {grand_patterns:>10}"
    )
    print()
    print(
        f"Summary: {total_stats['removed']} old display-math removed, "
        f"{total_stats['display_inserted']} new display equations inserted, "
        f"{total_stats['inline_rebuilt']} inline math paragraphs rebuilt"
    )
    print(
        f"         {total_stats['display_skipped']} display equations could not be placed"
    )
    print()

    # Ensure CSS is present
    css_path = os.path.join(BOOK_DIR, "book.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    if ".display-math" not in css:
        css += '\n\n/* Display equations */\np.display-math { text-align: center; margin: 1.2em 0; font-size: 1.1em; }\np.display-math em.math { font-style: italic; font-family: "Cambria Math", "STIX Two Math", serif; }\n'
        with open(css_path, "w", encoding="utf-8") as f:
            f.write(css)
        print("Added .display-math CSS to book.css")

    print("Done.")


if __name__ == "__main__":
    main()
