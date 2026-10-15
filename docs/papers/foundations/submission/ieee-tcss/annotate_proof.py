"""Annotate the TCSS-2026-03-0366 IEEE proof with author corrections.

Usage: python annotate_proof.py [--check]
Reads TCSS-2026-03-0366_proof-for-review.pdf, writes
TCSS-2026-03-0366_proof-annotated.pdf. --check only reports search hits.
Page numbers below are PDF page indices (0 = author-query page,
n = article page n).
"""
import sys
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
SRC = HERE / "TCSS-2026-03-0366_proof-for-review.pdf"
OUT = HERE / "TCSS-2026-03-0366_proof-annotated.pdf"

# (pdf page, search text, occurrence index, comment)
AQ = [
    (0, "AQ1:", 0, "AQ1: The running head is correct as set."),
    (0, "AQ2:", 0,
     "AQ2: Please renumber Tables III and IV. The current Table IV (reference "
     "points and alternatives as implemented) becomes Table III, and the current "
     "Table III (encoding mechanisms and audit status) becomes Table IV. Please "
     "update every in-text citation of the two tables to match."),
    (0, "AQ3:", 0,
     "AQ3: Accessed: Sep. 7, 2026. Please also restore the version, date and DOI "
     "of [28], which were dropped (see the note at [28])."),
    (0, "AQ4:", 0,
     "AQ4: The year is 2020 (version 3 of the Zenodo record, deposited Apr. 2020, "
     "doi: 10.5281/zenodo.3764693)."),
    (0, "AQ5:", 0,
     "AQ5: B.S. in Electrical Engineering; M.S. in Software Engineering."),
    (0, "AQ6:", 0, "AQ6: Raleigh, NC, USA."),
    (0, "AQ7:", 0,
     "AQ7: Lecturer, Department of Computer Engineering, San Jose State University."),
    (0, "AQ8:", 0,
     "AQ8: B.S.E.E. 1991; M.S.S.E. 2013. Note: the master's degree is M.S.S.E. "
     "(Software Engineering), not M.S.E.E. as written in this query."),
]

