"""Build the tutorial notebooks in notebooks/tutorials/ from the example scripts.

    python scripts/build_tutorial_notebooks.py          # write the notebooks
    python scripts/build_tutorial_notebooks.py --check  # exit 1 if a notebook is out of date

A tutorial notebook is an introduction, one cell that installs the library from this repository,
and the code of an example script, so a notebook cannot drift from the script it teaches. Edit
the script (src/erisml/examples/) or the introductions below, then run this.

Two things differ between a script and its notebook, both because a notebook is not a command
line: a script whose ``main`` parses arguments is called as ``main([])``, and a notebook that
shows several scripts imports them from the installed package and runs each ``main``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(ROOT, "src", "erisml", "examples")
OUT = os.path.join(ROOT, "notebooks", "tutorials")
REPO = "https://github.com/ahb-sjsu/erisml-lib"
INSTALL = f'%pip install -q "git+{REPO}.git"'
FOOT = (
    "*Interactive tutorial for the Geometric Ethics reference implementation (ErisML). {source} "
    "Runs top-to-bottom; no API key required.*"
)
MAIN_GUARD = 'if __name__ == "__main__":\n    main()\n'


def script_link(name: str) -> str:
    return f"[`{name}`]({REPO}/blob/main/src/erisml/examples/{name})"


def script_source(name: str, main_call: str = "main()") -> str:
    """The script's code as one notebook cell, ending in a call to its main."""
    with open(os.path.join(EXAMPLES, name), encoding="utf-8") as fh:
        src = fh.read().replace("\r\n", "\n")
    if not src.endswith(MAIN_GUARD):
        raise SystemExit(f"{name} does not end with the usual main guard")
    return src[: -len(MAIN_GUARD)] + main_call + "\n"


def from_script(name: str, main_call: str = "main()"):
    return [("code", script_source(name, main_call))], f"Adapted from {script_link(name)}."


def appendix_d():
    cells = []
    studies = [
        ("appendix_d_cs1_triage", "Case study 1: emergency triage"),
        ("appendix_d_cs2_whistleblower", "Case study 2: the whistleblower's dilemma"),
        ("appendix_d_cs3_av_dilemma", "Case study 3: the autonomous vehicle"),
        ("appendix_d_cs4_hiring", "Case study 4: algorithmic hiring"),
        ("appendix_d_cs5_climate", "Case study 5: climate policy"),
    ]
    for module, title in studies:
        cells.append(
            (
                "markdown",
                f"### {title}\n\nSource: {script_link(module + '.py')}. Each case study runs the shared "
                f"utilities of {script_link('appendix_d_pipeline.py')} and checks the values printed "
                "in Appendix D of the book.",
            )
        )
        cells.append(("code", f"from erisml.examples import {module}\n\n{module}.main()\n"))
    return cells, "Runs the five case-study scripts of the library."


NOTEBOOKS = [
    {
        "file": "01_hello_deme.ipynb",
        "title": "Hello DEME",
        "intro": "Your first ethics evaluation. Create EthicalFacts objects, instantiate the "
        "RightsFirstEM module, and compare two options.",
        "build": lambda: from_script("hello_deme.py"),
    },
    {
        "file": "02_bond_invariance.ipynb",
        "title": "The Bond Invariance Principle",
        "intro": "Test whether moral evaluations are invariant under re-description. The demo "
        "applies re-descriptions that should not change a verdict (reordering, relabelling, a "
        "change of units) and one that should, and reports which verdicts moved.",
        "build": lambda: from_script("bond_invariance_demo.py", "main([])"),
    },
    {
        "file": "03_triage_ethics_pipeline.ipynb",
        "title": "Triage Ethics Pipeline",
        "intro": "A triage decision under a stakeholder profile: ethics modules judge each "
        "option's EthicalFacts, and the profile's governance (weights, vetoes, a constitutional "
        "base module) selects among them. This is the profile-driven V1 path. For the tensor "
        "computation of the triage case (obligation vectors, interest covectors, contraction, "
        "residue) see tutorial 06, case study 1.",
        "build": lambda: from_script("triage_ethics_demo.py"),
    },
    {
        "file": "04_hohfeld_v4.ipynb",
        "title": "Hohfeld Symmetry: the Klein Four-Group V4",
        "intro": "Explore the group structure of Hohfeldian jural relations and verify it "
        "computationally. The two demonstrated operations — the correlative swap (s) and deontic "
        "negation (n) — commute, so the group they generate is the Klein four-group V4 = "
        "{e, n, s, sn}, machine-checked in `formal/HohfeldV4.lean`. The order-8 dihedral group D4 "
        "is obsolete: no quarter-turn has been demonstrated as a normative operation.",
        "build": lambda: from_script("hohfeld_v4_demo.py"),
    },
    {
        "file": "05_governed_pipeline.ipynb",
        "title": "The Governed Pipeline (DEME 3.2)",
        "intro": "The DEME pipeline of version 3.2 on one small scene, a care robot with a resident "
        "who has fallen. A governance profile is executed; the `hard_shell` composition lets the "
        "safety and consent modules veto before anything is ranked; the deontic gate vetoes a "
        "deception and escalates a deception meant to protect, as a conflict of duties for a "
        "human to settle; and, given facts per party, each module judges each party's view of an "
        "act.",
        "build": lambda: from_script("governed_pipeline_demo.py"),
    },
    {
        "file": "06_appendix_d_case_studies.ipynb",
        "title": "Appendix D: End-to-End Case Studies",
        "intro": "Five complete pipelines — Emergency Triage, Whistleblower's Dilemma, Autonomous "
        "Vehicle, Algorithmic Hiring, Climate Policy — with the tensor computation and the Bond "
        "Index of each, as in Appendix D of *Geometric Ethics*.",
        "build": appendix_d,
    },
]


def lines(text: str):
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def cell(kind: str, text: str, n: int) -> dict:
    c = {"cell_type": kind, "id": f"cell-{n}", "metadata": {}, "source": lines(text)}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


def notebook(spec: dict) -> str:
    body, source = spec["build"]()
    cells = [
        ("markdown", f"# {spec['title']}\n\n{spec['intro']}\n\n" + FOOT.format(source=source)),
        ("code", INSTALL),
        ("markdown", "## Tutorial"),
    ] + body
    nb = {
        "cells": [cell(k, t, i) for i, (k, t) in enumerate(cells)],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
            "colab": {"provenance": []},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="do not write; exit 1 if a notebook is out of date")
    a = ap.parse_args(argv)
    stale = []
    for spec in NOTEBOOKS:
        path = os.path.join(OUT, spec["file"])
        text = notebook(spec)
        old = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                old = fh.read().replace("\r\n", "\n")
        if old != text:
            stale.append(spec["file"])
            if not a.check:
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
    if a.check:
        if stale:
            print("out of date, run scripts/build_tutorial_notebooks.py:", ", ".join(stale))
            return 1
        print(f"{len(NOTEBOOKS)} tutorial notebooks are up to date")
        return 0
    print(f"wrote {len(stale)} of {len(NOTEBOOKS)} notebooks to {OUT}" + (": " + ", ".join(stale) if stale else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
