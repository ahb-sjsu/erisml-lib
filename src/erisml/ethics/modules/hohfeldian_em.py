# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Hohfeldian Ethics Module for D4 Gauge Verification.

This module implements gauge symmetry verification for DEME 2.0,
checking that moral reasoning satisfies correlative consistency
constraints derived from Hohfeldian jurisprudence.

The module does not compute primary moral judgements—it verifies
that other EMs' outputs are consistent across perspective swaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from erisml.ethics import EthicalFacts, EthicalJudgement
from erisml.ethics.modules.base import BaseEthicsModule
from erisml.ethics.hohfeld import (
    HohfeldianState,
    D4Element,
    HohfeldianVerdict,
    correlative,
    compute_bond_index,
    compute_wilson_observable,
    is_in_klein_four,
    requires_nonabelian_structure,
)


@dataclass
class GaugeVerificationResult:
    """Result of D4 gauge symmetry verification."""

    bond_index: float
    passed: bool
    violations: List[str] = field(default_factory=list)
    party_verdicts: Dict[str, HohfeldianState] = field(default_factory=dict)
    expected_transforms: List[D4Element] = field(default_factory=list)
    observed_transforms: List[D4Element] = field(default_factory=list)


class HohfeldianEM(BaseEthicsModule):
    """
    Ethics Module that verifies D4 gauge symmetry in moral reasoning.

    This EM checks that moral reasoning satisfies correlative consistency:
    - If party A is evaluated as having Obligation (O), then party B
      should be evaluated as having Claim (C) for the same relation.

    The module computes:
    - Bond Index: Deviation from perfect correlative symmetry
    - Gauge violations: Specific consistency failures
    - Wilson observable: Path-dependence detection

    Configuration:
        gauge_violation_threshold: Bond index above which to flag (default: 0.1)
        strict_enforcement: If True, gauge violations produce "avoid" verdict
        tau: Temperature parameter for bond index scaling (default: 1.0)

    Example:
        >>> em = HohfeldianEM(gauge_violation_threshold=0.15)
        >>> judgement = em.evaluate("option_1", facts)
        >>> print(judgement.metadata["bond_index"])
        0.0  # Perfect symmetry
    """

    em_name: str = "hohfeldian_gauge"
    em_version: str = "1.0.0"
    stakeholder: str = "all_parties"  # Gauge verification applies to all parties

    def __init__(
        self,
        gauge_violation_threshold: float = 0.1,
        strict_enforcement: bool = False,
        tau: float = 1.0,
        stakeholder: str = "all_parties",
    ):
        """
        Initialize HohfeldianEM.

        Args:
            gauge_violation_threshold: Bond index threshold for flagging
            strict_enforcement: If True, violations produce "avoid" verdict
            tau: Temperature parameter for bond index scaling
            stakeholder: Stakeholder perspective for this EM
        """
        self.gauge_violation_threshold = gauge_violation_threshold
        self.strict_enforcement = strict_enforcement
        self.tau = tau
        self.stakeholder = stakeholder

    def evaluate(self, option_id: str, facts: EthicalFacts) -> EthicalJudgement:
        """
        Evaluate gauge consistency for an option.

        This method extracts Hohfeldian positions from EthicalFacts
        (via rights_and_duties dimensions) and verifies correlative
        consistency across parties.

        Args:
            option_id: Identifier for the option being evaluated
            facts: EthicalFacts containing rights/duties information

        Returns:
            EthicalJudgement with gauge verification results
        """
        # Extract Hohfeldian positions from facts
        positions = self._extract_hohfeldian_positions(facts)

        # If insufficient data for gauge check, return neutral
        if len(positions) < 2:
            return EthicalJudgement(
                option_id=option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="neutral",
                normative_score=0.5,
                reasons=["Insufficient party data for gauge verification"],
                metadata={
                    "gauge_check": "SKIPPED",
                    "reason": "fewer than 2 parties",
                },
            )

        # Verify gauge consistency
        result = self._verify_gauge_consistency(positions)

        # Build judgement based on result
        if result.passed:
            return EthicalJudgement(
                option_id=option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict="neutral",
                normative_score=0.5
                + (
                    0.5 * (1.0 - result.bond_index)
                ),  # Higher score for lower bond index
                reasons=[
                    "Gauge consistency verified",
                    f"Bond Index: {result.bond_index:.4f}",
                ],
                metadata={
                    "gauge_check": "PASSED",
                    "bond_index": result.bond_index,
                    "party_verdicts": {
                        k: v.value for k, v in result.party_verdicts.items()
                    },
                },
            )
        else:
            verdict = "avoid" if self.strict_enforcement else "neutral"
            score = 0.2 if self.strict_enforcement else 0.4

            return EthicalJudgement(
                option_id=option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict=verdict,
                normative_score=score,
                reasons=[
                    f"Gauge violation detected: Bond Index = {result.bond_index:.4f}",
                    "Correlative symmetry violated between parties",
                    *result.violations,
                ],
                metadata={
                    "gauge_check": "FAILED",
                    "bond_index": result.bond_index,
                    "violations": result.violations,
                    "party_verdicts": {
                        k: v.value for k, v in result.party_verdicts.items()
                    },
                },
            )

    def _extract_hohfeldian_positions(
        self, facts: EthicalFacts
    ) -> Dict[str, HohfeldianState]:
        """
        Extract Hohfeldian positions from EthicalFacts.

        Positions can be specified via tags in the format:
        - "hohfeld:party_name:STATE" where STATE is O, C, L, or N

        Example tags:
        - "hohfeld:patient:C" - patient has Claim
        - "hohfeld:hospital:O" - hospital has Obligation

        Also infers from rights_and_duties dimensions:
        - violates_rights=True -> affected party likely had Claim
        - role_duty_conflict=True -> actor likely had Obligation

        Returns:
            Dictionary mapping party names to their Hohfeldian states
        """
        positions: Dict[str, HohfeldianState] = {}

        # Extract from tags (primary method)
        if facts.tags:
            for tag in facts.tags:
                if tag.startswith("hohfeld:"):
                    parts = tag.split(":")
                    if len(parts) == 3:
                        _, party, state_str = parts
                        try:
                            positions[party] = HohfeldianState(state_str)
                        except ValueError:
                            pass  # Invalid state, skip

        # If no tags, try to infer from rights_and_duties
        if not positions and facts.rights_and_duties is not None:
            rd = facts.rights_and_duties

            # If violating rights, affected party had Claim
            if rd.violates_rights:
                positions["affected"] = HohfeldianState.C
                # Actor likely had obligation they violated
                positions["actor"] = HohfeldianState.O

            # Role duty conflict implies actor had Obligation
            elif rd.role_duty_conflict:
                positions["actor"] = HohfeldianState.O

        return positions

    def _verify_gauge_consistency(
        self, positions: Dict[str, HohfeldianState]
    ) -> GaugeVerificationResult:
        """
        Verify D4 gauge consistency across party positions.

        Checks that correlative pairs are consistent:
        - If party A has O, party B should have C
        - If party A has L, party B should have N

        Returns:
            GaugeVerificationResult with bond index and violations
        """
        violations: List[str] = []
        party_list = list(positions.keys())

        # Build verdict lists for bond index computation
        verdicts_a: List[HohfeldianVerdict] = []
        verdicts_b: List[HohfeldianVerdict] = []

        # Check all pairs
        for i, party_a in enumerate(party_list):
            for party_b in party_list[i + 1 :]:
                state_a = positions[party_a]
                state_b = positions[party_b]
                expected_b = correlative(state_a)

                verdicts_a.append(HohfeldianVerdict(party_a, state_a))
                verdicts_b.append(HohfeldianVerdict(party_b, state_b))

                if state_b != expected_b:
                    violations.append(
                        f"{party_a}({state_a.value}) <-> {party_b}({state_b.value}): "
                        f"expected {party_b} to have {expected_b.value}"
                    )

        # Compute bond index
        if verdicts_a:
            bond_index = compute_bond_index(verdicts_a, verdicts_b, tau=self.tau)
        else:
            bond_index = 0.0

        passed = bond_index <= self.gauge_violation_threshold

        return GaugeVerificationResult(
            bond_index=bond_index,
            passed=passed,
            violations=violations,
            party_verdicts=positions,
        )

    def verify_decision_path(
        self,
        path: List[D4Element],
        initial_state: HohfeldianState,
        observed_final: HohfeldianState,
    ) -> Tuple[D4Element, bool, str]:
        """
        Verify a decision path using Wilson observable.

        Checks if a sequence of transformations produces the expected
        final state (holonomy verification).

        Args:
            path: Sequence of D4 elements (transformations applied)
            initial_state: Starting Hohfeldian position
            observed_final: Actually observed final state

        Returns:
            (holonomy, matched, explanation): The computed holonomy,
            whether it matched observation, and human-readable explanation
        """
        holonomy, matched = compute_wilson_observable(
            path, initial_state, observed_final
        )

        if matched:
            explanation = (
                f"Path verification PASSED: "
                f"{initial_state.value} --[{','.join(e.value for e in path)}]--> "
                f"{observed_final.value} (holonomy={holonomy.value})"
            )
        else:
            # Compute what we expected
            from erisml.ethics.hohfeld import d4_apply_to_state

            expected_final = initial_state
            for elem in path:
                expected_final = d4_apply_to_state(elem, expected_final)

            explanation = (
                f"Path verification FAILED: "
                f"Expected {expected_final.value} but observed {observed_final.value} "
                f"(holonomy={holonomy.value})"
            )

        return holonomy, matched, explanation

    def check_nonabelian_signature(
        self, observed_operations: List[D4Element]
    ) -> Tuple[bool, str]:
        """
        Check if observed operations demonstrate non-abelian structure.

        To prove the full D4 structure (not just the abelian Klein-4
        subgroup), we need to observe quarter-turn operations.

        Args:
            observed_operations: List of D4 elements observed in reasoning

        Returns:
            (is_nonabelian, explanation): Whether non-abelian structure
            is demonstrated and why
        """
        needs_nonabelian = requires_nonabelian_structure(observed_operations)

        if needs_nonabelian:
            nonabelian_ops = [
                e.value for e in observed_operations if not is_in_klein_four(e)
            ]
            explanation = (
                f"Non-abelian D4 structure demonstrated via operations: "
                f"{nonabelian_ops}. Order of operations matters."
            )
        else:
            explanation = (
                f"Only abelian (Klein-4) operations observed: "
                f"{[e.value for e in observed_operations]}. "
                f"Cannot confirm non-abelian structure without quarter-turns (r, r³, sr, sr³)."
            )

        return needs_nonabelian, explanation


# Register in EM registry
def register_hohfeldian_em():
    """Register HohfeldianEM in the global EM registry."""
    from erisml.ethics.modules import EM_REGISTRY

    EM_REGISTRY["hohfeldian_gauge"] = HohfeldianEM


# Convenience function for quick gauge check
def quick_gauge_check(
    party_positions: Dict[str, str],
    threshold: float = 0.1,
) -> GaugeVerificationResult:
    """
    Quick utility function for gauge consistency check.

    Args:
        party_positions: Dictionary mapping party names to state strings
                        ("O", "C", "L", or "N")
        threshold: Bond index threshold for passing

    Returns:
        GaugeVerificationResult

    Example:
        >>> result = quick_gauge_check({"patient": "C", "hospital": "O"})
        >>> print(result.passed)  # True - correlative consistent
        True
    """
    positions = {
        party: HohfeldianState(state) for party, state in party_positions.items()
    }

    em = HohfeldianEM(gauge_violation_threshold=threshold)
    return em._verify_gauge_consistency(positions)
