#!/usr/bin/env python3
"""
Add KaTeX math rendering to all chapter HTML files in the geometric-* book directories.

This script:
1. Fixes broken A*/h^*/etc patterns where markdown ate the * as italic
2. Converts <em class="math">content</em> to $content$ for KaTeX inline rendering
3. Converts <span class="math-block">content</span> to $$content$$ for display rendering
4. Converts <p class="display-math"><em class="math">content</em></p> properly
5. Fixes display math inside <table> cells
6. Adds KaTeX CSS/JS to <head> and auto-render script to <body>
"""

import glob
import os
import re

DOCS_DIR = r"C:\source\erisml-lib\docs"
SUBDIRS = [
    "geometric-reasoning",
    "geometric-economics",
    "geometric-law",
    "geometric-cognition",
    "geometric-communication",
    "geometric-medicine",
]

KATEX_HEAD = """\
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>"""

KATEX_BODY = """\
<script>
document.addEventListener("DOMContentLoaded", function() {
  renderMathInElement(document.body, {
    delimiters: [
      {left: "$$", right: "$$", display: true},
      {left: "$", right: "$", display: false},
      {left: "\\\\(", right: "\\\\)", display: false},
      {left: "\\\\[", right: "\\\\]", display: true}
    ],
    throwOnError: false
  });
});
</script>"""


def add_katex_head(html):
    if "katex" in html.lower():
        return html
    html = html.replace("</head>", KATEX_HEAD + "\n</head>", 1)
    return html


def add_katex_body(html):
    if "renderMathInElement" in html:
        return html
    html = html.replace("</body>", KATEX_BODY + "\n</body>", 1)
    return html


def fix_star_corruption(html):
    r"""Fix patterns where markdown converted * to italic <em> tags.

    The core problem: In the source text, A* and h^* contained literal
    asterisks. The markdown-to-HTML converter treated * as italic markers,
    creating broken <em>...</em> spans.

    Key patterns:

    1. A<em> text ... </em>  or  A<em> text ... A</em> text
       Two A* in one sentence: first * opens italic, second * closes it.

    2. <em class="math">h^</em>(x)</em>
       h^* inside math: the * closed an outer A* italic, making h^</em>.

    3. <em class="math">h^<em>(x)</em>
       h^* where * started a NEW italic inside the math em.

    4. <em class="math">P^<em></em>
       P^* where * opened and immediately closed an empty italic.

    Strategy: Multiple targeted passes, each handling one pattern type.
    """

    # PASS 1: Fix var^<em></em> (empty italic from ^*)
    # e.g., h^<em></em> -> h^*
    html = re.sub(r"(\w)\^<em></em>", r"\1^*", html)

    # PASS 2: Fix var^<em>(content)</em> inside <em class="math">
    # e.g., <em class="math">h^<em>(x)</em> -> <em class="math">h^*(x)</em>
    # Note: This replaces the inner broken <em> but the outer math em is still there
    # We apply this repeatedly since there may be multiple in one math span
    for _ in range(5):
        new = re.sub(
            r'(<em class="math">[^<]*?)\^<em>([^<]*?)</em>', r"\1^*\2</em>", html
        )
        if new == html:
            break
        html = new

    # PASS 3: Fix var^</em> inside <em class="math">
    # e.g., <em class="math">h(x) = h^</em>(x)</em>
    # Here the </em> after ^ was closing an outer italic (from A*), not this math em
    # We need: <em class="math">h(x) = h^*(x)</em>
    for _ in range(5):
        new = re.sub(
            r'(<em class="math">[^<]*?)\^</em>([^<]*?)</em>', r"\1^*\2</em>", html
        )
        if new == html:
            break
        html = new

    # PASS 4: Fix var^</em> outside math em
    # Standalone occurrences like g^</em> -> g^*
    html = re.sub(r"(\w)\^</em>", r"\1^*", html)

    # PASS 5: Fix the A* italic pairs.
    # Pattern: A<em> ... </em> where the * from A* opens italic
    # and another * (possibly from another A*) closes it.
    #
    # The approach: Process the html character by character, looking for
    # A<em> patterns. When found, scan forward to find the matching </em>,
    # handling nested <em class="math">...</em> properly.
    # Replace A<em> with A* and the matching </em> with empty string.
    # Also check if the character just before </em> is 'A' (meaning
    # the second A* where * closes the italic), and if so, append *.

    html = _fix_a_star_pairs(html)

    # PASS 6: Any remaining standalone A</em> -> A*
    # But NOT when preceded by > (which means it's inside <em class="math">A</em>)
    html = re.sub(r"(?<=[^a-zA-Z>])A</em>(?=[^<])", "A*", html)

    # PASS 7: Any remaining orphaned A<em> (where matching </em> was consumed
    # by earlier passes). Replace A<em> followed by a space with A*.
    # But NOT A<em class= (which is <em class="math">)
    html = re.sub(r"(?<=[^a-zA-Z])A<em>(?=[\s,.])", "A*", html)
    html = re.sub(r"(?<=[^a-zA-Z])A<em>(?=<strong>)", "A*", html)

    return html


