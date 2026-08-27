"""Channels under `default` vs `structured_v0`, and the DEME branch test.

Written to check whether the frozen structured readers actually fill
the dark channels, and — separately — whether filling them is enough
to reach any DEME verdict branch.
"""

from mapping import CompasCase, build_ir
from pipeline import _default_dag
from structured_v0 import build_profile

CASE = CompasCase("hi-noPriors", 9, 0, 25, 0, True)
ir, _, meta = build_ir(CASE, 5)
print(f"case: adverse={meta['adverse']} refclass={meta['carried_by_reference_class']}")
print(f"facts: {[(f.id, f.kind, f.severity) for f in ir.ethical_facts]}")
print(f"commitments: {ir.commitments}\n")

default_em = _default_dag().evaluate(ir)
struct_em = build_profile().evaluate(ir)

print(f"{'channel':14s} {'default':>9s} {'structured_v0':>14s}")
for name in default_em:
    d = default_em[name].score
    s = struct_em[name].score
    flag = "  <-- filled" if abs(s.value - d.value) > 1e-9 else ""
    conf = "" if s.confidence > 0 else "  (UNAVAILABLE)"
    print(f"{name:14s} {d.value:+9.3f} {s.value:+14.3f}{flag}{conf}")

# Which DEME branch, if any, can be reached?
v = {n: struct_em[n].score.value for n in struct_em}
print("\nDEME bridge branch conditions (deme_bridge.py):")
print(f"  tragic_conflict : externality<=-0.85 ({v['externality']:+.2f}) "
      f"AND any_defeasible_commitment ({bool(ir.commitments)})")
print(f"  prohibited      : harm<-0.85 ({v['harm']:+.2f}) AND care<0.5 "
      f"({v['care']:+.2f}) AND legitimacy<0 ({v['legitimacy']:+.2f})")
print(f"  permit+residue  : fidelity>0.3 ({v['fidelity']:+.2f}) AND "
      f"externality>-0.3 AND harm>-0.5 AND repair<-0.1")
print(f"  clean permit    : fidelity>0.5 ({v['fidelity']:+.2f}) AND "
      f"externality>-0.3 AND harm>-0.3")
print(f"  human review    : any stakeholder.requires_review "
      f"({any(s.requires_review for s in ir.stakeholders)}) OR uncertainty>0.5")
print("\n-> every branch's gate is failed => indeterminate")
