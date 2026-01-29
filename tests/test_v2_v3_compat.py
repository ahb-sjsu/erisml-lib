# Copyright (c) 2026 Andrew H. Bond
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.
# ruff: noqa: E402
"""
Comprehensive tests for V2/V3 compatibility layer.

Tests conversion functions, round-trip invariance, and mixed-mode
operations between MoralVector (V2) and MoralTensor (V3).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from erisml.ethics.moral_vector import MoralVector
from erisml.ethics.moral_tensor import MoralTensor
from erisml.ethics.moral_landscape import MoralLandscape
from erisml.ethics.compat import (
    promote_v2_to_v3,
    collapse_v3_to_v2,
    ensure_tensor,
    ensure_vector,
    is_v3_compatible,
    promote_vectors_to_tensor,
    collapse_tensor_to_vectors,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_vector() -> MoralVector:
    """Standard MoralVector for testing."""
    return MoralVector(
        physical_harm=0.2,
        rights_respect=0.9,
        fairness_equity=0.8,
        autonomy_respect=0.85,
        privacy_protection=0.9,
        societal_environmental=0.8,
        virtue_care=0.85,
        legitimacy_trust=0.75,
        epistemic_quality=0.7,
    )


@pytest.fixture
def vetoed_vector() -> MoralVector:
    """MoralVector with veto flags."""
    return MoralVector(
        physical_harm=0.8,
        rights_respect=0.1,
        fairness_equity=0.3,
        autonomy_respect=0.4,
        privacy_protection=0.5,
        societal_environmental=0.4,
        virtue_care=0.3,
        legitimacy_trust=0.2,
        epistemic_quality=0.5,
        veto_flags=["RIGHTS_VIOLATION", "HIGH_HARM"],
        reason_codes=["rights_violated", "harm_above_threshold"],
    )


@pytest.fixture
def sample_rank1_tensor() -> MoralTensor:
    """Rank-1 tensor equivalent to sample_vector."""
    return MoralTensor.from_dense(
        np.array([0.2, 0.9, 0.8, 0.85, 0.9, 0.8, 0.85, 0.75, 0.7])
    )


@pytest.fixture
def sample_rank2_tensor() -> MoralTensor:
    """Rank-2 tensor with 3 parties."""
    data = np.array(
        [
            [0.1, 0.2, 0.3],  # physical_harm
            [0.9, 0.8, 0.7],  # rights_respect
            [0.8, 0.85, 0.9],  # fairness_equity
            [0.85, 0.8, 0.75],  # autonomy_respect
            [0.9, 0.85, 0.8],  # privacy_protection
            [0.8, 0.75, 0.7],  # societal_environmental
            [0.85, 0.9, 0.8],  # virtue_care
            [0.75, 0.8, 0.85],  # legitimacy_trust
            [0.7, 0.75, 0.8],  # epistemic_quality
        ]
    )
    return MoralTensor.from_dense(
        data,
        axis_labels={"n": ["alice", "bob", "carol"]},
    )


# =============================================================================
# Test promote_v2_to_v3
# =============================================================================


class TestPromoteV2ToV3:
    """Tests for MoralVector to MoralTensor promotion."""

    def test_basic_conversion(self, sample_vector: MoralVector):
        """Test basic V2 to V3 conversion."""
        tensor = promote_v2_to_v3(sample_vector)

        assert isinstance(tensor, MoralTensor)
        assert tensor.rank == 1
        assert tensor.shape == (9,)

    def test_preserves_values(self, sample_vector: MoralVector):
        """Test that promotion preserves dimension values."""
        tensor = promote_v2_to_v3(sample_vector)
        data = tensor.to_dense()

        assert np.isclose(data[0], 0.2)  # physical_harm
        assert np.isclose(data[1], 0.9)  # rights_respect
        assert np.isclose(data[2], 0.8)  # fairness_equity
        assert np.isclose(data[3], 0.85)  # autonomy_respect
        assert np.isclose(data[4], 0.9)  # privacy_protection
        assert np.isclose(data[5], 0.8)  # societal_environmental
        assert np.isclose(data[6], 0.85)  # virtue_care
        assert np.isclose(data[7], 0.75)  # legitimacy_trust
        assert np.isclose(data[8], 0.7)  # epistemic_quality

    def test_preserves_vetoes(self, vetoed_vector: MoralVector):
        """Test that promotion preserves veto flags."""
        tensor = promote_v2_to_v3(vetoed_vector)

        assert "RIGHTS_VIOLATION" in tensor.veto_flags
        assert "HIGH_HARM" in tensor.veto_flags

    def test_preserves_reason_codes(self, vetoed_vector: MoralVector):
        """Test that promotion preserves reason codes."""
        tensor = promote_v2_to_v3(vetoed_vector)

        assert "rights_violated" in tensor.reason_codes
        assert "harm_above_threshold" in tensor.reason_codes

    def test_promote_to_rank2(self, sample_vector: MoralVector):
        """Test promoting to rank-2 tensor."""
        tensor = promote_v2_to_v3(sample_vector, target_rank=2, axis_sizes={"n": 3})

        assert tensor.rank == 2
        assert tensor.shape == (9, 3)

        # Values should be broadcast
        data = tensor.to_dense()
        for i in range(3):
            assert np.isclose(data[0, i], 0.2)  # physical_harm broadcast

    def test_promote_to_rank2_requires_axis_sizes(self, sample_vector: MoralVector):
        """Test that rank > 1 requires axis_sizes."""
        with pytest.raises(ValueError, match="axis_sizes required"):
            promote_v2_to_v3(sample_vector, target_rank=2)


# =============================================================================
# Test collapse_v3_to_v2
# =============================================================================


class TestCollapseV3ToV2:
    """Tests for MoralTensor to MoralVector collapse."""

    def test_rank1_collapse(self, sample_rank1_tensor: MoralTensor):
        """Test collapsing rank-1 tensor (direct conversion)."""
        vector = collapse_v3_to_v2(sample_rank1_tensor)

        assert isinstance(vector, MoralVector)
        assert np.isclose(vector.physical_harm, 0.2)
        assert np.isclose(vector.rights_respect, 0.9)

    def test_mean_strategy(self, sample_rank2_tensor: MoralTensor):
        """Test mean collapse strategy."""
        vector = collapse_v3_to_v2(sample_rank2_tensor, strategy="mean")

        # physical_harm mean: (0.1 + 0.2 + 0.3) / 3 = 0.2
        assert np.isclose(vector.physical_harm, 0.2)
        # rights_respect mean: (0.9 + 0.8 + 0.7) / 3 = 0.8
        assert np.isclose(vector.rights_respect, 0.8)

    def test_worst_case_strategy(self, sample_rank2_tensor: MoralTensor):
        """Test worst-case collapse strategy."""
        vector = collapse_v3_to_v2(sample_rank2_tensor, strategy="worst_case")

        # For physical_harm: higher is worse, so max(0.1, 0.2, 0.3) = 0.3
        assert np.isclose(vector.physical_harm, 0.3)
        # For others: lower is worse, so min across parties
        assert np.isclose(vector.rights_respect, 0.7)  # min(0.9, 0.8, 0.7)
        assert np.isclose(vector.fairness_equity, 0.8)  # min(0.8, 0.85, 0.9)

    def test_best_case_strategy(self, sample_rank2_tensor: MoralTensor):
        """Test best-case collapse strategy."""
        vector = collapse_v3_to_v2(sample_rank2_tensor, strategy="best_case")

        # For physical_harm: lower is better, so min(0.1, 0.2, 0.3) = 0.1
        assert np.isclose(vector.physical_harm, 0.1)
        # For others: higher is better, so max across parties
        assert np.isclose(vector.rights_respect, 0.9)  # max(0.9, 0.8, 0.7)
        assert np.isclose(vector.fairness_equity, 0.9)  # max(0.8, 0.85, 0.9)

    def test_weighted_strategy_requires_weights(self, sample_rank2_tensor: MoralTensor):
        """Test that weighted strategy requires weights."""
        with pytest.raises(ValueError, match="requires weights"):
            collapse_v3_to_v2(sample_rank2_tensor, strategy="weighted")

    def test_unknown_strategy_raises(self, sample_rank2_tensor: MoralTensor):
        """Test that unknown strategy raises ValueError."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            collapse_v3_to_v2(sample_rank2_tensor, strategy="unknown")

    def test_preserves_vetoes(self):
        """Test that collapse preserves veto flags."""
        tensor = MoralTensor.from_dense(
            np.random.rand(9, 3),
            veto_flags=["RIGHTS_VIOLATION"],
            reason_codes=["test_reason"],
        )
        vector = collapse_v3_to_v2(tensor)

        assert "RIGHTS_VIOLATION" in vector.veto_flags
        assert "test_reason" in vector.reason_codes


