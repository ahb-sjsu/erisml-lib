"""
Tests for Appendix D: End-to-End Case Studies.

Verifies that all five case studies produce numerical results matching
the explicit values in the book (Geometric Ethics, Appendix D, v1.13).

Tolerances: atol=0.01 for individual tensor entries (book rounds to 3 decimals),
atol=0.02 for aggregated quantities (accumulated rounding).
"""

from __future__ import annotations

import numpy as np
import pytest

from erisml.examples.appendix_d_pipeline import (
    compute_evaluation_tensor,
    compute_shapley_values,
    contraction_expert_weighted,
    contraction_rawlsian,
    contraction_utilitarian,
    metric_distance_euclidean,
    metric_distance_weighted,
)


# ═══════════════════════════════════════════════════════════════════════════
# CS1: Emergency Triage
# ═══════════════════════════════════════════════════════════════════════════


class TestCS1EmergencyTriage:
    """Case Study 1: Emergency ventilator allocation (3 options, 6 dims, 5 agents)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from erisml.examples.appendix_d_cs1_triage import run_case_study_1

        self.results = run_case_study_1()

    def test_evaluation_tensor_shape(self):
        M = self.results["evaluation_tensor"]
        assert M.shape == (3, 5)  # 3 options x 5 agents

    def test_evaluation_tensor_values(self):
        M = self.results["evaluation_tensor"]
        expected = np.array(
            [
                [0.703, 0.687, 0.668, 0.557, 0.632],  # alpha (A+B)
                [0.820, 0.775, 0.668, 0.792, 0.758],  # beta (A+C)
                [0.602, 0.443, 0.563, 0.545, 0.567],  # gamma (B+C)
            ]
        )
        np.testing.assert_allclose(M, expected, atol=0.01)

    def test_utilitarian_contraction(self):
        S = self.results["utilitarian"]
        np.testing.assert_allclose(S, [3.247, 3.813, 2.720], atol=0.02)

    def test_utilitarian_winner(self):
        S = self.results["utilitarian"]
        assert np.argmax(S) == 1  # beta wins

    def test_rawlsian_contraction(self):
        S = self.results["rawlsian"]
        np.testing.assert_allclose(S, [0.557, 0.668, 0.443], atol=0.01)

    def test_rawlsian_winner(self):
        S = self.results["rawlsian"]
        assert np.argmax(S) == 1  # beta wins

    def test_expert_weighted_contraction(self):
        S = self.results["expert_weighted"]
        np.testing.assert_allclose(S, [0.659, 0.776, 0.564], atol=0.02)

    def test_expert_weighted_winner(self):
        S = self.results["expert_weighted"]
        assert np.argmax(S) == 1  # beta wins

    def test_all_contractions_agree_beta(self):
        """All three contractions should select beta (A+C)."""
        assert np.argmax(self.results["utilitarian"]) == 1
        assert np.argmax(self.results["rawlsian"]) == 1
        assert np.argmax(self.results["expert_weighted"]) == 1

    def test_euclidean_distances(self):
        d = self.results["euclid_distances"]
        np.testing.assert_allclose(
            [d["alpha"], d["beta"], d["gamma"]],
            [0.896, 0.715, 1.170],
            atol=0.02,
        )

    def test_euclidean_beta_closest(self):
        d = self.results["euclid_distances"]
        assert d["beta"] == min(d.values())

    def test_weighted_distances(self):
        d = self.results["weighted_distances"]
        np.testing.assert_allclose(
            [d["alpha"], d["beta"], d["gamma"]],
            [0.971, 0.740, 1.411],
            atol=0.02,
        )

    def test_weighted_beta_closest(self):
        d = self.results["weighted_distances"]
        assert d["beta"] == min(d.values())

    def test_moral_residue_patient_b(self):
        R = self.results["moral_residue_B"]
        expected = np.array([0.50, 0.70, 0.35, 0.80, 0.20, 0.60])
        np.testing.assert_allclose(R, expected, atol=0.01)

    def test_decision_is_beta(self):
        assert self.results["decision"] == "beta"

    def test_bond_index_zero(self):
        assert self.results["bond_index"] == pytest.approx(0.0, abs=0.01)

    def test_audit_artifact_has_required_fields(self):
        a = self.results["audit"]
        assert a["case_id"] == "CS1-Triage"
        assert "cryptographic_hash" in a


# ═══════════════════════════════════════════════════════════════════════════
# CS2: Whistleblower's Dilemma
# ═══════════════════════════════════════════════════════════════════════════


class TestCS2Whistleblower:
    """Case Study 2: Whistleblower (2 options, 7 dims, 4 agents, stratum constraint)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from erisml.examples.appendix_d_cs2_whistleblower import run_case_study_2

        self.results = run_case_study_2()

    def test_evaluation_tensor_shape(self):
        M = np.array(self.results["evaluation_tensor"])
        assert M.shape == (2, 4)  # 2 options x 4 agents

    def test_evaluation_tensor_values(self):
        M = np.array(self.results["evaluation_tensor"])
        expected = np.array(
            [
                [0.709, 0.837, 0.852, 0.653],  # Report
                [0.486, 0.244, 0.349, 0.610],  # Silence
            ]
        )
        np.testing.assert_allclose(M, expected, atol=0.01)

    def test_stratum_is_obligatory(self):
        assert self.results["stratum"] == "S_obl"

    def test_silence_forbidden_in_obligatory_stratum(self):
        constraints = self.results["stratum_constraints"]
        assert constraints["Report"] == 0.0
        assert constraints["Silence"] == float("-inf")

    def test_all_contractions_select_report(self):
        c = self.results["contractions"]
        assert c["utilitarian"]["verdict"] == "Report"
        assert c["rawlsian"]["verdict"] == "Report"
        assert c["expert_weighted"]["verdict"] == "Report"

    def test_utilitarian_report_score(self):
        scores = self.results["contractions"]["utilitarian"]["scores"]
        np.testing.assert_allclose(scores[0], 3.051, atol=0.02)

    def test_rawlsian_report_score(self):
        scores = self.results["contractions"]["rawlsian"]["scores"]
        np.testing.assert_allclose(scores[0], 0.653, atol=0.01)

    def test_expert_weighted_report_score(self):
        scores = self.results["contractions"]["expert_weighted"]["scores"]
        np.testing.assert_allclose(scores[0], 0.787, atol=0.02)

    def test_penumbral_zone_not_in_penumbral(self):
        """The unconstrained score gap is large enough that this scenario
        is NOT in the penumbral zone."""
        pz = self.results["penumbral_zone"]
        assert pz["in_penumbral_zone"] is False

    def test_penumbral_zone_post_collapse_verdict(self):
        pz = self.results["penumbral_zone"]
        assert pz["post_collapse_verdict"] == "Report"

    def test_bond_index_zero(self):
        assert self.results["bond_index"] == pytest.approx(0.0, abs=0.01)

    def test_decision_is_report(self):
        assert self.results["final_verdict"] == "Report"

    def test_audit_artifact_has_required_fields(self):
        a = self.results["audit_artifact"]
        assert a["case_id"] == "CS2-whistleblower"
        assert "cryptographic_hash" in a


