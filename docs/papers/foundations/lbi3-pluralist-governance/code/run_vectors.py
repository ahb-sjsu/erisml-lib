"""Run the 31 preregistered vectors and check the RQ1/E1 bar.

The bar has two halves and BOTH must hold:

  (a) 31/31 exact match on per-gate outcome and verdict;
  (b) zero case-, vector-, or defendant-specific identifiers inside
      the gate logic — the half that actually tests "no ad-hoc logic",
      since (a) alone could be passed by hard-coding.

Run:  python run_vectors.py            (from this directory)
Exit code 0 iff both halves hold.
"""

from __future__ import annotations

import inspect
import json
import re
import sys

from doctrinal import DoctrinalProjection, is_undetermined
from vectors import GATES, VECTORS


def outcome(finding) -> str:
    if is_undetermined(finding):
        return "undet"
    return "pass" if finding.passed else "fire"


def check_vectors() -> tuple[int, list[dict]]:
    proj = DoctrinalProjection()
    passed, failures = 0, []
    for v in VECTORS:
        result = proj.project(record=v.record, profile=v.profile)
        got = {f.name: outcome(f) for f in result.findings}
        gate_ok = all(got.get(g) == v.expect[g] for g in GATES)
        verdict_ok = v.expect_verdict is None or result.verdict == v.expect_verdict
        if gate_ok and verdict_ok:
            passed += 1
        else:
            failures.append({
                "vector": v.vid,
                "class": v.klass,
                "note": v.note,
                "gate_diff": {
                    g: {"expected": v.expect[g], "got": got.get(g)}
                    for g in GATES if got.get(g) != v.expect[g]
                },
                "verdict": {"expected": v.expect_verdict, "got": result.verdict},
            })
    return passed, failures


# Names that must never appear inside the gate logic. Profiles are DATA
# and are excluded from this scan by construction (only the projection
# class's source is scanned).
_FORBIDDEN = re.compile(
    r"\bV-[PFUNJCA]\d|loomis|compas|broward|northpointe|equivant|defendant_id",
    re.IGNORECASE,
)


def check_no_ad_hoc_logic() -> list[str]:
    src = inspect.getsource(DoctrinalProjection)
    return sorted({m.group(0) for m in _FORBIDDEN.finditer(src)})


def main() -> int:
    n_pass, failures = check_vectors()
    leaks = check_no_ad_hoc_logic()
    total = len(VECTORS)

    print(f"(a) vectors: {n_pass}/{total} exact match")
    for f in failures:
        print(f"    FAIL {f['vector']} ({f['class']}): {f['note']}")
        for g, d in f["gate_diff"].items():
            print(f"         gate {g}: expected {d['expected']}, got {d['got']}")
        if f["verdict"]["expected"] != f["verdict"]["got"]:
            print(f"         verdict: expected {f['verdict']['expected']}, "
                  f"got {f['verdict']['got']}")
    print(f"(b) ad-hoc-logic scan of gate source: "
          f"{'CLEAN' if not leaks else 'LEAKS ' + ', '.join(leaks)}")

    ok = (n_pass == total) and not leaks
    print(f"\nE1 BAR: {'PASS' if ok else 'FAIL'}")

    with open("vector_results.json", "w") as fh:
        json.dump(
            {"n_pass": n_pass, "n_total": total, "failures": failures,
             "ad_hoc_leaks": leaks, "bar_met": ok},
            fh, indent=1,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