# =============================================================================
# Test Round-Trip Invariance
# =============================================================================


class TestRoundTrip:
    """Tests for V2 <-> V3 round-trip invariance."""

    def test_v2_v3_v2_roundtrip(self, sample_vector: MoralVector):
        """Test V2 -> V3 -> V2 preserves values."""
        tensor = promote_v2_to_v3(sample_vector)
        recovered = collapse_v3_to_v2(tensor, strategy="mean")

        # Check all dimensions
        assert np.isclose(recovered.physical_harm, sample_vector.physical_harm)
        assert np.isclose(recovered.rights_respect, sample_vector.rights_respect)
        assert np.isclose(recovered.fairness_equity, sample_vector.fairness_equity)
        assert np.isclose(recovered.autonomy_respect, sample_vector.autonomy_respect)
        assert np.isclose(
            recovered.privacy_protection, sample_vector.privacy_protection
        )
        assert np.isclose(
            recovered.societal_environmental, sample_vector.societal_environmental
        )
        assert np.isclose(recovered.virtue_care, sample_vector.virtue_care)
        assert np.isclose(recovered.legitimacy_trust, sample_vector.legitimacy_trust)
        assert np.isclose(recovered.epistemic_quality, sample_vector.epistemic_quality)

    def test_v3_v2_v3_roundtrip_rank1(self, sample_rank1_tensor: MoralTensor):
        """Test V3 rank-1 -> V2 -> V3 preserves values."""
        vector = collapse_v3_to_v2(sample_rank1_tensor)
        recovered = promote_v2_to_v3(vector)

        original_data = sample_rank1_tensor.to_dense()
        recovered_data = recovered.to_dense()

        np.testing.assert_array_almost_equal(original_data, recovered_data)

    def test_roundtrip_preserves_vetoes(self, vetoed_vector: MoralVector):
        """Test that round-trip preserves veto flags."""
        tensor = promote_v2_to_v3(vetoed_vector)
        recovered = collapse_v3_to_v2(tensor)

        assert set(recovered.veto_flags) == set(vetoed_vector.veto_flags)
        assert set(recovered.reason_codes) == set(vetoed_vector.reason_codes)


