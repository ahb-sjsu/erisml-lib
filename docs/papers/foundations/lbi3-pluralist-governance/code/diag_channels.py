"""Diagnostic: what moral-vector channels do the mapped IRs produce?"""

from mapping import CompasCase, build_ir
from pipeline import _default_dag

CASES = [
    ("lo-noPriors", CompasCase("a", 2, 0, 25, 0, True)),
    ("hi-noPriors", CompasCase("b", 9, 0, 25, 0, True)),
    ("hi-manyPriors", CompasCase("c", 9, 8, 40, 0, True)),
]

dag = _default_dag()

for label, case in CASES:
    ir, sub, meta = build_ir(case, 5)
    em = dag.evaluate(ir)
    print(f"\n--- {label} (adverse={meta['adverse']}, "
          f"refclass={meta['carried_by_reference_class']})")
    for mod_name, out in em.items():
        s = out.score
        print(f"   {mod_name:14s} value={s.value:+.3f} conf={s.confidence:.2f} "
              f"unc={s.uncertainty:.2f}  {s.explanation[:52]}")
