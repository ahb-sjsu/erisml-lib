#!/usr/bin/env python3
r"""
Fix rendering issues in book chapter HTML files.

Problem 1: A* rendering - markdown-to-HTML conversion mangled "A*" text
by turning asterisks into <em> italic tags.

Problem 2: Raw LaTeX in $...$ and $$...$$ blocks not rendered - convert
to HTML math markup.

This script processes all chapter-*.html files in the geometric-* book directories.
"""

import glob
import os
import re

# ============================================================
# Problem 1: Fix A* rendering issues
# ============================================================


def fix_astar_rendering(html: str) -> str:
    r"""Fix broken A* rendering caused by markdown asterisk -> <em> conversion.

    Uses a multi-phase approach:
    Phase 1: Fix simple patterns (X^<em></em>, X^</em>, X^<em>)
    Phase 2: Fix A<em>...A</em> pairs with proper em tag matching
    Phase 3: Fix remaining orphaned em tags from phase 2
    """
    lines = html.split("\n")
    fixed_lines = []
    for line in lines:
        fixed_lines.append(fix_astar_in_line(line))
    return "\n".join(fixed_lines)


def fix_astar_in_line(line: str) -> str:
    """Fix A* rendering issues in a single line."""

    if "<em" not in line:
        return line

    # Phase 1: Fix simple caret-based patterns
    # These are unambiguous and safe to fix.

    # X^<em></em> -> X* (empty em from X^*)
    line = re.sub(r"(\w)\^<em></em>", r"\1*", line)

    # X^</em> -> X* (premature em close from X^* inside math)
    line = re.sub(r"(\w)\^</em>", r"\1*", line)

    # X^<em> -> X* (em opened by * after ^, NOT class= attributes)
    line = re.sub(r"(\w)\^<em>(?!\s*class)", r"\1*", line)

    # g^<em> and g^</em> patterns
    line = re.sub(r"g\^<em>(?!\s*class)", "g*", line)
    line = re.sub(r"g\^</em>", "g*", line)

    # Phase 2: Fix A<em>...A</em> and similar paired patterns
    # Use stack-based approach to find matching em pairs
    line = fix_paired_astar_em(line)

    return line


def fix_paired_astar_em(line: str) -> str:
    """Fix paired A<em>...A</em> patterns using stack-based em matching.

    When markdown converts "A* text A*" it creates "A<em> text A</em>".
    When "A* text *italic*" is converted, it creates "A<em> text </em>italic<em>".
    (The * from A* pairs with the * from *italic*)

    We detect broken A* references by finding <em> tags that:
    - Are immediately preceded by 'A' (not part of math context)
    - Are bare <em> (not <em class="math">)

    Then we remove the matching </em> as well.
    """

    # Tokenize the line into text segments and em tags
    tokens = tokenize_em_tags(line)

    # Find broken A* patterns (A followed by bare <em> in non-math context)
    # and fix them by removing the <em> and its matching </em>

    changed = True
    while changed:
        changed = False
        tokens = tokenize_em_tags("".join(tokens))

        for i, token in enumerate(tokens):
            if token != "<em>":
                continue

            # Check if preceded by 'A' at end of previous text token
            if i == 0:
                continue

            prev_text = tokens[i - 1]
            if not prev_text:
                continue

            # Check: is this A<em> in non-math context?
            # The A must be preceded by non-letter (word boundary)
            # and NOT preceded by '="math">' or similar math context
            if not prev_text.endswith("A"):
                continue

            # Check the character before A
            if len(prev_text) > 1:
                char_before_a = prev_text[-2]
                # Must be non-letter (space, >, punctuation, etc.)
                if char_before_a.isalpha():
                    continue
                # Check for math context: "math">A or similar
                if prev_text.endswith('">A') or prev_text.endswith("'>A"):
                    continue

            # Found a broken A<em> pattern!
            # Remove this <em> (replace with *)
            # and find+remove the matching </em>

            # Replace A<em> with A*
            tokens[i - 1] = prev_text[:-1] + "A*"  # Remove the A, add A*
            # But wait, prev_text ends with A, so just replace the token
            tokens[i] = ""  # Remove the <em>

            # Find the matching </em>
            # Track em nesting depth to find the correct close
            depth = 1
            for j in range(i + 1, len(tokens)):
                if tokens[j] == "<em>":
                    depth += 1
                elif tokens[j] == "</em>":
                    depth -= 1
                    if depth == 0:
                        # This is the matching </em>
                        # Check context: is this A</em> (another A*)?
                        if j > 0 and tokens[j - 1].endswith("A"):
                            # Another A* reference
                            prev = tokens[j - 1]
                            if len(prev) > 1:
                                char_before = prev[-2]
                                if not char_before.isalpha():
                                    tokens[j - 1] = prev[:-1] + "A*"
                                    tokens[j] = ""
                                    break
                            else:
                                # prev is just 'A'
                                tokens[j - 1] = "A*"
                                tokens[j] = ""
                                break

                        # Not A</em> - this </em> was closing
                        # a legitimate italic that got consumed.
                        # We need to remove it.
                        tokens[j] = ""
                        break

            changed = True
            break  # Restart the loop after making changes

    return "".join(tokens)