# =============================================================================
# Test MoralVector V3 Integration Methods
# =============================================================================


class TestMoralVectorIntegration:
    """Tests for MoralVector V3 integration methods."""

    def test_to_tensor_method(self, sample_vector: MoralVector):
        """Test MoralVector.to_tensor() method."""
        tensor = sample_vector.to_tensor()

        assert isinstance(tensor, MoralTensor)
        assert tensor.rank == 1
        data = tensor.to_dense()
        assert np.isclose(data[0], sample_vector.physical_harm)

    def test_from_tensor_classmethod(self, sample_rank1_tensor: MoralTensor):
        """Test MoralVector.from_tensor() classmethod."""
        vector = MoralVector.from_tensor(sample_rank1_tensor)

        assert isinstance(vector, MoralVector)
        assert np.isclose(vector.physical_harm, 0.2)

    def test_from_tensor_with_strategy(self, sample_rank2_tensor: MoralTensor):
        """Test MoralVector.from_tensor() with collapse strategy."""
        vector = MoralVector.from_tensor(sample_rank2_tensor, strategy="worst_case")

        # worst_case for physical_harm: max = 0.3
        assert np.isclose(vector.physical_harm, 0.3)

    def test_is_v3_compatible(self, sample_vector: MoralVector):
        """Test MoralVector.is_v3_compatible() method."""
        assert sample_vector.is_v3_compatible() is True


