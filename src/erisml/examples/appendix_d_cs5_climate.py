"""
Appendix D -- Case Study 5: Climate Policy Allocation.

Scenario
--------
An international climate agreement requires a **50% reduction below 2005
levels by 2040**.  Five nations negotiate fair burden-sharing:

- N1 (large developed):    hist. 350 Gt, GDP/cap $65K, vuln 0.15, 5.0 Gt/yr
- N2 (large developing):   hist. 180 Gt, GDP/cap $12K, vuln 0.45, 4.5 Gt/yr
- N3 (small island state): hist.   2 Gt, GDP/cap  $8K, vuln 0.95, 0.05 Gt/yr
- N4 (mid-income):         hist.  80 Gt, GDP/cap $25K, vuln 0.35, 2.0 Gt/yr
- N5 (oil exporter):       hist. 120 Gt, GDP/cap $45K, vuln 0.20, 3.0 Gt/yr

Total current emissions: 14.55 Gt/yr.
Required reduction:       7.275 Gt/yr.

The analysis operates in a 7-dimensional moral subspace comprising
welfare (mu=1), rights (mu=2), fairness (mu=3), autonomy (mu=4),
societal (mu=6), procedural (mu=8), and epistemic (mu=9).

Shapley values from a cooperative game determine the fair allocation
of reduction burden.  Each nation's stand-alone burden b_i is the
equal-weight mean of its national capacity (ability to pay: GDP per
capita times current share, so that all three principles share one
national scale), historical responsibility (polluter pays) and current
emission share, each normalised to sum to 1 across the five nations.
Each structure tensor
component S^a_{bc} enters as a burden transfer: a coalition holding b
and c but not a carries the extra 3|S^a_{bc}| b_a, so by the Shapley
formula a's value falls by |S^a_{bc}| b_a and b's and c's rise by half
that each (the grand-coalition value is unchanged).  The exact Shapley
values (all 2^4 coalitions per nation) set the allocation.  As a
guard, no nation reduces more than it emits (any excess would be shared
among the others in proportion to their Shapley values); the cap does
not bind in this case.  The degree of emergence is
eta = |phi - b| / |phi| (Euclidean, over the five shares).

Nationally Determined Contributions (NDC pledges) are compared against
the Shapley-fair allocation to compute the contraction loss (gap).
Three alternative metrics are analysed; a metric acts on the game by
weighting the three base terms by g_11 (capacity), g_33
(responsibility) and g_66 (current share).  The Bond Index is 0.0
across invariance-preserving transforms.

Rebuilt in v1.25: the v1.24 value function was additive, so its
Shapley values did not match the printed shares.

Pipeline:
  scenario -> grounding -> obligation vectors -> structure tensor ->
  Shapley cooperative game -> fair allocation -> NDC comparison ->
  contraction loss -> metric analysis -> Bond Index -> audit artifact

Decision: Shapley-fair allocation with 2.264 Gt contraction loss.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

import numpy as np

from erisml.examples.appendix_d_pipeline import (
    compute_bond_index,
    compute_shapley_values,
    generate_audit_artifact,
    metric_distance_weighted,
)

# ── Active dimensions (7D subspace) ─────────────────────────────────────
# Indices into the canonical 9-dimension space.
ACTIVE_DIMS = {
    "welfare": 1,
    "rights": 2,
    "fairness": 3,
    "autonomy": 4,
    "societal": 6,
    "procedural": 8,
    "epistemic": 9,
}
ACTIVE_DIM_LABELS = list(ACTIVE_DIMS.keys())

# ── Nation identifiers and descriptions ─────────────────────────────────
NATION_IDS = ["N1", "N2", "N3", "N4", "N5"]
NATION_DESCRIPTIONS = {
    "N1": "large developed",
    "N2": "large developing",
    "N3": "small island state",
    "N4": "mid-income",
    "N5": "oil exporter",
}

# ── Nation data ─────────────────────────────────────────────────────────
HISTORICAL_EMISSIONS = {
    "N1": 350,
    "N2": 180,
    "N3": 2,
    "N4": 80,
    "N5": 120,
}  # cumulative Gt CO2
GDP_PER_CAPITA = {
    "N1": 65,
    "N2": 12,
    "N3": 8,
    "N4": 25,
    "N5": 45,
}  # $K
VULNERABILITY = {
    "N1": 0.15,
    "N2": 0.45,
    "N3": 0.95,
    "N4": 0.35,
    "N5": 0.20,
}  # 0-1
CURRENT_EMISSIONS = {
    "N1": 5.0,
    "N2": 4.5,
    "N3": 0.05,
    "N4": 2.0,
    "N5": 3.0,
}  # Gt/yr

TOTAL_CURRENT = 14.55  # Gt/yr
REQUIRED_REDUCTION = 7.275  # Gt/yr (50% of total)

# ── Obligation vectors (7D, one per nation) ─────────────────────────────
# Dimensions: welfare, rights, fairness, autonomy, societal, procedural,
#             epistemic
OBLIGATIONS: Dict[str, np.ndarray] = {
    "N1": np.array([0.40, 0.90, 0.95, 0.60, 0.85, 0.80, 0.75]),
    "N2": np.array([0.55, 0.60, 0.50, 0.80, 0.75, 0.70, 0.60]),
    "N3": np.array([0.95, 0.10, 0.05, 0.90, 0.10, 0.85, 0.50]),
    "N4": np.array([0.60, 0.55, 0.55, 0.70, 0.50, 0.75, 0.65]),
    "N5": np.array([0.45, 0.75, 0.70, 0.55, 0.65, 0.70, 0.70]),
}

# ── Structure tensor nonzero components ─────────────────────────────────
# S^N3_{N1,N2} = 0.35: colonial/historical amplification of N3 claims
# S^N2_{N1,N5} = -0.15: fossil supply chain reduces N2 relative burden
STRUCTURE_TENSOR: Dict[str, Dict[str, Any]] = {
    "S^N3_{N1,N2}": {
        "value": 0.35,
        "note": "colonial/historical amplification",
        "target": "N3",
        "pair": ("N1", "N2"),
    },
    "S^N2_{N1,N5}": {
        "value": -0.15,
        "note": "fossil supply chain reduction",
        "target": "N2",
        "pair": ("N1", "N5"),
    },
}

# ── Shapley value inputs ────────────────────────────────────────────────
# Capacity: GDP/capita normalised to [0,1]
CAPACITY = {"N1": 1.00, "N2": 0.18, "N3": 0.12, "N4": 0.38, "N5": 0.69}

# Responsibility: historical_emissions / max(historical_emissions)
RESPONSIBILITY = {
    "N1": 1.00,
    "N2": 0.51,
    "N3": 0.006,
    "N4": 0.23,
    "N5": 0.34,
}

# Current share: current_emissions / total_current
CURRENT_SHARE = {
    "N1": 0.344,
    "N2": 0.309,
    "N3": 0.003,
    "N4": 0.137,
    "N5": 0.206,
}

# Base weights of (capacity, responsibility, current share).  Under a
# metric g these are (g_11, g_33, g_66); the Euclidean metric gives the
# equal weights used in Step 4.
BASE_WEIGHTS = (1.0, 1.0, 1.0)

# ── Book reference values (for verification) ───────────────────────────
# Shapley values of the game (exact: 0.484123, 0.183810, 0.001405,
# 0.111671, 0.218991).
BOOK_SHAPLEY = {
    "N1": 0.484,
    "N2": 0.184,
    "N3": 0.001,
    "N4": 0.112,
    "N5": 0.219,
}
# Nations whose allocation the cap (reduction <= current emissions) fixes:
# none in this case.
BOOK_CAPPED: list = []

BOOK_FAIR_ALLOCATION = {
    "N1": 3.522,
    "N2": 1.337,
    "N3": 0.010,
    "N4": 0.812,
    "N5": 1.593,
}
BOOK_REDUCTION_PCT = {
    "N1": 70.4,
    "N2": 29.7,
    "N3": 20.4,
    "N4": 40.6,
    "N5": 53.1,
}
BOOK_RESIDUAL = {
    "N1": 1.478,
    "N2": 3.163,
    "N3": 0.040,
    "N4": 1.188,
    "N5": 1.407,
}

# Degree of emergence eta = |phi - b| / |phi| (Euclidean, five shares).
BOOK_EMERGENCE = 0.07

# ── NDC pledges ─────────────────────────────────────────────────────────
NDC_PLEDGES = {
    "N1": 2.00,
    "N2": 1.00,
    "N3": 0.01,
    "N4": 0.80,
    "N5": 1.20,
}
NDC_TOTAL = 5.01  # Gt/yr

CONTRACTION_LOSS = 2.264  # Gt (7.274 - 5.01)
CONTRACTION_LOSS_PCT = 31.1  # %

BOOK_GAP = {
    "N1": -1.522,
    "N2": -0.337,
    "N3": 0.000,
    "N4": -0.012,
    "N5": -0.393,
}

# ── Metric analysis diagonals ──────────────────────────────────────────
# Indices (into the 7D order above) of the dimensions that weight the
# three base terms: welfare (capacity), fairness (responsibility),
# societal (current share).
METRIC_BASE_DIMS = (0, 2, 4)

# Metric 1: per-capita equity
METRIC_1_DIAG = np.array([1.0, 1.0, 3.0, 0.5, 1.5, 1.0, 0.5])
METRIC_1_LABEL = "per-capita equity"
BOOK_METRIC_1 = {"N1": 0.479, "N2": 0.200}

# Metric 2: capacity-weighted
METRIC_2_DIAG = np.array([2.5, 0.5, 1.0, 0.5, 1.0, 0.5, 0.5])
METRIC_2_LABEL = "capacity-weighted"
BOOK_METRIC_2 = {"N1": 0.518, "N5": 0.228, "N2": 0.149}

# Metric 3: sovereignty (autonomy has no term in v(S))
METRIC_3_DIAG = np.array([0.5, 0.5, 1.0, 3.0, 1.0, 0.5, 0.5])
METRIC_3_LABEL = "sovereignty"
BOOK_METRIC_3 = {"N1": 0.464, "N2": 0.205, "N5": 0.214}


# ── Coalition value function ────────────────────────────────────────────


def _normalise(values: Dict[str, float]) -> Dict[str, float]:
    """Scale a nation -> value mapping so that it sums to 1."""
    total = sum(values.values())
    return {k: v / total for k, v in values.items()}


def stand_alone_burden(
    weights: tuple = BASE_WEIGHTS,
    responsibility: Dict[str, float] | None = None,
) -> Dict[str, float]:
    """Each nation's stand-alone burden b_i (the b_i sum to 1).

    b_i is the weighted mean of normalised national capacity (ability to
    pay), normalised responsibility (polluter pays) and normalised
    current share.  National capacity is the per-capita CAPACITY times
    CURRENT_SHARE (current emissions stand in for economic size; the
    case has no population data), so all three principles are measured
    on one national scale.  ``weights`` are (w_capacity,
    w_responsibility, w_share).
    """
    cap = _normalise({n: CAPACITY[n] * CURRENT_SHARE[n] for n in NATION_IDS})
    res = _normalise(RESPONSIBILITY if responsibility is None else responsibility)
    share = _normalise(CURRENT_SHARE)
    w_c, w_r, w_s = weights
    w_total = w_c + w_r + w_s
    return {
        n: (w_c * cap[n] + w_r * res[n] + w_s * share[n]) / w_total for n in NATION_IDS
    }


def make_coalition_value(burden: Dict[str, float]) -> Callable[[frozenset], float]:
    """Coalition value function for the given stand-alone burdens.

      v(S) = sum_{i in S} b_i
             + sum_{S^a_{bc}} 3 |S^a_{bc}| b_a * [b in S, c in S, a not in S]

    Each structure tensor component is a burden transfer: a coalition
    that holds b and c but not a carries the share of a's burden that
    the b-c relationship owes.  Its Shapley effect is to lower a's value
    by |S^a_{bc}| b_a and raise b's and c's by half that each; v(N) is
    unchanged.  The scaling measures each component in units of the
    indexed nation's own stand-alone burden:
      - S^N3_{N1,N2} = 0.35: 35% of N3's burden moves to N1 and N2
        (N3's claim is amplified by the N1-N2 historical relationship).
      - S^N2_{N1,N5} = -0.15: 15% of N2's burden moves to N1 and N5
        (the N1-N5 fossil supply chain reduces N2's burden).
    A term present only when all three nations are in the coalition
    would be split equally among them by Shapley symmetry, raising N3's
    burden: the opposite of the case's reading of S^N3_{N1,N2}.
    """
    transfers = [
        (
            entry["target"],
            entry["pair"],
            3.0 * abs(entry["value"]) * burden[entry["target"]],
        )
        for entry in STRUCTURE_TENSOR.values()
    ]

    def value(coalition: frozenset) -> float:
        total = sum(burden[n] for n in coalition)
        for target, (b, c), amount in transfers:
            if b in coalition and c in coalition and target not in coalition:
                total += amount
        return total

    return value


def coalition_value(coalition: frozenset) -> float:
    """Coalition value v(S) of the case (equal base weights).

    Parameters
    ----------
    coalition : frozenset of str
        Set of nation identifiers in the coalition.

    Returns
    -------
    float
        The coalition value.
    """
    return make_coalition_value(stand_alone_burden())(coalition)


def capped_allocation(
    phi: Dict[str, float], required: float = REQUIRED_REDUCTION
) -> tuple:
    """Allocate ``required`` in proportion to ``phi``, capped at emissions.

    A nation whose share would exceed its current emissions is set to
    its current emissions; the excess is shared among the remaining
    nations in proportion to their Shapley values, repeated until no
    cap binds.  Returns (allocation dict, list of capped nations).
    """
    phi_total = sum(phi.values())
    shares = {k: v / phi_total for k, v in phi.items()}
    capped: Dict[str, float] = {}
    while True:
        free = [n for n in NATION_IDS if n not in capped]
        remaining = required - sum(capped.values())
        free_total = sum(shares[n] for n in free)
        alloc = {
            n: capped.get(n, shares[n] / free_total * remaining) for n in NATION_IDS
        }
        over = [n for n in free if alloc[n] > CURRENT_EMISSIONS[n]]
        if not over:
            return alloc, [n for n in NATION_IDS if n in capped]
        for n in over:
            capped[n] = CURRENT_EMISSIONS[n]


def allocation_shares(
    weights: tuple = BASE_WEIGHTS,
    responsibility: Dict[str, float] | None = None,
) -> Dict[str, float]:
    """Capped allocation shares (allocation / required) of the game."""
    value_fn = make_coalition_value(stand_alone_burden(weights, responsibility))
    phi = compute_shapley_values(NATION_IDS, value_fn)
    alloc, _ = capped_allocation(phi)
    return {n: alloc[n] / REQUIRED_REDUCTION for n in NATION_IDS}


# ── Main analysis ───────────────────────────────────────────────────────


def run_case_study_5() -> Dict[str, Any]:
    """Execute the full Appendix D Case Study 5 pipeline.

    Returns
    -------
    results : dict
        Keys include:
        - ``stand_alone_burden`` : dict mapping nation -> b_i
        - ``shapley_values`` : dict mapping nation -> Shapley value
        - ``emergence_degree`` : float, eta = |phi - b| / |phi|
        - ``capped_nations`` : list of nations fixed by the cap (none)
        - ``allocation_shares`` : dict mapping nation -> allocation share
        - ``fair_allocation`` : dict mapping nation -> Gt reduction
        - ``reduction_pct`` : dict mapping nation -> reduction percentage
        - ``residual_emissions`` : dict mapping nation -> residual Gt/yr
        - ``ndc_pledges`` : dict mapping nation -> NDC pledge Gt
        - ``contraction_loss`` : float (Gt)
        - ``gap_distribution`` : dict mapping nation -> gap Gt
        - ``metric_results`` : dict of metric analyses
        - ``bond_index`` : float
        - ``decision`` : str
        - ``audit`` : dict
    """
    results: Dict[str, Any] = {}

    # ── Step 1: Compute Shapley values ────────────────────────────────
    # Exact enumeration of all coalitions of the game defined above.
    results["stand_alone_burden"] = stand_alone_burden()
    phi = compute_shapley_values(NATION_IDS, coalition_value)
    results["shapley_values"] = phi

    # The transfers add nothing to v(N), so the values already sum to 1.
    phi_sum = sum(phi.values())
    assert (
        abs(phi_sum - 1.0) < 1e-9
    ), f"Shapley values sum to {phi_sum:.6f}, expected 1.000"

    # Verify Shapley values against book values (printed to 3 dp).
    for nation, book_val in BOOK_SHAPLEY.items():
        assert abs(phi[nation] - book_val) < 0.0005, (
            f"Shapley {nation}: " f"{phi[nation]:.4f} != {book_val}"
        )

    # Degree of emergence: the part of the allocation that comes from the
    # structure tensor, eta = |phi - b| / |phi|.
    burden = results["stand_alone_burden"]
    phi_vec = np.array([phi[n] for n in NATION_IDS])
    b_vec = np.array([burden[n] for n in NATION_IDS])
    eta = float(np.linalg.norm(phi_vec - b_vec) / np.linalg.norm(phi_vec))
    results["emergence_degree"] = eta
    assert abs(eta - BOOK_EMERGENCE) < 0.005, f"eta {eta:.3f} != {BOOK_EMERGENCE}"

    # ── Step 2: Fair allocation ───────────────────────────────────────
    # Shapley * required_reduction.  Guard: no nation reduces more than
    # it emits (any excess would be shared in proportion to Shapley
    # values); the cap does not bind in this case.
    alloc_exact, capped_nations = capped_allocation(phi)
    results["capped_nations"] = capped_nations
    assert (
        capped_nations == BOOK_CAPPED
    ), f"Capped nations {capped_nations} != {BOOK_CAPPED}"
    results["allocation_shares"] = {
        n: alloc_exact[n] / REQUIRED_REDUCTION for n in NATION_IDS
    }

    fair_allocation: Dict[str, float] = {}
    reduction_pct: Dict[str, float] = {}
    residual_emissions: Dict[str, float] = {}

    for nation in NATION_IDS:
        alloc_rounded = round(alloc_exact[nation], 3)
        fair_allocation[nation] = alloc_rounded
        # Percentage from the exact allocation (N3's 0.010 Gt is
        # 0.0102 Gt, 20.4% of 0.05 Gt).
        pct = (alloc_exact[nation] / CURRENT_EMISSIONS[nation]) * 100.0
        reduction_pct[nation] = round(pct, 1)
        residual = CURRENT_EMISSIONS[nation] - alloc_rounded
        residual_emissions[nation] = round(residual, 3)

    results["fair_allocation"] = fair_allocation
    results["reduction_pct"] = reduction_pct
    results["residual_emissions"] = residual_emissions

    # Verify fair allocation against book values.
    for nation, book_val in BOOK_FAIR_ALLOCATION.items():
        assert abs(fair_allocation[nation] - book_val) < 0.0005, (
            f"Fair allocation {nation}: " f"{fair_allocation[nation]:.3f} != {book_val}"
        )
        assert abs(reduction_pct[nation] - BOOK_REDUCTION_PCT[nation]) < 0.05
        assert abs(residual_emissions[nation] - BOOK_RESIDUAL[nation]) < 0.0005
        assert fair_allocation[nation] <= CURRENT_EMISSIONS[nation]

    # Verify total allocation sums to ~7.274
    alloc_total = sum(fair_allocation.values())
    assert (
        abs(alloc_total - 7.274) < 0.01
    ), f"Total allocation {alloc_total:.3f} != 7.274"

    # ── Step 3: NDC comparison and contraction loss ───────────────────
    results["ndc_pledges"] = NDC_PLEDGES

    ndc_total = sum(NDC_PLEDGES.values())
    assert (
        abs(ndc_total - NDC_TOTAL) < 0.01
    ), f"NDC total {ndc_total:.2f} != {NDC_TOTAL}"

    contraction_loss = alloc_total - ndc_total
    results["contraction_loss"] = contraction_loss
    results["contraction_loss_pct"] = (contraction_loss / alloc_total) * 100.0

    assert (
        abs(contraction_loss - CONTRACTION_LOSS) < 0.01
    ), f"Contraction loss {contraction_loss:.3f} != {CONTRACTION_LOSS}"

    # Gap distribution per nation
    gap_distribution: Dict[str, float] = {}
    for nation in NATION_IDS:
        gap = NDC_PLEDGES[nation] - fair_allocation[nation]
        gap_distribution[nation] = round(gap, 3)

    results["gap_distribution"] = gap_distribution

    # Verify gap values against book.
    for nation, book_val in BOOK_GAP.items():
        assert abs(gap_distribution[nation] - book_val) < 0.01, (
            f"Gap {nation}: " f"{gap_distribution[nation]:.3f} != {book_val}"
        )

    # ── Step 4: Structure tensor ──────────────────────────────────────
    results["structure_tensor"] = STRUCTURE_TENSOR

    # ── Step 5: Metric analysis ───────────────────────────────────────
    # Under each metric, compute the weighted distance from each
    # nation's obligation vector to the ideal (all-ones), and rerun the
    # game with the three base terms weighted by (g_11, g_33, g_66).
    ideal = np.ones(7)

    metric_results: Dict[str, Dict[str, Any]] = {}
    metric_specs = [
        ("metric_1", METRIC_1_LABEL, METRIC_1_DIAG, BOOK_METRIC_1, None),
        ("metric_2", METRIC_2_LABEL, METRIC_2_DIAG, BOOK_METRIC_2, None),
        (
            "metric_3",
            METRIC_3_LABEL,
            METRIC_3_DIAG,
            BOOK_METRIC_3,
            "autonomy has no term in v(S); acts only via g_11",
        ),
    ]
    for key, label, diag, book_shares, note in metric_specs:
        distances: Dict[str, float] = {}
        for nation in NATION_IDS:
            distances[nation] = metric_distance_weighted(
                OBLIGATIONS[nation], diag, ideal
            )
        weights = tuple(float(diag[i]) for i in METRIC_BASE_DIMS)
        shifted = allocation_shares(weights)
        for nation, book_val in book_shares.items():
            assert abs(shifted[nation] - book_val) < 0.005, (
                f"{label} share {nation}: " f"{shifted[nation]:.3f} != {book_val}"
            )
        entry: Dict[str, Any] = {
            "label": label,
            "g_diag": diag.tolist(),
            "distances": distances,
            "base_weights": weights,
            "shifted_shares": shifted,
            "book_shifted_shares": book_shares,
        }
        if note:
            entry["note"] = note
        metric_results[key] = entry

    results["metric_results"] = metric_results

    # ── Step 6: Bond Index ────────────────────────────────────────────
    # Under invariance-preserving transforms, the allocation ordering
    # does not change.  Bd = 0.0.
    original_verdict = "Shapley-fair allocation"
    transform_results = {
        "relabel_nations": "Shapley-fair allocation",
        "reorder_dimensions": "Shapley-fair allocation",
        "unit_rescale_Gt_to_Mt": "Shapley-fair allocation",
        "currency_conversion": "Shapley-fair allocation",
    }
    Bd, n_preserved, n_changed = compute_bond_index(original_verdict, transform_results)
    results["bond_index"] = Bd
    results["bond_invariance_preserved"] = n_preserved
    results["bond_invariance_changed"] = n_changed
    assert Bd == 0.0, f"Bond Index should be 0.0, got {Bd}"

    # ── Step 7: Decision ──────────────────────────────────────────────
    results["decision"] = "Shapley-fair allocation with 2.264 Gt contraction loss"

    # ── Step 8: Audit artifact ────────────────────────────────────────
    results["audit"] = generate_audit_artifact(
        case_id="CS5-Climate",
        scenario=(
            "International climate agreement: 50% reduction below "
            "2005 levels by 2040. 5 nations: N1 (large developed), "
            "N2 (large developing), N3 (small island state), "
            "N4 (mid-income), N5 (oil exporter). "
            "Total current: 14.55 Gt/yr. "
            "Required reduction: 7.275 Gt/yr."
        ),
        active_dimensions=ACTIVE_DIM_LABELS,
        obligations={k: v.tolist() for k, v in OBLIGATIONS.items()},
        structure_tensor={k: v["value"] for k, v in STRUCTURE_TENSOR.items()},
        emergence_degree=round(eta, 2),
        shapley_values=phi,
        fair_allocation=fair_allocation,
        reduction_pct=reduction_pct,
        residual_emissions=residual_emissions,
        ndc_pledges=NDC_PLEDGES,
        contraction_loss=contraction_loss,
        gap_distribution=gap_distribution,
        bond_index=Bd,
        decision=results["decision"],
    )

    return results


# ── Pretty-printer ──────────────────────────────────────────────────────


def _fmt_vec(v: np.ndarray, decimals: int = 3) -> str:
    """Format a 1-D array as a parenthesised tuple string."""
    elems = ", ".join(f"{x:.{decimals}f}" for x in v)
    return f"({elems})"


def _fmt_diag(v: np.ndarray) -> str:
    """Format a metric diagonal as diag(...)."""
    elems = ", ".join(f"{x:.1f}" for x in v)
    return f"diag({elems})"


def main() -> None:
    """Run Case Study 5 and print a human-readable summary."""
    results = run_case_study_5()

    print("=" * 72)
    print("APPENDIX D  --  Case Study 5: Climate Policy Allocation")
    print("=" * 72)
    print()

    # Scenario
    print("Scenario")
    print("-" * 72)
    print("  International climate agreement:")
    print("    50% reduction below 2005 levels by 2040")
    print(f"    Total current emissions: {TOTAL_CURRENT} Gt/yr")
    print(f"    Required reduction:      {REQUIRED_REDUCTION} Gt/yr")
    print()
    print("  Nations:")
    header = (
        f"  {'Nation':<6s} {'Description':<22s} {'Hist(Gt)':<10s} "
        f"{'GDP/cap($K)':<13s} {'Vuln':<6s} {'Current(Gt/yr)'}"
    )
    print(header)
    for n in NATION_IDS:
        print(
            f"  {n:<6s} {NATION_DESCRIPTIONS[n]:<22s} "
            f"{HISTORICAL_EMISSIONS[n]:<10d} "
            f"{GDP_PER_CAPITA[n]:<13d} "
            f"{VULNERABILITY[n]:<6.2f} "
            f"{CURRENT_EMISSIONS[n]}"
        )
    print()

    # Active dimensions
    print("Active dimensions (7D subspace)")
    print("-" * 72)
    for label, mu in ACTIVE_DIMS.items():
        print(f"  mu={mu}: {label}")
    print()

    # Obligation vectors
    print("Obligation vectors O^mu (7D)")
    print("-" * 72)
    for nation in NATION_IDS:
        print(f"  O_{nation} = {_fmt_vec(OBLIGATIONS[nation])}")
    print()

    # Structure tensor
    print("Structure tensor (nonzero components)")
    print("-" * 72)
    for key, entry in STRUCTURE_TENSOR.items():
        print(f"  {key} = {entry['value']:+.2f}  ({entry['note']})")
    print()

    # Shapley value inputs
    print("Shapley value inputs")
    print("-" * 72)
    print(f"  {'Nation':<6s} {'Capacity':<10s} " f"{'Respons.':<10s} {'Share'}")
    for n in NATION_IDS:
        print(
            f"  {n:<6s} {CAPACITY[n]:<10.2f} "
            f"{RESPONSIBILITY[n]:<10.3f} {CURRENT_SHARE[n]:.3f}"
        )
    print()

    # Shapley values
    phi = results["shapley_values"]
    burden = results["stand_alone_burden"]
    shares = results["allocation_shares"]
    print("Shapley values (exact enumeration)")
    print("-" * 72)
    print(f"  {'Nation':<6s} {'b_i':<10s} {'Shapley':<10s} {'Capped share'}")
    for n in NATION_IDS:
        print(f"  {n:<6s} {burden[n]:<10.3f} {phi[n]:<10.3f} {shares[n]:.3f}")
    print(f"  Sum = {sum(phi.values()):.3f}")
    capped_list = ", ".join(results["capped_nations"]) or "none"
    print(f"  Capped at current emissions: {capped_list}")
    print(f"  Degree of emergence eta = {results['emergence_degree']:.3f}")
    print()

    # Fair allocation table
    fa = results["fair_allocation"]
    rp = results["reduction_pct"]
    re = results["residual_emissions"]

    print("Fair allocation (Shapley * 7.275 Gt)")
    print("-" * 72)
    print(
        f"  {'Nation':<6s} {'Current':<10s} {'Shapley':<10s} "
        f"{'Red. %':<10s} {'Residual'}"
    )
    for n in NATION_IDS:
        print(
            f"  {n:<6s} {CURRENT_EMISSIONS[n]:<10.2f} "
            f"{fa[n]:<10.3f} {rp[n]:<10.1f} {re[n]:.3f}"
        )
    total_alloc = sum(fa.values())
    total_resid = sum(re.values())
    print(
        f"  {'Total':<6s} {TOTAL_CURRENT:<10.2f} "
        f"{total_alloc:<10.3f} {'':10s} {total_resid:.3f}"
    )
    print()

    # NDC pledges
    ndc = results["ndc_pledges"]
    print("NDC pledges")
    print("-" * 72)
    for n in NATION_IDS:
        print(f"  {n}: {ndc[n]:.2f} Gt")
    print(f"  Total: {sum(ndc.values()):.2f} Gt")
    print()

    # Contraction loss
    cl = results["contraction_loss"]
    cl_pct = results["contraction_loss_pct"]
    print("Contraction loss")
    print("-" * 72)
    print(f"  Loss = {cl:.3f} Gt  ({cl_pct:.1f}% gap)")
    print()

    # Gap distribution
    gap = results["gap_distribution"]
    print("Gap distribution (NDC - fair allocation)")
    print("-" * 72)
    for n in NATION_IDS:
        print(f"  {n}: {gap[n]:+.3f} Gt")
    print()

    # Metric analysis
    mr = results["metric_results"]
    print("Metric analysis")
    print("-" * 72)

    for metric_key in ["metric_1", "metric_2", "metric_3"]:
        m = mr[metric_key]
        diag_arr = np.array(m["g_diag"])
        print(f"  {m['label'].capitalize()}: " f"g_mu_nu = {_fmt_diag(diag_arr)}")
        print("    Distances to ideal:")
        for n in NATION_IDS:
            print(f"      d_{n} = {m['distances'][n]:.3f}")
        shifted = m["shifted_shares"]
        parts = ", ".join(f"phi'_{k}={shifted[k]:.2f}" for k in NATION_IDS)
        print(f"    Shifted shares (after cap): {parts}")
        if m.get("note"):
            print(f"    Note: {m['note']}")
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
    print(f"DECISION: {results['decision']}")
    print("=" * 72)
    print()

    # Audit
    audit = results["audit"]
    print(f"Audit hash: {audit['cryptographic_hash']}")


if __name__ == "__main__":
    main()