FIX = [
    (2, "activates 3-D,", 0,
     "Change \"activates 3-D,\" to \"activates three dimensions:\". "
     "\"3-D\" here reads as a fourth list item; the sentence lists the three "
     "active dimensions."),
    (2, "model who is", 0,
     "Change \"model who is encoding rules, metric, choice rules; temperature "
     "constants\" to \"model whose encoding rules, metric, choice rules, "
     "temperature constants\" (\"whose\", and a comma instead of the semicolon)."),
    (2, "MultiAttribute", 0,
     "Heading: change \"MultiAttribute\" to \"Multi-Attribute\"."),
    (4, "How It is Treated", 0,
     "Table II header: change \"How It is Treated\" to \"How It Is Treated\"."),
    (6, "Reject", 0,
     "Table IV: please restore a space on each side of every \"/\" that "
     "separates two alternatives (accept / reject; gain domain / loss domain), "
     "e.g. \"0.1 + 0.8 m(x) / 0.8\", \"x / 0\", \"1 / max(0, 1 - 0.3|min L|/1000)\", "
     "\"0.3 + 0.7 cert(L) / 0.3 + 0.7(1 - cert(L))\", \"0.7 if certain, else 0.4 / "
     "0.3 if certain, else 0.5\". Without the spaces these cells read as "
     "divisions. Keep the true divisions unspaced: (1.75 - 0.5f)/1.75 and "
     "|min L|/1000."),
    (7, "4-D,", 0,
     "Change \"4-D, d2, d4, d5, and d8, take\" to \"Four dimensions, d2, d4, "
     "d5, and d8, take\"."),
    (7, "the elbow", 0, "Fig. 1 caption: capitalize \"The elbow\"."),
    (8, "beyond 3-D", 0,
     "Change \"beyond 3-D.\" to \"beyond three dimensions.\"."),
    (9, "FRASER--NETTLE", 0,
     "Table VI title: \"FRASER--NETTLE\" (two hyphens) should be FRASER, "
     "en dash, NETTLE, i.e. a single en dash as in the text."),
    (11, "Dimension sensitivity", 0,
     "Fig. 2: please replace the graphic with the revised file uploaded with "
     "these corrections (TCSS-2026-03-0366_fig2_revised.pdf). In the current "
     "graphic the x-axis labels \"Conseq\" and \"Rights\" run together; the "
     "revised file shortens the first to \"Cons.\". Size and content are "
     "otherwise unchanged."),
    (11, "domain;", 0,
     "Change the semicolon after \"domain\" to a comma; this is a three-item "
     "list (lower MAE ..., the same 6/6 pass count ..., and a higher pass count ...)."),
    (12, "Lottery Mae", 0,
     "Heading: \"Lottery Mae\" should be \"Lottery MAE\"."),
    (12, "A 4-D or", 0,
     "Change \"A 4-D or 5-D does not\" to \"A fourth or fifth dimension does "
     "not\"."),
    (12, "In the ultimatum,", 0,
     "Change \"In the ultimatum, encoding the offer share moves\" to \"In the "
     "ultimatum encoding, the offer share moves\". As set, the comma changes "
     "the meaning."),
    (13, "fraser", 0, "Fig. 3 caption: capitalize \"Fraser–Nettle\"."),
    (13, "andersen", 2, "Fig. 4 caption: capitalize \"Andersen\"."),
    (13, "bars show", 0, "Fig. 4 caption: capitalize \"Bars show\"."),
    (13, "Proposed behavior", 0,
     "Subfigure caption: change \"(a) Proposed behavior by stakes.\" to \"(a) "
     "Proposer behavior by stakes.\""),
    (15, "on 9-D", 1,
     "Change \"on 9-D\" to \"on nine dimensions\" (noun, not adjective)."),
    (15, "all 9-D", 0, "Change \"all 9-D\" to \"all nine dimensions\"."),
    (15, "weight the 9-D", 0,
     "Change \"weight the 9-D\" to \"weight the nine dimensions\"."),
    (14, "literatures’canonical", 0,
     "Insert a space: \"literatures' canonical\"."),
    (17, "111453", 0,
     "[12]: restore the date and DOI: \"... vol. 173, Art. no. 111453, Dec. 2025, "
     "doi: 10.1016/j.ijepes.2025.111453.\""),
    (17, "eris-econ", 0,
     "[28]: please restore: A. H. Bond, \"eris-econ: Geometric economics on "
     "multi-dimensional decision manifolds,\" ver. 0.1.0, Zenodo, Jun. 2026, "
     "doi: 10.5281/zenodo.20660123. [Online]. Available: "
     "https://pypi.org/project/eris-econ/ (Accessed: Sep. 7, 2026). The version "
     "and DOI identify the exact code that reproduces the reported results."),
    (17, "version 3", 0,
     "[33]: the nested title lost its closing single quote: \"... not an "
     "ultimatum game',\" Zenodo ..."),
    (17, "May 1998.", 0,
     "[35]: change \"May 1998.\" to \"May 1998,\" before the DOI."),
    (17, "ACM.,", 0,
     "[39]: change \"J. ACM.,\" to \"J. ACM,\" and restore \"vol. 56, no. 3, Art. "
     "no. 14, May 2009\"."),
    (17, "Econ. Rev,", 0, "[6]: add the abbreviation period: \"Amer. Econ. Rev.,\"."),
    (17, "J. Econ,", 0, "[26]: add the abbreviation period: \"Quart. J. Econ.,\"."),
    (17, "Physiol,", 0, "[30]: add the abbreviation period: \"Physiol.,\"."),
    (17, "Behav. Org,", 0, "[32]: add the abbreviation period: \"J. Econ. Behav. Org.,\"."),
    (17, "the North", 0,
     "Biography: delete \"the\": \"from North Carolina State University\"."),
    (17, "Senior Member IEEE", 0,
     "Biography: \"(Senior Member, IEEE)\" (comma)."),
]


RED = (0.8, 0, 0)
AUTHOR = "Andrew H. Bond"


def find(doc, page, text, occ):
    hits = doc[page].search_for(text)
    return hits[occ] if len(hits) > occ else None


def where(doc, page, r):
    col = "left" if (r.x0 + r.x1) / 2 < doc[page].rect.width / 2 else "right"
    return f"p. {page}, {col} column"


