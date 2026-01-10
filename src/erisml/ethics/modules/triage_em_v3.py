# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
TriageEMV3: Triage ethics module with per-party assessment.

This is a Tier 2 (Rights/Fairness) EM that extends the Case Study 1
Triage EM to support distributed multi-party ethics assessment via
MoralTensor. It computes weighted composite scores for each affected
party with epistemic penalties.

Key V3 Features:
- Per-party harm/benefit tracking with vulnerability weighting
- Per-party urgency and resource allocation fairness
- Per-party epistemic penalty computation
- Distributional fairness metrics (Gini, Rawlsian maximin)

Version: 3.0.0 (DEME V3 - Sprint 6)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np

from erisml.ethics.facts import EthicalFacts
from erisml.ethics.judgement import Verdict
from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.moral_tensor import MoralTensor
from erisml.ethics.modules.base_v3 import BaseEthicsModuleV3, aggregate_party_verdicts
from erisml.ethics.modules.registry import EMRegistry

if TYPE_CHECKING:
    from erisml.ethics.facts_v3 import EthicalFactsV3


@EMRegistry.register(
    tier=2,
    default_weight=5.0,
    veto_capable=True,
    description="Triage ethics with per-party distributional assessment (V3)",
    tags=["triage", "fairness", "distributional", "v3", "healthcare"],
)
@dataclass
class TriageEMV3(BaseEthicsModuleV3):
    """
    Triage EM with per-party distributional ethics assessment.

    Extends CaseStudy1TriageEM to V3 with:
    - Per-party composite scores based on harm, benefit, urgency
    - Distributional fairness across parties (Gini, maximin)
    - Per-party epistemic penalties
    - Vulnerability-adjusted prioritization

    Hard vetoes (per-party):
    - Rights violations for specific parties
    - Explicit rule violations

    Soft penalties (per-party):
    - High harm relative to benefit
    - Low urgency weight
    - Not prioritizing disadvantaged
    - Poor procedural legitimacy
    - High epistemic uncertainty
    """

    em_name: str = "triage_em_v3"
    stakeholder: str = "patients_and_public"
    em_tier: int = 2

    # Weights over ethical dimensions (summing to 1.0)
    w_benefit: float = 0.35
    w_harm: float = 0.25
    w_urgency: float = 0.20
    w_disadvantaged: float = 0.15
    w_procedural: float = 0.05

    # Thresholds
    vulnerability_threshold: float = 0.7
    """Parties with vulnerability_weight >= this get priority weighting."""

    high_harm_threshold: float = 0.6
    """Harm level above which extra scrutiny applies."""

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """
        Fast veto check for reflex layer (V2 interface).

        Returns True if option should be vetoed immediately.
        """
        rd = facts.rights_and_duties
        if rd.violates_rights or rd.violates_explicit_rule:
            return True
        return False

    def reflex_check_distributed(
        self, facts: "EthicalFactsV3"
    ) -> Dict[str, Optional[bool]]:
        """
        Per-party fast veto check for reflex layer.

        Checks each party for rights violations.
        """
        results: Dict[str, Optional[bool]] = {}

        for party_rights in facts.rights_and_duties.per_party:
            party_id = party_rights.party_id
            if party_rights.rights_violated:
                results[party_id] = True
            else:
                results[party_id] = False

        return results

    def evaluate_vector(
        self,
        facts: EthicalFacts,
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        """
        V2-compatible evaluation returning MoralVector.

        Implements the original CaseStudy1TriageEM logic.
        """
        veto_flags: List[str] = []
        reason_codes: List[str] = []
        reasons: List[str] = []
        metadata: Dict[str, Any] = {}

        rd = facts.rights_and_duties
        c = facts.consequences
        j = facts.justice_and_fairness
        p = facts.procedural_and_legitimacy

        # 1. Hard veto check
        if rd.violates_rights or rd.violates_explicit_rule:
            veto_reasons: List[str] = [
                "Option is forbidden because it violates fundamental rights "
                "and/or explicit rules or regulations."
            ]
            if rd.violates_rights:
                veto_flags.append("RIGHTS_VIOLATION")
                veto_reasons.append("violates_rights = True")
            if rd.violates_explicit_rule:
                veto_flags.append("RULE_VIOLATION")
                veto_reasons.append("violates_explicit_rule = True")

            return (
                "forbid",
                MoralVector(
                    physical_harm=1.0,
                    rights_respect=0.0,
                    fairness_equity=0.0,
                    autonomy_respect=0.0,
                    privacy_protection=0.5,
                    societal_environmental=0.5,
                    virtue_care=0.5,
                    legitimacy_trust=0.0,
                    epistemic_quality=0.5,
                    veto_flags=veto_flags,
                    reason_codes=["hard_veto"],
                ),
                veto_reasons,
                {"kind": "hard_veto"},
            )

        # 2. Compute procedural score
        procedural_score = 0.5
        if p is not None:
            procedural_score = 0.0
            if p.followed_approved_procedure:
                procedural_score += 0.5
            if p.stakeholders_consulted:
                procedural_score += 0.25
            if p.decision_explainable_to_public:
                procedural_score += 0.25

        # 3. Compute base composite score
        benefit_term = c.expected_benefit
        harm_term = 1.0 - c.expected_harm
        urgency_term = c.urgency
        disadvantaged_term = 1.0 if j.prioritizes_most_disadvantaged else 0.0

        base_score = (
            self.w_benefit * benefit_term
            + self.w_harm * harm_term
            + self.w_urgency * urgency_term
            + self.w_disadvantaged * disadvantaged_term
            + self.w_procedural * procedural_score
        )

        # 4. Epistemic penalty
        es = facts.epistemic_status
        epistemic_factor = 1.0
        epistemic_quality = 1.0

        if es is not None:
            base_factor = 1.0 - 0.4 * es.uncertainty_level
            base_factor = max(0.0, min(1.0, base_factor))

            quality_mult_map = {
                "high": 1.0,
                "medium": 0.95,
                "low": 0.85,
            }
            quality_mult = quality_mult_map.get(es.evidence_quality.lower(), 0.9)
            factor = base_factor * quality_mult

            if es.novel_situation_flag:
                factor *= 0.9

            epistemic_factor = max(0.0, min(1.0, factor))
            epistemic_quality = epistemic_factor

            reasons.append(
                f"Epistemic penalty: uncertainty={es.uncertainty_level:.2f}, "
                f"quality={es.evidence_quality}, novel={es.novel_situation_flag}, "
                f"multiplier={epistemic_factor:.2f}"
            )

        score = base_score * epistemic_factor

        # 5. Map score to verdict
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

        reasons.insert(
            0,
            "Composite triage judgement based on benefit, harm, urgency, "
            "priority for the disadvantaged, and procedural legitimacy.",
        )

        # Construct moral vector
        moral_vector = MoralVector(
            physical_harm=c.expected_harm,
            rights_respect=1.0,
            fairness_equity=1.0 if j.prioritizes_most_disadvantaged else 0.7,
            autonomy_respect=1.0 if rd.has_valid_consent else 0.7,
            privacy_protection=1.0,
            societal_environmental=1.0,
            virtue_care=0.9 if j.prioritizes_most_disadvantaged else 0.7,
            legitimacy_trust=procedural_score,
            epistemic_quality=epistemic_quality,
            veto_flags=veto_flags,
            reason_codes=reason_codes,
        )

        metadata = {
            "kind": "triage_em",
            "base_score": base_score,
            "epistemic_factor": epistemic_factor,
            "final_score": score,
        }

        return verdict, moral_vector, reasons, metadata

    def evaluate_tensor(
        self,
        facts: "EthicalFactsV3",
    ) -> Tuple[Verdict, MoralTensor, Dict[str, Verdict], List[str], Dict[str, Any]]:
        """
        V3 evaluation returning MoralTensor with per-party triage scores.

        Evaluates each party individually with:
        - Per-party harm/benefit weighted scores
        - Vulnerability-adjusted prioritization
        - Per-party epistemic penalties
        - Distributional fairness assessment
        """
        party_consequences = facts.consequences.per_party
        party_rights = {p.party_id: p for p in facts.rights_and_duties.per_party}
        party_justice = {p.party_id: p for p in facts.justice_and_fairness.per_party}

        n_parties = len(party_consequences)
        party_labels = [p.party_id for p in party_consequences]

        # Initialize tensor data (9 dimensions x n parties)
        data = np.ones((9, n_parties), dtype=np.float64)

        per_party_verdicts: Dict[str, Verdict] = {}
        per_party_scores: Dict[str, float] = {}
        veto_flags: List[str] = []
        veto_locations: List[Tuple[int, ...]] = []
        reasons: List[str] = []
        metadata: Dict[str, Any] = {"per_party_details": {}}

        # Compute global epistemic factor
        es = facts.epistemic_status
        epistemic_factor = 1.0
        if es is not None:
            base_factor = 1.0 - 0.4 * es.uncertainty_level
            base_factor = max(0.0, min(1.0, base_factor))
            quality_mult_map = {"high": 1.0, "medium": 0.95, "low": 0.85}
            quality_mult = quality_mult_map.get(es.evidence_quality.lower(), 0.9)
            factor = base_factor * quality_mult
            if es.novel_situation_flag:
                factor *= 0.9
            epistemic_factor = max(0.0, min(1.0, factor))

        # Compute procedural score (global)
        p = facts.procedural_and_legitimacy
        procedural_score = 0.5
        if p is not None:
            procedural_score = 0.0
            if p.followed_approved_procedure:
                procedural_score += 0.5
            if p.stakeholders_consulted:
                procedural_score += 0.25
            if p.decision_explainable_to_public:
                procedural_score += 0.25

        # Evaluate each party
        for j, party_conseq in enumerate(party_consequences):
            party_id = party_conseq.party_id
            party_reasons: List[str] = []
            party_veto = False

            rights = party_rights.get(party_id)
            justice = party_justice.get(party_id)

            # Check hard veto conditions
            if rights and rights.rights_violated:
                party_veto = True
                veto_flags.append(f"RIGHTS_VIOLATION_{party_id}")
                veto_locations.append((j,))
                party_reasons.append(f"Rights violated for {party_id}")

            # Get party-specific values
            harm = party_conseq.expected_harm
            benefit = party_conseq.expected_benefit
            vulnerability = party_conseq.vulnerability_weight
            urgency = getattr(party_conseq, "urgency", 0.5)

            # Check if party is disadvantaged
            is_disadvantaged = justice.is_disadvantaged if justice else False

            # Compute per-party composite score
            benefit_term = benefit
            harm_term = 1.0 - harm
            urgency_term = urgency
            disadvantaged_term = 1.0 if is_disadvantaged else 0.0

            # Vulnerability-adjusted weighting
            vuln_multiplier = 1.0
            if vulnerability >= self.vulnerability_threshold:
                vuln_multiplier = 1.2  # Boost score for vulnerable parties
                party_reasons.append(f"Vulnerable party {party_id} prioritized")

            base_score = (
                self.w_benefit * benefit_term
                + self.w_harm * harm_term
                + self.w_urgency * urgency_term
                + self.w_disadvantaged * disadvantaged_term
                + self.w_procedural * procedural_score
            ) * vuln_multiplier

            # Apply epistemic penalty
            party_score = base_score * epistemic_factor
            party_score = max(0.0, min(1.0, party_score))
            per_party_scores[party_id] = party_score

            # Populate tensor dimensions
            # Dim 0: physical_harm (higher = worse)
            data[0, j] = harm

            # Dim 1: rights_respect
            if party_veto:
                data[1, j] = 0.0
            else:
                data[1, j] = 1.0

            # Dim 2: fairness_equity
            if (
                is_disadvantaged
                and not facts.justice_and_fairness.prioritizes_most_disadvantaged
            ):
                data[2, j] = 0.6
                party_reasons.append(f"Disadvantaged party {party_id} not prioritized")
            else:
                data[2, j] = 1.0 if is_disadvantaged else 0.85

            # Dim 3: autonomy_respect
            if rights and not rights.consent_given:
                data[3, j] = 0.7
                party_reasons.append(f"Consent not given by {party_id}")
            else:
                data[3, j] = 1.0

            # Dim 4: privacy_protection (default)
            data[4, j] = 1.0

            # Dim 5: societal_environmental (default)
            data[5, j] = 1.0

            # Dim 6: virtue_care (based on vulnerability attention)
            if vulnerability >= self.vulnerability_threshold:
                if harm > self.high_harm_threshold:
                    data[6, j] = 0.5
                    party_reasons.append(f"High harm to vulnerable party {party_id}")
                else:
                    data[6, j] = 0.9
            else:
                data[6, j] = 0.8

            # Dim 7: legitimacy_trust
            data[7, j] = procedural_score

            # Dim 8: epistemic_quality
            data[8, j] = epistemic_factor

            # Determine per-party verdict from composite score
            if party_veto:
                per_party_verdicts[party_id] = "forbid"
            elif party_score >= 0.8:
                per_party_verdicts[party_id] = "strongly_prefer"
            elif party_score >= 0.6:
                per_party_verdicts[party_id] = "prefer"
            elif party_score >= 0.4:
                per_party_verdicts[party_id] = "neutral"
            elif party_score >= 0.2:
                per_party_verdicts[party_id] = "avoid"
            else:
                per_party_verdicts[party_id] = "forbid"

            # Collect per-party metadata
            reasons.extend(party_reasons)
            metadata["per_party_details"][party_id] = {
                "harm": float(harm),
                "benefit": float(benefit),
                "urgency": float(urgency),
                "vulnerability": float(vulnerability),
                "is_disadvantaged": is_disadvantaged,
                "base_score": float(base_score),
                "final_score": float(party_score),
                "verdict": per_party_verdicts[party_id],
                "veto": party_veto,
                "reasons": party_reasons,
            }

        # Compute distributional fairness metrics
        scores = np.array(list(per_party_scores.values()))
        if len(scores) > 1:
            # Gini coefficient of scores
            sorted_scores = np.sort(scores)
            n = len(sorted_scores)
            index = np.arange(1, n + 1)
            gini = (
                (2 * np.sum(index * sorted_scores) - (n + 1) * np.sum(sorted_scores))
                / (n * np.sum(sorted_scores))
                if np.sum(sorted_scores) > 0
                else 0.0
            )
            metadata["score_gini"] = float(gini)

            # Rawlsian maximin (worst-off party)
            worst_party_idx = np.argmin(scores)
            worst_party = party_labels[worst_party_idx]
            metadata["worst_off_party"] = worst_party
            metadata["worst_off_score"] = float(scores[worst_party_idx])

            # Add fairness reasoning
            if gini > 0.3:
                reasons.append(
                    f"High inequality in outcomes (Gini={gini:.2f}). "
                    f"Worst-off party: {worst_party}"
                )

        # Create MoralTensor
        moral_tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n"),
            axis_labels={"n": party_labels},
            veto_flags=veto_flags,
            veto_locations=veto_locations,
        )

        # Determine global verdict (conservative strategy)
        verdict = aggregate_party_verdicts(per_party_verdicts, strategy="conservative")

        # Summary metadata
        metadata["n_parties"] = n_parties
        metadata["n_vetoes"] = len(veto_locations)
        metadata["hard_veto"] = len(veto_locations) > 0
        metadata["epistemic_factor"] = epistemic_factor
        metadata["procedural_score"] = procedural_score

        reasons.insert(
            0,
            "Per-party triage assessment based on harm, benefit, urgency, "
            "vulnerability, and procedural legitimacy.",
        )

        return verdict, moral_tensor, per_party_verdicts, reasons, metadata


