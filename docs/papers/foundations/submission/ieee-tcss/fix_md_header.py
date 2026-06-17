"""Rewrite the Andersen section markdown header (cell 35) cleanly."""
from __future__ import annotations
import json
from pathlib import Path

NB = Path(r"C:/source/erisml-lib/docs/papers/foundations/submission/ieee-tcss/tcss_public_data_analysis.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

md = """# High-stakes ultimatum boundary-condition test (Andersen et al. 2011)

The TCSS revision frames the money-zero result as a *context-specific finding* rather than a universal law: monetary stakes are inactive in the studied low-stakes paradigms, but the framework predicts that monetary sensitivity should reactivate in genuinely high-stakes settings.

Andersen, Ertac, Gneezy, Hoffman & List (2011, AER) is the cleanest empirical test: stakes from Rs 20 to Rs 20,000 (a 1000x range; the highest condition is approximately 1.6x monthly income in their Indonesia sample).

If money-zero is universal (sigma^2_1 = infinity everywhere), then under the manuscript section VII.A *stake-scaling invariance* argument:

- mean `percent_offer` should be flat across stakes,
- rejection rate should be flat across stakes,
- the logit `reject ~ offer_share + log_stake` should not improve on `reject ~ offer_share`.

If any of these is violated, money-zero is falsified at high stakes -- exactly the boundary the revised manuscript predicts.

The cells below load the openICPSR 112485 archive, restrict to Andersen IN==1 by default, compute mean offer/rejection rates per stake level, run the formal invariance tests (chi-square + Kruskal-Wallis + logit likelihood-ratio), and produce the falsification figure.
"""

nb["cells"][35]["source"] = md.splitlines(keepends=True)
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("Markdown header fixed.")