# ═══════════════════════════════════════════════════════════════════════════
# CS3: Autonomous Vehicle Dilemma
# ═══════════════════════════════════════════════════════════════════════════


class TestCS3AutonomousVehicle:
    """Case Study 3: AV dilemma (3 options, 7 dims, 5 agents, metric-dependence)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from erisml.examples.appendix_d_cs3_av_dilemma import run_case_study_3

        self.results = run_case_study_3()

    def test_evaluation_tensor_shape(self):
        M = self.results["evaluation_tensor"]
        assert M.shape == (3, 5)

    def test_evaluation_tensor_values(self):
        M = self.results["evaluation_tensor"]
        expected = np.array(
            [
                [0.343, 0.376, 0.341, 0.366, 0.398],  # A (straight)
                [0.646, 0.648, 0.649, 0.638, 0.635],  # B (swerve left)
                [0.166, 0.183, 0.153, 0.158, 0.193],  # C (swerve right)
            ]
        )
        np.testing.assert_allclose(M, expected, atol=0.01)

    def test_b_dominates_all_perspectives(self):
        """Option B should dominate across all 5 perspectives."""
        M = self.results["evaluation_tensor"]
        assert np.all(M[1] > M[0])  # B > A for all agents
        assert np.all(M[1] > M[2])  # B > C for all agents

    def test_utilitarian_contraction(self):
        S = self.results["utilitarian"]
        np.testing.assert_allclose(S, [1.824, 3.216, 0.853], atol=0.02)

    def test_utilitarian_selects_b(self):
        assert np.argmax(self.results["utilitarian"]) == 1

    def test_rawlsian_contraction(self):
        S = self.results["rawlsian"]
        np.testing.assert_allclose(S, [0.341, 0.635, 0.153], atol=0.01)

    def test_rawlsian_selects_b(self):
        assert np.argmax(self.results["rawlsian"]) == 1

    def test_strict_deontology_selects_a(self):
        """Strict non-redirection deontology should select A (no redirection)."""
        assert self.results["deontological_strict_decision"] == "A"

    def test_consent_adjusted_deontology_selects_b(self):
        assert self.results["deontological_consent_decision"] == "B"

    def test_c_forbidden_under_all_deontological(self):
        """Option C should be forbidden under consent-adjusted deontology."""
        assert self.results["c_forbidden_deontological"] is True

    def test_moral_residue_nonzero(self):
        """Residue from selecting B is nonzero (Proposition 15.1)."""
        R = self.results["moral_residue"]
        assert np.any(np.abs(R) > 0.01)

    def test_bond_index_zero(self):
        assert self.results["bond_index"] == pytest.approx(0.0, abs=0.01)

    def test_decision_is_b(self):
        assert self.results["decision"] == "B"


# ═══════════════════════════════════════════════════════════════════════════
# CS4: Algorithmic Hiring
# ═══════════════════════════════════════════════════════════════════════════


class TestCS4AlgorithmicHiring:
    """Case Study 4: Algorithmic hiring (2 candidates, 8 dims, BIP bias detection)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from erisml.examples.appendix_d_cs4_hiring import run_case_study_4

        self.results = run_case_study_4()

    def test_evaluation_tensor_j_values(self):
        M = self.results["evaluation_tensor"]
        expected_J = {
            "company": 0.835,
            "candidate": 0.839,
            "regulator": 0.820,
            "society": 0.791,
        }
        for agent, exp_val in expected_J.items():
            assert M["J"][agent] == pytest.approx(exp_val, abs=0.01)

    def test_evaluation_tensor_k_values(self):
        M = self.results["evaluation_tensor"]
        expected_K = {
            "company": 0.805,
            "candidate": 0.824,
            "regulator": 0.800,
            "society": 0.735,
        }
        for agent, exp_val in expected_K.items():
            assert M["K"][agent] == pytest.approx(exp_val, abs=0.01)

    def test_j_dominates_all_perspectives(self):
        M = self.results["evaluation_tensor"]
        for agent in ["company", "candidate", "regulator", "society"]:
            assert M["J"][agent] > M["K"][agent]

    def test_utilitarian_contraction(self):
        c = self.results["contractions"]["utilitarian"]
        assert c["J"] == pytest.approx(3.285, abs=0.02)
        assert c["K"] == pytest.approx(3.164, abs=0.02)

    def test_rawlsian_contraction(self):
        c = self.results["contractions"]["rawlsian"]
        assert c["J"] == pytest.approx(0.791, abs=0.01)
        assert c["K"] == pytest.approx(0.735, abs=0.01)

    def test_expert_weighted_contraction(self):
        c = self.results["contractions"]["expert_weighted"]
        assert c["J"] == pytest.approx(0.821, abs=0.02)
        assert c["K"] == pytest.approx(0.791, abs=0.02)

    def test_all_contractions_select_j(self):
        c = self.results["contractions"]
        assert c["utilitarian"]["J"] > c["utilitarian"]["K"]
        assert c["rawlsian"]["J"] > c["rawlsian"]["K"]
        assert c["expert_weighted"]["J"] > c["expert_weighted"]["K"]

    def test_pure_meritocracy_still_selects_j(self):
        S = self.results["pure_meritocracy"]
        assert S["J"] == pytest.approx(0.854, abs=0.02)
        assert S["K"] == pytest.approx(0.831, abs=0.02)
        assert S["J"] > S["K"]

    def test_unbiased_system_bond_index_zero(self):
        bip = self.results["bip_unbiased"]
        assert bip["Bd"] == pytest.approx(0.0, abs=0.01)

    def test_biased_system_bond_index(self):
        bip = self.results["bip_biased"]
        assert bip["Bd"] == pytest.approx(0.51, abs=0.05)

    def test_decision_j_ranks_above_k(self):
        assert self.results["decision"] == "J ranks above K"