@EMRegistry.register(
    tier=2,
    default_weight=8.0,
    veto_capable=True,
    description="Rights-first compliance with per-party tracking (V3)",
    tags=["rights", "compliance", "v3", "veto"],
)
@dataclass
class RightsFirstEMV3(BaseEthicsModuleV3):
    """
    Rights-first compliance EM with per-party tracking.

    Hard vetoes any option that violates rights or explicit rules
    for any party. Otherwise returns high preference.

    Intended as a veto-capable EM in governance pipelines.
    """

    em_name: str = "rights_first_compliance_v3"
    stakeholder: str = "patients_and_public"
    em_tier: int = 2

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """Fast veto check."""
        rd = facts.rights_and_duties
        if rd.violates_rights or rd.violates_explicit_rule:
            return True
        return False

    def reflex_check_distributed(
        self, facts: "EthicalFactsV3"
    ) -> Dict[str, Optional[bool]]:
        """Per-party fast veto check."""
        results: Dict[str, Optional[bool]] = {}
        for party_rights in facts.rights_and_duties.per_party:
            party_id = party_rights.party_id
            results[party_id] = party_rights.rights_violated
        return results

    def evaluate_vector(
        self,
        facts: EthicalFacts,
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        """V2-compatible evaluation."""
        rd = facts.rights_and_duties
        reasons: List[str] = []
        veto_flags: List[str] = []

        if rd.violates_rights or rd.violates_explicit_rule:
            verdict: Verdict = "forbid"
            reasons.append("Forbid: option violates rights and/or explicit rules.")
            if rd.violates_rights:
                veto_flags.append("RIGHTS_VIOLATION")
                reasons.append("violates_rights = True")
            if rd.violates_explicit_rule:
                veto_flags.append("RULE_VIOLATION")
                reasons.append("violates_explicit_rule = True")

            return (
                verdict,
                MoralVector(
                    physical_harm=0.5,
                    rights_respect=0.0,
                    fairness_equity=0.5,
                    autonomy_respect=0.5,
                    privacy_protection=0.5,
                    societal_environmental=0.5,
                    virtue_care=0.5,
                    legitimacy_trust=0.0,
                    epistemic_quality=0.5,
                    veto_flags=veto_flags,
                    reason_codes=["rights_violated"],
                ),
                reasons,
                {"kind": "rights_first", "veto": True},
            )
        else:
            verdict = "prefer"
            reasons.append("Rights and explicit rules are respected.")
            return (
                verdict,
                MoralVector(
                    physical_harm=0.2,
                    rights_respect=1.0,
                    fairness_equity=0.8,
                    autonomy_respect=0.8,
                    privacy_protection=0.8,
                    societal_environmental=0.8,
                    virtue_care=0.8,
                    legitimacy_trust=1.0,
                    epistemic_quality=0.8,
                    veto_flags=[],
                    reason_codes=[],
                ),
                reasons,
                {"kind": "rights_first", "veto": False},
            )

    def evaluate_tensor(
        self,
        facts: "EthicalFactsV3",
    ) -> Tuple[Verdict, MoralTensor, Dict[str, Verdict], List[str], Dict[str, Any]]:
        """V3 evaluation with per-party rights checking."""
        party_consequences = facts.consequences.per_party
        party_rights = {p.party_id: p for p in facts.rights_and_duties.per_party}

        n_parties = len(party_consequences)
        party_labels = [p.party_id for p in party_consequences]

        data = np.ones((9, n_parties), dtype=np.float64) * 0.8
        per_party_verdicts: Dict[str, Verdict] = {}
        veto_flags: List[str] = []
        veto_locations: List[Tuple[int, ...]] = []
        reasons: List[str] = []
        metadata: Dict[str, Any] = {}

        for j, party_conseq in enumerate(party_consequences):
            party_id = party_conseq.party_id
            rights = party_rights.get(party_id)

            if rights and rights.rights_violated:
                # Rights violation for this party
                data[1, j] = 0.0  # rights_respect
                data[7, j] = 0.0  # legitimacy_trust
                veto_flags.append(f"RIGHTS_VIOLATION_{party_id}")
                veto_locations.append((j,))
                per_party_verdicts[party_id] = "forbid"
                reasons.append(f"Rights violated for {party_id}")
            else:
                data[1, j] = 1.0
                data[7, j] = 1.0
                per_party_verdicts[party_id] = "prefer"

        moral_tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n"),
            axis_labels={"n": party_labels},
            veto_flags=veto_flags,
            veto_locations=veto_locations,
        )

        verdict = aggregate_party_verdicts(per_party_verdicts, strategy="conservative")

        if not veto_flags:
            reasons.insert(0, "Rights and explicit rules respected for all parties.")
        else:
            reasons.insert(0, "Rights violations detected for some parties.")

        metadata["n_parties"] = n_parties
        metadata["n_vetoes"] = len(veto_locations)
        metadata["hard_veto"] = len(veto_locations) > 0

        return verdict, moral_tensor, per_party_verdicts, reasons, metadata


__all__ = [
    "TriageEMV3",
    "RightsFirstEMV3",
]
