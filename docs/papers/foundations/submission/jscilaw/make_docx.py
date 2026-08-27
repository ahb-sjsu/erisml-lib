#!/usr/bin/env python3
"""Build lbi_manuscript.docx from lbi_manuscript.tex via pandoc.

Pipeline (submission artifact is the Word file; the tex is the source
of record):
 1. resolve natbib citations to literal text (the tex carries its own
    thebibliography, so no .bib/citeproc);
 2. point figures at the PNG twins (Word cannot display PDF images);
 3. resolve \\S\\ref{...} cross-references to fixed section numbers;
 4. add a References heading before the bibliography;
 5. pandoc -f latex -t docx.

Run:  python make_docx.py   (from this directory)
"""

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEX = (HERE / "lbi_manuscript.tex").read_text(encoding="utf-8")

# 1 -- citation map (must match thebibliography labels)
CITE = {
    "angwin2016": ("Angwin et al.", "2016"),
    "barocas2016": ("Barocas and Selbst", "2016"),
    "bond2026geometric": ("Bond", "2026a"),
    "bond2026tractability": ("Bond", "2026b"),
    "chouldechova2017": ("Chouldechova", "2017"),
    "citron2008": ("Citron", "2008"),
    "dieterich2016": ("Dieterich et al.", "2016"),
    "dwork2012": ("Dwork et al.", "2012"),
    "feldman2015": ("Feldman et al.", "2015"),
    "hardt2016": ("Hardt et al.", "2016"),
    "huq2019": ("Huq", "2019"),
    "kleinberg2017": ("Kleinberg et al.", "2017"),
    "kusner2017": ("Kusner et al.", "2017"),
    "mahalanobis1936": ("Mahalanobis", "1936"),
    "mayson2019": ("Mayson", "2019"),
    "starr2014": ("Starr", "2014"),
}


def _cite(m):
    style = m.group(1)
    keys = [k.strip() for k in m.group(2).split(",")]
    for k in keys:
        if k not in CITE:
            sys.exit(f"unknown citation key: {k}")
    if style == "citep":
        inner = "; ".join(f"{CITE[k][0]}, {CITE[k][1]}" for k in keys)
        return f"({inner})"
    if style == "citealp":
        return "; ".join(f"{CITE[k][0]}, {CITE[k][1]}" for k in keys)
    # citet
    return "; ".join(f"{CITE[k][0]} ({CITE[k][1]})" for k in keys)


tex = re.sub(r"\\(citep|citet|citealp)\{([^}]*)\}", _cite, TEX)

# 0 -- author block: pandoc drops \quad, gluing email to ORCID
tex = tex.replace(
    "\\texttt{andrew.bond@sjsu.edu}\\quad ORCID: 0009-0003-2599-6158",
    "\\texttt{andrew.bond@sjsu.edu}\\\\ ORCID: 0009-0003-2599-6158")

# 2 -- figures: .pdf -> .png
tex = re.sub(r"(\\includegraphics\[[^\]]*\]\{figures/[^}]*)\.pdf\}",
             r"\1.png}", tex)

# 2b -- booktabs partial rules: pandoc leaks their arguments as cell
# text ("2-3(lr)4-5"); the docx table needs no mid-rules
tex = re.sub(r"\\cmidrule\([^)]*\)\{[^}]*\}", "", tex)

# 3 -- section cross-references (fixed numbering of this manuscript)
SEC = {
    "sec:intro": "1", "sec:background": "2", "sec:lbi": "3",
    "sec:inference": "3.3", "sec:empirical": "4",
    "sec:lbiresults": "4.4", "sec:distdiag": "4.5",
    "sec:inferenceresults": "4.6", "sec:scorerep": "4.7",
    "sec:robustness": "4.8", "sec:synthetic": "4.9",
    "sec:implementation": "4.10", "sec:discussion": "5",
    "sec:individualfairness": "5.2", "sec:policy": "6",
    "sec:doctrine": "6.3", "sec:conclusion": "7",
}
tex = re.sub(r"\\S\\ref\{([^}]*)\}",
             lambda m: "\u00a7" + SEC[m.group(1)], tex)
