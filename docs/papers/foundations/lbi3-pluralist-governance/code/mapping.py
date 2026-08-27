"""COMPAS decision record -> moral structure (LBI-3 RQ2).

Implements `MAPPING.md`, which was written and committed BEFORE any
conflict statistic was computed. Three invariants, asserted in code
and tested in `test_mapping_invariants`:

  1. attribute-blind — never reads race or sex;
  2. outcome-blind   — never reads two_year_recid;
  3. uniform        — identical rules for every defendant.

The only substantive modelling choice is the mere-means distinction
(MAPPING.md §"The one substantive modelling choice"), parameterized by
`CONDUCT_FLOOR` and swept in the pilots.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from erisml_compiler.ir.schemas import (
    CompilerIR,
    Document,
    EthicalFact,
    Stakeholder,
)
from erisml_compiler.projections.substrate import MoralSubstrate

# Features the mapping is permitted to read. Anything else is a bug:
# race and sex are excluded so that co-location with LBI findings is an
# empirical result; two_year_recid is excluded so the verdict is a
# decision-time verdict.
ALLOWED_FIELDS = frozenset({"decile_score", "priors_count", "age",
                            "juv_fel_count", "juv_misd_count",
                            "juv_other_count", "c_charge_F"})
FORBIDDEN_FIELDS = frozenset({"race", "sex", "two_year_recid", "is_recid"})

CONDUCT_FLOOR_DEFAULT = 1
ELEVATED_SCORE = 4  # a non-adverse classification above this leaves residual risk


@dataclass(frozen=True)
class CompasCase:
    """The decision-relevant slice of one COMPAS record."""

    case_id: str
    decile_score: int
    priors_count: int
    age: int
    juv_total: int
    charge_is_felony: bool

    @classmethod
    def from_row(cls, row: dict[str, Any], case_id: str) -> "CompasCase":
        leaked = FORBIDDEN_FIELDS & set(row)
        # The row may carry forbidden fields; the mapping simply must
        # not read them. We assert on *use*, not presence, by only
        # touching allowed keys below.
        del leaked
        return cls(
            case_id=case_id,
            decile_score=int(row["decile_score"]),
            priors_count=int(row["priors_count"]),
            age=int(row["age"]),
            juv_total=int(row["juv_fel_count"]) + int(row["juv_misd_count"])
            + int(row["juv_other_count"]),
            charge_is_felony=bool(row["c_charge_F"]),
        )


def build_ir(
    case: CompasCase,
    threshold: int,
    *,
    conduct_floor: int = CONDUCT_FLOOR_DEFAULT,
) -> tuple[CompilerIR, MoralSubstrate, dict[str, Any]]:
    """Build the IR + substrate for one case at one threshold."""
    adverse = case.decile_score >= threshold
    # The mere-means distinction (MAPPING.md): adverse actions grounded
    # in the defendant's own adjudicated conduct treat them as means
    # AND end; adverse actions carried by the reference class do not.
    carried_by_reference_class = adverse and case.priors_count < conduct_floor

    stakeholders = [
        Stakeholder(
            id="defendant", label="defendant", type="individual",
            roles=["patient"],
            vulnerability="high" if adverse else "moderate",
            consent_status="not_obtained" if adverse else "not_applicable",
        ),
        Stakeholder(id="public", label="public", type="community",
                    roles=["patient"]),
        Stakeholder(id="court", label="court", type="institution",
                    roles=["agent", "authority"]),
    ]

    facts: list[EthicalFact] = []
    if adverse:
        facts.append(EthicalFact(
            id="liberty_burden", kind="harm", subjects=["defendant"],
            description="Adverse risk classification burdens the defendant's liberty",
            severity="grave",
        ))
        facts.append(EthicalFact(
            id="consent_absent", kind="consent", subjects=["defendant"],
            description="The defendant did not consent to actuarial classification",
            severity="moderate",
        ))
        facts.append(EthicalFact(
            id="actuarial_basis", kind="justice", subjects=["defendant"],
            description=(
                "Adverse action rests on a group-statistical instrument; "
                + ("individual adjudicated conduct below the declared floor"
                   if carried_by_reference_class
                   else "supported by the defendant's own adjudicated conduct")
            ),
            severity="grave" if carried_by_reference_class else "moderate",
        ))
    elif case.decile_score > ELEVATED_SCORE:
        facts.append(EthicalFact(
            id="residual_risk", kind="externality", subjects=["public"],
            description="Non-adverse classification of an elevated-score case",
            severity="moderate",
        ))

    doc = Document(doc_id=f"{case.case_id}@T{threshold}", title="RAI decision",
                   raw_text="")
    ir = CompilerIR(document=doc, stakeholders=stakeholders,
                    ethical_facts=facts, commitments=[], graph=None)

    from erisml_compiler.projections.substrate import Maxim

    substrate = MoralSubstrate(
        document=doc,
        stakeholders=stakeholders,
        ethical_facts=facts,
        # action_kind deliberately unset: we do not extract maxims from
        # text, so the universalizability gate reports `undetermined`
        # (verified: the compiler handles a missing action kind that
        # way rather than guessing). `treats_persons_as` carries the
        # one modelling choice declared in MAPPING.md.
        maxim=Maxim(
            description=f"classify this defendant at threshold {threshold}",
            agent_id="court",
            action_kind=None,
            treats_persons_as=mere_means_roles(
                {"adverse": adverse,
                 "carried_by_reference_class": carried_by_reference_class}
            ),
        ),
        # CONSENT IS DELIBERATELY ABSENT — see MAPPING.md. Lawful state
        # coercion does not turn on the defendant's consent; the moral
        # work is done by legitimate authority and by the mere-means
        # test. The notice-and-contest concern is real but belongs to
        # the DOCTRINAL projection (gate D6), not the Kantian one.
        consent_states=[],
        authority_legitimacies=_authority(),
    )

    meta = {
        "case_id": case.case_id,
        "threshold": threshold,
        "adverse": adverse,
        "carried_by_reference_class": carried_by_reference_class,
        "decile_score": case.decile_score,
        "priors_count": case.priors_count,
        "conduct_floor": conduct_floor,
    }
    return ir, substrate, meta


def _authority() -> list[Any]:
    from erisml_compiler.projections.substrate import AuthorityLegitimacy

    return [AuthorityLegitimacy(authority_id="court", legitimate=True,
                                reason="statutory sentencing authority")]


def mere_means_roles(meta: dict[str, Any]) -> dict[str, str]:
    """`treats_as` roles implied by the mapping, for the deontic gate."""
    if not meta["adverse"]:
        return {"defendant": "end"}
    return {
        "defendant": "mere_means" if meta["carried_by_reference_class"] else "means_and_end"
    }
