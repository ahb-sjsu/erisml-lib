from __future__ import annotations

from dataclasses import dataclass
from typing import List

from erisml.ethics.facts import EthicalFacts
from erisml.ethics.judgement import EthicalJudgement, Verdict
from erisml.ethics.modules.base import EthicsModule


@dataclass
class CaseStudy1TriageEM(EthicsModule):
    """
    Example triage ethics module for Case Study 1.

    Uses only EthicalFacts, never raw ICD codes or clinical data. It:
      - Hard-forbids options that violate rights or explicit rules.
      - Computes a weighted composite score based on benefit, harm, urgency,
        priority for the disadvantaged, and procedural legitimacy.
      - Applies an epistemic penalty: high uncertainty, low evidence quality,
        and novel situations reduce the normative score.
    """

    em_name: str = "case_study_1_triage"
    stakeholder: str = "patients_and_public"

    # Weights over ethical dimensions (summing to ~1.0)
    w_benefit: float = 0.35
    w_harm: float = 0.25
    w_urgency: float = 0.20
    w_disadvantaged: float = 0.15
    w_procedural: float = 0.05

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        # 1. Hard deontic veto: rights / explicit rule violations → forbid.
        rd = facts.rights_and_duties
        if rd.violates_rights or rd.violates_explicit_rule:
            veto_reasons: List[str] = [
                (
                    "Option is forbidden because it violates fundamental rights "
                    "and/or explicit rules or regulations."
                )
            ]
            if rd.violates_rights:
                veto_reasons.append("• violates_rights = True")
            if rd.violates_explicit_rule:
                veto_reasons.append("• violates_explicit_rule = True")

            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="forbid",
                normative_score=0.0,
                reasons=veto_reasons,
                metadata={"kind": "hard_veto"},
            )

        # 2. Base composite score from EthicalFacts.
        c = facts.consequences
        j = facts.justice_and_fairness
        p = facts.procedural_and_legitimacy

        # If procedural block missing, treat as neutral.
        procedural_score = 0.5
        if p is not None:
            procedural_score = 0.0
            if p.followed_approved_procedure:
                procedural_score += 0.5
            if p.stakeholders_consulted:
                procedural_score += 0.25
            if p.decision_explainable_to_public:
                procedural_score += 0.25

        benefit_term = c.expected_benefit
        harm_term = 1.0 - c.expected_harm  # lower harm → higher score
        urgency_term = c.urgency
        disadvantaged_term = 1.0 if j.prioritizes_most_disadvantaged else 0.0

        base_score = (
            self.w_benefit * benefit_term
            + self.w_harm * harm_term
            + self.w_urgency * urgency_term
            + self.w_disadvantaged * disadvantaged_term
            + self.w_procedural * procedural_score
        )

        # 3. Epistemic penalty: reduce score when uncertainty is high,
        #    evidence quality is low, or situation is novel.
        es = facts.epistemic_status
        epistemic_factor = 1.0
        epistemic_reason = None

        if es is not None:
            # Start with a penalty proportional to uncertainty.
            #   uncertainty_level in [0, 1]
            #   0.0  -> multiplier ~ 1.0
            #   1.0  -> multiplier ~ 0.6
            base_factor = 1.0 - 0.4 * es.uncertainty_level
            base_factor = max(0.0, min(1.0, base_factor))

            # Adjust for evidence quality.
            quality_mult_map = {
                "high": 1.0,
                "medium": 0.95,
                "low": 0.85,
            }
            quality_mult = quality_mult_map.get(es.evidence_quality.lower(), 0.9)

            factor = base_factor * quality_mult

            # Novel / out-of-distribution situations get a further 10% penalty.
            if es.novel_situation_flag:
                factor *= 0.9

            epistemic_factor = max(0.0, min(1.0, factor))

            epistemic_reason = (
                "Epistemic penalty applied: uncertainty_level="
                f"{es.uncertainty_level:.2f}, evidence_quality="
                f"{es.evidence_quality}, novel_situation_flag="
                f"{es.novel_situation_flag}. "
                f"Multiplier={epistemic_factor:.2f}."
            )

        score = base_score * epistemic_factor

        # 4. Map score → verdict.
        if score >= 0.8:
            verdict: Verdict = "strongly_prefer"
        elif score >= 0.6:
            verdict = "prefer"
        elif score >= 0.4:
            verdict = "neutral"
        elif score >= 0.2:
            verdict = "avoid"
        else:
            verdict = "forbid"

        reasons: List[str] = [
            (
                "Composite triage judgement based on benefit, harm, urgency, "
                "priority for the disadvantaged, autonomy, and procedural legitimacy."
            )
        ]
        if epistemic_reason is not None:
            reasons.append(epistemic_reason)

        return EthicalJudgement(
            option_id=facts.option_id,
            em_name=self.em_name,
            stakeholder=self.stakeholder,
            verdict=verdict,
            normative_score=score,
            reasons=reasons,
            metadata={
                "kind": "triage_em",
                "epistemic_factor": epistemic_factor,
                "base_score": base_score,
            },
        )


@dataclass
class RightsFirstEM(EthicsModule):
    """
    Simple rights-compliance EM.

    - Forbids any option that violates rights or explicit rules.
    - Otherwise returns a fixed 'prefer' with a high normative score.
    This is intended to plug into governance as a veto-capable EM.
    """

    em_name: str = "rights_first_compliance"
    stakeholder: str = "patients_and_public"

    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        rd = facts.rights_and_duties
        reasons: List[str] = []
        verdict: Verdict
        score: float

        if rd.violates_rights or rd.violates_explicit_rule:
            verdict = "forbid"
            score = 0.0
            reasons.append(
                "Forbid: option violates rights and/or explicit rules, "
                "which take precedence over other considerations."
            )
            if rd.violates_rights:
                reasons.append("• violates_rights = True")
            if rd.violates_explicit_rule:
                reasons.append("• violates_explicit_rule = True")
        else:
            verdict = "prefer"
            score = 0.8
            reasons.append(
                "Rights and explicit rules are respected; "
                "no deontic veto from this module."
            )

        return EthicalJudgement(
            option_id=facts.option_id,
            em_name=self.em_name,
            stakeholder=self.stakeholder,
            verdict=verdict,
            normative_score=score,
            reasons=reasons,
            metadata={"kind": "rights_first"},
        )


__all__ = ["CaseStudy1TriageEM", "RightsFirstEM"]