def label(pg, r, n):
    """Red correction number in the outer margin, level with the highlight."""
    W = pg.rect.width
    box = (fitz.Rect(1, r.y0 - 1, 15, r.y0 + 9) if r.x0 < W / 2
           else fitz.Rect(W - 15, r.y0 - 1, W - 1, r.y0 + 9))
    a = pg.add_freetext_annot(box, str(n), fontsize=7, fontname="hebo",
                              text_color=RED, align=fitz.TEXT_ALIGN_CENTER)
    a.set_info(title=AUTHOR)
    a.update()


def highlight(pg, r, note):
    h = pg.add_highlight_annot(r)
    h.set_info(content=note, title=AUTHOR)
    h.update()


def wrap(text, width):
    import textwrap
    return textwrap.wrap(text, width) or [""]


def add_list_pages(doc, items):
    """Append pages that print every numbered correction in full."""
    lines = [("h", "AUTHOR CORRECTIONS"),
             ("t", "Each number matches a red label in the page margin next to a "
                   "highlight. The same text is attached to each highlight as a comment."),
             ("t", "")]
    for n, (loc, note) in enumerate(items, 1):
        first = True
        for ln in wrap(f"{loc}: {note}", 98):
            lines.append(("n" if first else "t", (f"{n}." if first else "", ln)))
            first = False
        lines.append(("t", ""))
    W, H = doc[1].rect.width, doc[1].rect.height
    y, pg = None, None
    for kind, txt in lines:
        if pg is None or y > H - 60:
            pg = doc.new_page(width=W, height=H)
            y = 60
        if kind == "h":
            pg.insert_text((50, y), txt, fontname="hebo", fontsize=12, color=RED)
            y += 20
        elif kind == "n":
            pg.insert_text((50, y), txt[0], fontname="hebo", fontsize=9, color=RED)
            pg.insert_text((72, y), txt[1], fontname="helv", fontsize=9)
            y += 12
        else:
            body = txt[1] if isinstance(txt, tuple) else txt
            pg.insert_text((72 if isinstance(txt, tuple) else 50, y), body,
                           fontname="helv", fontsize=9)
            y += 12


def add_aq_answers(doc):
    """Print the query answers in the free space under the query list."""
    pg = doc[0]
    # AQ8 wraps onto a second line; leave room for it
    last = find(doc, 0, "AQ8:", 0).y1 + 14
    text = "AUTHOR RESPONSES\n\n" + "\n\n".join(note for _, _, _, note in AQ)
    box = fitz.Rect(50, last + 10, pg.rect.width - 50, pg.rect.height - 12)
    a = pg.add_freetext_annot(box, text, fontsize=8, fontname="helv",
                              text_color=RED, fill_color=(1, 1, 1), border_width=0.8)
    a.set_info(title=AUTHOR)
    a.update()


def main():
    check = "--check" in sys.argv
    doc = fitz.open(SRC)
    ok = True
    for page, text, occ, note in AQ:
        if find(doc, page, text, occ) is None:
            print(f"MISS p{page} {text!r}"); ok = False
    found = []
    for page, text, occ, note in FIX:
        r = find(doc, page, text, occ)
        if r is None:
            print(f"MISS p{page} {text!r}"); ok = False
            continue
        col = 0 if (r.x0 + r.x1) / 2 < doc[page].rect.width / 2 else 1
        found.append(((page, col, r.y0), page, r, note))
    if check:
        print("all anchors found" if ok else "anchors missing")
        return
    found.sort(key=lambda f: f[0])  # reading order: page, column, height
    items = []
    for n, (_, page, r, note) in enumerate(found, 1):
        highlight(doc[page], r, f"[{n}] {note}")
        label(doc[page], r, n)
        items.append((where(doc, page, r), note))
    for page, text, occ, note in AQ:
        highlight(doc[page], find(doc, page, text, occ), note)
    add_aq_answers(doc)
    add_list_pages(doc, items)
    doc.save(OUT, garbage=3, deflate=True)
    print(f"wrote {OUT}: {len(items)} corrections, {len(AQ)} query answers")
    for n, (loc, note) in enumerate(items, 1):
        print(n, loc, note[:60])


if __name__ == "__main__":
    main()