def tokenize_em_tags(html: str) -> list:
    """Split HTML into tokens of text and em tags.

    Returns a list where:
    - Text segments are plain strings
    - <em> tags are '<em>'
    - </em> tags are '</em>'
    - <em class="math"> tags are kept as part of surrounding text
      (they are NOT broken A* patterns)

    Note: <em class="..."> tags are NOT tokenized - they stay in text.
    Only bare <em> and </em> are tokenized.
    """
    tokens = []
    pos = 0

    while pos < len(html):
        # Look for <em> or </em> (bare, no attributes)
        # <em> must be followed by > immediately (no space/class)
        # </em> is always </em>

        if html[pos : pos + 5] == "</em>":
            # Check if this is really a close for a bare em or a math em
            # We tokenize all </em> - the matching logic handles context
            if tokens and isinstance(tokens[-1], str):
                pass  # previous token is text, good
            else:
                tokens.append("")  # empty text before
            tokens.append("</em>")
            pos += 5
            continue

        if html[pos : pos + 4] == "<em>":
            # Bare <em> tag - tokenize it
            if not tokens:
                tokens.append("")  # empty text before
            elif tokens[-1] in ("<em>", "</em>"):
                tokens.append("")  # empty text between tags
            tokens.append("<em>")
            pos += 4
            continue

        if html[pos : pos + 4] == "<em ":
            # <em with attributes like <em class="math">
            # Don't tokenize - keep as text
            # Find the closing >
            end = html.find(">", pos)
            if end == -1:
                end = len(html)
            # Include everything up to and including >
            chunk = html[pos : end + 1]
            if (
                tokens
                and isinstance(tokens[-1], str)
                and tokens[-1] not in ("<em>", "</em>")
            ):
                tokens[-1] += chunk
            else:
                tokens.append(chunk)
            pos = end + 1
            continue

        # Regular character - add to current text token
        if not tokens or tokens[-1] in ("<em>", "</em>"):
            tokens.append(html[pos])
        else:
            tokens[-1] += html[pos]
        pos += 1

    return tokens


# ============================================================
# Problem 2: Convert raw LaTeX to HTML
# ============================================================