def _fix_a_star_pairs(html):
    """Fix A<em>...</em> pairs where A* markdown created italic spans."""
    result = []
    i = 0
    n = len(html)

    while i < n:
        # Look for A<em> preceded by non-alpha (or start of string)
        if (
            i < n - 4
            and html[i] == "A"
            and html[i + 1 : i + 5] == "<em>"
            and (i == 0 or not html[i - 1].isalpha())
        ):

            # Found A<em> - need to find matching </em>
            # Track depth to skip over <em class="math">...</em> pairs
            depth = 1
            j = i + 5  # position after A<em>

            while j < n and depth > 0:
                if html[j : j + 17] == '<em class="math">':
                    depth += 1
                    j += 17
                elif html[j : j + 4] == "<em>" and not html[j : j + 17].startswith(
                    "<em class="
                ):
                    # Another bare <em> (italic start, not a class="math" em)
                    depth += 1
                    j += 4
                elif html[j : j + 5] == "</em>":
                    depth -= 1
                    if depth == 0:
                        # Found the matching </em>
                        inner = html[i + 5 : j]
                        result.append("A*")

                        # Check if inner ends with A (another A*)
                        # e.g., "...text, A" where A</em> was the pattern
                        if (
                            inner.endswith(" A")
                            or inner.endswith(",A")
                            or inner.endswith(", A")
                        ):
                            # The A at the end was the second A*, append *
                            result.append(
                                inner[:-1]
                            )  # everything except the trailing A
                            result.append("A*")
                        else:
                            result.append(inner)

                        i = j + 5  # skip past </em>
                        break
                    else:
                        j += 5
                else:
                    j += 1
            else:
                # No matching </em> found, leave A as-is
                result.append(html[i])
                i += 1
        else:
            result.append(html[i])
            i += 1

    return "".join(result)


def fix_table_display_math(html):
    """Fix display math equations split across table <th>/<td> cells."""

    def rebuild_table_math(match):
        full_table = match.group(0)

        if "$$" not in full_table:
            return full_table

        rows = re.findall(r"<tr>(.*?)</tr>", full_table, re.DOTALL)
        if not rows:
            return full_table

        result_parts = []
        for row in rows:
            cells = re.findall(r"<t[hd](?:\s[^>]*)?>(.*?)</t[hd]>", row, re.DOTALL)
            if not cells:
                continue
            joined = "".join(cells).strip()
            if joined:
                result_parts.append(joined)

        if not result_parts:
            return full_table

        output_parts = []
        for part in result_parts:
            stripped = part.strip()
            if stripped.startswith("$$") or "$$" in stripped:
                output_parts.append(f'<p class="display-math">{stripped}</p>')
            else:
                output_parts.append(f'<p class="body-text">{stripped}</p>')

        return "\n".join(output_parts)

    html = re.sub(
        r'<div class="table-wrapper"><table class="book-table">.*?</table></div>',
        rebuild_table_math,
        html,
        flags=re.DOTALL,
    )
    return html


