"""Make cell 36 search for the Andersen .dta in both the project root and
its ./data/ subdirectory (the openICPSR archive ships it inside data/)."""
from __future__ import annotations
import json
from pathlib import Path

NB = Path(r"C:/source/erisml-lib/docs/papers/foundations/submission/ieee-tcss/tcss_public_data_analysis.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

new_36 = '''# Load Andersen et al. (2011) "Stakes Matter in Ultimatum Games" data.
# The .dta also contains pooled Slonim-Roth (SR) and Cameron (C) re-analysis
# rows; the published headline analysis uses Andersen's own subset (IN==1).
ANDERSEN_DTA_CANDIDATES = [
    openicpsr_dir / OPENICPSR_DTA_FILENAME,
    openicpsr_dir / "data" / OPENICPSR_DTA_FILENAME,
]
ANDERSEN_DTA = next((p for p in ANDERSEN_DTA_CANDIDATES if p.exists()), None)
ANDERSEN_INCLUDE_POOLED = False  # set True to use all three studies via DaysW

def load_andersen_data() -> pd.DataFrame | None:
    if ANDERSEN_DTA is None or not ANDERSEN_DTA.exists():
        print("Andersen .dta not found in any of:")
        for c in ANDERSEN_DTA_CANDIDATES:
            print(f"  - {c}")
        print("Place the openICPSR 112485 archive there to enable this section.")
        return None
    df = pd.read_stata(ANDERSEN_DTA, convert_categoricals=False)
    print(f"Loaded {df.shape[0]} rows from {ANDERSEN_DTA.name}")
    print(f"Columns: {list(df.columns)}")
    if ANDERSEN_INCLUDE_POOLED:
        sub = df.copy()
        sub["study"] = np.where(sub["IN"]==1, "Andersen",
                                np.where(sub["SR"]==1, "Slonim-Roth", "Cameron"))
    else:
        sub = df[df["IN"]==1].copy()
        sub["study"] = "Andersen"
    sub["reject"] = 1 - sub["accept"]
    sub = sub.dropna(subset=["stakes", "percent_offer", "accept"])
    print(f"Working sample: n={len(sub)} "
          f"({'pooled three studies via DaysW' if ANDERSEN_INCLUDE_POOLED else 'Andersen IN==1 only'})")
    print(f"Stakes levels: {sorted(sub['stakes'].unique())}")
    return sub

andersen_df = load_andersen_data()
if andersen_df is not None:
    display(andersen_df.head())
'''

nb["cells"][36]["source"] = new_36.splitlines(keepends=True)
for c in nb["cells"]:
    if c["cell_type"] == "code":
        c["outputs"] = []
        c["execution_count"] = None
NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("Patched cell 36 to search ./data/ subdirectory.")