def convert_latex_to_html(text: str) -> str:
    r"""Convert LaTeX math expressions to HTML."""
    result = text

    # \mathbf{X} -> <strong>X</strong>
    result = re.sub(r"\\mathbf\{([^}]+)\}", r"<strong>\1</strong>", result)

    # \mathcal{X} -> unicode script letter
    mathcal_map = {
        "A": "\U0001d49c",
        "B": "\U0001d49d",
        "C": "\U0001d49e",
        "D": "\U0001d49f",
        "E": "\U0001d4a0",
        "F": "\U0001d4a1",
        "G": "\U0001d4a2",
        "H": "\u210b",
        "I": "\u2110",
        "J": "\U0001d4a5",
        "K": "\U0001d4a6",
        "L": "\u2112",
        "M": "\u2133",
        "N": "\U0001d4a9",
        "O": "\U0001d4aa",
        "P": "\U0001d4ab",
        "Q": "\U0001d4ac",
        "R": "\u211b",
        "S": "\U0001d4ae",
        "T": "\U0001d4af",
        "U": "\U0001d4b0",
        "V": "\U0001d4b1",
        "W": "\U0001d4b2",
        "X": "\U0001d4b3",
        "Y": "\U0001d4b4",
        "Z": "\U0001d4b5",
    }

    def replace_mathcal(m):
        return mathcal_map.get(m.group(1), m.group(1))

    result = re.sub(r"\\mathcal\{([^}]+)\}", replace_mathcal, result)

    # \mathbb{R} -> unicode double-struck
    mathbb_map = {
        "R": "\u211d",
        "N": "\u2115",
        "Z": "\u2124",
        "Q": "\u211a",
        "C": "\u2102",
    }

    def replace_mathbb(m):
        return mathbb_map.get(m.group(1), m.group(1))

    result = re.sub(r"\\mathbb\{([^}]+)\}", replace_mathbb, result)

    # \text{word} -> word
    result = re.sub(r"\\text\{([^}]+)\}", r"\1", result)

    # \operatorname{X} -> X
    result = re.sub(r"\\operatorname\{([^}]+)\}", r"\1", result)

    # Symbol replacements (longest patterns first)
    symbol_replacements = [
        ("\\Rightarrow", "\u21d2"),
        ("\\Leftarrow", "\u21d0"),
        ("\\Leftrightarrow", "\u21d4"),
        ("\\rightarrow", "\u2192"),
        ("\\leftarrow", "\u2190"),
        ("\\leftrightarrow", "\u2194"),
        ("\\mapsto", "\u21a6"),
        ("\\implies", "\u27f9"),
        ("\\iff", "\u27fa"),
        ("\\varepsilon", "\u03b5"),
        ("\\epsilon", "\u03b5"),
        ("\\subseteq", "\u2286"),
        ("\\supseteq", "\u2287"),
        ("\\subset", "\u2282"),
        ("\\supset", "\u2283"),
        ("\\emptyset", "\u2205"),
        ("\\notin", "\u2209"),
        ("\\ldots", "\u2026"),
        ("\\cdots", "\u22ef"),
        ("\\cdot", "\u00b7"),
        ("\\times", "\u00d7"),
        ("\\leq", "\u2264"),
        ("\\geq", "\u2265"),
        ("\\neq", "\u2260"),
        ("\\approx", "\u2248"),
        ("\\infty", "\u221e"),
        ("\\alpha", "\u03b1"),
        ("\\beta", "\u03b2"),
        ("\\gamma", "\u03b3"),
        ("\\delta", "\u03b4"),
        ("\\zeta", "\u03b6"),
        ("\\eta", "\u03b7"),
        ("\\theta", "\u03b8"),
        ("\\iota", "\u03b9"),
        ("\\kappa", "\u03ba"),
        ("\\lambda", "\u03bb"),
        ("\\mu", "\u03bc"),
        ("\\nu", "\u03bd"),
        ("\\xi", "\u03be"),
        ("\\pi", "\u03c0"),
        ("\\rho", "\u03c1"),
        ("\\sigma", "\u03c3"),
        ("\\tau", "\u03c4"),
        ("\\upsilon", "\u03c5"),
        ("\\phi", "\u03c6"),
        ("\\chi", "\u03c7"),
        ("\\psi", "\u03c8"),
        ("\\omega", "\u03c9"),
        ("\\Gamma", "\u0393"),
        ("\\Delta", "\u0394"),
        ("\\Theta", "\u0398"),
        ("\\Lambda", "\u039b"),
        ("\\Xi", "\u039e"),
        ("\\Pi", "\u03a0"),
        ("\\Sigma", "\u03a3"),
        ("\\Phi", "\u03a6"),
        ("\\Psi", "\u03a8"),
        ("\\Omega", "\u03a9"),
        ("\\sum", "\u2211"),
        ("\\prod", "\u220f"),
        ("\\int", "\u222b"),
        ("\\partial", "\u2202"),
        ("\\nabla", "\u2207"),
        ("\\forall", "\u2200"),
        ("\\exists", "\u2203"),
        ("\\cup", "\u222a"),
        ("\\cap", "\u2229"),
        ("\\wedge", "\u2227"),
        ("\\vee", "\u2228"),
        ("\\neg", "\u00ac"),
        ("\\in", "\u2208"),
        ("\\to", "\u2192"),
        ("\\ell", "\u2113"),
        ("\\sim", "\u223c"),
        ("\\gg", "\u226b"),
        ("\\ll", "\u226a"),
        ("\\mid", "|"),
        ("\\varphi", "\u03c6"),
        ("\\circ", "\u2218"),
        ("\\oplus", "\u2295"),
        ("\\succ", "\u227b"),
        ("\\prec", "\u227a"),
        ("\\langle", "\u27e8"),
        ("\\rangle", "\u27e9"),
        ("\\top", "\u22a4"),
        ("\\bot", "\u22a5"),
        ("\\pm", "\u00b1"),
        ("\\mp", "\u2213"),
        ("\\cong", "\u2245"),
        ("\\propto", "\u221d"),
        ("\\hookrightarrow", "\u21aa"),
        ("\\setminus", "\u2216"),  # set minus
        ("\\diamond", "\u25c7"),
        ("\\triangle", "\u25b3"),
        ("\\perp", "\u22a5"),
        ("\\star", "\u22c6"),
        ("\\bullet", "\u2022"),
        ("\\not", "\u0338"),
        ("\\degree", "\u00b0"),
        ("\\oint", "\u222e"),
        ("\\updownarrow", "\u2195"),
        ("\\quad", "  "),
        ("\\qquad", "    "),
    ]

    for latex_cmd, replacement in symbol_replacements:
        escaped = re.escape(latex_cmd)
        result = re.sub(escaped + r"(?![a-zA-Z])", replacement, result)

    # Small spacing - always convert, no lookahead needed
    result = result.replace("\\,", " ")
    result = result.replace("\\;", " ")
    result = result.replace("\\!", "")
    result = result.replace("\\%", "%")
    result = result.replace("\\_", "_")
    result = result.replace("\\#", "#")
    result = result.replace("\\&", "&")

    # \sqrt{x}
    def replace_sqrt(m):
        c = m.group(1)
        return f"\u221a{c}" if len(c) == 1 else f"\u221a({c})"

    result = re.sub(r"\\sqrt\{([^}]+)\}", replace_sqrt, result)

    # \frac{a}{b} - handle nested braces and HTML content
    def replace_frac(m):
        return f"({m.group(1)})/({m.group(2)})"

    # Try simple non-nested first
    result = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", replace_frac, result)
    # Also handle cases where braces contain HTML tags (which have > and < but no })
    # Match \frac{ ... }{ ... } more greedily when content has HTML
    result = re.sub(r"\\frac\{(.+?)\}\{(.+?)\}", replace_frac, result)

    # \binom{n}{k}
    result = re.sub(r"\\binom\{([^}]+)\}\{([^}]+)\}", r"C(\1,\2)", result)
    result = re.sub(r"\\binom\{(.+?)\}\{(.+?)\}", r"C(\1,\2)", result)

    # \xrightarrow{x}
    result = re.sub(
        r"\\xrightarrow\{([^}]+)\}", lambda m: "--" + m.group(1) + "\u2192", result
    )

    # \mathrm{X} -> X (upright text in math)
    result = re.sub(r"\\mathrm\{([^}]+)\}", r"\1", result)

    # \mathfrak{X} -> X
    result = re.sub(r"\\mathfrak\{([^}]+)\}", r"\1", result)

    # \vec{x} -> x with combining arrow
    result = re.sub(r"\\vec\{([^}]+)\}", lambda m: m.group(1) + "\u20d7", result)

    # \underbrace{x}_{text} -> x (simplified)
    result = re.sub(r"\\underbrace\{([^}]+)\}", r"\1", result)

    # \tfrac{a}{b} -> (a)/(b) (text-style fraction)
    result = re.sub(r"\\tfrac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", result)

    # \xleftarrow{x} -> <--x
    result = re.sub(
        r"\\xleftarrow\{([^}]+)\}", lambda m: "\u2190" + m.group(1) + "--", result
    )

    # \xleftrightarrow{x} -> <--x-->
    result = re.sub(
        r"\\xleftrightarrow\{([^}]+)\}", lambda m: "\u2194" + m.group(1), result
    )

    # \scriptstyle -> (ignore, just remove)
    result = result.replace("\\scriptstyle", "")

    # Math functions
    for func in [
        "log",
        "ln",
        "exp",
        "sin",
        "cos",
        "tan",
        "arccos",
        "arcsin",
        "arctan",
        "arctanh",
        "tanh",
        "sinh",
        "cosh",
        "max",
        "min",
        "sup",
        "inf",
        "lim",
        "det",
        "dim",
        "ker",
        "arg",
        "argmin",
        "argmax",
        "Pr",
    ]:
        result = re.sub(r"\\" + func + r"(?![a-zA-Z])", func, result)

    # Accents
    result = re.sub(r"\\dot\{([^}]+)\}", lambda m: m.group(1) + "\u0307", result)
    result = re.sub(r"\\ddot\{([^}]+)\}", lambda m: m.group(1) + "\u0308", result)
    result = re.sub(r"\\bar\{([^}]+)\}", lambda m: m.group(1) + "\u0304", result)
    result = re.sub(r"\\hat\{([^}]+)\}", lambda m: m.group(1) + "\u0302", result)
    result = re.sub(r"\\tilde\{([^}]+)\}", lambda m: m.group(1) + "\u0303", result)
    result = re.sub(r"\\overline\{([^}]+)\}", lambda m: m.group(1) + "\u0305", result)

    # Subscripts and superscripts (braced)
    result = re.sub(r"_\{([^}]+)\}", r"<sub>\1</sub>", result)
    result = re.sub(r"\^\{([^}]+)\}", r"<sup>\1</sup>", result)

    # Single char sub/superscripts
    result = re.sub(r"_([a-zA-Z0-9])(?![a-zA-Z0-9{])", r"<sub>\1</sub>", result)
    result = re.sub(r"\^([a-zA-Z0-9])(?![a-zA-Z0-9{])", r"<sup>\1</sup>", result)

    # Delimiters
    result = re.sub(r"\\left\s*([(\[|])", r"\1", result)
    result = re.sub(r"\\right\s*([)\]|])", r"\1", result)
    result = result.replace("\\left", "")
    result = result.replace("\\right", "")

    # Big delimiters
    result = re.sub(r"\\[Bb]ig[lr]?\s*", "", result)

    # Norms
    result = result.replace("\\lVert", "\u2016")
    result = result.replace("\\rVert", "\u2016")
    result = result.replace("\\|", "\u2016")

    # Escaped braces
    result = result.replace("\\{", "{")
    result = result.replace("\\}", "}")

    # Special symbols
    result = result.replace("\\square", "\u25a1")
    result = result.replace("\\S", "\u00a7")  # Section symbol
    result = result.replace("\\equiv", "\u2261")
    result = result.replace("\\downarrow", "\u2193")
    result = result.replace("\\uparrow", "\u2191")
    result = result.replace("\\nearrow", "\u2197")
    result = result.replace("\\searrow", "\u2198")
    result = result.replace("\\updownarrowopposite", "\u21c5")

    # \textbf{x} -> <strong>x</strong>
    result = re.sub(r"\\textbf\{([^}]+)\}", r"<strong>\1</strong>", result)

    # Environments - remove markers, they're already laid out
    result = result.replace("\\begin{cases}", "")
    result = result.replace("\\end{cases}", "")
    result = result.replace("\\begin{pmatrix}", "")
    result = result.replace("\\end{pmatrix}", "")
    result = result.replace("\\begin{bmatrix}", "")
    result = result.replace("\\end{bmatrix}", "")
    result = result.replace("\\begin{array}{ccc}", "")
    result = re.sub(r"\\begin\{array\}\{[^}]*\}", "", result)
    result = result.replace("\\end{array}", "")

    # Line breaks
    result = result.replace("\\\\", "<br>")

    return result


