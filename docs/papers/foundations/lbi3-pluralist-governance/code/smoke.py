"""Smoke test: does the RQ2 pipeline run, and does it vary?"""
import time

from mapping import CompasCase
from pipeline import evaluate

CASES = [
    CompasCase("lo-noPriors", 2, 0, 25, 0, True),
    CompasCase("hi-noPriors", 9, 0, 25, 0, True),
    CompasCase("hi-manyPriors", 9, 8, 40, 0, True),
    CompasCase("mid-noPriors", 5, 0, 30, 1, False),
    CompasCase("mid-manyPriors", 5, 6, 35, 0, False),
]

t0 = time.perf_counter()
n = 0
for c in CASES:
    for T in (5, 8):
        r = evaluate(c, T)
        n += 1
        print(f"{c.case_id:15s} T={T} adv={str(r['adverse']):5s} "
              f"refclass={str(r['carried_by_reference_class']):5s} "
              f"hard={str(r['hard_conflict']):5s} dc_hard={str(r['dc_hard_conflict']):5s}")
        print(f"                 verdicts={r['verdicts']}")
        print(f"                 polarities={r['polarities']}")
print(f"\nper-eval ms: {(time.perf_counter() - t0) * 1000 / n:.1f}")
