"""DoctrinalProjection — jurisdictional doctrine as gates (LBI-3 RQ1).

A fifth projection alongside erisml-compiler's four ethical-theory
projections. Doctrine is not a moral theory: it is positive law that
constrains which theory-verdicts an institution may act on, so it
lives beside the Kantian/consequentialist/virtue/care readings rather
than inside them.

**Research code, not a released component.** The doctrinal content is
UNVERIFIED (see CONSTRAINT-SUITE.md §7: quote-verification against
881 N.W.2d 749 and legal review are both open), which is why this
does not ship in the `erisml-compiler` package.

Three properties are load-bearing and tested by the vector set:

1. *No ad-hoc logic.* Gates are general functions of a
   `DecisionRecord` and a data-only `JurisdictionProfile`. No gate
   may reference a specific case, defendant, or vector id.
2. *Undetermined is not compliant.* A gate whose required record
   fields are missing does not fire, but it also cannot license a
   `permissible` verdict — an incomplete record cannot certify
   compliance. This is the failure mode most likely to matter in
   deployment.
3. *Profiles, not forks.* Changing jurisdiction changes data, never
   code.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from erisml_compiler.projections.base import (
    GateFinding,
    Projection,
    ProjectionResult,
)

AttributePolicy = Literal["foreclosed", "permitted", "permitted_with_justification"]
UNDETERMINED = "undetermined"


class JurisdictionProfile(BaseModel):
    """Doctrine as data. Swapping this must change verdicts without
    changing a line of gate code (tested by V-J1/V-J2)."""

    model_config = ConfigDict(frozen=True)

    id: str
    source: str
    required_warnings: tuple[str, ...] = ()
    determinative_use_forbidden: bool = True
    attribute_policy: dict[str, AttributePolicy] = Field(default_factory=dict)
    sanctioned_decision_points: tuple[str, ...] = ()
    population_validation_required: bool = True
    contestability_required: bool = True


class DecisionRecord(BaseModel):
    """One RAI-assisted decision, as an auditor could obtain it.

    Every field an external auditor may be unable to observe is
    `None`-able, and `None` means *unobserved*, never *absent*. That
    distinction is the whole point of the auditability-gap endpoint
    (E4): the public COMPAS corpus supplies the instrument-side
    fields and none of the court-side ones.
    """

    model_config = ConfigDict(frozen=True)

    record_id: str
    instrument: str
    score: float | None = None
    decision_point: str | None = None
    instrument_inputs: tuple[str, ...] | None = None
    # court-side fields — typically unobservable from public data
    warnings_given: tuple[str, ...] | None = None
    stated_basis: tuple[str, ...] | None = None
    asserts_individual_prediction: bool | None = None
    defendant_notified: bool | None = None
    contest_opportunity: bool | None = None
    validated_populations: tuple[str, ...] | None = None
    deployment_population: str | None = None


def _undetermined(name: str, missing: list[str], severity: str) -> GateFinding:
    """A gate that cannot be evaluated. Does not fire; does not clear."""
    return GateFinding(
        name=name,
        passed=True,
        reason=f"Undetermined: record lacks {', '.join(missing)}",
        severity=severity,  # type: ignore[arg-type]
        detail={"result": UNDETERMINED, "missing": missing},
    )


def is_undetermined(f: GateFinding) -> bool:
    return f.detail.get("result") == UNDETERMINED


class DoctrinalProjection(Projection):
    """Jurisdictional constraints on RAI use, as categorical gates."""

    framework = "doctrinal_jurisdictional"

    def project(  # type: ignore[override]
        self,
        substrate: Any = None,
        *,
        graph: Any = None,
        record: DecisionRecord | None = None,
        profile: JurisdictionProfile | None = None,
        **kwargs: Any,
    ) -> ProjectionResult:
        if record is None or profile is None:
            raise ValueError("DoctrinalProjection requires `record` and `profile`")

        findings = [
            self._d1_required_warnings(record, profile),
            self._d2_not_determinative(record, profile),
            self._d3_group_to_individual(record, profile),
            self._d4_validated_for_population(record, profile),
            self._d5_purpose_fit(record, profile),
            self._d6_contestability(record, profile),
            self._d7_attribute_policy(record, profile),
        ]

        fired = [f for f in findings if not f.passed]
        undet = [f for f in findings if is_undetermined(f)]
        grave = [f for f in fired if f.severity in ("grave", "catastrophic")]
        moderate = [f for f in fired if f.severity == "moderate"]

        if grave:
            verdict = "forbidden"
        elif moderate:
            verdict = "requires_review"
        elif undet:
            # Property 2: an incomplete record cannot certify compliance.
            verdict = "requires_review"
        else:
            verdict = "permissible"

        return ProjectionResult(
            framework=self.framework,
            verdict=verdict,
            confidence=1.0,
            findings=findings,
            framework_specific={
                "profile_id": profile.id,
                "n_fired": len(fired),
                "n_undetermined": len(undet),
                "undetermined_gates": [f.name for f in undet],
                "auditable_fraction": (len(findings) - len(undet)) / len(findings),
            },
            metadata={
                "projection_version": "v0_research_unverified_doctrine",
                "source": profile.source,
            },
        )

    # ------------------------------------------------------------------ D1
    def _d1_required_warnings(
        self, r: DecisionRecord, p: JurisdictionProfile
    ) -> GateFinding:
        name = "required_warnings_present"
        if not p.required_warnings:
            return GateFinding(
                name=name, passed=True, reason="Profile requires no warnings",
                severity="grave",
            )
        if r.warnings_given is None:
            return _undetermined(name, ["warnings_given"], "grave")
        missing = [w for w in p.required_warnings if w not in r.warnings_given]
        if missing:
            return GateFinding(
                name=name, passed=False,
                reason=f"Required warning(s) absent from record: {', '.join(missing)}",
                severity="grave", detail={"missing_warnings": missing},
            )
        return GateFinding(
            name=name, passed=True,
            reason=f"All {len(p.required_warnings)} required warnings present",
            severity="grave",
        )

    # ------------------------------------------------------------------ D2
    def _d2_not_determinative(
        self, r: DecisionRecord, p: JurisdictionProfile
    ) -> GateFinding:
        name = "not_determinative"
        if not p.determinative_use_forbidden:
            return GateFinding(
                name=name, passed=True,
                reason="Profile does not forbid determinative use", severity="catastrophic",
            )
        if r.stated_basis is None:
            return _undetermined(name, ["stated_basis"], "catastrophic")
        non_score = [b for b in r.stated_basis if b != "risk_score"]
        if "risk_score" in r.stated_basis and not non_score:
            return GateFinding(
                name=name, passed=False,
                reason="Stated basis for the decision reduces to the risk score alone",
                severity="catastrophic", detail={"stated_basis": list(r.stated_basis)},
            )
        return GateFinding(
            name=name, passed=True,
            reason=f"Decision rests on {len(non_score)} basis element(s) beyond the score",
            severity="catastrophic",
        )

    # ------------------------------------------------------------------ D3
    def _d3_group_to_individual(
        self, r: DecisionRecord, p: JurisdictionProfile
    ) -> GateFinding:
        name = "group_to_individual_inference"
        if r.asserts_individual_prediction is None:
            return _undetermined(name, ["asserts_individual_prediction"], "grave")
        if r.asserts_individual_prediction:
            return GateFinding(
                name=name, passed=False,
                reason="Record asserts an individualized prediction from a group-based score",
                severity="grave",
            )
        return GateFinding(
            name=name, passed=True,
            reason="Record does not convert the group statistic into an individual claim",
            severity="grave",
        )

    # ------------------------------------------------------------------ D4
    def _d4_validated_for_population(
        self, r: DecisionRecord, p: JurisdictionProfile
    ) -> GateFinding:
        name = "validated_for_population"
        if not p.population_validation_required:
            return GateFinding(
                name=name, passed=True, reason="Profile requires no local validation",
                severity="moderate",
            )
        missing = [
            f for f, v in (
                ("validated_populations", r.validated_populations),
                ("deployment_population", r.deployment_population),
            ) if v is None
        ]
        if missing:
            return _undetermined(name, missing, "moderate")
        assert r.validated_populations is not None
        if r.deployment_population not in r.validated_populations:
            return GateFinding(
                name=name, passed=False,
                reason=(
                    f"Instrument not validated for deployment population "
                    f"'{r.deployment_population}'"
                ),
                severity="moderate",
                detail={"validated_for": list(r.validated_populations)},
            )
        return GateFinding(
            name=name, passed=True,
            reason=f"Validated for deployment population '{r.deployment_population}'",
            severity="moderate",
        )

    # ------------------------------------------------------------------ D5
    def _d5_purpose_fit(self, r: DecisionRecord, p: JurisdictionProfile) -> GateFinding:
        name = "purpose_fit"
        if not p.sanctioned_decision_points:
            return GateFinding(
                name=name, passed=True, reason="Profile sanctions all decision points",
                severity="grave",
            )
        if r.decision_point is None:
            return _undetermined(name, ["decision_point"], "grave")
        if r.decision_point not in p.sanctioned_decision_points:
            return GateFinding(
                name=name, passed=False,
                reason=(
                    f"Decision point '{r.decision_point}' outside the instrument's "
                    f"sanctioned use under profile {p.id}"
                ),
                severity="grave",
                detail={"sanctioned": list(p.sanctioned_decision_points)},
            )
        return GateFinding(
            name=name, passed=True,
            reason=f"Decision point '{r.decision_point}' is sanctioned",
            severity="grave",
        )

    # ------------------------------------------------------------------ D6
    def _d6_contestability(
        self, r: DecisionRecord, p: JurisdictionProfile
    ) -> GateFinding:
        name = "contestability"
        if not p.contestability_required:
            return GateFinding(
                name=name, passed=True, reason="Profile requires no contest opportunity",
                severity="grave",
            )
        missing = [
            f for f, v in (
                ("defendant_notified", r.defendant_notified),
                ("contest_opportunity", r.contest_opportunity),
            ) if v is None
        ]
        if missing:
            return _undetermined(name, missing, "grave")
        if not (r.defendant_notified and r.contest_opportunity):
            lacks = []
            if not r.defendant_notified:
                lacks.append("notice of the score")
            if not r.contest_opportunity:
                lacks.append("opportunity to contest its inputs")
            return GateFinding(
                name=name, passed=False,
                reason=f"Defendant lacked {' and '.join(lacks)}",
                severity="grave",
            )
        return GateFinding(
            name=name, passed=True,
            reason="Defendant had notice and an opportunity to contest the inputs",
            severity="grave",
        )

    # ------------------------------------------------------------------ D7
    def _d7_attribute_policy(
        self, r: DecisionRecord, p: JurisdictionProfile
    ) -> GateFinding:
        name = "attribute_policy"
        if r.instrument_inputs is None:
            return _undetermined(name, ["instrument_inputs"], "catastrophic")
        foreclosed = [
            a for a in r.instrument_inputs
            if p.attribute_policy.get(a) == "foreclosed"
        ]
        if foreclosed:
            return GateFinding(
                name=name, passed=False,
                reason=(
                    f"Instrument takes attribute(s) foreclosed under {p.id}: "
                    f"{', '.join(foreclosed)}"
                ),
                severity="catastrophic",
                subjects=foreclosed,
                detail={"policy": dict(p.attribute_policy)},
            )
        flagged = [
            a for a in r.instrument_inputs
            if p.attribute_policy.get(a) == "permitted_with_justification"
        ]
        return GateFinding(
            name=name, passed=True,
            reason=(
                "No foreclosed attribute among instrument inputs"
                + (f"; justification required for: {', '.join(flagged)}" if flagged else "")
            ),
            severity="catastrophic",
            detail={"requires_justification": flagged},
        )


# --------------------------------------------------------------------------
# Profiles (DATA — doctrine unverified, see CONSTRAINT-SUITE.md §7)
# --------------------------------------------------------------------------

WI_2016_LOOMIS = JurisdictionProfile(
    id="wi-2016-loomis",
    source=(
        "State v. Loomis, 881 N.W.2d 749 (Wis. 2016), cert. denied, "
        "137 S. Ct. 2290 (2017) — ENCODING UNVERIFIED, pending pin-cite "
        "verification and legal review"
    ),
    required_warnings=(
        "proprietary_methodology",
        "group_based_not_individual",
        "accuracy_questioned_across_groups",
        "not_validated_for_local_population",
        "not_designed_for_this_decision_point",
    ),
    determinative_use_forbidden=True,
    attribute_policy={
        "race": "foreclosed",
        "sex": "permitted_with_justification",
        "age": "permitted",
        "priors_count": "permitted",
    },
    sanctioned_decision_points=("post_sentencing_corrections",),
    population_validation_required=True,
    contestability_required=True,
)

# Counterfactual profile used ONLY to test that doctrine lives in data
# (V-J2). It is not a claim about any real jurisdiction.
PERMISSIVE_CONTROL = WI_2016_LOOMIS.model_copy(
    update={
        "id": "control-permissive",
        "source": "Synthetic control profile — not a real jurisdiction",
        "attribute_policy": {**WI_2016_LOOMIS.attribute_policy, "race": "permitted"},
    }
)
