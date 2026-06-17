"""Apply two fixes to tcss_public_data_analysis.ipynb:

1. Cell 21 (RUGGERI_TARGETS): add bare-numeric aliases ("1", "3", ...) so
   the auto-mapper finds Ruggeri's numeric item columns.

2. Cell 30 (find_contribution_column): exclude columns whose normalized
   name contains "group", "pool", "total", "share", or "lagged", which are
   aggregate / derived quantities. Without this, the picker grabs
   "Group.Contribution" instead of the per-individual "Contribution".
"""
from __future__ import annotations
import json
from pathlib import Path

NB = Path(r"C:/source/erisml-lib/docs/papers/foundations/submission/ieee-tcss/tcss_public_data_analysis.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

# ---- Patch 1: cell 21 ----
new_cell_21 = '''RUGGERI_TARGETS = {
    "P1_Allais_certainty": {
        "aliases": ["1", "P1", "Q1", "Problem1", "Problem_1", "KT1", "Item1", "Choice1", "X1"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P1_Allais_certainty"],
        "description": "Allais/certainty effect; risky option vs certain 2400-like option",
    },
    "P3_Strong_certainty": {
        "aliases": ["3", "P3", "Q3", "Problem3", "Problem_3", "KT3", "Item3", "Choice3", "X3"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P3_Strong_certainty"],
        "description": "80% chance of large gain vs certain smaller gain",
    },
    "P7_Reflection": {
        "aliases": ["7", "P7", "Q7", "Problem7", "Problem_7", "KT7", "Item7", "Choice7", "X7"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P7_Reflection"],
        "description": "loss-domain reflection of P3",
    },
    "P11_Isolation": {
        "aliases": ["11", "P11", "Q11", "Problem11", "Problem_11", "KT11", "Item11", "Choice11", "X11"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P11_Isolation"],
        "description": "isolation/two-stage framing item",
    },
    "P16_Small_prob_gain": {
        "aliases": ["16", "P16", "Q16", "Problem16", "Problem_16", "KT16", "Item16", "Choice16", "X16"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P16_Small_prob_gain"],
        "description": "small-probability gain item",
    },
    "P17_Small_prob_loss": {
        "aliases": ["17", "P17", "Q17", "Problem17", "Problem_17", "KT17", "Item17", "Choice17", "X17"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P17_Small_prob_loss"],
        "description": "small-probability loss/insurance-like item",
    },
}


def binary_candidate_columns(df: pd.DataFrame, *, min_nonmissing: int = 50, max_unique: int = 6) -> list[str]:
    cols = []
    for col in df.columns:
        s = df[col].dropna()
        if len(s) < min_nonmissing:
            continue
        # Exclude obvious IDs, timestamps, and free-text columns.
        ncol = normalized_name(col)
        if any(tok in ncol for tok in ["id", "time", "date", "duration", "age", "country", "language", "gender"]):
            continue
        uniques = pd.Series(s.unique())
        if len(uniques) <= max_unique:
            cols.append(col)
    return cols


def find_likely_ruggeri_table(root: Path) -> tuple[Path | None, pd.DataFrame | None]:
    candidates = []
    for path in discover_table_files(root):
        try:
            df = load_table(path)
        except Exception:
            continue
        bin_cols = binary_candidate_columns(df, min_nonmissing=max(20, min(200, len(df) // 10)))
        score = len(df) * max(1, len(bin_cols))
        name_score = 100000 if any(tok in path.name.lower() for tok in ["prospect", "ruggeri", "ptr", "data"]) else 0
        candidates.append((score + name_score, path, df, len(bin_cols)))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[0], reverse=True)
    print("Top likely Ruggeri tables:")
    for score, path, df, nbin in candidates[:10]:
        print(f" - {path.name}: rows={len(df)}, cols={df.shape[1]}, binary_candidates={nbin}, score={score:.0f}")
    return candidates[0][1], candidates[0][2]

ruggeri_path, ruggeri_df = find_likely_ruggeri_table(ruggeri_dir)
if ruggeri_df is None:
    print("No Ruggeri table was loaded. Check the OSF download and the table inventory.")
else:
    print("Selected Ruggeri table:", ruggeri_path)
    display(ruggeri_df.head())
    print("Shape:", ruggeri_df.shape)
'''

# ---- Patch 2: cell 30 - find_contribution_column with exclusion ----
old_cell_30_src = ''.join(nb['cells'][30]['source'])
assert 'def find_contribution_column' in old_cell_30_src, "cell 30 layout changed"
new_cell_30 = old_cell_30_src.replace(
    '''def find_contribution_column(df: pd.DataFrame) -> str | None:
    candidates = []
    for col in numeric_columns(df):
        n = normalized_name(col)
        if any(tok in n for tok in ["contrib", "contribution", "publicgoods", "pgcontrib", "amountcontributed", "tokenscontributed"]):
            x = pd.to_numeric(df[col], errors="coerce")
            candidates.append((x.notna().sum(), col))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return None''',
    '''def find_contribution_column(df: pd.DataFrame) -> str | None:
    # Per-individual contribution preferred; exclude aggregate/derived columns.
    EXCLUDE_TOKENS = ("group", "pool", "total", "share", "lagged", "punishment", "initial", "final", "payoff", "received", "sent")
    candidates = []
    for col in numeric_columns(df):
        n = normalized_name(col)
        if not any(tok in n for tok in ["contrib", "contribution", "publicgoods", "pgcontrib", "amountcontributed", "tokenscontributed"]):
            continue
        if any(bad in n for bad in EXCLUDE_TOKENS):
            continue
        x = pd.to_numeric(df[col], errors="coerce")
        # Prefer the exact-name "contribution" column when present.
        exact_bonus = 10**9 if n == "contribution" else 0
        candidates.append((x.notna().sum() + exact_bonus, col))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return None'''
)
assert new_cell_30 != old_cell_30_src, "cell 30 patch did not apply"

# Apply patches
nb['cells'][21]['source'] = new_cell_21.splitlines(keepends=True)
nb['cells'][30]['source'] = new_cell_30.splitlines(keepends=True)
# Clear any outputs/execution counts to keep notebook clean
for c in nb['cells']:
    if c['cell_type'] == 'code':
        c['outputs'] = []
        c['execution_count'] = None

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Patched {NB}")
print("Cell 21: numeric aliases added to RUGGERI_TARGETS")
print("Cell 30: find_contribution_column now excludes Group/Pool/Total/Share/Lagged variants")
