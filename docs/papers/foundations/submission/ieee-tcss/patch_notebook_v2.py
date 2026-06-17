"""Apply a third fix: cell 34's exp1 game-column picker.

The current picker:
  - Selected `TotalProposerTime` for UG_mean_offer (it matched "propos" with the
    same notna count as ProposedAmount, then alphabetical reverse-sort tie-break
    promoted the wrong column).
  - Selected nothing for Responder_MAO (the patterns "mao", "minimum",
    "minaccept", "acceptthreshold" do not match Fraser-Nettle's
    `LowestAcceptable`).
  - Selected nothing for Dictator_mean_giving (correct — Fraser-Nettle has no
    dictator game; that target should be dropped from this evaluation).

Fix: tighten the patterns and add exclusion tokens.
"""
from __future__ import annotations
import json
from pathlib import Path

NB = Path(r"C:/source/erisml-lib/docs/papers/foundations/submission/ieee-tcss/tcss_public_data_analysis.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

cell_34 = ''.join(nb['cells'][34]['source'])
assert 'pick_first_matching_column' in cell_34, "cell 34 layout changed"

new_cell_34 = cell_34.replace(
    '''def pick_first_matching_column(df: pd.DataFrame, patterns: list[str], *, endowment: float) -> str | None:
    candidates = []
    for col in numeric_columns(df):
        n = normalized_name(col)
        if any(re.search(p, n) for p in patterns):
            x = as_percentage(df[col], endowment=endowment)
            candidates.append((x.notna().sum(), col))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]''',
    '''def pick_first_matching_column(df: pd.DataFrame, patterns: list[str], *, endowment: float, exclude: tuple[str, ...] = ()) -> str | None:
    candidates = []
    for col in numeric_columns(df):
        n = normalized_name(col)
        if not any(re.search(p, n) for p in patterns):
            continue
        if exclude and any(bad in n for bad in exclude):
            continue
        x = as_percentage(df[col], endowment=endowment)
        candidates.append((x.notna().sum(), col))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]'''
)
assert new_cell_34 != cell_34, "pick_first_matching_column patch failed"

new_cell_34 = new_cell_34.replace(
    '''    auto_cols = {
        "UG_mean_offer": pick_first_matching_column(df, [r"offer", r"propos"], endowment=ULTIMATUM_ENDOWMENT),
        "Responder_MAO": pick_first_matching_column(df, [r"mao", r"minimum", r"minaccept", r"acceptthreshold"], endowment=ULTIMATUM_ENDOWMENT),
        "Dictator_mean_giving": pick_first_matching_column(df, [r"dictator", r"dg", r"giving", r"give"], endowment=ULTIMATUM_ENDOWMENT),
    }''',
    '''    UG_EXCLUDE = ("time", "first", "info")
    auto_cols = {
        "UG_mean_offer": pick_first_matching_column(df, [r"proposedamount", r"\\bamount\\b", r"offer", r"propos"], endowment=ULTIMATUM_ENDOWMENT, exclude=UG_EXCLUDE),
        "Responder_MAO": pick_first_matching_column(df, [r"lowestaccept", r"minaccept", r"mao", r"minimumoffer", r"acceptthreshold"], endowment=ULTIMATUM_ENDOWMENT, exclude=("highest",)),
        "Dictator_mean_giving": pick_first_matching_column(df, [r"dictator", r"\\bdg\\b", r"\\bgiving\\b", r"\\bgive\\b"], endowment=ULTIMATUM_ENDOWMENT),
    }'''
)
assert "UG_EXCLUDE" in new_cell_34, "auto_cols patch failed"

nb['cells'][34]['source'] = new_cell_34.splitlines(keepends=True)
for c in nb['cells']:
    if c['cell_type'] == 'code':
        c['outputs'] = []
        c['execution_count'] = None

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Patched {NB}: cell 34 pickers tightened")