tex = re.sub(r"Section~\\ref\{([^}]*)\}",
             lambda m: "Section " + SEC[m.group(1)], tex)
tex = re.sub(r"Section\s*\\ref\{([^}]*)\}",
             lambda m: "Section " + SEC[m.group(1)], tex)

# 3b -- non-section cross-references (fixed numbering of this manuscript)
REF = {
    "def:lbi": "1", "eq:mahalanobis": "the Mahalanobis metric",
    "eq:lbi": "the LBI ratio (Definition 1)",
    "tab:standard": "1", "tab:lbi": "2", "tab:distdiag": "3",
    "tab:matchparity": "4", "tab:nulls": "5", "tab:scorerep": "6",
    "tab:robust": "7", "tab:synthetic": "8", "tab:summary": "9",
    "fig:lbi-by-attribute": "1", "fig:distdiag": "2",
    "fig:gapdist": "3", "fig:permutation": "4", "fig:synthetic": "5",
}
tex = re.sub(r"\\eqref\{([^}]*)\}", lambda m: REF[m.group(1)], tex)
tex = re.sub(r"(Definition|Table|Figure)~\\ref\{([^}]*)\}",
             lambda m: f"{m.group(1)} {REF[m.group(2)]}", tex)
if re.search(r"\\ref\{", tex):
    leftover = sorted(set(re.findall(r"\\ref\{([^}]*)\}", tex)))
    sys.exit(f"unresolved \\ref keys: {leftover}")

# 3c -- number the captions in appearance order (pandoc does not)
def number_captions(src, env, word):
    out, n, pos = [], 0, 0
    pat = re.compile(r"\\begin\{" + env + r"\}.*?\\end\{" + env + r"\}",
                     re.S)
    for m in pat.finditer(src):
        n += 1
        block = m.group(0).replace("\\caption{",
                                   f"\\caption{{{word} {n}: ", 1)
        out.append(src[pos:m.start()])
        out.append(block)
        pos = m.end()
    out.append(src[pos:])
    return "".join(out)

tex = number_captions(tex, "table", "Table")
tex = number_captions(tex, "figure", "Figure")

# 3d -- give display equations their own paragraph so Word shows them
# as displays rather than squeezing them into the surrounding sentence
tex = re.sub(r"\n(\\begin\{equation\})", r"\n\n\1", tex)
tex = re.sub(r"(\\end\{equation\})\n", r"\1\n\n", tex)

# 4 -- References heading
# pandoc does not know the thebibliography environment: its "{99}"
# width argument leaks into the docx as a literal paragraph (caught by
# the editors). Strip the environment entirely — citations are already
# resolved to literal text, and each \bibitem block is its own
# blank-line-separated paragraph in the source.
tex = tex.replace("\\begin{thebibliography}{99}",
                  "\\section*{References}")
tex = tex.replace("\\end{thebibliography}", "")
tex = re.sub(r"\\bibitem\[[^\]]*\]\{[^}]*\}\s*\n", "", tex)

tmp = HERE / "_lbi_docx_build.tex"
tmp.write_text(tex, encoding="utf-8")

out = HERE / "lbi_manuscript.docx"
cmd = ["pandoc", str(tmp), "-f", "latex", "-t", "docx", "-o", str(out),
       "--resource-path", str(HERE), "--metadata",
       "title=The Legal Bond Index: A Matched-Neighbourhood Diagnostic "
       "of Algorithmic Disparity, Applied to COMPAS"]
r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
print(r.stdout)
print(r.stderr[-3000:] if r.stderr else "(no warnings)")
if r.returncode:
    sys.exit(r.returncode)
print("wrote", out)
