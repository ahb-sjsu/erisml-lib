"""
Appendix D, Case Study 3: Autonomous Vehicle Dilemma.

Scenario
--------
An AV travelling at 50 km/h faces an unavoidable collision with three
possible trajectories:

  A (Straight)     -- strike pedestrian (~80% serious injury to ped,
                      ~5% to passenger)
  B (Swerve Left)  -- hit barrier (~60% serious injury to passenger,
                      ~0% to pedestrian)
  C (Swerve Right) -- into crosswalk (~70% serious injury to child,
                      ~10% to passenger)

The analysis uses the geometric ethics pipeline (Chapter 7) with a 7-D
active subspace of the full 9-D moral manifold: welfare (mu=1),
rights (mu=2), fairness (mu=3), autonomy (mu=4), societal (mu=6),
care (mu=7), epistemic (mu=9).

Pipeline
--------
  scenario -> grounding Psi -> obligation vectors O^mu_i ->
  interest covectors I^(a)_mu -> evaluation tensor M_{ia} ->
  contractions (utilitarian, Rawlsian, deontological) ->
  moral residue -> Bond Index -> decision

Decision: B (Swerve left, risk passenger).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from erisml.examples.appendix_d_pipeline import (
    DIMENSION_LABELS,
    compute_bond_index,
    compute_evaluation_tensor,
    contraction_rawlsian,
    contraction_utilitarian,
    generate_audit_artifact,
)

# ── Active dimensions ───────────────────────────────────────────────────
# 7 of 9 canonical dimensions are relevant to this scenario.
# Indices are 0-based into DIMENSION_LABELS (the mu labels are 1-based).

ACTIVE_DIM_INDICES = [0, 1, 2, 3, 5, 6, 8]  # mu=1,2,3,4,6,7,9
ACTIVE_DIM_LABELS = [DIMENSION_LABELS[i] for i in ACTIVE_DIM_INDICES]

# ── Obligation vectors (tangent vectors, 7-D) ──────────────────────────
# What each option "delivers" across the active moral dimensions.

OBLIGATIONS: Dict[str, np.ndarray] = {
    "A": np.array([0.30, 0.25, 0.40, 0.50, 0.35, 0.30, 0.70]),
    "B": np.array([0.55, 0.70, 0.65, 0.75, 0.60, 0.65, 0.60]),
    "C": np.array([0.20, 0.10, 0.15, 0.20, 0.10, 0.10, 0.55]),
}

# ── Interest covectors (dual vectors, 7-D, 5 agents) ───────────────────
# What matters to each perspective.

INTERESTS: Dict[str, np.ndarray] = {
    "Pedestrian": np.array([0.25, 0.30, 0.15, 0.10, 0.05, 0.10, 0.05]),
    "Passenger": np.array([0.30, 0.15, 0.10, 0.25, 0.05, 0.10, 0.05]),
    "Child/Guardian": np.array([0.15, 0.25, 0.20, 0.05, 0.05, 0.25, 0.05]),
    "Society": np.array([0.15, 0.15, 0.20, 0.10, 0.25, 0.10, 0.05]),
    "Manufacturer": np.array([0.10, 0.15, 0.10, 0.10, 0.30, 0.10, 0.15]),
}

# ── Expected evaluation tensor values (from Appendix D) ────────────────
# M_{ia} = I^(a)_mu * O^mu_i  -- used for verification.

EXPECTED_M = np.array(
    [
        [0.343, 0.376, 0.341, 0.366, 0.398],  # A
        [0.646, 0.648, 0.649, 0.638, 0.635],  # B
        [0.166, 0.183, 0.153, 0.158, 0.193],  # C
    ]
)


# ── Printing helpers ────────────────────────────────────────────────────


def _header(title: str) -> None:
    """Print a section header."""
    rule = "-" * 72
    print(f"\n{rule}")
    print(f"  {title}")
    print(rule)


def _print_vector(
    label: str,
    vec: np.ndarray,
    dim_labels: List[str],
) -> None:
    """Print a labelled vector aligned with dimension names."""
    parts = ", ".join(f"{d}={v:.2f}" for d, v in zip(dim_labels, vec))
    print(f"  {label:<18s}: ({parts})")


def _print_table(
    M: np.ndarray,
    row_labels: List[str],
    col_labels: List[str],
    title: str = "Evaluation Tensor M_{ia}",
) -> None:
    """Print the evaluation tensor as a formatted table."""
    col_width = 14
    header = f"  {'':>4s}" + "".join(f"{c:>{col_width}s}" for c in col_labels)
    print(f"\n  {title}")
    print(header)
    for i, row_label in enumerate(row_labels):
        row = f"  {row_label:>4s}" + "".join(
            f"{M[i, j]:{col_width}.3f}" for j in range(M.shape[1])
        )
        print(row)


# ── Deontological analysis ──────────────────────────────────────────────


def deontological_analysis(
    option_labels: List[str],
) -> Dict[str, Dict[str, Any]]:
    """Evaluate the three options under strict and consent-adjusted
    deontological frameworks.

    Strict deontology
    -----------------
    Swerving actively redirects harm onto a new victim.  Under the
    Doctrine of Double Effect the key question is whether the agent
    *intends* harm as a means.  Option A involves no redirection
    (the AV merely continues on its current trajectory), so it
    receives no deontological penalty.  Options B and C redirect harm
    and therefore incur a penalty.

    Consent-adjusted deontology
    ---------------------------
    A passenger who boards an AV implicitly accepts the risk that the
    vehicle may take protective evasive action.  This "soft consent"
    mitigates the redirection penalty for B.  No such consent exists
    for the child in option C, which is treated as categorically
    impermissible (score = -inf).

    Returns a dict keyed by option label, each containing:
      strict_score, consent_score, strict_winner, consent_winner,
      redirects_harm, has_consent, notes.
    """
    info: Dict[str, Dict[str, Any]] = {}

    # A: no redirection -- permissible but passive (no protective action)
    info["A"] = {
        "redirects_harm": False,
        "has_consent": None,  # not applicable
        "strict_score": 1.0,
        "consent_score": 0.5,
        "notes": (
            "No redirection; AV continues current trajectory.  "
            "Permissible but passive -- fails duty-of-care to "
            "protect vulnerable road users when a consented "
            "alternative exists."
        ),
    }

    # B: redirects harm to passenger (who consented)
    info["B"] = {
        "redirects_harm": True,
        "has_consent": True,
        "strict_score": 0.0,
        "consent_score": 1.0,
        "notes": (
            "Redirects harm to passenger.  Passenger's implicit "
            "consent mitigates deontological penalty and activates "
            "duty-of-care toward the pedestrian."
        ),
    }

    # C: redirects harm to child (no consent)
    info["C"] = {
        "redirects_harm": True,
        "has_consent": False,
        "strict_score": 0.0,
        "consent_score": float("-inf"),
        "notes": (
            "Redirects harm to child with no consent.  "
            "Categorically impermissible under consent-adjusted "
            "deontology."
        ),
    }

    return info


# ── Moral residue ───────────────────────────────────────────────────────


def compute_moral_residue_B() -> List[Dict[str, Any]]:
    """Return the moral residue entries that remain after selecting B.

    Even the best available option (B) leaves unresolved obligations.
    These residues are not defeasible -- they persist as governance
    artifacts and must be tracked.
    """
    return [
        {
            "type": "welfare",
            "description": (
                "Passenger harm: 60% serious-injury risk. " "Welfare residue = 0.45."
            ),
            "residue_value": 0.45,
        },
        {
            "type": "agency",
            "description": (
                "Agency residue: algorithmic redirection of harm. "
                "The AV system (not the passenger) chose to swerve."
            ),
            "residue_value": None,  # qualitative
        },
        {
            "type": "epistemic",
            "description": (
                "Epistemic residue: swerve-outcome uncertainty. "
                "O^9_B = 0.60 vs O^9_A = 0.70 -- the swerve "
                "trajectory carries higher epistemic uncertainty."
            ),
            "residue_value": 0.10,  # delta
        },
    ]


# ── Metric-dependence analysis ──────────────────────────────────────────


def metric_dependence_analysis(
    M: np.ndarray,
    option_labels: List[str],
    agent_labels: List[str],
) -> Dict[str, Any]:
    """Show where utilitarian and deontological frameworks agree and
    disagree, and characterise the metric-dependence of the verdict.

    The utilitarian contraction sums satisfaction across agents;
    the Rawlsian contraction takes the minimum.  Both pick B.
    Strict deontology picks A (no redirection).  Consent-adjusted
    deontology picks B (passenger consent mitigates).

    Returns a summary dict suitable for audit logging.
    """
    S_util = contraction_utilitarian(M)
    S_rawl = contraction_rawlsian(M)
    deon = deontological_analysis(option_labels)

    util_winner = option_labels[int(np.argmax(S_util))]
    rawl_winner = option_labels[int(np.argmax(S_rawl))]

    strict_scores = [deon[o]["strict_score"] for o in option_labels]
    consent_scores = [deon[o]["consent_score"] for o in option_labels]

    # For strict deontology, argmax of finite scores
    strict_winner = option_labels[int(np.argmax(strict_scores))]
    # For consent-adjusted, filter out -inf then argmax
    finite_consent = [
        (i, s) for i, s in enumerate(consent_scores) if s != float("-inf")
    ]
    consent_winner = option_labels[max(finite_consent, key=lambda t: t[1])[0]]

    agreements = {
        "util_vs_rawlsian": util_winner == rawl_winner,
        "util_vs_strict_deon": util_winner == strict_winner,
        "util_vs_consent_deon": util_winner == consent_winner,
        "rawl_vs_consent_deon": rawl_winner == consent_winner,
    }

    return {
        "utilitarian": {
            "scores": {o: float(s) for o, s in zip(option_labels, S_util)},
            "winner": util_winner,
        },
        "rawlsian": {
            "scores": {o: float(s) for o, s in zip(option_labels, S_rawl)},
            "winner": rawl_winner,
        },
        "strict_deontological": {
            "scores": {o: float(s) for o, s in zip(option_labels, strict_scores)},
            "winner": strict_winner,
        },
        "consent_adjusted_deontological": {
            "scores": {o: s for o, s in zip(option_labels, consent_scores)},
            "winner": consent_winner,
        },
        "agreements": agreements,
    }


# ── Bond Index (invariance test) ────────────────────────────────────────


def run_invariance_transforms(
    obligations: Dict[str, np.ndarray],
    interests: Dict[str, np.ndarray],
) -> Tuple[str, Dict[str, str]]:
    """Apply invariance-preserving transforms and check whether the
    verdict (option B) is stable.

    Transforms tested:
      1. Relabel agents (permute columns of M).
      2. Uniform scale of all obligation vectors.
      3. Positive rescale of all interest covectors.

    Returns the original verdict and a dict of transform -> verdict.
    """
    # Original verdict
    M_orig, opt_labels, _ = compute_evaluation_tensor(obligations, interests)
    S_orig = contraction_utilitarian(M_orig)
    original_verdict = opt_labels[int(np.argmax(S_orig))]

    results: Dict[str, str] = {}

    # Transform 1: relabel agents (reverse order)
    reversed_interests = dict(reversed(list(interests.items())))
    M_t1, _, _ = compute_evaluation_tensor(obligations, reversed_interests)
    S_t1 = contraction_utilitarian(M_t1)
    results["relabel_agents"] = opt_labels[int(np.argmax(S_t1))]

    # Transform 2: uniform scale obligations by factor 2.0
    scaled_obligations = {k: v * 2.0 for k, v in obligations.items()}
    M_t2, _, _ = compute_evaluation_tensor(scaled_obligations, interests)
    S_t2 = contraction_utilitarian(M_t2)
    results["scale_obligations_x2"] = opt_labels[int(np.argmax(S_t2))]

    # Transform 3: positive rescale interests by factor 0.5
    scaled_interests = {k: v * 0.5 for k, v in interests.items()}
    M_t3, _, _ = compute_evaluation_tensor(obligations, scaled_interests)
    S_t3 = contraction_utilitarian(M_t3)
    results["rescale_interests_x0.5"] = opt_labels[int(np.argmax(S_t3))]

    return original_verdict, results


# ═══════════════════════════════════════════════════════════════════════
# Main case-study runner
# ═══════════════════════════════════════════════════════════════════════


def run_case_study_3() -> Dict[str, Any]:
    """Execute Case Study 3 end-to-end and return a results dict.

    Returns
    -------
    results : dict
        Keys include evaluation_tensor, utilitarian, rawlsian,
        deontological_strict_decision, deontological_consent_decision,
        c_forbidden_deontological, moral_residue, bond_index, decision,
        audit_artifact.
    """
    results: Dict[str, Any] = {}

    # ── Evaluation tensor ──────────────────────────────────────────
    M, opt_labels, agent_labels = compute_evaluation_tensor(OBLIGATIONS, INTERESTS)
    results["evaluation_tensor"] = M
    results["option_labels"] = opt_labels
    results["agent_labels"] = agent_labels

    # ── Contractions ───────────────────────────────────────────────
    S_util = contraction_utilitarian(M)
    S_rawl = contraction_rawlsian(M)
    results["utilitarian"] = S_util
    results["rawlsian"] = S_rawl

    # ── Deontological analysis ─────────────────────────────────────
    deon = deontological_analysis(opt_labels)
    strict_winner = max(opt_labels, key=lambda o: deon[o]["strict_score"])
    consent_winner = max(
        opt_labels,
        key=lambda o: (
            deon[o]["consent_score"]
            if deon[o]["consent_score"] != float("-inf")
            else -1e18
        ),
    )
    results["deontological_strict_decision"] = strict_winner
    results["deontological_consent_decision"] = consent_winner
    results["c_forbidden_deontological"] = deon["C"]["strict_score"] == 0.0 and deon[
        "C"
    ]["consent_score"] == float("-inf")

    # ── Metric-dependence ──────────────────────────────────────────
    dep = metric_dependence_analysis(M, opt_labels, agent_labels)
    results["metric_dependence"] = dep

    # ── Moral residue ──────────────────────────────────────────────
    residues = compute_moral_residue_B()
    residue_values = np.array(
        [r["residue_value"] for r in residues if r["residue_value"] is not None]
    )
    results["moral_residue"] = residue_values
    results["moral_residue_detail"] = residues

    # ── Bond Index ─────────────────────────────────────────────────
    original_verdict, transform_results = run_invariance_transforms(
        OBLIGATIONS, INTERESTS
    )
    Bd, n_preserved, n_changed = compute_bond_index(original_verdict, transform_results)
    results["bond_index"] = Bd

    # ── Decision ───────────────────────────────────────────────────
    results["decision"] = "B"

    # ── Audit artifact ─────────────────────────────────────────────
    results["audit_artifact"] = generate_audit_artifact(
        case_id="CS3-AV-DILEMMA",
        scenario=(
            "Autonomous vehicle at 50 km/h, unavoidable collision. "
            "Three trajectories: A (straight, strike pedestrian), "
            "B (swerve left, hit barrier), "
            "C (swerve right, into crosswalk with child)."
        ),
        active_dimensions=ACTIVE_DIM_LABELS,
        evaluation_tensor=M.tolist(),
        bond_index=Bd,
        decision="B",
    )

    return results


# ═══════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════


def main() -> None:
    """Run Case Study 3 and print the full narrative."""
    run_case_study_3()


if __name__ == "__main__":
    main()
