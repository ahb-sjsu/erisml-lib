"""
Appendix D -- Case Study 2: Whistleblower's Dilemma.

Scenario
--------
Dana, a financial analyst, discovers documented securities fraud at her
firm.  She faces two options:

  R  (Report)  -- File a formal whistleblower complaint.
  S  (Silence) -- Do not report the fraud.

The evidence quality (0.92) far exceeds the fraud threshold (tau_fraud
= 0.70), so the stratum gate fires into the **obligatory** stratum
S_obl, which sets the stratum constraint S_C(Silence) = -inf and
structurally forces the verdict to Report.

Pipeline stages exercised
-------------------------
  1. Scenario grounding and stratification gate
  2. 7-D obligation vectors and 4-agent interest covectors
  3. Evaluation tensor M_{ia} = I_mu^(a) O^mu_i
  4. Three contractions (utilitarian, Rawlsian, expert-weighted),
     all dominated by the stratum constraint
  5. Moral-residue analysis (privacy sacrifice, career disruption)
  6. Bond Index via invariance-preserving transforms
  7. Penumbral-zone / quantum-aspect modeling
  8. Audit artifact generation

All numerical values are taken verbatim from the book manuscript.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import numpy as np

from erisml.examples.appendix_d_pipeline import (
    DIMENSION_LABELS,
    compute_bond_index,
    compute_evaluation_tensor,
    contraction_expert_weighted,
    contraction_rawlsian,
    contraction_utilitarian,
    generate_audit_artifact,
)

# ── Constants ───────────────────────────────────────────────────────────

CASE_ID = "CS2-whistleblower"

# Active dimensions (7 of the canonical 9).
# Indices into the canonical 9-D label list.
ACTIVE_DIM_INDICES = [0, 1, 2, 3, 4, 5, 8]  # welfare..epistemic
ACTIVE_DIM_LABELS = [DIMENSION_LABELS[i] for i in ACTIVE_DIM_INDICES]
N_DIM = len(ACTIVE_DIM_LABELS)  # 7

# Stratification thresholds
TAU_FRAUD = 0.70
EVIDENCE_QUALITY = 0.92

# Negative-infinity sentinel for stratum constraint.
NEG_INF = float("-inf")

# Obligation vectors in S_obl (7-D)
#   dims: welfare, rights, fairness, autonomy, privacy, societal, epistemic
O_R = np.array([0.75, 0.90, 0.85, 0.80, 0.40, 0.90, 0.92])
O_S = np.array([0.45, 0.10, 0.10, 0.30, 0.90, 0.10, 0.92])

# Interest covectors (7-D, 4 agents)
I_ANALYST = np.array([0.30, 0.10, 0.05, 0.20, 0.25, 0.05, 0.05])
I_INVESTORS = np.array([0.15, 0.30, 0.25, 0.05, 0.05, 0.15, 0.05])
I_REGULATOR = np.array([0.10, 0.15, 0.15, 0.05, 0.05, 0.30, 0.20])
I_COMPANY = np.array([0.25, 0.05, 0.05, 0.10, 0.40, 0.05, 0.10])

# Expert weights for the weighted contraction
EXPERT_WEIGHTS = np.array([0.20, 0.30, 0.35, 0.15])  # analyst, invest, reg, co

# Expected evaluation-tensor values (from book Table D.2)
EXPECTED_M = np.array(
    [
        [0.709, 0.837, 0.852, 0.653],  # Report
        [0.486, 0.244, 0.349, 0.610],  # Silence
    ]
)

OPTION_LABELS = ["Report", "Silence"]
AGENT_LABELS = ["Analyst", "Investors", "Regulator", "Company"]


# ── Stratification Gate ─────────────────────────────────────────────────


def evaluate_stratum_gate(
    evidence_quality: float,
    tau_fraud: float,
) -> Tuple[str, Dict[str, float]]:
    """Evaluate the stratification gate for the whistleblower scenario.

    Parameters
    ----------
    evidence_quality : float
        Quality of the fraud evidence (0..1).
    tau_fraud : float
        Threshold above which reporting becomes obligatory.

    Returns
    -------
    stratum_name : str
        ``"S_obl"`` (obligatory) or ``"S_disc"`` (discretionary).
    stratum_constraints : dict
        Maps option label to its stratum constraint value.
        In S_obl, Silence receives ``-inf``.
    """
    if evidence_quality >= tau_fraud:
        return "S_obl", {"Report": 0.0, "Silence": NEG_INF}
    return "S_disc", {"Report": 0.0, "Silence": 0.0}


# ── Moral Residue ───────────────────────────────────────────────────────


def compute_moral_residue(
    O_chosen: np.ndarray,
    O_alt: np.ndarray,
    dim_labels: List[str],
) -> Dict[str, Any]:
    """Compute moral residue from choosing Report over Silence.

    The residue captures dimensions where the chosen option is
    *worse* than the foregone alternative -- the personal sacrifice
    Dana must bear even though the decision is structurally forced.

    Returns a dict with per-dimension deltas and a narrative summary.
    """
    delta = O_chosen - O_alt  # positive = chosen is better
    residue_dims: Dict[str, float] = {}
    for label, d in zip(dim_labels, delta):
        if d < 0.0:
            residue_dims[label] = float(d)

    narrative_items = [
        "Career disruption and professional retaliation risk",
        "Psychological burden of adversarial legal proceedings",
        f"Privacy breach (delta_privacy = {residue_dims.get('privacy', 0.0):+.2f})",
        "Potential social isolation within the firm",
    ]

    return {
        "chosen_option": "Report",
        "foregone_option": "Silence",
        "per_dimension_delta": {label: float(d) for label, d in zip(dim_labels, delta)},
        "sacrifice_dimensions": residue_dims,
        "narrative": narrative_items,
    }


# ── Penumbral Zone / Quantum Aspect Modeling ────────────────────────────


def penumbral_zone_analysis(
    M: np.ndarray,
    option_labels: List[str],
    agent_labels: List[str],
    stratum_constraints: Dict[str, float],
    epsilon: float = 0.10,
) -> Dict[str, Any]:
    """Penumbral-zone and quantum-aspect analysis.

    The *penumbral zone* is the region of moral space where the verdict
    is sensitive to small perturbations in obligation vectors or interest
    covectors.  A scenario lies in the penumbral zone when the score gap
    between the top two options is smaller than ``epsilon``.

    The *quantum aspect* models the scenario as a superposition of
    moral states until the stratum constraint "collapses" it to a
    definite verdict.  We report:

    - ``pre_collapse_amplitudes``: normalised scores treating both
      options as live (ignoring stratum constraints).
    - ``post_collapse_verdict``: the structurally determined outcome
      after the obligatory stratum fires.
    - ``in_penumbral_zone``: whether the unconstrained scores are
      within ``epsilon`` of each other (they are not in this case,
      but the machinery is exercised for completeness).
    - ``aspect_ratio``: ratio of the top score to the runner-up,
      measuring how "sharp" the collapse is.

    Parameters
    ----------
    M : ndarray, shape (n_options, n_agents)
        Evaluation tensor.
    option_labels : list of str
    agent_labels : list of str
    stratum_constraints : dict
        Maps option label to constraint value (0 or -inf).
    epsilon : float
        Penumbral-zone half-width.

    Returns
    -------
    dict with analysis fields.
    """
    # Unconstrained utilitarian scores (pre-collapse superposition)
    unconstrained_scores = M.sum(axis=1)
    total = unconstrained_scores.sum()
    amplitudes = unconstrained_scores / total if total > 0.0 else unconstrained_scores

    # Score gap (unconstrained)
    sorted_scores = np.sort(unconstrained_scores)[::-1]
    gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else np.inf
    in_penumbral = bool(gap < epsilon)

    # Aspect ratio
    aspect_ratio = (
        float(sorted_scores[0] / sorted_scores[1])
        if len(sorted_scores) > 1 and sorted_scores[1] > 0.0
        else float("inf")
    )

    # Apply stratum constraints to collapse the superposition
    constrained_scores = np.array(
        [
            unconstrained_scores[i] + stratum_constraints.get(opt, 0.0)
            for i, opt in enumerate(option_labels)
        ]
    )
    post_collapse_idx = int(np.argmax(constrained_scores))
    post_collapse_verdict = option_labels[post_collapse_idx]

    # Sensitivity analysis: how much would O_S have to improve
    # (in the unconstrained world) to flip the verdict?
    flip_margin = float(gap) if not in_penumbral else 0.0

    return {
        "unconstrained_scores": {
            opt: float(s) for opt, s in zip(option_labels, unconstrained_scores)
        },
        "pre_collapse_amplitudes": {
            opt: float(a) for opt, a in zip(option_labels, amplitudes)
        },
        "score_gap": float(gap),
        "in_penumbral_zone": in_penumbral,
        "epsilon": epsilon,
        "aspect_ratio": float(aspect_ratio),
        "post_collapse_verdict": post_collapse_verdict,
        "flip_margin_unconstrained": flip_margin,
        "stratum_constraint_applied": True,
        "note": (
            "Stratum constraint S_C(Silence) = -inf collapses the "
            "superposition to Report regardless of unconstrained scores."
        ),
    }


# ── Bond-Index Transforms ──────────────────────────────────────────────


def run_bond_index_transforms(
    obligations: Dict[str, np.ndarray],
    interests: Dict[str, np.ndarray],
    stratum_constraints: Dict[str, float],
    expert_weights: np.ndarray,
) -> Tuple[float, Dict[str, str]]:
    """Run invariance-preserving transforms and compute the Bond Index.

    Because the obligatory stratum constraint forces Report for *any*
    finite obligation vectors, every semantically valid transform
    preserves the verdict.  Bd = 0.0.

    Transforms tested:
      1. Scale all obligations by 0.5
      2. Permute agent order
      3. Shift all obligations by +0.05
      4. Replace interest covectors with uniform weights
    """
    transform_verdicts: Dict[str, str] = {}

    def _verdict(
        obls: Dict[str, np.ndarray],
        ints: Dict[str, np.ndarray],
        ew: np.ndarray,
    ) -> str:
        M, opt_labels, _ = compute_evaluation_tensor(obls, ints)
        scores_util = contraction_utilitarian(M)
        # Apply stratum constraints
        for i, opt in enumerate(opt_labels):
            scores_util[i] += stratum_constraints.get(opt, 0.0)
        return opt_labels[int(np.argmax(scores_util))]

    original_verdict = _verdict(obligations, interests, expert_weights)

    # Transform 1: scale obligations by 0.5
    scaled_obls = {k: v * 0.5 for k, v in obligations.items()}
    transform_verdicts["scale_obligations_0.5"] = _verdict(
        scaled_obls, interests, expert_weights
    )

    # Transform 2: permute agent ordering
    reversed_interests = dict(reversed(list(interests.items())))
    transform_verdicts["permute_agents"] = _verdict(
        obligations, reversed_interests, expert_weights[::-1]
    )

    # Transform 3: shift obligations by +0.05
    shifted_obls = {k: np.clip(v + 0.05, 0, 1) for k, v in obligations.items()}
    transform_verdicts["shift_obligations_+0.05"] = _verdict(
        shifted_obls, interests, expert_weights
    )

    # Transform 4: uniform interest covectors
    uniform = np.ones(N_DIM) / N_DIM
    uniform_ints = {agent: uniform for agent in interests}
    transform_verdicts["uniform_interests"] = _verdict(
        obligations, uniform_ints, expert_weights
    )

    Bd, n_preserving, n_changing = compute_bond_index(
        original_verdict, transform_verdicts
    )

    return Bd, transform_verdicts


# ── Pretty Printing ─────────────────────────────────────────────────────


def _header(title: str) -> None:
    bar = "=" * 72
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


def _subheader(title: str) -> None:
    print(f"\n--- {title} {'-' * max(0, 64 - len(title))}")


def _print_vector(name: str, vec: np.ndarray, labels: List[str]) -> None:
    parts = ", ".join(f"{lbl}={v:.2f}" for lbl, v in zip(labels, vec))
    print(f"  {name} = ({parts})")


def _print_matrix(
    M: np.ndarray,
    row_labels: List[str],
    col_labels: List[str],
) -> None:
    header = "".ljust(12) + "".join(c.rjust(12) for c in col_labels)
    print(header)
    for i, rl in enumerate(row_labels):
        vals = "".join(f"{M[i, j]:12.3f}" for j in range(M.shape[1]))
        print(f"  {rl:<10}{vals}")


# ── Main Case Study Runner ──────────────────────────────────────────────


def run_case_study_2() -> Dict[str, Any]:
    """Execute Case Study 2 end-to-end and return the audit artifact."""

    results: Dict[str, Any] = {}

    # ── 1. Scenario ─────────────────────────────────────────────────
    _header("Case Study 2: Whistleblower's Dilemma")
    print(
        "\nScenario: Dana, a financial analyst, discovers documented\n"
        "securities fraud at her firm.\n"
        "\nOptions:\n"
        "  R (Report)  -- File a formal whistleblower complaint\n"
        "  S (Silence) -- Do not report\n"
    )

    # ── 2. Stratification Gate ──────────────────────────────────────
    _subheader("Stratification Gate")
    stratum_name, stratum_constraints = evaluate_stratum_gate(
        EVIDENCE_QUALITY, TAU_FRAUD
    )
    print(f"  evidence_quality = {EVIDENCE_QUALITY:.2f}")
    print(f"  tau_fraud        = {TAU_FRAUD:.2f}")
    print(f"  stratum          = {stratum_name}")
    print(f"  S_C(Report)      = {stratum_constraints['Report']}")
    print(f"  S_C(Silence)     = {stratum_constraints['Silence']}")
    print(
        f"\n  Evidence quality {EVIDENCE_QUALITY:.2f} >> tau_fraud "
        f"{TAU_FRAUD:.2f}  -->  gate fires into S_obl."
    )
    results["stratum"] = stratum_name
    results["stratum_constraints"] = stratum_constraints

    # ── 3. Active Dimensions & Vectors ──────────────────────────────
    _subheader("Active Dimensions (7-D)")
    print(f"  Dimensions: {ACTIVE_DIM_LABELS}")
    print(f"  mu indices:  {ACTIVE_DIM_INDICES}")

    _subheader("Obligation Vectors (S_obl)")
    _print_vector("O_R", O_R, ACTIVE_DIM_LABELS)
    _print_vector("O_S", O_S, ACTIVE_DIM_LABELS)

    _subheader("Interest Covectors (4 agents)")
    _print_vector("I_analyst  ", I_ANALYST, ACTIVE_DIM_LABELS)
    _print_vector("I_investors", I_INVESTORS, ACTIVE_DIM_LABELS)
    _print_vector("I_regulator", I_REGULATOR, ACTIVE_DIM_LABELS)
    _print_vector("I_company  ", I_COMPANY, ACTIVE_DIM_LABELS)

    # ── 4. Evaluation Tensor ────────────────────────────────────────
    _subheader("Evaluation Tensor M_{ia}")

    obligations = {"Report": O_R, "Silence": O_S}
    interests = {
        "Analyst": I_ANALYST,
        "Investors": I_INVESTORS,
        "Regulator": I_REGULATOR,
        "Company": I_COMPANY,
    }

    M, opt_labels, agt_labels = compute_evaluation_tensor(obligations, interests)
    _print_matrix(M, opt_labels, agt_labels)

    # Validate against expected values
    if np.allclose(M, EXPECTED_M, atol=1e-3):
        print("\n  [ok] Evaluation tensor matches book Table D.2.")
    else:
        print("\n  [WARN] Evaluation tensor DIFFERS from expected values.")
        print(f"  Max absolute error: {np.max(np.abs(M - EXPECTED_M)):.6f}")
    results["evaluation_tensor"] = M.tolist()

    # ── 5. Contractions ─────────────────────────────────────────────
    _subheader("Contractions (with stratum constraint S_C)")

    # 5a. Utilitarian
    S_util = contraction_utilitarian(M)
    S_util_constrained = np.array(
        [
            S_util[i] + stratum_constraints.get(opt, 0.0)
            for i, opt in enumerate(opt_labels)
        ]
    )
    print("\n  Utilitarian: S_i = sum_a M_{ia}")
    for i, opt in enumerate(opt_labels):
        constraint_str = (
            f" + ({stratum_constraints[opt]})"
            if stratum_constraints[opt] != 0.0
            else ""
        )
        print(
            f"    S_{opt:<8} = {S_util[i]:.3f}{constraint_str}"
            f"  -->  {S_util_constrained[i]}"
        )
    util_verdict = opt_labels[int(np.argmax(S_util_constrained))]
    print(f"    Verdict: {util_verdict}")

    # 5b. Rawlsian
    S_rawls = contraction_rawlsian(M)
    S_rawls_constrained = np.array(
        [
            S_rawls[i] + stratum_constraints.get(opt, 0.0)
            for i, opt in enumerate(opt_labels)
        ]
    )
    print("\n  Rawlsian: S_i = min_a M_{ia}")
    for i, opt in enumerate(opt_labels):
        constraint_str = (
            f" + ({stratum_constraints[opt]})"
            if stratum_constraints[opt] != 0.0
            else ""
        )
        print(
            f"    S_{opt:<8} = {S_rawls[i]:.3f}{constraint_str}"
            f"  -->  {S_rawls_constrained[i]}"
        )
    rawls_verdict = opt_labels[int(np.argmax(S_rawls_constrained))]
    print(f"    Verdict: {rawls_verdict}")

    # 5c. Expert-weighted
    S_expert = contraction_expert_weighted(M, EXPERT_WEIGHTS)
    S_expert_constrained = np.array(
        [
            S_expert[i] + stratum_constraints.get(opt, 0.0)
            for i, opt in enumerate(opt_labels)
        ]
    )
    print(
        "\n  Expert-weighted: w = (reg=0.35, analyst=0.20, "
        "investors=0.30, company=0.15)"
    )
    for i, opt in enumerate(opt_labels):
        constraint_str = (
            f" + ({stratum_constraints[opt]})"
            if stratum_constraints[opt] != 0.0
            else ""
        )
        print(
            f"    S_{opt:<8} = {S_expert[i]:.3f}{constraint_str}"
            f"  -->  {S_expert_constrained[i]}"
        )
    expert_verdict = opt_labels[int(np.argmax(S_expert_constrained))]
    print(f"    Verdict: {expert_verdict}")

    results["contractions"] = {
        "utilitarian": {
            "scores": S_util.tolist(),
            "constrained": S_util_constrained.tolist(),
            "verdict": util_verdict,
        },
        "rawlsian": {
            "scores": S_rawls.tolist(),
            "constrained": S_rawls_constrained.tolist(),
            "verdict": rawls_verdict,
        },
        "expert_weighted": {
            "scores": S_expert.tolist(),
            "constrained": S_expert_constrained.tolist(),
            "verdict": expert_verdict,
        },
    }

    # ── 6. Moral Residue ────────────────────────────────────────────
    _subheader("Moral Residue")
    residue = compute_moral_residue(O_R, O_S, ACTIVE_DIM_LABELS)
    print(f"\n  Chosen: {residue['chosen_option']}")
    print(f"  Foregone: {residue['foregone_option']}")
    print("\n  Per-dimension delta (Report - Silence):")
    for dim, delta_val in residue["per_dimension_delta"].items():
        marker = "  <-- sacrifice" if delta_val < 0.0 else ""
        print(f"    {dim:<12} {delta_val:+.2f}{marker}")
    print("\n  Sacrifice dimensions (negative delta):")
    for dim, val in residue["sacrifice_dimensions"].items():
        print(f"    {dim}: {val:+.2f}")
    print("\n  Narrative:")
    for item in residue["narrative"]:
        print(f"    - {item}")
    results["moral_residue"] = residue

    # ── 7. Penumbral Zone / Quantum Aspect ──────────────────────────
    _subheader("Penumbral Zone / Quantum Aspect Modeling")
    pz = penumbral_zone_analysis(M, opt_labels, agt_labels, stratum_constraints)
    print("\n  Unconstrained utilitarian scores:")
    for opt, s in pz["unconstrained_scores"].items():
        print(f"    {opt}: {s:.3f}")
    print("\n  Pre-collapse amplitudes (normalised):")
    for opt, a in pz["pre_collapse_amplitudes"].items():
        print(f"    |{opt}> : {a:.4f}")
    print(f"\n  Score gap (unconstrained): {pz['score_gap']:.3f}")
    print(f"  In penumbral zone (eps={pz['epsilon']}): {pz['in_penumbral_zone']}")
    print(f"  Aspect ratio: {pz['aspect_ratio']:.4f}")
    print(f"  Flip margin (unconstrained): {pz['flip_margin_unconstrained']:.3f}")
    print(f"\n  Post-collapse verdict: {pz['post_collapse_verdict']}")
    print(f"  Note: {pz['note']}")
    results["penumbral_zone"] = pz

    # ── 8. Bond Index ───────────────────────────────────────────────
    _subheader("Bond Index")
    Bd, transform_verdicts = run_bond_index_transforms(
        obligations, interests, stratum_constraints, EXPERT_WEIGHTS
    )
    print("\n  Transform verdicts:")
    for t_name, t_verdict in transform_verdicts.items():
        print(f"    {t_name:<30} --> {t_verdict}")
    print(f"\n  Bond Index Bd = {Bd:.1f}")
    print(
        "  Interpretation: Bd = 0.0 means fully invariant -- the stratum\n"
        "  constraint makes the verdict structurally robust against all\n"
        "  semantically valid transforms."
    )
    results["bond_index"] = Bd
    results["bond_transforms"] = transform_verdicts

    # ── 9. Final Decision ───────────────────────────────────────────
    _subheader("Final Decision")
    final_verdict = "Report"
    print(f"\n  Decision: {final_verdict} (Option R)")
    print(
        "  Rationale: Structurally determined by stratum constraint.\n"
        f"  Evidence quality ({EVIDENCE_QUALITY:.2f}) exceeds fraud "
        f"threshold ({TAU_FRAUD:.2f}),\n"
        "  placing the scenario in S_obl where S_C(Silence) = -inf.\n"
        "  All three contractions agree: Report."
    )
    results["final_verdict"] = final_verdict

    # ── 10. Audit Artifact ──────────────────────────────────────────
    _subheader("Audit Artifact")
    artifact = generate_audit_artifact(
        case_id=CASE_ID,
        scenario=(
            "Dana discovers documented securities fraud. "
            "Evidence quality = 0.92 >> tau_fraud = 0.70."
        ),
        active_dimensions=ACTIVE_DIM_LABELS,
        stratum=stratum_name,
        evaluation_tensor=M.tolist(),
        contractions=results["contractions"],
        moral_residue=residue,
        penumbral_zone=pz,
        bond_index=Bd,
        final_verdict=final_verdict,
    )
    print(f"\n  {json.dumps(artifact, indent=2, default=str)}")
    results["audit_artifact"] = artifact

    return results


# ── Entry Point ─────────────────────────────────────────────────────────


def main() -> None:
    """Run Case Study 2 and print all pipeline stages."""
    run_case_study_2()


if __name__ == "__main__":
    main()