def convert_latex_in_existing_math_tags(html: str) -> str:
    """Convert LaTeX inside existing <em class="math"> and <span class="math-block"> tags."""

    # Convert <span class="math-block">CONTENT</span> -> <em class="math">CONVERTED</em>
    def convert_math_block(m):
        content = m.group(1)
        converted = convert_latex_to_html(content)
        return f'<em class="math">{converted}</em>'

    result = re.sub(
        r'<span class="math-block">(.+?)</span>',
        convert_math_block,
        html,
        flags=re.DOTALL,
    )

    # Convert LaTeX inside <em class="math">CONTENT</em>
    # Only convert if content contains backslash commands or _ / ^ patterns
    def convert_math_em(m):
        content = m.group(1)
        # Only convert if there's raw LaTeX to convert
        if "\\" in content or ("_" in content and "<sub>" not in content):
            converted = convert_latex_to_html(content)
            return f'<em class="math">{converted}</em>'
        return m.group(0)  # No change

    # Run multiple passes to handle content that needs re-processing
    for _ in range(3):
        new_result = re.sub(
            r'<em class="math">(.+?)</em>', convert_math_em, result, flags=re.DOTALL
        )
        if new_result == result:
            break
        result = new_result

    return result


def find_and_convert_dollar_math(html: str) -> str:
    """Find $...$ and $$...$$ blocks and convert to HTML math."""

    def convert_display_math(m):
        content = m.group(1).strip()
        converted = convert_latex_to_html(content)
        return f'<em class="math">{converted}</em>'

    # [$][$] matches literal $$ (not end-of-string anchor)
    result = re.sub(r"[$][$](.+?)[$][$]", convert_display_math, html, flags=re.DOTALL)

    def convert_inline_math(m):
        content = m.group(1).strip()
        # Skip if it looks like currency (starts with a digit)
        if m.group(1).strip()[:1].isdigit():
            return m.group(0)  # Keep original
        converted = convert_latex_to_html(content)
        return f'<em class="math">{converted}</em>'

    result = re.sub(
        r"(?<![$])[$](?![$])(.+?)(?<![$])[$](?![$])", convert_inline_math, result
    )

    return result