# =============================================================================
# Test Utility Functions
# =============================================================================


class TestUtilityFunctions:
    """Tests for ensure_tensor, ensure_vector, is_v3_compatible."""

    def test_ensure_tensor_from_vector(self, sample_vector: MoralVector):
        """Test ensure_tensor with MoralVector input."""
        result = ensure_tensor(sample_vector)

        assert isinstance(result, MoralTensor)

    def test_ensure_tensor_from_tensor(self, sample_rank1_tensor: MoralTensor):
        """Test ensure_tensor with MoralTensor input."""
        result = ensure_tensor(sample_rank1_tensor)

        assert result is sample_rank1_tensor  # Should return same object

    def test_ensure_tensor_invalid_type(self):
        """Test ensure_tensor with invalid type."""
        with pytest.raises(TypeError, match="Expected MoralVector or MoralTensor"):
            ensure_tensor("invalid")

    def test_ensure_vector_from_tensor(self, sample_rank1_tensor: MoralTensor):
        """Test ensure_vector with MoralTensor input."""
        result = ensure_vector(sample_rank1_tensor)

        assert isinstance(result, MoralVector)

    def test_ensure_vector_from_vector(self, sample_vector: MoralVector):
        """Test ensure_vector with MoralVector input."""
        result = ensure_vector(sample_vector)

        assert result is sample_vector  # Should return same object

    def test_ensure_vector_with_strategy(self, sample_rank2_tensor: MoralTensor):
        """Test ensure_vector with collapse strategy."""
        result = ensure_vector(sample_rank2_tensor, strategy="worst_case")

        # worst_case for physical_harm: max = 0.3
        assert np.isclose(result.physical_harm, 0.3)

    def test_is_v3_compatible_vector(self, sample_vector: MoralVector):
        """Test is_v3_compatible with MoralVector."""
        assert is_v3_compatible(sample_vector) is True

    def test_is_v3_compatible_tensor(self, sample_rank1_tensor: MoralTensor):
        """Test is_v3_compatible with MoralTensor."""
        assert is_v3_compatible(sample_rank1_tensor) is True

    def test_is_v3_compatible_invalid(self):
        """Test is_v3_compatible with invalid type."""
        assert is_v3_compatible("invalid") is False


# =============================================================================
# Test Batch Conversion Functions
# =============================================================================


class TestBatchConversion:
    """Tests for batch conversion functions."""

    def test_promote_vectors_to_tensor(self, sample_vector: MoralVector):
        """Test converting multiple vectors to a tensor."""
        vectors = {
            "alice": sample_vector,
            "bob": MoralVector(
                physical_harm=0.3,
                rights_respect=0.8,
                fairness_equity=0.7,
                autonomy_respect=0.75,
                privacy_protection=0.8,
                societal_environmental=0.7,
                virtue_care=0.8,
                legitimacy_trust=0.7,
                epistemic_quality=0.6,
            ),
        }
        tensor = promote_vectors_to_tensor(vectors)

        assert tensor.rank == 2
        assert tensor.shape == (9, 2)
        assert "n" in tensor.axis_labels

    def test_collapse_tensor_to_vectors(self, sample_rank2_tensor: MoralTensor):
        """Test converting tensor to multiple vectors."""
        vectors = collapse_tensor_to_vectors(sample_rank2_tensor)

        assert len(vectors) == 3
        assert "alice" in vectors
        assert "bob" in vectors
        assert "carol" in vectors

        # Check alice's values
        alice = vectors["alice"]
        assert np.isclose(alice.physical_harm, 0.1)
        assert np.isclose(alice.rights_respect, 0.9)

    def test_collapse_tensor_requires_rank2(self, sample_rank1_tensor: MoralTensor):
        """Test that collapse_tensor_to_vectors requires rank-2."""
        with pytest.raises(ValueError, match="Expected rank-2"):
            collapse_tensor_to_vectors(sample_rank1_tensor)


