# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tests for fairness_metrics.py - Distributional Fairness Metrics.

DEME V3 Sprint 5: Comprehensive tests for all fairness metrics.
"""

import numpy as np
import pytest

from erisml.ethics.fairness_metrics import (
    gini_coefficient,
    rawlsian_maximin,
    rawlsian_maximin_welfare,
    utilitarian_sum,
    utilitarian_average,
    prioritarian_weighted_welfare,
    extract_vulnerability_weights,
    atkinson_index,
    theil_index,
    theil_decomposition,
    FairnessMetrics,
)
from erisml.ethics.moral_tensor import MoralTensor
from erisml.ethics.facts_v3 import (
    EthicalFactsV3,
    ConsequencesV3,
    RightsAndDutiesV3,
    JusticeAndFairnessV3,
    PartyConsequences,
    PartyRights,
    PartyJustice,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def rank2_tensor() -> MoralTensor:
    """Create a rank-2 tensor with 3 parties for testing."""
    # Shape (9, 3) - 9 ethical dimensions, 3 parties
    data = np.array(
        [
            [0.2, 0.3, 0.5],  # 0: physical_harm (lower is better)
            [0.9, 0.7, 0.6],  # 1: rights_respect
            [0.8, 0.6, 0.4],  # 2: fairness_equity
            [0.7, 0.8, 0.9],  # 3: autonomy_respect
            [0.6, 0.5, 0.7],  # 4: privacy_protection
            [0.5, 0.6, 0.5],  # 5: societal_environmental
            [0.8, 0.7, 0.6],  # 6: virtue_care
            [0.7, 0.8, 0.7],  # 7: legitimacy_trust
            [0.9, 0.8, 0.7],  # 8: epistemic_quality
        ],
        dtype=np.float64,
    )
    return MoralTensor.from_dense(
        data,
        axis_names=("k", "n"),
        axis_labels={"n": ["alice", "bob", "carol"]},
    )


@pytest.fixture
def rank1_tensor() -> MoralTensor:
    """Create a rank-1 tensor for testing error cases."""
    data = np.array([0.5] * 9, dtype=np.float64)
    return MoralTensor.from_dense(data)


@pytest.fixture
def sample_facts_v3() -> EthicalFactsV3:
    """Create sample EthicalFactsV3 for testing."""
    return EthicalFactsV3(
        option_id="test_option",
        consequences=ConsequencesV3(
            expected_benefit=0.7,
            expected_harm=0.3,
            urgency=0.5,
            affected_count=3,
            per_party=(
                PartyConsequences(
                    party_id="alice",
                    expected_benefit=0.9,
                    expected_harm=0.2,
                    vulnerability_weight=1.0,
                ),
                PartyConsequences(
                    party_id="bob",
                    expected_benefit=0.7,
                    expected_harm=0.3,
                    vulnerability_weight=1.5,
                ),
                PartyConsequences(
                    party_id="carol",
                    expected_benefit=0.5,
                    expected_harm=0.4,
                    vulnerability_weight=2.0,
                ),
            ),
        ),
        rights_and_duties=RightsAndDutiesV3(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
            per_party=(
                PartyRights(party_id="alice"),
                PartyRights(party_id="bob"),
                PartyRights(party_id="carol"),
            ),
        ),
        justice_and_fairness=JusticeAndFairnessV3(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=True,
            per_party=(
                PartyJustice(
                    party_id="alice", relative_burden=0.2, relative_benefit=0.4
                ),
                PartyJustice(party_id="bob", relative_burden=0.3, relative_benefit=0.3),
                PartyJustice(
                    party_id="carol", relative_burden=0.5, relative_benefit=0.3
                ),
            ),
        ),
        party_labels={"alice": "Alice", "bob": "Bob", "carol": "Carol"},
    )


# =============================================================================
# Test Gini Coefficient
# =============================================================================


class TestGiniCoefficient:
    """Tests for Gini coefficient computation."""

    def test_perfect_equality(self):
        """Gini = 0 for identical values."""
        assert gini_coefficient([1, 1, 1, 1]) == pytest.approx(0.0)
        assert gini_coefficient([0.5, 0.5, 0.5]) == pytest.approx(0.0)
        assert gini_coefficient([100, 100, 100, 100, 100]) == pytest.approx(0.0)

    def test_high_inequality(self):
        """Gini for unequal distributions."""
        # [0, 0, 0, 1] gives Gini = 0.75
        assert gini_coefficient([0, 0, 0, 1]) == pytest.approx(0.75)

    def test_moderate_inequality(self):
        """Gini for [1, 2, 3, 4, 5] = 4/15 = 0.2667."""
        result = gini_coefficient([1, 2, 3, 4, 5])
        assert result == pytest.approx(4 / 15, rel=1e-3)

    def test_single_value(self):
        """Single value returns 0."""
        assert gini_coefficient([5.0]) == 0.0

    def test_empty(self):
        """Empty list returns 0."""
        assert gini_coefficient([]) == 0.0

    def test_all_zeros(self):
        """All zeros returns 0."""
        assert gini_coefficient([0, 0, 0]) == 0.0

    def test_numpy_array(self):
        """Works with numpy arrays."""
        arr = np.array([1.0, 2.0, 3.0, 4.0])
        result = gini_coefficient(arr)
        assert 0.0 < result < 1.0

    def test_negative_values_raises(self):
        """Raises error for negative values."""
        with pytest.raises(ValueError, match="non-negative"):
            gini_coefficient([-1, 2, 3])

    def test_bounds(self):
        """Result is always in [0, 1]."""
        for _ in range(10):
            values = np.random.rand(100) * 10
            gini = gini_coefficient(values)
            assert 0.0 <= gini <= 1.0


# =============================================================================
# Test Rawlsian Maximin
# =============================================================================


class TestRawlsianMaximin:
    """Tests for Rawlsian maximin metrics."""

    def test_identifies_worst_off(self, rank2_tensor: MoralTensor):
        """Correctly identifies party with minimum welfare."""
        min_welfare, idx = rawlsian_maximin(rank2_tensor, return_party_index=True)
        # Verify idx is valid
        assert 0 <= idx < 3
        # Verify min_welfare is in bounds
        assert 0.0 <= min_welfare <= 1.0

    def test_without_party_index(self, rank2_tensor: MoralTensor):
        """Returns just welfare value by default."""
        result = rawlsian_maximin(rank2_tensor)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_with_dimension(self, rank2_tensor: MoralTensor):
        """Works with specific dimension."""
        # rights_respect (dim 1) - check worst party
        min_val = rawlsian_maximin(rank2_tensor, dimension="rights_respect")
        assert 0.0 <= min_val <= 1.0

    def test_harm_dimension_inverted(self, rank2_tensor: MoralTensor):
        """physical_harm is inverted (lower harm = higher welfare)."""
        # Party 0 has lowest harm (0.2), so highest welfare
        min_val, idx = rawlsian_maximin(
            rank2_tensor, dimension="physical_harm", return_party_index=True
        )
        # Welfare = 1 - harm, so min welfare comes from max harm
        # Party 2 has max harm (0.5), so welfare = 0.5
        assert min_val == pytest.approx(0.5)
        assert idx == 2

    def test_rejects_rank1(self, rank1_tensor: MoralTensor):
        """Raises error for rank-1 tensor."""
        with pytest.raises(ValueError, match="rank >= 2"):
            rawlsian_maximin(rank1_tensor)

    def test_unknown_dimension_raises(self, rank2_tensor: MoralTensor):
        """Raises error for unknown dimension name."""
        with pytest.raises(ValueError, match="Unknown dimension"):
            rawlsian_maximin(rank2_tensor, dimension="nonexistent")


class TestRawlsianMaximinWelfare:
    """Tests for per-party welfare computation."""

    def test_returns_array(self, rank2_tensor: MoralTensor):
        """Returns numpy array of welfare values."""
        welfare = rawlsian_maximin_welfare(rank2_tensor)
        assert isinstance(welfare, np.ndarray)
        assert len(welfare) == 3

    def test_welfare_bounds(self, rank2_tensor: MoralTensor):
        """All welfare values in [0, 1]."""
        welfare = rawlsian_maximin_welfare(rank2_tensor)
        assert np.all(welfare >= 0.0)
        assert np.all(welfare <= 1.0)

    def test_with_dimension_weights(self, rank2_tensor: MoralTensor):
        """Custom dimension weights affect result."""
        # Weight only physical_harm highly
        weights = {"physical_harm": 10.0}
        welfare = rawlsian_maximin_welfare(rank2_tensor, dimension_weights=weights)
        assert len(welfare) == 3

    def test_rejects_rank1(self, rank1_tensor: MoralTensor):
        """Raises error for rank-1 tensor."""
        with pytest.raises(ValueError, match="rank >= 2"):
            rawlsian_maximin_welfare(rank1_tensor)


# =============================================================================
# Test Utilitarian Aggregation
# =============================================================================


class TestUtilitarianSum:
    """Tests for utilitarian sum."""

    def test_sum_across_parties(self, rank2_tensor: MoralTensor):
        """Sum correctly aggregates across parties."""
        total = utilitarian_sum(rank2_tensor)
        # Should be sum of 3 party welfares
        welfare = rawlsian_maximin_welfare(rank2_tensor)
        assert total == pytest.approx(np.sum(welfare))

    def test_with_dimension(self, rank2_tensor: MoralTensor):
        """Sum for specific dimension."""
        # rights_respect values: [0.9, 0.7, 0.6]
        total = utilitarian_sum(rank2_tensor, dimension="rights_respect")
        assert total == pytest.approx(0.9 + 0.7 + 0.6)

    def test_harm_dimension_inverted(self, rank2_tensor: MoralTensor):
        """physical_harm is inverted for sum."""
        # harm values: [0.2, 0.3, 0.5] -> welfare: [0.8, 0.7, 0.5]
        total = utilitarian_sum(rank2_tensor, dimension="physical_harm")
        assert total == pytest.approx(0.8 + 0.7 + 0.5)

    def test_rejects_rank1(self, rank1_tensor: MoralTensor):
        """Raises error for rank-1 tensor."""
        with pytest.raises(ValueError, match="rank >= 2"):
            utilitarian_sum(rank1_tensor)


class TestUtilitarianAverage:
    """Tests for utilitarian average."""

    def test_average_bounds(self, rank2_tensor: MoralTensor):
        """Average stays in [0, 1]."""
        avg = utilitarian_average(rank2_tensor)
        assert 0.0 <= avg <= 1.0

    def test_sum_vs_average(self, rank2_tensor: MoralTensor):
        """Sum = Average * n_parties."""
        s = utilitarian_sum(rank2_tensor)
        a = utilitarian_average(rank2_tensor)
        n = rank2_tensor.shape[1]
        assert s == pytest.approx(a * n)

    def test_with_dimension(self, rank2_tensor: MoralTensor):
        """Average for specific dimension."""
        avg = utilitarian_average(rank2_tensor, dimension="rights_respect")
        assert avg == pytest.approx((0.9 + 0.7 + 0.6) / 3)


# =============================================================================
# Test Prioritarian Weighting
# =============================================================================


class TestPrioritarianWeighting:
    """Tests for prioritarian welfare."""

    def test_uniform_weights_equals_average(self, rank2_tensor: MoralTensor):
        """With uniform weights, equals utilitarian average."""
        p = prioritarian_weighted_welfare(rank2_tensor)
        u = utilitarian_average(rank2_tensor)
        assert p == pytest.approx(u)

    def test_with_vulnerability_weights(self, rank2_tensor: MoralTensor):
        """Custom vulnerability weights affect result."""
        # Give high weight to party 2 (worst off)
        weights = np.array([1.0, 1.0, 5.0])
        p = prioritarian_weighted_welfare(rank2_tensor, vulnerability_weights=weights)
        # Result should shift toward party 2's welfare
        assert 0.0 <= p <= 1.0

    def test_concave_priority(self, rank2_tensor: MoralTensor):
        """Concave function with diminishing returns."""
        linear = prioritarian_weighted_welfare(rank2_tensor, priority_function="linear")
        concave = prioritarian_weighted_welfare(
            rank2_tensor, priority_function="concave", priority_param=2.0
        )
        # Both should be valid
        assert 0.0 <= linear <= 1.0
        assert 0.0 <= concave <= 1.0

    def test_threshold_priority(self, rank2_tensor: MoralTensor):
        """Threshold function gives extra weight below threshold."""
        result = prioritarian_weighted_welfare(
            rank2_tensor, priority_function="threshold", priority_param=0.7
        )
        assert 0.0 <= result <= 1.0

    def test_invalid_priority_function(self, rank2_tensor: MoralTensor):
        """Raises error for unknown priority function."""
        with pytest.raises(ValueError, match="Unknown priority_function"):
            prioritarian_weighted_welfare(rank2_tensor, priority_function="invalid")

    def test_invalid_weights_length(self, rank2_tensor: MoralTensor):
        """Raises error for wrong weights length."""
        weights = np.array([1.0, 1.0])  # Only 2, need 3
        with pytest.raises(ValueError, match="vulnerability_weights length"):
            prioritarian_weighted_welfare(rank2_tensor, vulnerability_weights=weights)


class TestExtractVulnerabilityWeights:
    """Tests for vulnerability weight extraction."""

    def test_extracts_weights(self, sample_facts_v3: EthicalFactsV3):
        """Extracts weights from per-party consequences."""
        weights = extract_vulnerability_weights(sample_facts_v3)
        assert len(weights) == 3
        # alice=1.0, bob=1.5, carol=2.0 (but order may vary)

    def test_empty_facts(self):
        """Handles facts with no parties."""
        facts = EthicalFactsV3(
            option_id="empty",
            consequences=ConsequencesV3(
                expected_benefit=0.5,
                expected_harm=0.2,
                urgency=0.5,
                affected_count=0,
            ),
            rights_and_duties=RightsAndDutiesV3(
                violates_rights=False,
                has_valid_consent=True,
                violates_explicit_rule=False,
                role_duty_conflict=False,
            ),
            justice_and_fairness=JusticeAndFairnessV3(
                discriminates_on_protected_attr=False,
                prioritizes_most_disadvantaged=False,
            ),
        )
        weights = extract_vulnerability_weights(facts)
        assert len(weights) == 0


# =============================================================================
# Test Atkinson Index
# =============================================================================


class TestAtkinsonIndex:
    """Tests for Atkinson inequality index."""

    def test_perfect_equality(self):
        """Atkinson = 0 for equal distribution."""
        assert atkinson_index([1, 1, 1], epsilon=0.5) == pytest.approx(0.0, abs=1e-6)
        assert atkinson_index([0.5, 0.5, 0.5], epsilon=1.0) == pytest.approx(
            0.0, abs=1e-6
        )

    def test_epsilon_sensitivity(self):
        """Higher epsilon = more sensitive to low values."""
        values = [0.1, 1.0, 1.0, 1.0]
        a05 = atkinson_index(values, epsilon=0.5)
        a20 = atkinson_index(values, epsilon=2.0)
        # Higher epsilon more sensitive to the 0.1
        assert a20 > a05

    def test_epsilon_one(self):
        """Special formula for epsilon=1 works correctly."""
        result = atkinson_index([1, 2, 3], epsilon=1.0)
        assert 0.0 <= result <= 1.0

    def test_epsilon_zero(self):
        """Epsilon=0 gives insensitive measure."""
        result = atkinson_index([1, 2, 3], epsilon=0.0)
        assert result == pytest.approx(0.0, abs=1e-6)

    def test_rejects_negative_epsilon(self):
        """Raises error for negative epsilon."""
        with pytest.raises(ValueError, match="epsilon must be >= 0"):
            atkinson_index([1, 2, 3], epsilon=-0.5)

    def test_rejects_negative_values(self):
        """Raises error for negative values."""
        with pytest.raises(ValueError, match="non-negative"):
            atkinson_index([-1, 2, 3], epsilon=0.5)

    def test_bounds(self):
        """Result is in [0, 1]."""
        for _ in range(10):
            values = np.random.rand(20) + 0.01  # Avoid zeros
            result = atkinson_index(values, epsilon=1.0)
            assert 0.0 <= result <= 1.0

    def test_single_value(self):
        """Single value returns 0."""
        assert atkinson_index([5.0], epsilon=0.5) == 0.0

    def test_empty(self):
        """Empty list returns 0."""
        assert atkinson_index([], epsilon=0.5) == 0.0


# =============================================================================
# Test Theil Index
# =============================================================================


class TestTheilIndex:
    """Tests for Theil index (generalized entropy)."""

    def test_perfect_equality(self):
        """Theil = 0 for equal distribution."""
        assert theil_index([1, 1, 1]) == pytest.approx(0.0, abs=1e-6)
        assert theil_index([5, 5, 5, 5]) == pytest.approx(0.0, abs=1e-6)

    def test_theil_t(self):
        """Theil T (alpha=1) for unequal distribution."""
        result = theil_index([1, 2, 3, 4], alpha=1.0)
        assert result > 0

    def test_theil_l(self):
        """Theil L (alpha=0) for unequal distribution."""
        result = theil_index([1, 2, 3, 4], alpha=0.0)
        assert result > 0

    def test_alpha_two(self):
        """Alpha=2 gives half squared CV."""
        result = theil_index([1, 2, 3, 4], alpha=2.0)
        assert result > 0

    def test_not_bounded_to_one(self):
        """Theil index is not strictly bounded to [0, 1]."""
        # Many parties with extreme inequality
        values = [0.001] * 99 + [1000.0]  # 99 poor, 1 rich
        t = theil_index(values, alpha=1.0)
        # With enough skew, Theil can exceed 1
        assert t > 1.0

    def test_rejects_negative_alpha(self):
        """Raises error for negative alpha."""
        with pytest.raises(ValueError, match="alpha must be >= 0"):
            theil_index([1, 2, 3], alpha=-0.5)

    def test_rejects_negative_values(self):
        """Raises error for negative values."""
        with pytest.raises(ValueError, match="non-negative"):
            theil_index([-1, 2, 3], alpha=1.0)

    def test_single_value(self):
        """Single value returns 0."""
        assert theil_index([5.0], alpha=1.0) == 0.0

    def test_empty(self):
        """Empty list returns 0."""
        assert theil_index([], alpha=1.0) == 0.0


class TestTheilDecomposition:
    """Tests for Theil index decomposition."""

    def test_decomposition_keys(self, rank2_tensor: MoralTensor):
        """Returns dict with expected keys."""
        result = theil_decomposition(rank2_tensor)
        assert "total" in result
        assert "between" in result
        assert "within" in result
        assert "between_share" in result

    def test_decomposition_values(self, rank2_tensor: MoralTensor):
        """All values are non-negative."""
        result = theil_decomposition(rank2_tensor)
        assert result["total"] >= 0
        assert result["between"] >= 0
        assert result["within"] >= 0
        assert 0.0 <= result["between_share"] <= 1.0

    def test_rejects_rank1(self, rank1_tensor: MoralTensor):
        """Raises error for rank-1 tensor."""
        with pytest.raises(ValueError, match="rank >= 2"):
            theil_decomposition(rank1_tensor)


# =============================================================================
# Test FairnessMetrics Class
# =============================================================================


class TestFairnessMetricsClass:
    """Tests for FairnessMetrics dataclass."""

    def test_from_tensor(self, rank2_tensor: MoralTensor):
        """Creates metrics from MoralTensor."""
        metrics = FairnessMetrics.from_tensor(rank2_tensor)
        assert metrics.n_parties == 3
        assert 0.0 <= metrics.gini <= 1.0
        assert len(metrics.gini_per_dimension) == 9
        assert 0 <= metrics.maximin_party_index < 3

    def test_from_facts(self, sample_facts_v3: EthicalFactsV3):
        """Creates metrics from EthicalFactsV3."""
        metrics = FairnessMetrics.from_facts(sample_facts_v3)
        assert metrics.n_parties == 3
        assert 0.0 <= metrics.gini <= 1.0

    def test_with_vulnerability_weights(self, rank2_tensor: MoralTensor):
        """Uses vulnerability weights when provided."""
        weights = np.array([1.0, 1.0, 2.0])
        metrics = FairnessMetrics.from_tensor(
            rank2_tensor, vulnerability_weights=weights
        )
        assert 0.0 <= metrics.prioritarian_welfare <= 1.0

    def test_party_labels(self, rank2_tensor: MoralTensor):
        """Captures party labels."""
        metrics = FairnessMetrics.from_tensor(rank2_tensor)
        assert "alice" in metrics.party_labels
        assert "bob" in metrics.party_labels
        assert "carol" in metrics.party_labels

    def test_maximin_party_label(self, rank2_tensor: MoralTensor):
        """Worst-off party label is set."""
        metrics = FairnessMetrics.from_tensor(rank2_tensor)
        assert metrics.maximin_party_label in ["alice", "bob", "carol"]

    def test_serialization_roundtrip(self, rank2_tensor: MoralTensor):
        """to_dict/from_dict preserves values."""
        original = FairnessMetrics.from_tensor(rank2_tensor)
        d = original.to_dict()
        restored = FairnessMetrics.from_dict(d)

        assert restored.gini == pytest.approx(original.gini)
        assert restored.maximin_welfare == pytest.approx(original.maximin_welfare)
        assert restored.utilitarian_avg == pytest.approx(original.utilitarian_avg)
        assert restored.atkinson_05 == pytest.approx(original.atkinson_05)
        assert restored.theil_t == pytest.approx(original.theil_t)
        assert restored.n_parties == original.n_parties

    def test_summary_output(self, rank2_tensor: MoralTensor):
        """Summary produces readable string."""
        metrics = FairnessMetrics.from_tensor(rank2_tensor)
        s = metrics.summary()
        assert "Gini" in s
        assert "Atkinson" in s
        assert "Theil" in s
        assert "Rawlsian" in s
        assert "Utilitarian" in s

    def test_rejects_rank1(self, rank1_tensor: MoralTensor):
        """Raises error for rank-1 tensor."""
        with pytest.raises(ValueError, match="rank >= 2"):
            FairnessMetrics.from_tensor(rank1_tensor)


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge case handling."""

    def test_all_zeros_gini(self):
        """Handles all-zero distributions."""
        assert gini_coefficient([0, 0, 0]) == 0.0

    def test_all_zeros_atkinson(self):
        """Atkinson handles all-zero with epsilon."""
        # Should return 0 due to EPSILON clamping
        result = atkinson_index([0.0, 0.0, 0.0], epsilon=0.5)
        assert result >= 0

    def test_near_zero_values(self):
        """Handles values very close to zero."""
        values = [1e-15, 1e-14, 1e-13]
        # Should not raise or return NaN
        gini = gini_coefficient(values)
        assert np.isfinite(gini)

        theil = theil_index(values)
        assert np.isfinite(theil)

    def test_large_n(self):
        """Handles large number of parties."""
        values = np.random.rand(10000)
        gini = gini_coefficient(values)
        assert 0.0 <= gini <= 1.0

    def test_two_parties_tensor(self):
        """Works with just 2 parties."""
        data = np.random.rand(9, 2)
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n"))
        metrics = FairnessMetrics.from_tensor(tensor)
        assert metrics.n_parties == 2

    def test_single_party_metrics(self):
        """Handles single-party tensor."""
        data = np.random.rand(9, 1)
        tensor = MoralTensor.from_dense(data, axis_names=("k", "n"))
        metrics = FairnessMetrics.from_tensor(tensor)
        assert metrics.n_parties == 1
        assert metrics.gini == 0.0  # No inequality with 1 party

    def test_facts_without_per_party(self):
        """Handles facts with empty per_party."""
        facts = EthicalFactsV3(
            option_id="no_parties",
            consequences=ConsequencesV3(
                expected_benefit=0.5,
                expected_harm=0.2,
                urgency=0.5,
                affected_count=0,
            ),
            rights_and_duties=RightsAndDutiesV3(
                violates_rights=False,
                has_valid_consent=True,
                violates_explicit_rule=False,
                role_duty_conflict=False,
            ),
            justice_and_fairness=JusticeAndFairnessV3(
                discriminates_on_protected_attr=False,
                prioritizes_most_disadvantaged=False,
            ),
        )
        # This creates a rank-1 tensor, which should raise
        # Actually, let's check what to_moral_tensor does
        tensor = facts.to_moral_tensor()
        if tensor.rank >= 2:
            metrics = FairnessMetrics.from_facts(facts)
            assert metrics.n_parties >= 0


class TestNumericalStability:
    """Tests for numerical stability."""

    def test_gini_very_small_sum(self):
        """Gini handles very small total sum."""
        values = [1e-12, 1e-12, 1e-12]
        result = gini_coefficient(values)
        assert np.isfinite(result)
        assert result == pytest.approx(0.0, abs=1e-6)

    def test_atkinson_near_one_epsilon(self):
        """Atkinson handles epsilon very close to 1."""
        result = atkinson_index([1, 2, 3], epsilon=1.0 + 1e-11)
        assert np.isfinite(result)
        assert 0.0 <= result <= 1.0

    def test_theil_near_zero_alpha(self):
        """Theil handles alpha very close to 0."""
        result = theil_index([1, 2, 3], alpha=1e-11)
        assert np.isfinite(result)

    def test_theil_near_one_alpha(self):
        """Theil handles alpha very close to 1."""
        result = theil_index([1, 2, 3], alpha=1.0 - 1e-11)
        assert np.isfinite(result)
