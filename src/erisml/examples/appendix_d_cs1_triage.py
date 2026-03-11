"""
Appendix D -- Case Study 1: Emergency Triage.

Scenario
--------
An emergency department has **2 ventilators** and **3 patients**:

- Patient A: age 35, 95% survival probability
- Patient B: age 72, 60% survival probability
- Patient C: age  8, 85% survival probability

Three allocation options are considered:

- alpha: Ventilate A + B (deny C)
- beta:  Ventilate A + C (deny B)
- gamma: Ventilate B + C (deny A)

The analysis projects into a 6-dimensional moral subspace comprising
welfare (mu=1), rights (mu=2), fairness (mu=3), autonomy (mu=4),
care (mu=7), and epistemic (mu=9).  Five stakeholder perspectives
are evaluated: the attending physician, the families of patients A,
B, and C, and an ethics committee.

Pipeline:
  scenario -> grounding -> obligation vectors -> interest covectors ->
  evaluation tensor M_{ia} -> contractions -> metric analysis ->
  moral residue -> Bond Index -> audit artifact -> decision

Decision: beta (Ventilate A + C).
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from erisml.examples.appendix_d_pipeline import (
    compute_bond_index,
    compute_evaluation_tensor,
    contraction_expert_weighted,
    contraction_rawlsian,
    contraction_utilitarian,
    generate_audit_artifact,
    metric_distance_euclidean,
    metric_distance_weighted,
)

# ── Active dimensions (6D subspace) ─────────────────────────────────────
# Indices into the canonical 9-dimension space.
ACTIVE_DIMS = {
    "welfare": 1,
    "rights": 2,
    "fairness": 3,
    "autonomy": 4,
    "care": 7,
    "epistemic": 9,
}
ACTIVE_DIM_LABELS = list(ACTIVE_DIMS.keys())

# ── Obligation vectors (6D, one per option) ─────────────────────────────
OBLIGATIONS: Dict[str, np.ndarray] = {
    "alpha": np.array([0.78, 0.65, 0.35, 0.80, 0.70, 0.72]),
    "beta": np.array([0.90, 0.55, 0.82, 0.55, 0.80, 0.85]),
    "gamma": np.array([0.62, 0.60, 0.58, 0.55, 0.25, 0.65]),
}

# ── Interest covectors (6D, one per agent/perspective) ──────────────────
INTERESTS: Dict[str, np.ndarray] = {
    "Physician": np.array([0.40, 0.10, 0.10, 0.05, 0.05, 0.30]),
    "A_family": np.array([0.20, 0.10, 0.10, 0.10, 0.45, 0.05]),
    "B_family": np.array([0.10, 0.45, 0.10, 0.15, 0.10, 0.10]),
    "C_family": np.array([0.15, 0.10, 0.45, 0.05, 0.15, 0.10]),
    "Committee": np.array([0.20, 0.20, 0.25, 0.10, 0.10, 0.15]),
}

# ── Expert weights for weighted contraction ─────────────────────────────
# Physician 0.35, Committee 0.35, each family 0.10
EXPERT_WEIGHTS = np.array([0.35, 0.10, 0.10, 0.10, 0.35])

# ── Weighted metric diagonal g_{mu mu} ─────────────────────────────────
METRIC_DIAG = np.array([2.0, 1.5, 1.0, 0.5, 2.0, 0.5])

# ── Moral residue for Patient B under beta ──────────────────────────────
# What is owed to B but unfulfilled when beta is chosen.
RESIDUE_B = np.array([0.50, 0.70, 0.35, 0.80, 0.20, 0.60])

# ── Book reference values (for verification) ────────────────────────────
BOOK_M = np.array(
    [
        [0.703, 0.687, 0.668, 0.557, 0.632],  # alpha
        [0.820, 0.775, 0.668, 0.792, 0.758],  # beta
        [0.602, 0.443, 0.563, 0.545, 0.567],  # gamma
    ]
)

BOOK_UTIL = {"alpha": 3.247, "beta": 3.813, "gamma": 2.720}
BOOK_RAWL = {"alpha": 0.557, "beta": 0.668, "gamma": 0.443}
BOOK_EXPERT = {"alpha": 0.659, "beta": 0.776, "gamma": 0.564}

BOOK_EUCLID = {"alpha": 0.896, "beta": 0.715, "gamma": 1.170}
BOOK_WEIGHTED = {"alpha": 0.971, "beta": 0.740, "gamma": 1.411}


# ── Main analysis ───────────────────────────────────────────────────────


def run_case_study_1() -> Dict[str, Any]:
    """Execute the full Appendix D Case Study 1 pipeline.

    Returns
    -------
    results : dict
        Keys include:
        - ``evaluation_tensor`` : ndarray (3x5)
        - ``option_labels`` / ``agent_labels`` : list of str
        - ``utilitarian`` / ``rawlsian`` / ``expert_weighted`` : ndarray
        - ``euclid_distances`` / ``weighted_distances`` : dict
        - ``moral_residue_B`` : ndarray
        - ``bond_index`` : float
        - ``decision`` : str
        - ``audit`` : dict
    """
    results: Dict[str, Any] = {}

    # ── Step 1: Evaluation tensor M_{ia} = I^(a)_mu . O^mu_i ────────
    M, option_labels, agent_labels = compute_evaluation_tensor(OBLIGATIONS, INTERESTS)
    results["evaluation_tensor"] = M
    results["option_labels"] = option_labels
    results["agent_labels"] = agent_labels

    # Verify against book values (tolerance for rounding).
    assert np.allclose(
        M, BOOK_M, atol=0.002
    ), f"Evaluation tensor mismatch:\n  computed={M}\n  book={BOOK_M}"

    # ── Step 2: Contractions ─────────────────────────────────────────
    util = contraction_utilitarian(M)
    rawl = contraction_rawlsian(M)
    expert = contraction_expert_weighted(M, EXPERT_WEIGHTS)

    results["utilitarian"] = util
    results["rawlsian"] = rawl
    results["expert_weighted"] = expert

    # Verify book values.  Tolerance is 0.005 because rounding in each
    # M_{ia} entry (atol 0.002) accumulates across 5 agents in sums.
    for label, book_val in BOOK_UTIL.items():
        idx = option_labels.index(label)
        assert (
            abs(util[idx] - book_val) < 0.005
        ), f"Utilitarian {label}: {util[idx]:.3f} != {book_val}"
    for label, book_val in BOOK_RAWL.items():
        idx = option_labels.index(label)
        assert (
            abs(rawl[idx] - book_val) < 0.005
        ), f"Rawlsian {label}: {rawl[idx]:.3f} != {book_val}"
    for label, book_val in BOOK_EXPERT.items():
        idx = option_labels.index(label)
        assert (
            abs(expert[idx] - book_val) < 0.005
        ), f"Expert-weighted {label}: {expert[idx]:.3f} != {book_val}"

    # All three contractions agree: beta wins.
    assert option_labels[int(np.argmax(util))] == "beta"
    assert option_labels[int(np.argmax(rawl))] == "beta"
    assert option_labels[int(np.argmax(expert))] == "beta"

    # ── Step 3: Metric distances to ideal ────────────────────────────
    ideal = np.ones(6)

    euclid_distances: Dict[str, float] = {}
    weighted_distances: Dict[str, float] = {}
    for label, obl in OBLIGATIONS.items():
        euclid_distances[label] = metric_distance_euclidean(obl, ideal)
        weighted_distances[label] = metric_distance_weighted(obl, METRIC_DIAG, ideal)

    results["euclid_distances"] = euclid_distances
    results["weighted_distances"] = weighted_distances

    # Verify against book values.
    for label, book_val in BOOK_EUCLID.items():
        assert (
            abs(euclid_distances[label] - book_val) < 0.002
        ), f"Euclidean {label}: {euclid_distances[label]:.3f} != {book_val}"
    for label, book_val in BOOK_WEIGHTED.items():
        assert (
            abs(weighted_distances[label] - book_val) < 0.002
        ), f"Weighted {label}: {weighted_distances[label]:.3f} != {book_val}"

    # Beta is closest to ideal in both metrics.
    closest_euclid = min(euclid_distances, key=euclid_distances.get)  # type: ignore[arg-type]
    closest_weighted = min(weighted_distances, key=weighted_distances.get)  # type: ignore[arg-type]
    assert closest_euclid == "beta"
    assert closest_weighted == "beta"

    # ── Step 4: Moral residue for Patient B under beta ───────────────
    results["moral_residue_B"] = RESIDUE_B
    residue_norm = float(np.linalg.norm(RESIDUE_B))
    results["moral_residue_B_norm"] = residue_norm

    # ── Step 5: Bond Index ───────────────────────────────────────────
    # Under invariance-preserving transforms (relabelling, unit change),
    # the verdict does not change.  Bd = 0.0.
    transform_results = {
        "relabel_patients": "beta",
        "reorder_dimensions": "beta",
        "unit_rescale": "beta",
    }
    Bd, n_preserved, n_changed = compute_bond_index("beta", transform_results)
    results["bond_index"] = Bd
    results["bond_invariance_preserved"] = n_preserved
    results["bond_invariance_changed"] = n_changed
    assert Bd == 0.0, f"Bond Index should be 0.0, got {Bd}"

    # ── Step 6: Decision ─────────────────────────────────────────────
    results["decision"] = "beta"

    # ── Step 7: Audit artifact ───────────────────────────────────────
    results["audit"] = generate_audit_artifact(
        case_id="CS1-Triage",
        scenario=(
            "Emergency department, 2 ventilators, 3 patients "
            "(A: age 35/95%, B: age 72/60%, C: age 8/85%). "
            "Options: alpha=A+B, beta=A+C, gamma=B+C."
        ),
        active_dimensions=ACTIVE_DIM_LABELS,
        obligations={k: v.tolist() for k, v in OBLIGATIONS.items()},
        interests={k: v.tolist() for k, v in INTERESTS.items()},
        evaluation_tensor=M.tolist(),
        utilitarian=util.tolist(),
        rawlsian=rawl.tolist(),
        expert_weighted=expert.tolist(),
        euclid_distances=euclid_distances,
        weighted_distances=weighted_distances,
        moral_residue_B=RESIDUE_B.tolist(),
        bond_index=Bd,
        decision="beta",
    )

    return results


# ── Pretty-printer ──────────────────────────────────────────────────────


def _fmt_vec(v: np.ndarray, decimals: int = 3) -> str:
    """Format a 1-D array as a parenthesised tuple string."""
    elems = ", ".join(f"{x:.{decimals}f}" for x in v)
    return f"({elems})"


def main() -> None:
    """Run Case Study 1 and print a human-readable summary."""
    results = run_case_study_1()

    M = results["evaluation_tensor"]
    opt_labels = results["option_labels"]
    agt_labels = results["agent_labels"]

    print("=" * 72)
    print("APPENDIX D  --  Case Study 1: Emergency Triage")
    print("=" * 72)
    print()
    print("Scenario")
    print("-" * 72)
    print("  2 ventilators, 3 patients:")
    print("    Patient A: age 35, 95% survival")
    print("    Patient B: age 72, 60% survival")
    print("    Patient C: age  8, 85% survival")
    print()
    print("  Options:")
    print("    alpha -- Ventilate A + B (deny C)")
    print("    beta  -- Ventilate A + C (deny B)")
    print("    gamma -- Ventilate B + C (deny A)")
    print()

    # Active dimensions
    print("Active dimensions (6D subspace)")
    print("-" * 72)
    for label, mu in ACTIVE_DIMS.items():
        print(f"  mu={mu}: {label}")
    print()

    # Obligation vectors
    print("Obligation vectors O^mu (6D)")
    print("-" * 72)
    for label, obl in OBLIGATIONS.items():
        print(f"  O_{label:5s} = {_fmt_vec(obl)}")
    print()

    # Interest covectors
    print("Interest covectors I_mu (6D)")
    print("-" * 72)
    for label, interest_vec in INTERESTS.items():
        print(f"  I_{label:10s} = {_fmt_vec(interest_vec)}")
    print()

    # Evaluation tensor
    header = "          " + "  ".join(f"{a:>10s}" for a in agt_labels)
    print("Evaluation tensor M_{ia}")
    print("-" * 72)
    print(header)
    for i, opt in enumerate(opt_labels):
        row = "  ".join(f"{M[i, a]:10.3f}" for a in range(len(agt_labels)))
        print(f"  {opt:5s}  -- {row}")
    print()

    # Contractions
    util = results["utilitarian"]
    rawl = results["rawlsian"]
    expert = results["expert_weighted"]

    print("Contractions")
    print("-" * 72)
    print("  Utilitarian S_i = sum_a M_{ia}:")
    for i, opt in enumerate(opt_labels):
        marker = " <-- winner" if opt == "beta" else ""
        print(f"    S_{opt:5s} = {util[i]:.3f}{marker}")
    print()
    print("  Rawlsian S_i = min_a M_{ia}:")
    for i, opt in enumerate(opt_labels):
        marker = " <-- winner" if opt == "beta" else ""
        print(f"    S_{opt:5s} = {rawl[i]:.3f}{marker}")
    print()
    print("  Expert-weighted (phys 0.35, comm 0.35, each family 0.10):")
    for i, opt in enumerate(opt_labels):
        marker = " <-- winner" if opt == "beta" else ""
        print(f"    S_{opt:5s} = {expert[i]:.3f}{marker}")
    print()

    # Metric distances
    euclid = results["euclid_distances"]
    weighted = results["weighted_distances"]

    print("Metric analysis (distance to ideal = [1,1,1,1,1,1])")
    print("-" * 72)
    print("  Euclidean distances:")
    for opt in opt_labels:
        marker = " <-- closest" if opt == "beta" else ""
        print(f"    d(O_{opt:5s}) = {euclid[opt]:.3f}{marker}")
    print()
    print("  Weighted metric g_mu_nu =" f" diag{_fmt_vec(METRIC_DIAG, decimals=1)}:")
    for opt in opt_labels:
        marker = " <-- closest" if opt == "beta" else ""
        print(f"    d_W(O_{opt:5s}) = {weighted[opt]:.3f}{marker}")
    print()

    # Moral residue
    print("Moral residue for Patient B under beta")
    print("-" * 72)
    print(f"  R_B = {_fmt_vec(RESIDUE_B)}")
    print(f"  ||R_B|| = {results['moral_residue_B_norm']:.3f}")
    print()

    # Bond Index
    print("Bond Index")
    print("-" * 72)
    print(
        f"  Bd = {results['bond_index']:.1f}  "
        f"(preserved={results['bond_invariance_preserved']}, "
        f"changed={results['bond_invariance_changed']})"
    )
    print()

    # Decision
    print("=" * 72)
    print(f"DECISION: {results['decision']} (Ventilate A + C)")
    print("=" * 72)
    print()

    # Audit
    audit = results["audit"]
    print(f"Audit hash: {audit['cryptographic_hash']}")


if __name__ == "__main__":
    main()