# =============================================================================
# Test MoralLandscape Mixed Input
# =============================================================================


class TestMoralLandscapeMixedInput:
    """Tests for MoralLandscape with mixed Vector/Tensor inputs."""

    def test_add_vector_assessment(self, sample_vector: MoralVector):
        """Test adding MoralVector to landscape."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_vector)

        assert len(landscape) == 1
        retrieved = landscape.get("option_a")
        assert retrieved is sample_vector

    def test_add_tensor_assessment(self, sample_rank2_tensor: MoralTensor):
        """Test adding MoralTensor to landscape."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_rank2_tensor)

        assert len(landscape) == 1
        retrieved = landscape.get("option_a")
        # Should be collapsed to vector
        assert isinstance(retrieved, MoralVector)

    def test_tensor_cached(self, sample_rank2_tensor: MoralTensor):
        """Test that original tensor is cached."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_rank2_tensor)

        assert landscape.has_tensor("option_a")
        cached = landscape.get_tensor("option_a")
        assert cached is sample_rank2_tensor

    def test_vector_not_cached_as_tensor(self, sample_vector: MoralVector):
        """Test that vectors are not cached as tensors."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_vector)

        assert not landscape.has_tensor("option_a")
        # get_tensor should promote the vector
        tensor = landscape.get_tensor("option_a")
        assert isinstance(tensor, MoralTensor)

    def test_mixed_assessments(
        self, sample_vector: MoralVector, sample_rank2_tensor: MoralTensor
    ):
        """Test adding both vectors and tensors."""
        landscape = MoralLandscape()
        landscape.add("vector_option", sample_vector)
        landscape.add("tensor_option", sample_rank2_tensor)

        assert len(landscape) == 2

        # Both should be retrievable as vectors
        v1 = landscape.get("vector_option")
        v2 = landscape.get("tensor_option")
        assert isinstance(v1, MoralVector)
        assert isinstance(v2, MoralVector)

    def test_collapse_strategy_parameter(self, sample_rank2_tensor: MoralTensor):
        """Test custom collapse strategy when adding tensor."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_rank2_tensor, collapse_strategy="worst_case")

        retrieved = landscape.get("option_a")
        # worst_case for physical_harm: max = 0.3
        assert np.isclose(retrieved.physical_harm, 0.3)

    def test_default_collapse_strategy(self, sample_rank2_tensor: MoralTensor):
        """Test default collapse strategy configuration."""
        landscape = MoralLandscape(default_collapse_strategy="best_case")
        landscape.add("option_a", sample_rank2_tensor)

        retrieved = landscape.get("option_a")
        # best_case for physical_harm: min = 0.1
        assert np.isclose(retrieved.physical_harm, 0.1)

    def test_remove_clears_tensor_cache(self, sample_rank2_tensor: MoralTensor):
        """Test that remove clears tensor cache."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_rank2_tensor)

        assert landscape.has_tensor("option_a")

        landscape.remove("option_a")

        assert not landscape.has_tensor("option_a")
        assert landscape.get("option_a") is None

    def test_filter_vetoed_preserves_tensor_cache(self):
        """Test that filter_vetoed preserves tensor cache."""
        good_tensor = MoralTensor.from_dense(np.array([0.2] * 9))
        bad_tensor = MoralTensor.from_dense(
            np.array([0.8] * 9),
            veto_flags=["VETO"],
        )

        landscape = MoralLandscape()
        landscape.add("good", good_tensor)
        landscape.add("bad", bad_tensor)

        filtered = landscape.filter_vetoed()

        assert len(filtered) == 1
        assert "good" in filtered.vectors
        assert filtered.has_tensor("good")


