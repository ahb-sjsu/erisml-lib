# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for MoralVector.

Covers:
- Creation and validation
- Scalar collapse
- Pareto dominance
- Merge operations
- Distance metrics
- Factory methods
"""

import pytest
from erisml.ethics.moral_vector import MoralVector


class TestMoralVectorCreation:
    """Tests for MoralVector creation and validation."""

    def test_default_creation(self):
        """Test default MoralVector has expected values."""
        vec = MoralVector()
        assert vec.physical_harm == 0.0
        assert vec.rights_respect == 1.0
        assert vec.fairness_equity == 1.0

    def test_custom_values(self):
        """Test MoralVector with custom values."""
        vec = MoralVector(physical_harm=0.5, rights_respect=0.8)
        assert vec.physical_harm == 0.5
        assert vec.rights_respect == 0.8

    def test_validation_rejects_out_of_bounds(self):
        """Test that values outside [0, 1] raise ValueError."""
        with pytest.raises(ValueError):
            MoralVector(physical_harm=1.5)

        with pytest.raises(ValueError):
            MoralVector(rights_respect=-0.1)

    def test_extensions_accepted(self):
        """Test that extension dimensions work."""
        vec = MoralVector(extensions={"custom_dim": 0.7})
        assert vec.extensions["custom_dim"] == 0.7

    def test_extensions_validated(self):
        """Test that extension dimensions are validated."""
        with pytest.raises(ValueError):
            MoralVector(extensions={"bad_dim": 1.5})


class TestMoralVectorScalar:
    """Tests for scalar collapse."""

    def test_to_scalar_default_weights(self, baseline_moral_vector):
        """Test scalar collapse with default weights."""
        score = baseline_moral_vector.to_scalar()
        assert 0.0 <= score <= 1.0

    def test_to_scalar_custom_weights(self, baseline_moral_vector):
        """Test scalar collapse with custom weights."""
        weights = {"physical_harm": 2.0, "rights_respect": 1.0}
        score = baseline_moral_vector.to_scalar(weights=weights)
        assert 0.0 <= score <= 1.0

    def test_to_scalar_inverts_harm(self):
        """Test that physical_harm is inverted (low harm = high score)."""
        low_harm = MoralVector(physical_harm=0.1)
        high_harm = MoralVector(physical_harm=0.9)
        assert low_harm.to_scalar() > high_harm.to_scalar()


class TestMoralVectorDominance:
    """Tests for Pareto dominance."""

    def test_dominates_strictly_better(self):
        """Test dominance when strictly better in all dimensions."""
        better = MoralVector(
            physical_harm=0.1,  # Lower harm is better
            rights_respect=0.9,
            fairness_equity=0.9,
        )
        worse = MoralVector(
            physical_harm=0.5,
            rights_respect=0.5,
            fairness_equity=0.5,
        )
        assert better.dominates(worse)
        assert not worse.dominates(better)

    def test_no_dominance_when_incomparable(self):
        """Test no dominance for incomparable vectors."""
        vec1 = MoralVector(physical_harm=0.2, rights_respect=0.8)
        vec2 = MoralVector(physical_harm=0.4, rights_respect=0.9)
        # vec1 is better on harm, vec2 is better on rights
        assert not vec1.dominates(vec2)
        assert not vec2.dominates(vec1)


class TestMoralVectorMerge:
    """Tests for merge operations."""

    def test_merge_average(self, baseline_moral_vector):
        """Test average merge strategy."""
        other = MoralVector(physical_harm=0.4, rights_respect=0.7)
        merged = baseline_moral_vector.merge(other, strategy="average")

        expected_harm = (baseline_moral_vector.physical_harm + 0.4) / 2
        assert abs(merged.physical_harm - expected_harm) < 0.01

    def test_merge_min(self, baseline_moral_vector):
        """Test min merge strategy."""
        other = MoralVector(physical_harm=0.4, rights_respect=0.7)
        merged = baseline_moral_vector.merge(other, strategy="min")

        assert merged.rights_respect == min(baseline_moral_vector.rights_respect, 0.7)

    def test_merge_combines_vetoes(self):
        """Test that merge combines veto flags."""
        vec1 = MoralVector(veto_flags=["FLAG1"])
        vec2 = MoralVector(veto_flags=["FLAG2"])
        merged = vec1.merge(vec2)
        assert "FLAG1" in merged.veto_flags
        assert "FLAG2" in merged.veto_flags


class TestMoralVectorDistance:
    """Tests for distance metrics."""

    def test_distance_euclidean(self, baseline_moral_vector):
        """Test Euclidean distance."""
        other = MoralVector()
        dist = baseline_moral_vector.distance(other, metric="euclidean")
        assert dist >= 0.0

    def test_distance_manhattan(self, baseline_moral_vector):
        """Test Manhattan distance."""
        other = MoralVector()
        dist = baseline_moral_vector.distance(other, metric="manhattan")
        assert dist >= 0.0

    def test_distance_to_self_is_zero(self, baseline_moral_vector):
        """Test that distance to self is zero."""
        dist = baseline_moral_vector.distance(baseline_moral_vector)
        assert dist == 0.0


class TestMoralVectorVeto:
    """Tests for veto functionality."""

    def test_has_veto_when_flags_present(self, vetoed_moral_vector):
        """Test has_veto returns True when flags present."""
        assert vetoed_moral_vector.has_veto()

    def test_has_veto_false_when_no_flags(self, baseline_moral_vector):
        """Test has_veto returns False when no flags."""
        assert not baseline_moral_vector.has_veto()


class TestMoralVectorFactories:
    """Tests for factory methods."""

    def test_zero_vector(self):
        """Test zero vector (worst case)."""
        zero = MoralVector.zero()
        assert zero.physical_harm == 1.0  # Max harm
        assert zero.rights_respect == 0.0  # No respect

    def test_ideal_vector(self):
        """Test ideal vector (best case)."""
        ideal = MoralVector.ideal()
        assert ideal.physical_harm == 0.0  # No harm
        assert ideal.rights_respect == 1.0  # Full respect

    def test_from_ethical_facts(self, baseline_ethical_facts):
        """Test creation from EthicalFacts."""
        vec = MoralVector.from_ethical_facts(baseline_ethical_facts)
        assert 0.0 <= vec.physical_harm <= 1.0
        assert 0.0 <= vec.rights_respect <= 1.0

    def test_from_ethical_facts_captures_harm(self, baseline_ethical_facts):
        """Test that harm is captured from consequences."""
        vec = MoralVector.from_ethical_facts(baseline_ethical_facts)
        assert vec.physical_harm == baseline_ethical_facts.consequences.expected_harm

    def test_from_ethical_facts_adds_veto_on_rights_violation(
        self, rights_violating_facts
    ):
        """Test that rights violation adds veto flag."""
        vec = MoralVector.from_ethical_facts(rights_violating_facts)
        assert "RIGHTS_VIOLATION" in vec.veto_flags


class TestMoralVectorArithmetic:
    """Tests for arithmetic operations."""

    def test_add_vectors(self):
        """Test vector addition."""
        vec1 = MoralVector(physical_harm=0.2, rights_respect=0.3)
        vec2 = MoralVector(physical_harm=0.3, rights_respect=0.4)
        result = vec1 + vec2
        assert result.physical_harm == 0.5
        assert result.rights_respect == 0.7

    def test_add_clamps_to_one(self):
        """Test that addition clamps to 1.0."""
        vec1 = MoralVector(physical_harm=0.7)
        vec2 = MoralVector(physical_harm=0.5)
        result = vec1 + vec2
        assert result.physical_harm == 1.0

    def test_scalar_multiply(self):
        """Test scalar multiplication."""
        vec = MoralVector(physical_harm=0.4, rights_respect=0.8)
        result = vec * 0.5
        assert abs(result.physical_harm - 0.2) < 0.01
        assert abs(result.rights_respect - 0.4) < 0.01

    def test_rmul(self):
        """Test right multiplication."""
        vec = MoralVector(physical_harm=0.4)
        result = 0.5 * vec
        assert abs(result.physical_harm - 0.2) < 0.01
