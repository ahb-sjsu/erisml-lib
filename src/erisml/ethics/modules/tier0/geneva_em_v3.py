# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
GenevaEMV3: Constitutional ethics module with per-party assessment.

This is a Tier 0 (Constitutional) EM that cannot be disabled and
always has veto capability. It extends GenevaEMV2 to support
distributed multi-party ethics assessment via MoralTensor.

Key V3 Features:
- Per-party harm/benefit tracking
- Per-party rights violation detection
- Per-party veto locations
- Distributional fairness awareness

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
    tier=0,
    default_weight=10.0,
    veto_capable=True,
    description="Geneva convention and fundamental rights constraints (V3 distributed)",
    tags=["constitutional", "rights", "geneva", "v3", "distributed"],
)
@dataclass
class GenevaEMV3(BaseEthicsModuleV3):
    """
    Constitutional EM enforcing Geneva convention principles with per-party tracking.

    Hard vetoes (per-party):
    - Rights violations for specific parties
    - Discrimination on protected attributes
    - Explicit rule violations

    Penalties (per-party):
    - Missing consent
    - Role duty conflicts
    - Vulnerability exploitation

    V3 Features:
    - Per-party moral tensor output
    - Distributional fairness tracking
    - Per-party veto locations
    """

    em_name: str = "geneva_constitutional_v3"
    stakeholder: str = "universal"
    em_tier: int = 0

    # Configuration
    strict_consent: bool = True
    """Require valid consent for non-veto pass."""

    vulnerability_threshold: float = 0.7
    """Parties with vulnerability_weight >= this get extra protection."""

    def reflex_check(self, facts: EthicalFacts) -> Optional[bool]:
        """
        Fast veto check for reflex layer (V2 interface).

        Returns True if option should be vetoed immediately.
        """
        # Check hard veto conditions
        if facts.rights_and_duties.violates_rights:
            return True
        if facts.justice_and_fairness.discriminates_on_protected_attr:
            return True
        if facts.rights_and_duties.violates_explicit_rule:
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

        # Check per-party rights
        for party_rights in facts.rights_and_duties.per_party:
            party_id = party_rights.party_id
            if party_rights.rights_violated:
                results[party_id] = True
            else:
                results[party_id] = False

        # Global discrimination check applies to all parties
        if facts.justice_and_fairness.discriminates_on_protected_attr:
            for party_id in results:
                results[party_id] = True

        return results

    def evaluate_vector(
        self,
        facts: EthicalFacts,
    ) -> Tuple[Verdict, MoralVector, List[str], Dict[str, Any]]:
        """
        V2-compatible evaluation returning MoralVector.

        Delegates to parent V2 logic.
        """
        veto_flags: List[str] = []
        reason_codes: List[str] = []
        reasons: List[str] = []
        metadata: Dict[str, Any] = {}

        # Start with baseline vector (9 dimensions)
        physical_harm = facts.consequences.expected_harm
        rights_respect = 1.0
        fairness_equity = 1.0
        autonomy_respect = 1.0
        privacy_protection = 1.0
        societal_environmental = 1.0
        virtue_care = 1.0
        legitimacy_trust = 1.0
        epistemic_quality = 1.0

        # Check hard vetoes
        if facts.rights_and_duties.violates_rights:
            rights_respect = 0.0
            veto_flags.append("RIGHTS_VIOLATION")
            reason_codes.append("rights_violated")
            reasons.append("Fundamental rights violation detected")

        if facts.justice_and_fairness.discriminates_on_protected_attr:
            fairness_equity = 0.0
            veto_flags.append("DISCRIMINATION")
            reason_codes.append("protected_attr_discrimination")
            reasons.append("Discrimination on protected attributes")

        if facts.rights_and_duties.violates_explicit_rule:
            legitimacy_trust = 0.0
            veto_flags.append("RULE_VIOLATION")
            reason_codes.append("explicit_rule_violated")
            reasons.append("Explicit rule or regulation violation")

        # Check soft constraints
        if not facts.rights_and_duties.has_valid_consent:
            if self.strict_consent:
                autonomy_respect *= 0.5
            reason_codes.append("consent_missing")
            reasons.append("Valid consent not present")

        if facts.rights_and_duties.role_duty_conflict:
            legitimacy_trust *= 0.7
            reason_codes.append("role_duty_conflict")
            reasons.append("Role or duty conflict detected")

        if facts.justice_and_fairness.exploits_vulnerable_population:
            fairness_equity *= 0.5
            reason_codes.append("exploits_vulnerable")
            reasons.append("Exploits vulnerable population")

        if facts.justice_and_fairness.exacerbates_power_imbalance:
            fairness_equity *= 0.8
            reason_codes.append("power_imbalance")
            reasons.append("Exacerbates power imbalance")

        # Epistemic quality
        if facts.epistemic_status is not None:
            es = facts.epistemic_status
            epistemic_quality = 1.0 - es.uncertainty_level
            if es.evidence_quality == "low":
                epistemic_quality *= 0.5
            elif es.evidence_quality == "medium":
                epistemic_quality *= 0.8

        # Determine verdict
        if veto_flags:
            verdict: Verdict = "forbid"
        elif all([rights_respect > 0.7, fairness_equity > 0.7, legitimacy_trust > 0.7]):
            if physical_harm < 0.2:
                verdict = "strongly_prefer"
            else:
                verdict = "prefer"
        elif all([rights_respect > 0.5, fairness_equity > 0.5, legitimacy_trust > 0.5]):
            verdict = "neutral"
        else:
            verdict = "avoid"

        moral_vector = MoralVector(
            physical_harm=physical_harm,
            rights_respect=rights_respect,
            fairness_equity=fairness_equity,
            autonomy_respect=autonomy_respect,
            privacy_protection=privacy_protection,
            societal_environmental=societal_environmental,
            virtue_care=virtue_care,
            legitimacy_trust=legitimacy_trust,
            epistemic_quality=epistemic_quality,
            veto_flags=veto_flags,
            reason_codes=reason_codes,
        )

        metadata["hard_veto"] = len(veto_flags) > 0

        return verdict, moral_vector, reasons, metadata

    def evaluate_tensor(
        self,
        facts: "EthicalFactsV3",
    ) -> Tuple[Verdict, MoralTensor, Dict[str, Verdict], List[str], Dict[str, Any]]:
        """
        V3 evaluation returning MoralTensor with per-party scores.

        Evaluates each party individually and constructs a rank-2 tensor.
        """
        # Extract party information
        party_consequences = facts.consequences.per_party
        party_rights = {p.party_id: p for p in facts.rights_and_duties.per_party}
        party_justice = {p.party_id: p for p in facts.justice_and_fairness.per_party}

        n_parties = len(party_consequences)
        party_labels = [p.party_id for p in party_consequences]

        # Initialize tensor data (9 dimensions × n parties)
        data = np.ones((9, n_parties), dtype=np.float64)

        # Track per-party verdicts and vetoes
        per_party_verdicts: Dict[str, Verdict] = {}
        veto_flags: List[str] = []
        veto_locations: List[Tuple[int, ...]] = []
        reasons: List[str] = []
        metadata: Dict[str, Any] = {"per_party_details": {}}

        # Global checks that apply to all parties
        global_discrimination = facts.justice_and_fairness.discriminates_on_protected_attr

        # Evaluate each party
        for j, party_conseq in enumerate(party_consequences):
            party_id = party_conseq.party_id
            party_reasons: List[str] = []
            party_veto = False

            # Get party-specific facts
            rights = party_rights.get(party_id)
            justice = party_justice.get(party_id)

            # Dimension 0: physical_harm
            harm = party_conseq.expected_harm
            benefit = party_conseq.expected_benefit
            # Higher harm = worse score (inverted for harm dimension)
            data[0, j] = harm

            # Dimension 1: rights_respect
            if rights and rights.rights_violated:
                data[1, j] = 0.0
                party_veto = True
                veto_flags.append(f"RIGHTS_VIOLATION_{party_id}")
                veto_locations.append((j,))
                party_reasons.append(f"Rights violated for {party_id}")
            else:
                data[1, j] = 1.0

            # Dimension 2: fairness_equity
            if global_discrimination:
                data[2, j] = 0.0
                if not party_veto:
                    party_veto = True
                    veto_flags.append(f"DISCRIMINATION_{party_id}")
                    if (j,) not in veto_locations:
                        veto_locations.append((j,))
                party_reasons.append("Discrimination on protected attributes")
            elif justice and justice.is_disadvantaged:
                # Penalty for disadvantaged parties being further harmed
                data[2, j] = 0.7
                party_reasons.append(f"Party {party_id} is disadvantaged")
            else:
                data[2, j] = 1.0

            # Dimension 3: autonomy_respect
            if rights and not rights.consent_given:
                if self.strict_consent:
                    data[3, j] = 0.5
                else:
                    data[3, j] = 0.8
                party_reasons.append(f"Consent not given by {party_id}")
            else:
                data[3, j] = 1.0

            # Dimension 4: privacy_protection (default high, no party-specific logic yet)
            data[4, j] = 1.0

            # Dimension 5: societal_environmental (default high)
            data[5, j] = 1.0

            # Dimension 6: virtue_care
            # Higher care for vulnerable parties
            vulnerability = party_conseq.vulnerability_weight
            if vulnerability >= self.vulnerability_threshold:
                # Extra scrutiny for vulnerable parties
                if harm > 0.3:
                    data[6, j] = 0.6
                    party_reasons.append(f"Vulnerable party {party_id} faces harm")
                else:
                    data[6, j] = 0.9
            else:
                data[6, j] = 1.0

            # Dimension 7: legitimacy_trust
            if rights and rights.duty_owed and harm > benefit:
                data[7, j] = 0.7
                party_reasons.append(f"Duty owed to {party_id} but net harm")
            else:
                data[7, j] = 1.0

            # Dimension 8: epistemic_quality (use global)
            if facts.epistemic_status is not None:
                es = facts.epistemic_status
                eq = 1.0 - es.uncertainty_level
                if es.evidence_quality == "low":
                    eq *= 0.5
                elif es.evidence_quality == "medium":
                    eq *= 0.8
                data[8, j] = eq
            else:
                data[8, j] = 1.0

            # Determine per-party verdict
            if party_veto:
                per_party_verdicts[party_id] = "forbid"
            elif all([data[1, j] > 0.7, data[2, j] > 0.7, data[7, j] > 0.7]):
                if harm < 0.2:
                    per_party_verdicts[party_id] = "strongly_prefer"
                else:
                    per_party_verdicts[party_id] = "prefer"
            elif all([data[1, j] > 0.5, data[2, j] > 0.5, data[7, j] > 0.5]):
                per_party_verdicts[party_id] = "neutral"
            else:
                per_party_verdicts[party_id] = "avoid"

            # Collect reasons
            reasons.extend(party_reasons)
            metadata["per_party_details"][party_id] = {
                "harm": float(harm),
                "benefit": float(benefit),
                "vulnerability": float(vulnerability),
                "verdict": per_party_verdicts[party_id],
                "veto": party_veto,
                "reasons": party_reasons,
            }

        # Create MoralTensor
        moral_tensor = MoralTensor.from_dense(
            data,
            axis_names=("k", "n"),
            axis_labels={"n": party_labels},
            veto_flags=veto_flags,
            veto_locations=veto_locations,
        )

        # Determine global verdict (conservative: any forbid → forbid)
        verdict = aggregate_party_verdicts(per_party_verdicts, strategy="conservative")

        # Add metadata
        metadata["n_parties"] = n_parties
        metadata["n_vetoes"] = len(veto_locations)
        metadata["hard_veto"] = len(veto_locations) > 0

        return verdict, moral_tensor, per_party_verdicts, reasons, metadata


__all__ = [
    "GenevaEMV3",
]
