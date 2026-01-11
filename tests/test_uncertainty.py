# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for DEME V3 Uncertainty Quantification (Sprint 14).

Tests Monte Carlo uncertainty propagation, risk measures, and
decision support under uncertainty.
"""

import pytest
import numpy as np
from numpy.testing import assert_allclose

from erisml.ethics.uncertainty import (
    # Types
    DistributionType,
    AggregationMethod,
    UncertaintyBounds,
    UncertainValue,
    UncertaintyAnalysis,
    # Sample generation
    generate_samples,
    generate_moral_samples,
    # Statistics
    expected_value,
    variance,
    std_dev,
    percentiles,
    confidence_interval,
    # Risk measures
    cvar,
    cvar_upper,
    worst_case,
    best_case,
    value_at_risk,
    # Aggregation
    aggregate_samples,
    # Analysis
    analyze_uncertainty,
    propagate_uncertainty,
    # Decision support
    compare_under_uncertainty,
    stochastic_dominance,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def rng():
    """Reproducible random number generator."""
    return np.random.default_rng(42)


@pytest.fixture
def sample_values(rng):
    """Sample values for testing."""
    return rng.uniform(0.3, 0.7, size=(9, 5))


@pytest.fixture
def sample_samples(rng):
    """Sample Monte Carlo samples (shape: (9, 1000))."""
    return rng.normal(0.5, 0.1, size=(9, 1000)).clip(0, 1)


# =============================================================================
# Test UncertaintyBounds
# =============================================================================


class TestUncertaintyBounds:
    """Tests for UncertaintyBounds dataclass."""

    def test_creation(self):
        """UncertaintyBounds should be created correctly."""
        bounds = UncertaintyBounds(
            mean=0.5,
            std=0.1,
            lower=0.3,
            upper=0.7,
            confidence=0.90,
        )
        assert bounds.mean == 0.5
        assert bounds.std == 0.1
        assert bounds.lower == 0.3
        assert bounds.upper == 0.7
        assert bounds.confidence == 0.90

    def test_contains(self):
        """contains should check if value is within bounds."""
        bounds = UncertaintyBounds(0.5, 0.1, 0.3, 0.7, 0.90)
        assert bounds.contains(0.5) is True
        assert bounds.contains(0.3) is True
        assert bounds.contains(0.7) is True
        assert bounds.contains(0.2) is False
        assert bounds.contains(0.8) is False

    def test_width(self):
        """width should return interval width."""
        bounds = UncertaintyBounds(0.5, 0.1, 0.3, 0.7, 0.90)
        assert bounds.width() == pytest.approx(0.4)

    def test_relative_width(self):
        """relative_width should return width/mean."""
        bounds = UncertaintyBounds(0.5, 0.1, 0.3, 0.7, 0.90)
        assert bounds.relative_width() == pytest.approx(0.8)


# =============================================================================
# Test UncertainValue
# =============================================================================


class TestUncertainValue:
    """Tests for UncertainValue class."""

    def test_creation(self, rng):
        """UncertainValue should be created from samples."""
        samples = rng.normal(0.5, 0.1, 1000)
        uv = UncertainValue(samples, name="test")
        assert uv.n_samples == 1000
        assert uv.name == "test"

    def test_statistics(self, rng):
        """Statistics should be computed correctly."""
        samples = rng.normal(0.5, 0.1, 10000)
        uv = UncertainValue(samples)

        assert uv.mean == pytest.approx(0.5, abs=0.02)
        assert uv.std == pytest.approx(0.1, abs=0.02)
        assert uv.median == pytest.approx(0.5, abs=0.02)

    def test_percentile(self, rng):
        """percentile should return correct values."""
        samples = rng.normal(0.5, 0.1, 10000)
        uv = UncertainValue(samples)

        # 50th percentile should be close to median
        assert uv.percentile(50) == pytest.approx(uv.median, abs=0.01)

    def test_bounds(self, rng):
        """bounds should return UncertaintyBounds."""
        samples = rng.normal(0.5, 0.1, 10000)
        uv = UncertainValue(samples)

        bounds = uv.bounds(confidence=0.90)
        assert isinstance(bounds, UncertaintyBounds)
        assert bounds.confidence == 0.90
        assert bounds.lower < bounds.mean < bounds.upper

    def test_cvar(self, rng):
        """cvar should compute expected shortfall."""
        samples = rng.normal(0.5, 0.1, 10000)
        uv = UncertainValue(samples)

        cvar_val = uv.cvar(alpha=0.05)
        # CVaR should be less than mean (worst outcomes)
        assert cvar_val < uv.mean

    def test_robust_value(self, rng):
        """robust_value should return worst-case percentile."""
        samples = rng.normal(0.5, 0.1, 10000)
        uv = UncertainValue(samples)

        robust = uv.robust_value(percentile=5.0)
        assert robust < uv.mean


# =============================================================================
# Test Sample Generation
# =============================================================================


class TestSampleGeneration:
    """Tests for sample generation functions."""

    def test_normal_samples(self):
        """generate_samples should produce normal samples."""
        samples = generate_samples(
            DistributionType.NORMAL,
            n_samples=10000,
            mean=0.5,
            std=0.1,
            seed=42,
        )
        assert samples.shape == (10000,)
        assert np.mean(samples) == pytest.approx(0.5, abs=0.02)
        assert np.std(samples) == pytest.approx(0.1, abs=0.02)

    def test_uniform_samples(self):
        """generate_samples should produce uniform samples."""
        samples = generate_samples(
            DistributionType.UNIFORM,
            n_samples=10000,
            low=0.2,
            high=0.8,
            seed=42,
        )
        assert samples.shape == (10000,)
        assert np.min(samples) >= 0.2
        assert np.max(samples) <= 0.8
        assert np.mean(samples) == pytest.approx(0.5, abs=0.02)

    def test_beta_samples(self):
        """generate_samples should produce beta samples."""
        samples = generate_samples(
            DistributionType.BETA,
            n_samples=10000,
            alpha=2.0,
            beta=5.0,
            seed=42,
        )
        assert samples.shape == (10000,)
        assert np.min(samples) >= 0.0
        assert np.max(samples) <= 1.0

    def test_truncated_normal_samples(self):
        """generate_samples should produce truncated normal samples."""
        samples = generate_samples(
            DistributionType.TRUNCATED_NORMAL,
            n_samples=10000,
            mean=0.5,
            std=0.3,
            low=0.0,
            high=1.0,
            seed=42,
        )
        assert samples.shape == (10000,)
        assert np.min(samples) >= 0.0
        assert np.max(samples) <= 1.0

    def test_shaped_samples(self):
        """generate_samples should support shaped output."""
        samples = generate_samples(
            DistributionType.NORMAL,
            n_samples=100,
            shape=(9, 5),
            mean=0.5,
            std=0.1,
            seed=42,
        )
        assert samples.shape == (9, 5, 100)


class TestMoralSampleGeneration:
    """Tests for moral sample generation."""

    def test_generate_moral_samples(self):
        """generate_moral_samples should add sample axis."""
        base = np.array([0.3, 0.5, 0.7])
        samples = generate_moral_samples(
            base,
            n_samples=1000,
            uncertainty=0.1,
            seed=42,
        )
        assert samples.shape == (3, 1000)
        # Samples should be bounded [0, 1]
        assert np.all(samples >= 0.0)
        assert np.all(samples <= 1.0)

    def test_samples_centered_on_base(self):
        """Samples should be centered on base values."""
        base = np.array([0.3, 0.5, 0.7])
        samples = generate_moral_samples(
            base,
            n_samples=10000,
            uncertainty=0.1,
            seed=42,
        )
        means = np.mean(samples, axis=-1)
        assert_allclose(means, base, atol=0.05)

    def test_multidimensional_base(self):
        """Should work with multidimensional base."""
        base = np.random.rand(9, 5)
        samples = generate_moral_samples(
            base,
            n_samples=100,
            uncertainty=0.1,
            seed=42,
        )
        assert samples.shape == (9, 5, 100)


# =============================================================================
# Test Statistical Functions
# =============================================================================


class TestStatistics:
    """Tests for statistical aggregation functions."""

    def test_expected_value(self, sample_samples):
        """expected_value should compute mean."""
        ev = expected_value(sample_samples, axis=-1)
        assert ev.shape == (9,)
        assert_allclose(ev, np.mean(sample_samples, axis=-1))

    def test_variance(self, sample_samples):
        """variance should compute variance."""
        var = variance(sample_samples, axis=-1)
        assert var.shape == (9,)
        assert np.all(var >= 0)

    def test_std_dev(self, sample_samples):
        """std_dev should compute standard deviation."""
        std = std_dev(sample_samples, axis=-1)
        assert std.shape == (9,)
        assert np.all(std >= 0)

    def test_percentiles(self, sample_samples):
        """percentiles should compute quantiles."""
        p = percentiles(sample_samples, [5, 50, 95], axis=-1)
        assert p.shape == (3, 9)
        # 5th < 50th < 95th
        assert np.all(p[0] <= p[1])
        assert np.all(p[1] <= p[2])

    def test_confidence_interval(self, sample_samples):
        """confidence_interval should return bounds."""
        lower, upper = confidence_interval(sample_samples, confidence=0.90, axis=-1)
        assert lower.shape == (9,)
        assert upper.shape == (9,)
        assert np.all(lower < upper)


# =============================================================================
# Test Risk Measures
# =============================================================================


class TestRiskMeasures:
    """Tests for risk measure functions."""

    def test_cvar(self, sample_samples):
        """cvar should compute expected shortfall."""
        cvar_val = cvar(sample_samples, alpha=0.05, axis=-1)
        mean_val = expected_value(sample_samples, axis=-1)
        assert cvar_val.shape == (9,)
        # CVaR (worst outcomes) should be less than mean
        assert np.all(cvar_val <= mean_val + 0.01)

    def test_cvar_upper(self, sample_samples):
        """cvar_upper should compute upper tail expected value."""
        cvar_up = cvar_upper(sample_samples, alpha=0.05, axis=-1)
        mean_val = expected_value(sample_samples, axis=-1)
        assert cvar_up.shape == (9,)
        # Upper CVaR (best outcomes) should be >= mean
        assert np.all(cvar_up >= mean_val - 0.01)

    def test_worst_case(self, sample_samples):
        """worst_case should return low percentile."""
        wc = worst_case(sample_samples, percentile=5.0, axis=-1)
        mean_val = expected_value(sample_samples, axis=-1)
        assert wc.shape == (9,)
        assert np.all(wc <= mean_val)

    def test_best_case(self, sample_samples):
        """best_case should return high percentile."""
        bc = best_case(sample_samples, percentile=95.0, axis=-1)
        mean_val = expected_value(sample_samples, axis=-1)
        assert bc.shape == (9,)
        assert np.all(bc >= mean_val)

    def test_value_at_risk(self, sample_samples):
        """value_at_risk should return quantile."""
        var = value_at_risk(sample_samples, alpha=0.05, axis=-1)
        wc = worst_case(sample_samples, percentile=5.0, axis=-1)
        assert_allclose(var, wc)


# =============================================================================
# Test Aggregation
# =============================================================================


class TestAggregation:
    """Tests for sample aggregation."""

    def test_aggregate_expected_value(self, sample_samples):
        """aggregate_samples with EXPECTED_VALUE should return mean."""
        result = aggregate_samples(
            sample_samples,
            method=AggregationMethod.EXPECTED_VALUE,
            axis=-1,
        )
        expected = expected_value(sample_samples, axis=-1)
        assert_allclose(result, expected)

    def test_aggregate_median(self, sample_samples):
        """aggregate_samples with MEDIAN should return median."""
        result = aggregate_samples(
            sample_samples,
            method=AggregationMethod.MEDIAN,
            axis=-1,
        )
        expected = np.median(sample_samples, axis=-1)
        assert_allclose(result, expected)

    def test_aggregate_worst_case(self, sample_samples):
        """aggregate_samples with WORST_CASE should return percentile."""
        result = aggregate_samples(
            sample_samples,
            method=AggregationMethod.WORST_CASE,
            axis=-1,
            percentile=5.0,
        )
        expected = worst_case(sample_samples, percentile=5.0, axis=-1)
        assert_allclose(result, expected)

    def test_aggregate_cvar(self, sample_samples):
        """aggregate_samples with CVAR should return CVaR."""
        result = aggregate_samples(
            sample_samples,
            method=AggregationMethod.CVAR,
            axis=-1,
            alpha=0.05,
        )
        expected = cvar(sample_samples, alpha=0.05, axis=-1)
        assert_allclose(result, expected)


# =============================================================================
# Test Uncertainty Analysis
# =============================================================================


class TestUncertaintyAnalysis:
    """Tests for uncertainty analysis."""

    def test_analyze_uncertainty(self, sample_samples):
        """analyze_uncertainty should return complete analysis."""
        analysis = analyze_uncertainty(
            sample_samples,
            axis=-1,
            confidence=0.90,
            cvar_alpha=0.05,
        )

        assert isinstance(analysis, UncertaintyAnalysis)
        assert analysis.mean.shape == (9,)
        assert analysis.std.shape == (9,)
        assert analysis.lower.shape == (9,)
        assert analysis.upper.shape == (9,)
        assert analysis.cvar.shape == (9,)
        assert analysis.var.shape == (9,)
        assert analysis.confidence == 0.90
        assert analysis.n_samples == 1000

    def test_analysis_bounds_ordering(self, sample_samples):
        """Analysis bounds should be properly ordered."""
        analysis = analyze_uncertainty(sample_samples, axis=-1)

        # lower < mean < upper
        assert np.all(analysis.lower <= analysis.mean + 0.01)
        assert np.all(analysis.mean <= analysis.upper + 0.01)

    def test_analysis_summary(self, sample_samples):
        """summary should return string."""
        analysis = analyze_uncertainty(sample_samples, axis=-1)
        summary = analysis.summary()
        assert isinstance(summary, str)
        assert "Uncertainty Analysis" in summary


class TestPropagateUncertainty:
    """Tests for uncertainty propagation."""

    def test_propagate_uncertainty(self, sample_values):
        """propagate_uncertainty should generate samples and analysis."""
        samples, analysis = propagate_uncertainty(
            sample_values,
            n_samples=1000,
            uncertainty=0.1,
            seed=42,
        )

        assert samples.shape == (*sample_values.shape, 1000)
        assert isinstance(analysis, UncertaintyAnalysis)

    def test_propagation_preserves_mean(self, sample_values):
        """Propagation should preserve base values as mean."""
        samples, analysis = propagate_uncertainty(
            sample_values,
            n_samples=10000,
            uncertainty=0.1,
            seed=42,
        )

        # Mean should be close to base values
        assert_allclose(analysis.mean, sample_values, atol=0.05)


# =============================================================================
# Test Decision Support
# =============================================================================


class TestDecisionSupport:
    """Tests for decision support functions."""

    def test_compare_under_uncertainty_clear_winner(self, rng):
        """compare_under_uncertainty should identify clear winner."""
        # A is clearly better than B
        samples_a = rng.normal(0.7, 0.1, 1000)
        samples_b = rng.normal(0.3, 0.1, 1000)

        a_preferred, confidence = compare_under_uncertainty(
            samples_a,
            samples_b,
            method=AggregationMethod.EXPECTED_VALUE,
        )

        assert a_preferred is True
        assert confidence > 0.9

    def test_compare_under_uncertainty_close_alternatives(self, rng):
        """compare_under_uncertainty should handle close alternatives."""
        # A and B are similar
        samples_a = rng.normal(0.5, 0.1, 1000)
        samples_b = rng.normal(0.5, 0.1, 1000)

        _, confidence = compare_under_uncertainty(
            samples_a,
            samples_b,
            method=AggregationMethod.EXPECTED_VALUE,
        )

        # Confidence should be around 0.5 for similar alternatives
        assert 0.3 < confidence < 0.7

    def test_stochastic_dominance_first_order(self, rng):
        """stochastic_dominance should detect first-order dominance."""
        # A always >= B (A dominates)
        samples_a = rng.uniform(0.6, 1.0, 1000)
        samples_b = rng.uniform(0.0, 0.5, 1000)

        dominates = stochastic_dominance(samples_a, samples_b, order=1)
        assert dominates is True

    def test_stochastic_dominance_no_dominance(self, rng):
        """stochastic_dominance should return False when no dominance."""
        # Overlapping distributions - no dominance
        samples_a = rng.normal(0.5, 0.2, 1000)
        samples_b = rng.normal(0.5, 0.2, 1000)

        dominates = stochastic_dominance(samples_a, samples_b, order=1)
        assert dominates is False


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_sample(self):
        """Functions should handle single sample."""
        samples = np.array([[0.5]])
        ev = expected_value(samples, axis=-1)
        assert ev.shape == (1,)
        assert ev[0] == 0.5

    def test_zero_uncertainty(self):
        """generate_moral_samples should handle zero uncertainty."""
        base = np.array([0.5, 0.5])
        samples = generate_moral_samples(
            base,
            n_samples=100,
            uncertainty=0.0,
            seed=42,
        )
        # With zero uncertainty, samples should equal base
        # (within numerical precision)
        assert_allclose(np.mean(samples, axis=-1), base, atol=0.01)

    def test_boundary_values(self):
        """Should handle values at boundaries."""
        base = np.array([0.0, 1.0, 0.5])
        samples = generate_moral_samples(
            base,
            n_samples=1000,
            uncertainty=0.1,
            seed=42,
        )
        # All samples should be in [0, 1]
        assert np.all(samples >= 0.0)
        assert np.all(samples <= 1.0)

    def test_high_dimensional(self):
        """Should handle high-dimensional tensors."""
        base = np.random.rand(9, 5, 10, 3)  # Rank-4
        samples = generate_moral_samples(
            base,
            n_samples=50,
            uncertainty=0.1,
            seed=42,
        )
        assert samples.shape == (9, 5, 10, 3, 50)