def fix_em_math_tags(html):
    """Replace <em class="math">content</em> with $content$."""

    def replace_em_math(match):
        content = match.group(1)
        content = re.sub(r"<sub>(.*?)</sub>", r"_{\1}", content)
        content = re.sub(r"<sup>(.*?)</sup>", r"^{\1}", content)
        content = re.sub(r"<[^>]+>", "", content)
        content = content.replace("&gt;", ">")
        content = content.replace("&lt;", "<")
        content = content.replace("&amp;", "&")
        return f"${content}$"

    html = re.sub(r'<em class="math">(.*?)</em>', replace_em_math, html)
    return html


def fix_math_block_spans(html):
    """Replace <span class="math-block">content</span> with $$content$$."""

    def replace_math_block(match):
        content = match.group(1)
        content = re.sub(r"<sub>(.*?)</sub>", r"_{\1}", content)
        content = re.sub(r"<sup>(.*?)</sup>", r"^{\1}", content)
        content = re.sub(r"<[^>]+>", "", content)
        content = content.replace("&gt;", ">")
        content = content.replace("&lt;", "<")
        content = content.replace("&amp;", "&")
        return f"$${content}$$"

    html = re.sub(r'<span class="math-block">(.*?)</span>', replace_math_block, html)
    return html


def fix_display_math_p(html):
    """Ensure <p class='display-math'> content is wrapped in $$."""

    def replace_display_math(match):
        content = match.group(1).strip()
        if content.startswith("$$") and content.endswith("$$"):
            return match.group(0)
        if (
            content.startswith("$")
            and content.endswith("$")
            and not content.startswith("$$")
        ):
            inner = content[1:-1]
            return f'<p class="display-math">$${inner}$$</p>'
        if not content.startswith("$$"):
            content = f"$${content}$$"
        return f'<p class="display-math">{content}</p>'

    html = re.sub(
        r'<p class="display-math">(.*?)</p>',
        replace_display_math,
        html,
        flags=re.DOTALL,
    )
    return html


def fix_stray_artifacts(html):
    """Clean up remaining artifacts."""
    # Fix triple+ dollar signs
    html = re.sub(r"\${3,}", "$$", html)
    return html


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    html = original

    # Step 1: Fix A*/h^* italic corruption
    html = fix_star_corruption(html)

    # Step 2: Fix table display math
    html = fix_table_display_math(html)

    # Step 3: Convert <em class="math"> to $...$
    html = fix_em_math_tags(html)

    # Step 4: Convert <span class="math-block"> to $$...$$
    html = fix_math_block_spans(html)

    # Step 5: Fix <p class="display-math"> content
    html = fix_display_math_p(html)

    # Step 6: Clean up
    html = fix_stray_artifacts(html)

    # Step 7: Add KaTeX
    html = add_katex_head(html)
    html = add_katex_body(html)

    if html != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    return False


def main():
    total_files = 0
    modified_files = 0

    for subdir in SUBDIRS:
        dirpath = os.path.join(DOCS_DIR, subdir)
        if not os.path.isdir(dirpath):
            print(f"WARNING: Directory not found: {dirpath}")
            continue

        pattern = os.path.join(dirpath, "chapter-*.html")
        files = sorted(glob.glob(pattern))
        print(f"\n{subdir}: found {len(files)} chapter files")

        for filepath in files:
            total_files += 1
            filename = os.path.basename(filepath)
            try:
                modified = process_file(filepath)
                if modified:
                    modified_files += 1
                    print(f"  MODIFIED: {filename}")
                else:
                    print(f"  unchanged: {filename}")
            except Exception as e:
                import traceback

                print(f"  ERROR: {filename}: {e}")
                traceback.print_exc()

    print(f"\nDone. Processed {total_files} files, modified {modified_files}.")


if __name__ == "__main__":
    main()
