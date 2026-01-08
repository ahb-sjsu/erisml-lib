# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
MoralLandscape: Collection operations for MoralVectors.

Provides Pareto frontier computation, dominated option identification,
and multi-objective optimization utilities for ethical decision-making.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from erisml.ethics.moral_vector import MoralVector


@dataclass
class MoralLandscape:
    """
    A collection of MoralVectors representing the ethical landscape of options.

    Provides operations for:
    - Pareto frontier identification
    - Dominated option filtering
    - Distance and similarity metrics
    - Trade-off analysis
    """

    vectors: Dict[str, MoralVector] = field(default_factory=dict)
    """Mapping from option_id to MoralVector."""

    def __len__(self) -> int:
        """Return number of options in the landscape."""
        return len(self.vectors)

    def add(self, option_id: str, vector: MoralVector) -> None:
        """Add a vector to the landscape."""
        self.vectors[option_id] = vector

    def get(self, option_id: str) -> Optional[MoralVector]:
        """Get a vector by option_id."""
        return self.vectors.get(option_id)

    def remove(self, option_id: str) -> Optional[MoralVector]:
        """Remove and return a vector by option_id."""
        return self.vectors.pop(option_id, None)

    def pareto_frontier(self) -> List[str]:
        """
        Identify the Pareto frontier of options.

        An option is on the Pareto frontier if no other option
        dominates it (is at least as good in all dimensions and
        strictly better in at least one).

        Returns:
            List of option_ids that are Pareto-optimal.
        """
        if not self.vectors:
            return []

        frontier: List[str] = []
        option_ids = list(self.vectors.keys())

        for candidate_id in option_ids:
            candidate = self.vectors[candidate_id]
            is_dominated = False

            for other_id in option_ids:
                if other_id == candidate_id:
                    continue
                other = self.vectors[other_id]
                if other.dominates(candidate):
                    is_dominated = True
                    break

            if not is_dominated:
                frontier.append(candidate_id)

        return frontier

    def dominated_options(self) -> List[str]:
        """
        Identify dominated options (not on the Pareto frontier).

        Returns:
            List of option_ids that are dominated by at least one other option.
        """
        frontier = set(self.pareto_frontier())
        return [oid for oid in self.vectors.keys() if oid not in frontier]

    def filter_vetoed(self) -> MoralLandscape:
        """
        Return a new landscape with vetoed options removed.

        Returns:
            New MoralLandscape containing only non-vetoed options.
        """
        filtered = {oid: vec for oid, vec in self.vectors.items() if not vec.has_veto()}
        return MoralLandscape(vectors=filtered)

    def vetoed_options(self) -> List[Tuple[str, List[str]]]:
        """
        Return list of vetoed options with their veto flags.

        Returns:
            List of (option_id, veto_flags) tuples.
        """
        return [
            (oid, vec.veto_flags) for oid, vec in self.vectors.items() if vec.has_veto()
        ]

    def distance(
        self,
        option_id_1: str,
        option_id_2: str,
        metric: str = "euclidean",
    ) -> float:
        """
        Compute distance between two options in the moral space.

        Args:
            option_id_1: First option ID.
            option_id_2: Second option ID.
            metric: Distance metric - "euclidean", "manhattan", "chebyshev".

        Returns:
            Distance between the two vectors.

        Raises:
            KeyError: If either option_id is not in the landscape.
        """
        v1 = self.vectors[option_id_1]
        v2 = self.vectors[option_id_2]
        return v1.distance(v2, metric=metric)

    def nearest_to_ideal(
        self,
        ideal: Optional[MoralVector] = None,
        metric: str = "euclidean",
    ) -> Optional[str]:
        """
        Find the option nearest to an ideal point.

        Args:
            ideal: The ideal point. Defaults to MoralVector.ideal().
            metric: Distance metric to use.

        Returns:
            option_id of the nearest option, or None if landscape is empty.
        """
        if not self.vectors:
            return None

        if ideal is None:
            ideal = MoralVector.ideal()

        best_id: Optional[str] = None
        best_dist = float("inf")

        for oid, vec in self.vectors.items():
            dist = vec.distance(ideal, metric=metric)
            if dist < best_dist:
                best_dist = dist
                best_id = oid

        return best_id

    def rank_by_scalar(
        self,
        weights: Optional[Dict[str, float]] = None,
        ascending: bool = False,
    ) -> List[Tuple[str, float]]:
        """
        Rank options by their scalar collapse.

        Args:
            weights: Per-dimension weights for scalar collapse.
            ascending: If True, sort worst-to-best. Default is best-to-worst.

        Returns:
            List of (option_id, score) tuples, sorted by score.
        """
        scores = [
            (oid, vec.to_scalar(weights=weights)) for oid, vec in self.vectors.items()
        ]
        scores.sort(key=lambda x: x[1], reverse=not ascending)
        return scores

    def trade_off_pairs(
        self,
        dim1: str,
        dim2: str,
    ) -> List[Tuple[str, float, float]]:
        """
        Extract trade-off pairs for two dimensions.

        Useful for visualizing trade-offs between competing values.

        Args:
            dim1: First dimension name (e.g., "physical_harm").
            dim2: Second dimension name (e.g., "autonomy_respect").

        Returns:
            List of (option_id, dim1_value, dim2_value) tuples.
        """
        result: List[Tuple[str, float, float]] = []
        for oid, vec in self.vectors.items():
            if dim1 in vec.extensions:
                v1 = vec.extensions[dim1]
            else:
                v1 = getattr(vec, dim1, None)
                if v1 is None:
                    continue

            if dim2 in vec.extensions:
                v2 = vec.extensions[dim2]
            else:
                v2 = getattr(vec, dim2, None)
                if v2 is None:
                    continue

            result.append((oid, v1, v2))
        return result

    def aggregate(
        self,
        strategy: str = "average",
        weights: Optional[Dict[str, float]] = None,
    ) -> MoralVector:
        """
        Aggregate all vectors into a single representative vector.

        Args:
            strategy: Aggregation strategy - "average", "median", "min", "max".
            weights: Per-option weights (option_id -> weight).

        Returns:
            Aggregated MoralVector.

        Raises:
            ValueError: If landscape is empty.
        """
        if not self.vectors:
            raise ValueError("Cannot aggregate empty landscape")

        if weights is None:
            weights = {oid: 1.0 for oid in self.vectors}

        if strategy == "average":
            return self._aggregate_weighted_average(weights)
        elif strategy == "min":
            return self._aggregate_min()
        elif strategy == "max":
            return self._aggregate_max()
        else:
            raise ValueError(f"Unknown aggregation strategy: {strategy}")

    def _aggregate_weighted_average(
        self,
        weights: Dict[str, float],
    ) -> MoralVector:
        """Compute weighted average of all vectors."""
        total_weight = sum(weights.get(oid, 1.0) for oid in self.vectors)
        if total_weight == 0:
            total_weight = len(self.vectors)

        # Initialize accumulators
        dims = MoralVector.core_dimension_names()
        sums = {dim: 0.0 for dim in dims}
        ext_sums: Dict[str, float] = {}
        ext_counts: Dict[str, int] = {}
        all_vetoes: Set[str] = set()
        all_reasons: List[str] = []

        for oid, vec in self.vectors.items():
            w = weights.get(oid, 1.0) / total_weight
            for dim in dims:
                sums[dim] += w * getattr(vec, dim)

            for ext_key, ext_val in vec.extensions.items():
                if ext_key not in ext_sums:
                    ext_sums[ext_key] = 0.0
                    ext_counts[ext_key] = 0
                ext_sums[ext_key] += w * ext_val
                ext_counts[ext_key] += 1

            all_vetoes.update(vec.veto_flags)
            all_reasons.extend(vec.reason_codes)

        # Normalize extension sums
        extensions = {k: v for k, v in ext_sums.items()}

        return MoralVector(
            physical_harm=sums["physical_harm"],
            rights_respect=sums["rights_respect"],
            fairness_equity=sums["fairness_equity"],
            autonomy_respect=sums["autonomy_respect"],
            legitimacy_trust=sums["legitimacy_trust"],
            epistemic_quality=sums["epistemic_quality"],
            extensions=extensions,
            veto_flags=list(all_vetoes),
            reason_codes=list(dict.fromkeys(all_reasons)),  # Dedupe preserving order
        )

    def _aggregate_min(self) -> MoralVector:
        """Compute element-wise minimum across all vectors."""
        dims = MoralVector.core_dimension_names()
        mins = {dim: 1.0 for dim in dims}
        ext_mins: Dict[str, float] = {}
        all_vetoes: Set[str] = set()
        all_reasons: List[str] = []

        for vec in self.vectors.values():
            for dim in dims:
                mins[dim] = min(mins[dim], getattr(vec, dim))

            for ext_key, ext_val in vec.extensions.items():
                if ext_key not in ext_mins:
                    ext_mins[ext_key] = 1.0
                ext_mins[ext_key] = min(ext_mins[ext_key], ext_val)

            all_vetoes.update(vec.veto_flags)
            all_reasons.extend(vec.reason_codes)

        return MoralVector(
            physical_harm=mins["physical_harm"],
            rights_respect=mins["rights_respect"],
            fairness_equity=mins["fairness_equity"],
            autonomy_respect=mins["autonomy_respect"],
            legitimacy_trust=mins["legitimacy_trust"],
            epistemic_quality=mins["epistemic_quality"],
            extensions=ext_mins,
            veto_flags=list(all_vetoes),
            reason_codes=list(dict.fromkeys(all_reasons)),
        )

    def _aggregate_max(self) -> MoralVector:
        """Compute element-wise maximum across all vectors."""
        dims = MoralVector.core_dimension_names()
        maxs = {dim: 0.0 for dim in dims}
        ext_maxs: Dict[str, float] = {}
        all_vetoes: Set[str] = set()
        all_reasons: List[str] = []

        for vec in self.vectors.values():
            for dim in dims:
                maxs[dim] = max(maxs[dim], getattr(vec, dim))

            for ext_key, ext_val in vec.extensions.items():
                if ext_key not in ext_maxs:
                    ext_maxs[ext_key] = 0.0
                ext_maxs[ext_key] = max(ext_maxs[ext_key], ext_val)

            all_vetoes.update(vec.veto_flags)
            all_reasons.extend(vec.reason_codes)

        return MoralVector(
            physical_harm=maxs["physical_harm"],
            rights_respect=maxs["rights_respect"],
            fairness_equity=maxs["fairness_equity"],
            autonomy_respect=maxs["autonomy_respect"],
            legitimacy_trust=maxs["legitimacy_trust"],
            epistemic_quality=maxs["epistemic_quality"],
            extensions=ext_maxs,
            veto_flags=list(all_vetoes),
            reason_codes=list(dict.fromkeys(all_reasons)),
        )


__all__ = [
    "MoralLandscape",
]