# ============================================================
# Main processing
# ============================================================


def process_file(filepath: str) -> tuple:
    """Process a single HTML file."""

    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    html = original
    changes = []

    # Fix A* rendering
    html_after_astar = fix_astar_rendering(html)
    if html_after_astar != html:
        changes.append("Fixed A* rendering")
    html = html_after_astar

    # Convert LaTeX inside existing math tags
    html_after_math_tags = convert_latex_in_existing_math_tags(html)
    if html_after_math_tags != html:
        changes.append("Converted LaTeX in math tags")
    html = html_after_math_tags

    # Fix raw LaTeX in $...$ blocks
    html_after_latex = find_and_convert_dollar_math(html)
    if html_after_latex != html:
        changes.append("Converted $-delimited LaTeX")
    html = html_after_latex

    if html != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return True, changes

    return False, changes


def main():
    base = os.path.join("C:", os.sep, "source", "erisml-lib", "docs")

    directories = [
        "geometric-reasoning",
        "geometric-economics",
        "geometric-law",
        "geometric-cognition",
        "geometric-communication",
        "geometric-medicine",
    ]

    total_files = 0
    changed_files = 0

    for dir_name in directories:
        pattern = os.path.join(base, dir_name, "chapter-*.html")
        files = sorted(glob.glob(pattern))

        print(f"\n{'='*60}")
        print(f"Processing {dir_name}/ ({len(files)} files)")
        print(f"{'='*60}")

        for filepath in files:
            total_files += 1
            filename = os.path.basename(filepath)

            changed, file_changes = process_file(filepath)

            if changed:
                changed_files += 1
                change_str = "; ".join(file_changes)
                print(f"  FIXED: {filename} ({change_str})")
            else:
                print(f"  ok:    {filename}")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total files processed: {total_files}")
    print(f"Files changed: {changed_files}")
    print(f"Files unchanged: {total_files - changed_files}")


if __name__ == "__main__":
    main()
