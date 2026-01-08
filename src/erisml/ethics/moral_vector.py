# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
MoralVector: k-dimensional vector representation of ethical assessment.

DEME 2.0 introduces multi-dimensional moral vectors that replace scalar
normative scores. This provides:

1. Explicit trade-off visibility across ethical dimensions
2. Pareto-optimal reasoning (no dimension dominates by default)
3. Domain-extensible dimensions for context-specific ethics
4. Veto flags for hard constraint violations

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.facts import EthicalFacts


# Default weights for scalar collapse (backward compatibility)
DEFAULT_DIMENSION_WEIGHTS: Dict[str, float] = {
    "physical_harm": 1.0,
    "rights_respect": 1.0,
    "fairness_equity": 1.0,
    "autonomy_respect": 1.0,
    "legitimacy_trust": 1.0,
    "epistemic_quality": 0.5,
}


@dataclass
class MoralVector:
    """
    k-dimensional vector [0,1] per ethical dimension.

    Core dimensions are always present. Domain-specific extensions
    can be added via the `extensions` dict.

    Dimension semantics:
    - physical_harm: 0=no harm, 1=severe harm (inverted for goodness)
    - rights_respect: 0=violated, 1=fully respected
    - fairness_equity: 0=discriminatory, 1=fair
    - autonomy_respect: 0=coerced, 1=full autonomy
    - legitimacy_trust: 0=illegitimate, 1=fully legitimate
    - epistemic_quality: 0=no evidence, 1=high quality evidence
    """

    # Core dimensions (always present)
    physical_harm: float = 0.0
    """Physical harm level [0,1]. 0=no harm, 1=severe/catastrophic harm."""

    rights_respect: float = 1.0
    """Rights respect level [0,1]. 0=severe violation, 1=fully respected."""

    fairness_equity: float = 1.0
    """Fairness level [0,1]. 0=discriminatory/unfair, 1=maximally fair."""

    autonomy_respect: float = 1.0
    """Autonomy level [0,1]. 0=coerced/manipulated, 1=full autonomy."""

    legitimacy_trust: float = 1.0
    """Legitimacy level [0,1]. 0=illegitimate process, 1=fully legitimate."""

    epistemic_quality: float = 1.0
    """Epistemic quality [0,1]. 0=high uncertainty/low evidence, 1=high quality."""

    # Domain extension dimensions (optional)
    extensions: Dict[str, float] = field(default_factory=dict)
    """
    Domain-specific dimensions, e.g.:
    - "therapeutic_benefit" for medical contexts
    - "environmental_impact" for sustainability
    - "privacy_level" for data governance
    """

    # Veto flags for hard constraints
    veto_flags: List[str] = field(default_factory=list)
    """
    List of triggered veto conditions, e.g.:
    - "RIGHTS_VIOLATION"
    - "DISCRIMINATION"
    - "CATASTROPHIC_HARM"
    """

    # Reason codes for audit trail
    reason_codes: List[str] = field(default_factory=list)
    """
    Machine-readable reason codes for each dimension assessment.
    Used for audit trails and decision proofs.
    """

    def __post_init__(self) -> None:
        """Validate dimension values are in [0, 1]."""
        self._validate_bounds()

    def _validate_bounds(self) -> None:
        """Ensure all dimensions are within [0, 1]."""
        for dim_name in self.core_dimension_names():
            value = getattr(self, dim_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Dimension {dim_name} must be in [0, 1], got {value}")
        for dim_name, value in self.extensions.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"Extension dimension {dim_name} must be in [0, 1], got {value}"
                )

    @staticmethod
    def core_dimension_names() -> List[str]:
        """Return names of core dimensions."""
        return [
            "physical_harm",
            "rights_respect",
            "fairness_equity",
            "autonomy_respect",
            "legitimacy_trust",
            "epistemic_quality",
        ]

    def to_dict(self) -> Dict[str, float]:
        """Return all dimensions as a dict."""
        result = {name: getattr(self, name) for name in self.core_dimension_names()}
        result.update(self.extensions)
        return result

    def to_scalar(
        self,
        weights: Optional[Dict[str, float]] = None,
        invert_harm: bool = True,
    ) -> float:
        """
        Collapse MoralVector to a single scalar score for backward compatibility.

        Args:
            weights: Per-dimension weights. Defaults to DEFAULT_DIMENSION_WEIGHTS.
            invert_harm: If True, converts physical_harm to (1 - harm) for scoring.

        Returns:
            Weighted average score in [0, 1].
        """
        if weights is None:
            weights = DEFAULT_DIMENSION_WEIGHTS

        total_weight = 0.0
        weighted_sum = 0.0

        for dim_name in self.core_dimension_names():
            w = weights.get(dim_name, 1.0)
            value = getattr(self, dim_name)

            # Invert harm dimension so higher score = better
            if dim_name == "physical_harm" and invert_harm:
                value = 1.0 - value

            weighted_sum += w * value
            total_weight += w

        # Include extension dimensions if weighted
        for dim_name, value in self.extensions.items():
            w = weights.get(dim_name, 0.0)
            if w > 0:
                weighted_sum += w * value
                total_weight += w

        if total_weight == 0:
            return 0.5  # Neutral if no weights

        return weighted_sum / total_weight

    def has_veto(self) -> bool:
        """Return True if any veto flags are set."""
        return len(self.veto_flags) > 0

    def dominates(self, other: MoralVector) -> bool:
        """
        Check if this vector Pareto-dominates another.

        A vector dominates another if it is at least as good in all dimensions
        and strictly better in at least one dimension.

        Note: physical_harm is inverted (lower is better).
        """
        dominated_dims = 0
        strictly_better = False

        for dim_name in self.core_dimension_names():
            self_val = getattr(self, dim_name)
            other_val = getattr(other, dim_name)

            # For physical_harm, lower is better
            if dim_name == "physical_harm":
                if self_val > other_val:
                    return False  # Worse in this dimension
                if self_val < other_val:
                    strictly_better = True
            else:
                # For all other dimensions, higher is better
                if self_val < other_val:
                    return False  # Worse in this dimension
                if self_val > other_val:
                    strictly_better = True

            dominated_dims += 1

        return strictly_better

    def merge(
        self,
        other: MoralVector,
        strategy: str = "average",
        self_weight: float = 0.5,
    ) -> MoralVector:
        """
        Merge two MoralVectors.

        Args:
            other: The other vector to merge with.
            strategy: Merge strategy - "average", "min", "max", "weighted".
            self_weight: Weight for this vector when strategy="weighted".

        Returns:
            New merged MoralVector.
        """
        result_dims: Dict[str, float] = {}

        for dim_name in self.core_dimension_names():
            self_val = getattr(self, dim_name)
            other_val = getattr(other, dim_name)

            if strategy == "average":
                result_dims[dim_name] = (self_val + other_val) / 2
            elif strategy == "min":
                result_dims[dim_name] = min(self_val, other_val)
            elif strategy == "max":
                result_dims[dim_name] = max(self_val, other_val)
            elif strategy == "weighted":
                result_dims[dim_name] = (
                    self_weight * self_val + (1 - self_weight) * other_val
                )
            else:
                raise ValueError(f"Unknown merge strategy: {strategy}")

        # Merge extensions (average by default)
        merged_extensions: Dict[str, float] = {}
        all_ext_keys = set(self.extensions.keys()) | set(other.extensions.keys())
        for key in all_ext_keys:
            self_val = self.extensions.get(key, 0.5)
            other_val = other.extensions.get(key, 0.5)
            if strategy == "average":
                merged_extensions[key] = (self_val + other_val) / 2
            elif strategy == "min":
                merged_extensions[key] = min(self_val, other_val)
            elif strategy == "max":
                merged_extensions[key] = max(self_val, other_val)
            elif strategy == "weighted":
                merged_extensions[key] = (
                    self_weight * self_val + (1 - self_weight) * other_val
                )

        # Merge veto flags (union)
        merged_vetoes = list(set(self.veto_flags) | set(other.veto_flags))

        # Merge reason codes (union, preserving order)
        seen: set[str] = set()
        merged_reasons = []
        for code in self.reason_codes + other.reason_codes:
            if code not in seen:
                seen.add(code)
                merged_reasons.append(code)

        return MoralVector(
            physical_harm=result_dims["physical_harm"],
            rights_respect=result_dims["rights_respect"],
            fairness_equity=result_dims["fairness_equity"],
            autonomy_respect=result_dims["autonomy_respect"],
            legitimacy_trust=result_dims["legitimacy_trust"],
            epistemic_quality=result_dims["epistemic_quality"],
            extensions=merged_extensions,
            veto_flags=merged_vetoes,
            reason_codes=merged_reasons,
        )

    def distance(self, other: MoralVector, metric: str = "euclidean") -> float:
        """
        Compute distance to another MoralVector.

        Args:
            other: The other vector.
            metric: Distance metric - "euclidean", "manhattan", "chebyshev".

        Returns:
            Distance value (>= 0).
        """
        diffs = []
        for dim_name in self.core_dimension_names():
            self_val = getattr(self, dim_name)
            other_val = getattr(other, dim_name)
            diffs.append(abs(self_val - other_val))

        if metric == "euclidean":
            return math.sqrt(sum(d**2 for d in diffs))
        elif metric == "manhattan":
            return sum(diffs)
        elif metric == "chebyshev":
            return max(diffs) if diffs else 0.0
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def __add__(self, other: MoralVector) -> MoralVector:
        """Element-wise addition (for weighted aggregation)."""
        return MoralVector(
            physical_harm=min(1.0, self.physical_harm + other.physical_harm),
            rights_respect=min(1.0, self.rights_respect + other.rights_respect),
            fairness_equity=min(1.0, self.fairness_equity + other.fairness_equity),
            autonomy_respect=min(1.0, self.autonomy_respect + other.autonomy_respect),
            legitimacy_trust=min(1.0, self.legitimacy_trust + other.legitimacy_trust),
            epistemic_quality=min(
                1.0, self.epistemic_quality + other.epistemic_quality
            ),
            extensions={
                k: min(1.0, self.extensions.get(k, 0) + other.extensions.get(k, 0))
                for k in set(self.extensions) | set(other.extensions)
            },
            veto_flags=list(set(self.veto_flags) | set(other.veto_flags)),
            reason_codes=self.reason_codes + other.reason_codes,
        )

    def __mul__(self, scalar: float) -> MoralVector:
        """Scalar multiplication (for weighting)."""
        return MoralVector(
            physical_harm=max(0.0, min(1.0, self.physical_harm * scalar)),
            rights_respect=max(0.0, min(1.0, self.rights_respect * scalar)),
            fairness_equity=max(0.0, min(1.0, self.fairness_equity * scalar)),
            autonomy_respect=max(0.0, min(1.0, self.autonomy_respect * scalar)),
            legitimacy_trust=max(0.0, min(1.0, self.legitimacy_trust * scalar)),
            epistemic_quality=max(0.0, min(1.0, self.epistemic_quality * scalar)),
            extensions={
                k: max(0.0, min(1.0, v * scalar)) for k, v in self.extensions.items()
            },
            veto_flags=self.veto_flags.copy(),
            reason_codes=self.reason_codes.copy(),
        )

    def __rmul__(self, scalar: float) -> MoralVector:
        """Right scalar multiplication."""
        return self.__mul__(scalar)

    @classmethod
    def from_ethical_facts(cls, facts: EthicalFacts) -> MoralVector:
        """
        Extract a MoralVector from EthicalFacts.

        This provides a standard mapping from the structured facts
        to the moral vector dimensions.
        """
        veto_flags: List[str] = []
        reason_codes: List[str] = []

        # Physical harm from consequences
        physical_harm = facts.consequences.expected_harm

        # Rights respect from rights_and_duties
        rights_respect = 1.0
        if facts.rights_and_duties.violates_rights:
            rights_respect = 0.0
            veto_flags.append("RIGHTS_VIOLATION")
            reason_codes.append("rights_violated")
        elif not facts.rights_and_duties.has_valid_consent:
            rights_respect = 0.5
            reason_codes.append("consent_missing")

        # Fairness from justice_and_fairness
        fairness_equity = 1.0
        if facts.justice_and_fairness.discriminates_on_protected_attr:
            fairness_equity = 0.0
            veto_flags.append("DISCRIMINATION")
            reason_codes.append("protected_attr_discrimination")
        elif facts.justice_and_fairness.exploits_vulnerable_population:
            fairness_equity = 0.3
            reason_codes.append("exploits_vulnerable")
        elif not facts.justice_and_fairness.prioritizes_most_disadvantaged:
            fairness_equity = 0.7
            reason_codes.append("no_disadvantaged_priority")

        # Autonomy from autonomy_and_agency (if present)
        autonomy_respect = 1.0
        if facts.autonomy_and_agency is not None:
            aa = facts.autonomy_and_agency
            if aa.coercion_or_undue_influence:
                autonomy_respect = 0.2
                reason_codes.append("coercion_present")
            elif aa.manipulative_design_present:
                autonomy_respect = 0.4
                reason_codes.append("manipulative_design")
            elif not aa.has_meaningful_choice:
                autonomy_respect = 0.6
                reason_codes.append("limited_choice")

        # Legitimacy from procedural_and_legitimacy (if present)
        legitimacy_trust = 1.0
        if facts.procedural_and_legitimacy is not None:
            pl = facts.procedural_and_legitimacy
            if not pl.followed_approved_procedure:
                legitimacy_trust -= 0.3
                reason_codes.append("procedure_not_followed")
            if not pl.stakeholders_consulted:
                legitimacy_trust -= 0.2
                reason_codes.append("stakeholders_not_consulted")
            if not pl.decision_explainable_to_public:
                legitimacy_trust -= 0.2
                reason_codes.append("not_explainable")
            legitimacy_trust = max(0.0, legitimacy_trust)

        # Epistemic quality from epistemic_status (if present)
        epistemic_quality = 1.0
        if facts.epistemic_status is not None:
            es = facts.epistemic_status
            epistemic_quality = 1.0 - es.uncertainty_level
            if es.evidence_quality == "low":
                epistemic_quality = min(epistemic_quality, 0.3)
            elif es.evidence_quality == "medium":
                epistemic_quality = min(epistemic_quality, 0.6)
            if es.novel_situation_flag:
                epistemic_quality *= 0.8
                reason_codes.append("novel_situation")

        # Extension dimensions
        extensions: Dict[str, float] = {}

        # Privacy dimension from privacy_and_data (if present)
        if facts.privacy_and_data is not None:
            pd = facts.privacy_and_data
            privacy_level = 1.0 - pd.privacy_invasion_level
            if pd.secondary_use_without_consent:
                privacy_level *= 0.5
            extensions["privacy_level"] = privacy_level

        # Environmental dimension from societal_and_environmental (if present)
        if facts.societal_and_environmental is not None:
            se = facts.societal_and_environmental
            env_impact = 1.0 - se.environmental_harm
            extensions["environmental_impact"] = env_impact

        return cls(
            physical_harm=physical_harm,
            rights_respect=rights_respect,
            fairness_equity=fairness_equity,
            autonomy_respect=autonomy_respect,
            legitimacy_trust=legitimacy_trust,
            epistemic_quality=epistemic_quality,
            extensions=extensions,
            veto_flags=veto_flags,
            reason_codes=reason_codes,
        )

    @classmethod
    def zero(cls) -> MoralVector:
        """Create a zero vector (worst case for all dimensions)."""
        return cls(
            physical_harm=1.0,
            rights_respect=0.0,
            fairness_equity=0.0,
            autonomy_respect=0.0,
            legitimacy_trust=0.0,
            epistemic_quality=0.0,
        )

    @classmethod
    def ideal(cls) -> MoralVector:
        """Create an ideal vector (best case for all dimensions)."""
        return cls(
            physical_harm=0.0,
            rights_respect=1.0,
            fairness_equity=1.0,
            autonomy_respect=1.0,
            legitimacy_trust=1.0,
            epistemic_quality=1.0,
        )


__all__ = [
    "MoralVector",
    "DEFAULT_DIMENSION_WEIGHTS",
]
