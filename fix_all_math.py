"""Fix ALL math rendering in ALL chapter HTML files.
Adds KaTeX CDN + fixes double-escaped LaTeX."""

import os

KATEX_HEAD = '  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">\n  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>\n  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>'

KATEX_BODY = '<script>\ndocument.addEventListener("DOMContentLoaded", function() {\n  renderMathInElement(document.body, {\n    delimiters: [\n      {left: "$$", right: "$$", display: true},\n      {left: "$", right: "$", display: false}\n    ],\n    throwOnError: false\n  });\n});\n</script>'

LATEX_CMDS = [
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "theta",
    "lambda",
    "mu",
    "sigma",
    "omega",
    "phi",
    "psi",
    "rho",
    "tau",
    "pi",
    "eta",
    "nu",
    "kappa",
    "chi",
    "Sigma",
    "Omega",
    "Delta",
    "Gamma",
    "Lambda",
    "Phi",
    "Psi",
    "Pi",
    "Theta",
    "mathbf",
    "mathcal",
    "mathbb",
    "mathrm",
    "text",
    "textbf",
    "frac",
    "sqrt",
    "sum",
    "int",
    "prod",
    "partial",
    "nabla",
    "infty",
    "times",
    "cdot",
    "ldots",
    "dots",
    "cdots",
    "leq",
    "geq",
    "neq",
    "approx",
    "equiv",
    "sim",
    "left",
    "right",
    "langle",
    "rangle",
    "begin",
    "end",
    "quad",
    "qquad",
    "vec",
    "hat",
    "bar",
    "tilde",
    "overline",
    "forall",
    "exists",
    "notin",
    "subset",
    "cup",
    "cap",
    "to",
    "rightarrow",
    "leftarrow",
    "mapsto",
    "log",
    "max",
    "min",
    "arg",
    "sup",
    "inf",
    "lim",
]

docs = "docs"
count = 0

for book in [
    "book",
    "geometric-reasoning",
    "geometric-economics",
    "geometric-law",
    "geometric-cognition",
    "geometric-communication",
    "geometric-medicine",
]:
    book_dir = os.path.join(docs, book)
    if not os.path.isdir(book_dir):
        continue
    for fn in sorted(os.listdir(book_dir)):
        if not fn.endswith(".html") or fn == "index.html":
            continue
        path = os.path.join(book_dir, fn)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        modified = False

        # 1. Add KaTeX CDN if not present
        if "katex" not in content.lower():
            content = content.replace("</head>", KATEX_HEAD + "\n</head>")
            content = content.replace("</body>", KATEX_BODY + "\n</body>")
            modified = True

        # 2. Fix double-escaped LaTeX commands
        for cmd in LATEX_CMDS:
            double = "\\\\" + cmd
            single = "\\" + cmd
            if double in content:
                content = content.replace(double, single)
                modified = True

        # 3. Fix escaped underscores and carets in math
        if "\\_" in content:
            content = content.replace("\\_", "_")
            modified = True

        if modified:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            count += 1
            print(f"  Fixed: {book}/{fn}")

print(f"\nTotal: {count} files fixed")
