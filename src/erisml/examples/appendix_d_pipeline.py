"""
Appendix D: Shared Pipeline Utilities for End-to-End Case Studies.

Implements the geometric ethics pipeline described in Chapter 7 and
exercised across all five case studies in Appendix D:

  scenario → grounding Ψ → EthicalFacts → tensor quantities →
  metric and contraction choice → moral residue → Bond Index →
  audit artifact → governance decision

The nine moral dimensions are (μ = 1..9):
  1: Consequences/Welfare, 2: Rights/Duties, 3: Justice/Fairness,
  4: Autonomy/Agency, 5: Privacy/Data Governance,
  6: Societal/Environmental Impact, 7: Virtue/Care,
  8: Procedural Legitimacy, 9: Epistemic Status

Obligation vectors O^μ are tangent vectors (what is owed).
Interest covectors I_μ are dual vectors (what matters to a perspective).
Satisfaction is the contraction S = I_μ O^μ.
The moral metric g_μν defines the inner product for comparing moral vectors.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Canonical dimension labels
DIMENSION_LABELS = [
    "welfare",  # μ=1: Consequences/Welfare
    "rights",  # μ=2: Rights/Duties
    "fairness",  # μ=3: Justice/Fairness
    "autonomy",  # μ=4: Autonomy/Agency
    "privacy",  # μ=5: Privacy/Data Governance
    "societal",  # μ=6: Societal/Environmental Impact
    "care",  # μ=7: Virtue/Care
    "procedural",  # μ=8: Procedural Legitimacy
    "epistemic",  # μ=9: Epistemic Status
]


# ── Evaluation Tensor ────────────────────────────────────────────────────


def compute_evaluation_tensor(
    obligations: Dict[str, np.ndarray],
    interests: Dict[str, np.ndarray],
) -> Tuple[np.ndarray, List[str], List[str]]:
    """Compute the multi-agent evaluation tensor M_{ia} = I^(a)_μ · O^μ_i.

    Parameters
    ----------
    obligations : dict
        Maps option label → obligation vector (1-D numpy array).
    interests : dict
        Maps agent/perspective label → interest covector (1-D numpy array).

    Returns
    -------
    M : ndarray of shape (n_options, n_agents)
    option_labels : list of str
    agent_labels : list of str
    """
    option_labels = list(obligations.keys())
    agent_labels = list(interests.keys())
    n_options = len(option_labels)
    n_agents = len(agent_labels)

    M = np.zeros((n_options, n_agents))
    for i, opt in enumerate(option_labels):
        for a, agent in enumerate(agent_labels):
            M[i, a] = float(np.dot(interests[agent], obligations[opt]))

    return M, option_labels, agent_labels


# ── Contractions ─────────────────────────────────────────────────────────


def contraction_utilitarian(M: np.ndarray) -> np.ndarray:
    """Utilitarian contraction: S_i = Σ_a M_{ia}."""
    return M.sum(axis=1)


def contraction_rawlsian(M: np.ndarray) -> np.ndarray:
    """Rawlsian contraction: S_i = min_a M_{ia}."""
    return M.min(axis=1)


def contraction_expert_weighted(M: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Expert-weighted contraction: S_i = Σ_a w_a · M_{ia}."""
    return M @ weights


# ── Metric Distances ─────────────────────────────────────────────────────


def metric_distance_euclidean(
    obligation: np.ndarray, ideal: Optional[np.ndarray] = None
) -> float:
    """Euclidean distance from obligation vector to ideal (default: all ones)."""
    if ideal is None:
        ideal = np.ones_like(obligation)
    return float(np.sqrt(np.sum((ideal - obligation) ** 2)))


def metric_distance_weighted(
    obligation: np.ndarray,
    metric_diag: np.ndarray,
    ideal: Optional[np.ndarray] = None,
) -> float:
    """Weighted distance: sqrt(Σ g_μμ · (ideal_μ − O_μ)²)."""
    if ideal is None:
        ideal = np.ones_like(obligation)
    diff = ideal - obligation
    return float(np.sqrt(np.sum(metric_diag * diff**2)))


# ── Bond Index ───────────────────────────────────────────────────────────


def compute_bond_index(
    original_verdict: str,
    transform_results: Dict[str, str],
    tau: float = 0.01,
) -> Tuple[float, int, int]:
    """Compute aggregate Bond Index from invariance-preserving transforms.

    Parameters
    ----------
    original_verdict : str
        The verdict from the original (untransformed) scenario.
    transform_results : dict
        Maps transform name → resulting verdict string.
    tau : float
        Normalization threshold.

    Returns
    -------
    Bd : float
        Bond Index (0.0 = fully invariant).
    invariance_preserving : int
        Count of transforms that preserved the verdict.
    bond_changing : int
        Count of transforms that changed the verdict.
    """
    invariance_preserving = 0
    bond_changing = 0
    for verdict in transform_results.values():
        if verdict == original_verdict:
            invariance_preserving += 1
        else:
            bond_changing += 1

    n = len(transform_results)
    D_op = bond_changing / n if n > 0 else 0.0
    Bd = D_op / tau
    return Bd, invariance_preserving, bond_changing


# ── Audit Artifact ───────────────────────────────────────────────────────


def generate_audit_artifact(case_id: str, scenario: str, **kwargs: Any) -> dict:
    """Generate a DEME audit artifact with a cryptographic hash."""
    artifact: Dict[str, Any] = {
        "case_id": case_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario": scenario,
    }
    artifact.update(kwargs)

    content = json.dumps(artifact, sort_keys=True, default=str)
    hash_hex = hashlib.sha256(content.encode()).hexdigest()[:12]
    artifact["cryptographic_hash"] = f"sha256:{hash_hex}...bind to audit chain"
    return artifact


# ── Shapley Value (for CS5 Climate) ──────────────────────────────────────


def compute_shapley_values(
    agent_ids: List[str],
    value_fn: Any,
) -> Dict[str, float]:
    """Compute Shapley values for a coalition game.

    Parameters
    ----------
    agent_ids : list of str
        Identifiers for each agent/player.
    value_fn : callable
        Maps frozenset of agent_ids → coalition value (float).

    Returns
    -------
    phi : dict mapping agent_id → Shapley value
    """
    from itertools import combinations
    from math import factorial

    n = len(agent_ids)
    phi: Dict[str, float] = {a: 0.0 for a in agent_ids}

    for i, agent in enumerate(agent_ids):
        others = [a for a in agent_ids if a != agent]
        for size in range(0, n):
            for subset in combinations(others, size):
                S = frozenset(subset)
                S_with_i = S | {agent}
                marginal = value_fn(S_with_i) - value_fn(S)
                weight = factorial(len(S)) * factorial(n - len(S) - 1) / factorial(n)
                phi[agent] += weight * marginal

    return phi