# =============================================================================
# Test Backward Compatibility
# =============================================================================


class TestBackwardCompatibility:
    """Tests for backward compatibility with V2 code."""

    def test_existing_v2_code_unchanged(self, sample_vector: MoralVector):
        """Test that existing V2 code still works."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_vector)

        # All existing operations should work
        assert len(landscape) == 1
        assert landscape.get("option_a") is sample_vector
        assert landscape.pareto_frontier() == ["option_a"]

    def test_v2_aggregation_still_works(self, sample_vector: MoralVector):
        """Test that V2 aggregation still works."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_vector)
        landscape.add(
            "option_b",
            MoralVector(
                physical_harm=0.3,
                rights_respect=0.8,
                fairness_equity=0.7,
                autonomy_respect=0.75,
                privacy_protection=0.8,
                societal_environmental=0.7,
                virtue_care=0.8,
                legitimacy_trust=0.7,
                epistemic_quality=0.6,
            ),
        )

        aggregated = landscape.aggregate(strategy="average")
        assert isinstance(aggregated, MoralVector)

    def test_v2_distance_still_works(self, sample_vector: MoralVector):
        """Test that V2 distance metrics still work."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_vector)
        landscape.add(
            "option_b",
            MoralVector(
                physical_harm=0.3,
                rights_respect=0.8,
                fairness_equity=0.7,
                autonomy_respect=0.75,
                privacy_protection=0.8,
                societal_environmental=0.7,
                virtue_care=0.8,
                legitimacy_trust=0.7,
                epistemic_quality=0.6,
            ),
        )

        distance = landscape.distance("option_a", "option_b")
        assert distance > 0

    def test_v2_rank_by_scalar_still_works(self, sample_vector: MoralVector):
        """Test that V2 rank_by_scalar still works."""
        landscape = MoralLandscape()
        landscape.add("option_a", sample_vector)
        landscape.add(
            "option_b",
            MoralVector(
                physical_harm=0.3,
                rights_respect=0.8,
                fairness_equity=0.7,
                autonomy_respect=0.75,
                privacy_protection=0.8,
                societal_environmental=0.7,
                virtue_care=0.8,
                legitimacy_trust=0.7,
                epistemic_quality=0.6,
            ),
        )

        ranked = landscape.rank_by_scalar()
        assert len(ranked) == 2
        assert ranked[0][0] in ["option_a", "option_b"]


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_vector_promotion(self):
        """Test promoting a 'zero' (worst-case) vector."""
        zero_vec = MoralVector.zero()
        tensor = promote_v2_to_v3(zero_vec)

        data = tensor.to_dense()
        # MoralVector.zero() = worst case: physical_harm=1.0, others=0.0
        expected = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        np.testing.assert_array_equal(data, expected)

    def test_ideal_vector_promotion(self):
        """Test promoting an ideal vector."""
        ideal_vec = MoralVector.ideal()
        tensor = promote_v2_to_v3(ideal_vec)

        data = tensor.to_dense()
        expected = np.array([0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        np.testing.assert_array_equal(data, expected)

    def test_collapse_single_party_tensor(self):
        """Test collapsing a tensor with single party."""
        single_party = MoralTensor.from_dense(
            np.array([[0.2], [0.9], [0.8], [0.85], [0.9], [0.8], [0.85], [0.75], [0.7]])
        )
        vector = collapse_v3_to_v2(single_party, strategy="mean")

        assert np.isclose(vector.physical_harm, 0.2)
        assert np.isclose(vector.rights_respect, 0.9)

    def test_empty_landscape_operations(self):
        """Test operations on empty landscape."""
        landscape = MoralLandscape()

        assert len(landscape) == 0
        assert landscape.pareto_frontier() == []
        assert landscape.dominated_options() == []
        assert landscape.get("nonexistent") is None
        assert landscape.get_tensor("nonexistent") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
