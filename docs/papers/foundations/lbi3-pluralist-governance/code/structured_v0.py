"""`structured_v0` EM profile — channels from structure, not keywords.

Implements `EM-READERS-SPEC.md` §A, frozen before any RQ2 conflict
statistic was computed (Finding I-01's ordering rule).

Each module reads fact `kind` + `severity` only. **No module reads a
fact's description text**, which is the property that keeps the
verdict from being set by our choice of adjectives — asserted by
`test_no_text_dependence` below.

`rights` is deliberately absent: the compiler's fact vocabulary has no
rights kind, and xbse's `rights_respect` encoder failed its
pre-registered bar, so neither path can fill it. It reports
`unavailable` rather than a confident 0.0 — the silent-zero behaviour
is exactly what made Finding I-01 hard to see.
"""

from __future__ import annotations

from erisml_compiler.em_dag.base import EthicalModule
from erisml_compiler.em_dag.modules._helpers import aggregate_negative, facts_of_kind
from erisml_compiler.ir.schemas import CompilerIR, DimensionScore, EMOutput

# channel -> fact kinds, per EM-READERS-SPEC.md §A. Frozen.
CHANNEL_KINDS: dict[str, tuple[str, ...]] = {
    "fairness": ("justice",),
    "legitimacy": ("legitimacy", "coercion"),
    "autonomy": ("consent", "coercion"),
    "epistemic": ("truth", "deception", "uncertainty"),
}


class _StructuredEM(EthicalModule):
    """Aggregate all facts of this channel's kinds by severity."""

    name = "_structured_base"  # overridden by every concrete subclass
    dimension = "_base"
    kinds: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()

    def evaluate(self, ir: CompilerIR, upstream: dict[str, EMOutput]) -> EMOutput:
        facts = []
        for kind in self.kinds:
            facts.extend(facts_of_kind(ir, kind))  # type: ignore[arg-type]
        score = aggregate_negative(
            facts, explanation_prefix=f"{self.name} (structured_v0): "
        )
        return EMOutput(
            module_name=self.name,
            score=score,
            contributing_facts=[f.id for f in facts],
            upstream_dependencies=[],
            notes=f"structured_v0: kinds={list(self.kinds)}; no text read",
        )


class FairnessStructuredEM(_StructuredEM):
    name = "fairness"
    dimension = "fairness_equity"
    kinds = CHANNEL_KINDS["fairness"]


class LegitimacyStructuredEM(_StructuredEM):
    name = "legitimacy"
    dimension = "legitimacy_trust"
    kinds = CHANNEL_KINDS["legitimacy"]


class AutonomyStructuredEM(_StructuredEM):
    name = "autonomy"
    dimension = "autonomy_respect"
    kinds = CHANNEL_KINDS["autonomy"]


class EpistemicStructuredEM(_StructuredEM):
    name = "epistemic"
    dimension = "epistemic_quality"
    kinds = CHANNEL_KINDS["epistemic"]


class RightsUnavailableEM(EthicalModule):
    """`rights` has no structured source and no validated encoder.

    Reports `unavailable` explicitly (confidence 0, uncertainty 1)
    instead of the confident 0.0 that the keyword module emits, so a
    dark channel cannot be mistaken for a clean reading.
    """

    name = "rights"
    dimension = "rights_respect"
    dependencies: tuple[str, ...] = ()

    def evaluate(self, ir: CompilerIR, upstream: dict[str, EMOutput]) -> EMOutput:
        return EMOutput(
            module_name=self.name,
            score=DimensionScore(
                value=0.0,
                confidence=0.0,
                uncertainty=1.0,
                direction="neutral",
                explanation=(
                    "rights: UNAVAILABLE — no rights fact kind in the IR "
                    "vocabulary, and the xbse rights_respect encoder failed "
                    "its pre-registered bar (AUROC 0.509). Not a zero reading."
                ),
                source_spans=[],
            ),
            contributing_facts=[],
            upstream_dependencies=[],
            notes="structured_v0: channel unavailable by construction",
        )


def build_profile():
    """The `structured_v0` EM-DAG: default modules, keyword ones replaced."""
    import erisml_compiler.em_dag.dag as dagmod
    from pathlib import Path

    base = dagmod.load_profile(
        Path(dagmod.__file__).parent / "profiles" / "default.yaml"
    )
    replacements = {
        "fairness": FairnessStructuredEM(),
        "legitimacy": LegitimacyStructuredEM(),
        "autonomy": AutonomyStructuredEM(),
        "epistemic": EpistemicStructuredEM(),
        "rights": RightsUnavailableEM(),
    }
    # EMDAG keeps instances in `_modules` (name -> instance); `.modules`
    # is the name list.
    instances = [base._modules[n] for n in base._modules]
    modules = [replacements.get(m.name, m) for m in instances]
    return dagmod.EMDAG(modules=modules, name="structured_v0")


def test_no_text_dependence() -> list[str]:
    """The spec's load-bearing property: descriptions must not matter.

    Same IR twice, with every fact description replaced by unrelated
    text. Any channel whose value moves is reading text and violates
    the spec.
    """
    import copy

    from mapping import CompasCase, build_ir

    dag = build_profile()
    failures: list[str] = []
    for case in (
        CompasCase("t1", 9, 0, 25, 0, True),
        CompasCase("t2", 9, 8, 40, 0, True),
        CompasCase("t3", 2, 0, 25, 0, True),
        CompasCase("t4", 6, 0, 30, 2, False),
    ):
        for threshold in (5, 8):
            ir_a, _, _ = build_ir(case, threshold)
            ir_b = copy.deepcopy(ir_a)
            for i, f in enumerate(ir_b.ethical_facts):
                ir_b.ethical_facts[i] = f.model_copy(
                    update={"description": f"unrelated filler text {i} lorem ipsum"}
                )
            a, b = dag.evaluate(ir_a), dag.evaluate(ir_b)
            for name in a:
                va, vb = a[name].score.value, b[name].score.value
                if abs(va - vb) > 1e-12:
                    failures.append(
                        f"{case.case_id}@T{threshold} channel {name}: "
                        f"{va:+.3f} -> {vb:+.3f} when descriptions changed"
                    )
    return failures


if __name__ == "__main__":
    fails = test_no_text_dependence()
    print("no-text-dependence check:",
          "PASS" if not fails else "FAIL")
    for f in fails:
        print("  ", f)
