"""Run the four ethical projections over mapped COMPAS cases (RQ2).

Conflict is measured on the compiler's own normalized polarity
(`permit | forbid | escalate | neutral`), which exists precisely so
cross-framework comparison does not fire on vocabulary differences.

Two statistics, both reported:
  * `hard_conflict` — some projection permits while another forbids.
    This is the "no scalar verdict can be right" case and is primary.
  * `any_disagree`  — polarities are not unanimous (weaker).
"""

from __future__ import annotations

from typing import Any

from erisml_compiler.projections.care_ethics import CareEthicsProjection
from erisml_compiler.projections.consequentialist import ConsequentialistProjection
from erisml_compiler.projections.deontic import DeonticProjection
from erisml_compiler.projections.virtue import VirtueProjection

from mapping import CompasCase, build_ir

def _default_dag():
    """The compiler's bundled default EM-DAG profile.

    Using the bundled default rather than a hand-tuned profile is
    deliberate: the ethos weights are not ours to choose for a
    governance claim, and the two alternative profiles shipped with the
    compiler (AITA / Dear Abby Social-Chem fits) carry documented
    population biases that have no business deciding a criminal-justice
    verdict. Profile sensitivity is a declared robustness axis.
    """
    from pathlib import Path

    import erisml_compiler.em_dag.dag as dagmod

    profile = (
        Path(dagmod.__file__).parent / "profiles" / "default.yaml"
    )
    return dagmod.load_profile(profile)


EM_PROFILE = "default.yaml"
_DEONTIC = DeonticProjection()
_CONSEQ = ConsequentialistProjection(dag=_default_dag())
_VIRTUE = VirtueProjection()
_CARE = CareEthicsProjection()


def _safe(proj, substrate, **kw) -> tuple[str, str]:
    """(verdict, polarity); projections that cannot run return `neutral`."""
    try:
        r = proj.project(substrate, **kw)
        return r.verdict, r.polarity
    except Exception as exc:  # recorded, never silently dropped
        return f"error:{type(exc).__name__}", "neutral"


def evaluate(
    case: CompasCase, threshold: int, *, conduct_floor: int = 1
) -> dict[str, Any]:
    ir, substrate, meta = build_ir(case, threshold, conduct_floor=conduct_floor)

    verdicts: dict[str, tuple[str, str]] = {
        "deontic": _safe(_DEONTIC, substrate, graph=None),
        "consequentialist": _safe(_CONSEQ, substrate, ir=ir, graph=None),
        "virtue": _safe(_VIRTUE, substrate),
        "care": _safe(_CARE, substrate),
    }

    pols = {k: v[1] for k, v in verdicts.items()}
    signed = {p for p in pols.values() if p in ("permit", "forbid")}
    hard = signed == {"permit", "forbid"}
    any_dis = len(set(pols.values())) > 1

    dc = {pols["deontic"], pols["consequentialist"]}
    return {
        **meta,
        "verdicts": {k: v[0] for k, v in verdicts.items()},
        "polarities": pols,
        "hard_conflict": hard,
        "any_disagree": any_dis,
        # the P2 pair specifically
        "dc_hard_conflict": dc == {"permit", "forbid"},
        "dc_disagree": pols["deontic"] != pols["consequentialist"],
    }


def evaluate_many(
    cases: list[CompasCase], threshold: int, *, conduct_floor: int = 1
) -> list[dict[str, Any]]:
    return [evaluate(c, threshold, conduct_floor=conduct_floor) for c in cases]