# ═══════════════════════════════════════════════════════════════════════════
# CS5: Climate Policy Allocation
# ═══════════════════════════════════════════════════════════════════════════


class TestCS5ClimatePolicy:
    """Case Study 5: Climate allocation (5 nations, 7 dims, Shapley values)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from erisml.examples.appendix_d_cs5_climate import run_case_study_5

        self.results = run_case_study_5()

    def test_shapley_values(self):
        phi = self.results["shapley_values"]
        np.testing.assert_allclose(
            [phi["N1"], phi["N2"], phi["N3"], phi["N4"], phi["N5"]],
            [0.387, 0.212, 0.003, 0.128, 0.270],
            atol=0.02,
        )

    def test_shapley_values_sum_to_one(self):
        phi = self.results["shapley_values"]
        total = sum(phi.values())
        assert total == pytest.approx(1.0, abs=0.02)

    def test_fair_allocation(self):
        alloc = self.results["fair_allocation"]
        np.testing.assert_allclose(
            [alloc["N1"], alloc["N2"], alloc["N3"], alloc["N4"], alloc["N5"]],
            [2.815, 1.542, 0.022, 0.931, 1.964],
            atol=0.03,
        )

    def test_fair_allocation_sums_to_required(self):
        alloc = self.results["fair_allocation"]
        total = sum(alloc.values())
        assert total == pytest.approx(7.275, abs=0.05)

    def test_ndc_pledges(self):
        ndc = self.results["ndc_pledges"]
        assert ndc == {"N1": 2.00, "N2": 1.00, "N3": 0.01, "N4": 0.80, "N5": 1.20}

    def test_contraction_loss(self):
        loss = self.results["contraction_loss"]
        assert loss == pytest.approx(2.264, abs=0.05)

    def test_gap_distribution(self):
        gap = self.results["gap_distribution"]
        np.testing.assert_allclose(
            [gap["N1"], gap["N2"], gap["N3"], gap["N4"], gap["N5"]],
            [-0.815, -0.542, -0.012, -0.131, -0.764],
            atol=0.03,
        )

    def test_n1_bears_largest_absolute_burden(self):
        alloc = self.results["fair_allocation"]
        assert alloc["N1"] == max(alloc.values())

    def test_n5_bears_highest_proportional_burden(self):
        pct = self.results["reduction_pct"]
        assert pct["N5"] == max(pct.values())

    def test_n3_bears_negligible_burden(self):
        alloc = self.results["fair_allocation"]
        assert alloc["N3"] < 0.05

    def test_bond_index_zero(self):
        assert self.results["bond_index"] == pytest.approx(0.0, abs=0.01)

    def test_audit_artifact_has_shapley(self):
        a = self.results["audit"]
        assert "shapley_values" in a
        assert "cryptographic_hash" in a


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline Utilities
# ═══════════════════════════════════════════════════════════════════════════


class TestPipelineUtilities:
    """Unit tests for the shared pipeline functions."""

    def test_evaluation_tensor_simple(self):
        obligations = {"opt1": np.array([1.0, 0.0]), "opt2": np.array([0.0, 1.0])}
        interests = {"agent1": np.array([0.5, 0.5])}
        M, opts, agents = compute_evaluation_tensor(obligations, interests)
        assert M.shape == (2, 1)
        np.testing.assert_allclose(M[:, 0], [0.5, 0.5])

    def test_contraction_utilitarian_simple(self):
        M = np.array([[1.0, 2.0], [3.0, 4.0]])
        S = contraction_utilitarian(M)
        np.testing.assert_allclose(S, [3.0, 7.0])

    def test_contraction_rawlsian_simple(self):
        M = np.array([[1.0, 2.0], [3.0, 0.5]])
        S = contraction_rawlsian(M)
        np.testing.assert_allclose(S, [1.0, 0.5])

    def test_contraction_expert_weighted_simple(self):
        M = np.array([[1.0, 2.0], [3.0, 4.0]])
        w = np.array([0.3, 0.7])
        S = contraction_expert_weighted(M, w)
        np.testing.assert_allclose(S, [1.7, 3.7])

    def test_metric_distance_euclidean_zero(self):
        obl = np.ones(5)
        d = metric_distance_euclidean(obl)
        assert d == pytest.approx(0.0)

    def test_metric_distance_euclidean_known(self):
        obl = np.array([0.5, 0.5])
        d = metric_distance_euclidean(obl)
        expected = np.sqrt(0.25 + 0.25)
        assert d == pytest.approx(expected, abs=1e-10)

    def test_metric_distance_weighted_identity_equals_euclidean(self):
        obl = np.array([0.3, 0.7, 0.5])
        g = np.ones(3)
        d_w = metric_distance_weighted(obl, g)
        d_e = metric_distance_euclidean(obl)
        assert d_w == pytest.approx(d_e, abs=1e-10)

    def test_shapley_values_unanimity_game(self):
        """In a unanimity game, Shapley values are equal."""
        agents = ["a", "b", "c"]

        def v(S):
            return 1.0 if len(S) == 3 else 0.0

        phi = compute_shapley_values(agents, v)
        for a in agents:
            assert phi[a] == pytest.approx(1.0 / 3.0, abs=1e-10)

    def test_shapley_values_dictator_game(self):
        """In a dictator game, only the dictator has nonzero value."""
        agents = ["a", "b"]

        def v(S):
            return 1.0 if "a" in S else 0.0

        phi = compute_shapley_values(agents, v)
        assert phi["a"] == pytest.approx(1.0)
        assert phi["b"] == pytest.approx(0.0)
