# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
BIP Verifier: Bond Invariance Principle verification.

Verifies that ethical decisions are invariant under transformations
that do not change morally relevant structure.

Key principle: If two representations describe the same physical/moral
situation, they must lead to the same decision.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.decision_proof import DecisionProof


class TransformType(str, Enum):
    """Types of representational transformations."""

    # Bond-preserving transforms (should not change decision)
    UNIT_CHANGE = "unit_change"
    """Change of measurement units (e.g., meters to feet)."""

    COORDINATE_CHANGE = "coordinate_change"
    """Change of coordinate system."""

    GAUGE_TRANSFORM = "gauge_transform"
    """Gauge transformation (e.g., Hohfeldian perspective swap)."""

    RENAMING = "renaming"
    """Renaming of entities without semantic change."""

    REORDERING = "reordering"
    """Reordering of equivalent options."""

    # Bond-changing transforms (may change decision)
    VALUE_CHANGE = "value_change"
    """Actual change in values/facts."""

    STAKEHOLDER_CHANGE = "stakeholder_change"
    """Change in stakeholder perspective."""

    PROFILE_CHANGE = "profile_change"
    """Change in governance profile."""


# Transforms that should not change the canonical decision
BOND_PRESERVING_TRANSFORMS = {
    TransformType.UNIT_CHANGE,
    TransformType.COORDINATE_CHANGE,
    TransformType.GAUGE_TRANSFORM,
    TransformType.RENAMING,
    TransformType.REORDERING,
}


@dataclass
class BIPVerificationResult:
    """Result of a BIP verification check."""

    passed: bool
    """Whether the verification passed."""

    transform_type: TransformType
    """Type of transform that was applied."""

    original_decision: Optional[str]
    """Original selected option ID."""

    transformed_decision: Optional[str]
    """Decision after transform."""

    delta_score: float = 0.0
    """Change in aggregate score."""

    delta_vector: Dict[str, float] = field(default_factory=dict)
    """Per-dimension change in MoralVector."""

    message: str = ""
    """Human-readable explanation."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional verification data."""


class BIPVerifier:
    """
    Verify Bond Invariance Properties for decision proofs.

    Bond Invariance means that decisions depend on morally relevant
    structure, not on arbitrary representational choices.

    Usage:
        verifier = BIPVerifier(reference_proof)
        result = verifier.verify_transform(transformed_proof, TransformType.UNIT_CHANGE)
        assert result.passed, result.message
    """

    def __init__(
        self,
        reference_proof: DecisionProof,
        tolerance: float = 0.01,
    ) -> None:
        """
        Initialize verifier with a reference decision.

        Args:
            reference_proof: The original decision proof.
            tolerance: Tolerance for numerical differences.
        """
        self.reference = reference_proof
        self.tolerance = tolerance

    def verify_transform(
        self,
        transformed_proof: DecisionProof,
        transform_type: TransformType,
    ) -> BIPVerificationResult:
        """
        Verify that a transformed decision is invariant under the transform.

        Args:
            transformed_proof: Decision proof after transformation.
            transform_type: Type of transform that was applied.

        Returns:
            BIPVerificationResult indicating pass/fail.
        """
        if transform_type in BOND_PRESERVING_TRANSFORMS:
            return self._verify_invariance(transformed_proof, transform_type)
        else:
            return self._compute_delta(transformed_proof, transform_type)

    def _verify_invariance(
        self,
        transformed_proof: DecisionProof,
        transform_type: TransformType,
    ) -> BIPVerificationResult:
        """Verify that decision is invariant under bond-preserving transform."""
        # Check canonical decision equivalence
        same_decision = (
            self.reference.selected_option_id == transformed_proof.selected_option_id
        )

        # Check ranking equivalence (allowing for reordering of equal-scored options)
        same_ranking = self._check_ranking_equivalence(
            self.reference.ranked_options,
            transformed_proof.ranked_options,
        )

        # Check forbidden options equivalence
        same_forbidden = set(self.reference.forbidden_options) == set(
            transformed_proof.forbidden_options
        )

        passed = same_decision and same_ranking and same_forbidden

        message = ""
        if not same_decision:
            message = (
                f"Decision changed: {self.reference.selected_option_id} → "
                f"{transformed_proof.selected_option_id}"
            )
        elif not same_ranking:
            message = "Ranking order changed"
        elif not same_forbidden:
            message = "Forbidden options changed"
        else:
            message = f"Invariance verified under {transform_type.value}"

        return BIPVerificationResult(
            passed=passed,
            transform_type=transform_type,
            original_decision=self.reference.selected_option_id,
            transformed_decision=transformed_proof.selected_option_id,
            message=message,
            metadata={
                "same_decision": same_decision,
                "same_ranking": same_ranking,
                "same_forbidden": same_forbidden,
            },
        )

    def _compute_delta(
        self,
        transformed_proof: DecisionProof,
        transform_type: TransformType,
    ) -> BIPVerificationResult:
        """Compute the delta for bond-changing transforms."""
        same_decision = (
            self.reference.selected_option_id == transformed_proof.selected_option_id
        )

        # Compute vector deltas if available
        delta_vector: Dict[str, float] = {}
        if (
            self.reference.moral_vector_summary
            and transformed_proof.moral_vector_summary
        ):
            for option_id in self.reference.moral_vector_summary:
                if option_id in transformed_proof.moral_vector_summary:
                    ref_vec = self.reference.moral_vector_summary[option_id]
                    trans_vec = transformed_proof.moral_vector_summary[option_id]

                    for dim in ref_vec:
                        if dim in trans_vec:
                            delta = trans_vec[dim] - ref_vec[dim]
                            if abs(delta) > self.tolerance:
                                delta_vector[f"{option_id}.{dim}"] = delta

        message = f"Transform {transform_type.value}: "
        if same_decision:
            message += "Decision unchanged"
        else:
            message += (
                f"Decision changed: {self.reference.selected_option_id} → "
                f"{transformed_proof.selected_option_id}"
            )

        return BIPVerificationResult(
            passed=True,  # Bond-changing transforms don't "fail"
            transform_type=transform_type,
            original_decision=self.reference.selected_option_id,
            transformed_decision=transformed_proof.selected_option_id,
            delta_vector=delta_vector,
            message=message,
        )

    def _check_ranking_equivalence(
        self,
        ranking1: List[str],
        ranking2: List[str],
    ) -> bool:
        """Check if two rankings are equivalent up to tie-breaking."""
        if len(ranking1) != len(ranking2):
            return False

        # For now, require exact match
        # A more sophisticated version would allow permutations
        # within score-equivalent tiers
        return ranking1 == ranking2

    def verify_hohfeld_gauge(
        self,
        perspective_swapped_proof: DecisionProof,
    ) -> BIPVerificationResult:
        """
        Verify Hohfeldian gauge invariance.

        Under correlative perspective swap (O↔C, L↔N), the decision
        should remain consistent with the transformed normative positions.

        Args:
            perspective_swapped_proof: Proof after correlative transform.

        Returns:
            Verification result.
        """
        return self.verify_transform(
            perspective_swapped_proof,
            TransformType.GAUGE_TRANSFORM,
        )


__all__ = [
    "TransformType",
    "BOND_PRESERVING_TRANSFORMS",
    "BIPVerificationResult",
    "BIPVerifier",
]
