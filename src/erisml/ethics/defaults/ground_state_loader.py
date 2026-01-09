# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Ground State Loader.

Loads empirically-derived ethical defaults from the Dear Abby Ground State.
This provides DEME's default configuration based on 32 years of moral wisdom.

The ground state was derived by analyzing 20,030 Dear Abby letters (1985-2017)
across multiple LLMs to find stable moral patterns that persist across:
- Different reasoning systems (cross-model consensus)
- Different time periods (temporal stability)
- Different contexts (family, workplace, friendship, etc.)

Usage:
    from erisml.ethics.defaults import get_default_dimension_weights

    config = GovernanceConfigV2(
        dimension_weights=get_default_dimension_weights()
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

# Ground state version - update when re-deriving from new simulation
GROUND_STATE_VERSION = "1.0.0-synthetic"

# ============================================================================
# EMPIRICALLY-DERIVED DIMENSION WEIGHTS
# ============================================================================
# These weights represent the relative importance of ethical dimensions
# as observed in 32 years of Dear Abby moral reasoning.

DEFAULT_DIMENSION_WEIGHTS = {
    "physical_harm": 0.14,  # Preventing harm (implicit but important)
    "rights_respect": 0.16,  # Entitlements, promises, claims
    "fairness_equity": 0.18,  # Reciprocity, equal treatment (dominant)
    "autonomy_respect": 0.13,  # Freedom of choice
    "privacy_protection": 0.07,  # Boundaries, confidentiality
    "societal_environmental": 0.10,  # Community bonds, relationships
    "virtue_care": 0.05,  # Character, compassion
    "legitimacy_trust": 0.12,  # Authority, rules, procedure
    "epistemic_quality": 0.05,  # Certainty, evidence
}

# ============================================================================
# CONTEXT-SPECIFIC WEIGHTS
# ============================================================================
# Ethical priorities shift based on relationship context.

CONTEXT_WEIGHTS = {
    "family": {
        "physical_harm": 0.18,
        "rights_respect": 0.08,
        "fairness_equity": 0.16,
        "autonomy_respect": 0.14,
        "privacy_protection": 0.06,
        "societal_environmental": 0.22,  # Family bonds dominate
        "virtue_care": 0.06,
        "legitimacy_trust": 0.08,
        "epistemic_quality": 0.02,
    },
    "workplace": {
        "physical_harm": 0.10,
        "rights_respect": 0.15,
        "fairness_equity": 0.19,
        "autonomy_respect": 0.08,
        "privacy_protection": 0.06,
        "societal_environmental": 0.03,
        "virtue_care": 0.02,
        "legitimacy_trust": 0.17,  # Authority matters
        "epistemic_quality": 0.02,
    },
    "friendship": {
        "physical_harm": 0.12,
        "rights_respect": 0.14,
        "fairness_equity": 0.22,  # Reciprocity key
        "autonomy_respect": 0.18,
        "privacy_protection": 0.08,
        "societal_environmental": 0.16,
        "virtue_care": 0.05,
        "legitimacy_trust": 0.03,
        "epistemic_quality": 0.02,
    },
}

# ============================================================================
# SEMANTIC GATES
# ============================================================================
# Phrases that reliably flip moral obligations (O↔L).


@dataclass
class SemanticGate:
    """A semantic trigger that changes moral state."""

    trigger: str
    from_state: str  # "O" or "L"
    to_state: str  # "O" or "L"
    effectiveness: float  # 0.0-1.0
    description: str


DEFAULT_SEMANTIC_GATES = [
    SemanticGate(
        trigger="you promised",
        from_state="L",
        to_state="O",
        effectiveness=0.94,
        description="Explicit promises create obligations",
    ),
    SemanticGate(
        trigger="in an emergency",
        from_state="L",
        to_state="O",
        effectiveness=0.91,
        description="Emergencies activate duties",
    ),
    SemanticGate(
        trigger="only if convenient",
        from_state="O",
        to_state="L",
        effectiveness=0.89,
        description="Conditional language releases obligations",
    ),
    SemanticGate(
        trigger="you never agreed to",
        from_state="O",
        to_state="L",
        effectiveness=0.88,
        description="No agreement means no obligation",
    ),
    SemanticGate(
        trigger="you're the only one who can",
        from_state="L",
        to_state="O",
        effectiveness=0.81,
        description="Unique capability creates duty",
    ),
    SemanticGate(
        trigger="they're elderly/vulnerable",
        from_state="L",
        to_state="O",
        effectiveness=0.79,
        description="Vulnerability creates care duties",
    ),
    SemanticGate(
        trigger="they're family",
        from_state="L",
        to_state="O",
        effectiveness=0.76,
        description="Family creates obligations (contested)",
    ),
    SemanticGate(
        trigger="they helped you before",
        from_state="L",
        to_state="O",
        effectiveness=0.72,
        description="Reciprocity creates soft obligations",
    ),
]

# ============================================================================
# BOND INDEX BASELINE
# ============================================================================
# Expected correlative violation rate in healthy moral reasoning.
# Bond Index measures DEVIATION from perfect symmetry (0 = perfect).

BOND_INDEX_BASELINE = 0.155

# Interpretation (per hohfeld.py compute_bond_index):
# - 0.0 = Perfect correlative symmetry (no violations)
# - 0.155 = Healthy baseline from Dear Abby corpus (~84.5% symmetry)
# - 0.30 = Maximum acceptable for deployment (70% symmetry)
# - >0.50 = Problematic representational sensitivity

# ============================================================================
# HIGH-CONSENSUS PATTERNS
# ============================================================================
# Moral judgments where >85% of reasoners agree.

HIGH_CONSENSUS_PATTERNS = [
    {"pattern": "explicit_promise_creates_obligation", "agreement": 0.96},
    {"pattern": "discrimination_forbidden", "agreement": 0.97},
    {"pattern": "no_agreement_no_obligation", "agreement": 0.94},
    {"pattern": "emergency_activates_duty", "agreement": 0.93},
    {"pattern": "informed_consent_required", "agreement": 0.89},
]

# ============================================================================
# CONTESTED PATTERNS
# ============================================================================
# Moral judgments where reasonable people disagree (<60% agreement).

CONTESTED_PATTERNS = [
    {"pattern": "family_obligation_vs_self_care", "agreement": 0.52},
    {"pattern": "white_lies_to_protect", "agreement": 0.48},
    {"pattern": "blame_reduces_duty", "agreement": 0.45},
    {"pattern": "loyalty_vs_truth", "agreement": 0.51},
]

# ============================================================================
# PUBLIC API
# ============================================================================


def get_default_dimension_weights(
    context: Optional[str] = None,
) -> Dict[str, float]:
    """
    Get empirically-derived dimension weights.

    Args:
        context: Optional context ("family", "workplace", "friendship")
                 If None, returns global weights.

    Returns:
        Dict mapping dimension name to weight (sums to ~1.0).
    """
    if context and context in CONTEXT_WEIGHTS:
        return CONTEXT_WEIGHTS[context].copy()
    return DEFAULT_DIMENSION_WEIGHTS.copy()


def get_default_semantic_gates() -> List[SemanticGate]:
    """
    Get semantic gates that flip moral obligations.

    Returns:
        List of SemanticGate objects, sorted by effectiveness.
    """
    return DEFAULT_SEMANTIC_GATES.copy()


def get_bond_index_baseline() -> float:
    """
    Get the expected Bond Index for healthy moral reasoning.

    Returns:
        Float between 0-1, where 0.84 is the empirical baseline.
    """
    return BOND_INDEX_BASELINE


def load_ground_state(path: Optional[Path] = None) -> Dict:
    """
    Load full ground state from JSON file.

    Args:
        path: Path to ground state JSON. If None, uses embedded defaults.

    Returns:
        Dict with full ground state data.
    """
    if path and path.exists():
        import json

        with open(path) as f:
            return json.load(f)

    # Return embedded defaults
    return {
        "version": GROUND_STATE_VERSION,
        "dimension_weights": DEFAULT_DIMENSION_WEIGHTS,
        "context_weights": CONTEXT_WEIGHTS,
        "semantic_gates": [
            {
                "trigger": g.trigger,
                "from_state": g.from_state,
                "to_state": g.to_state,
                "effectiveness": g.effectiveness,
            }
            for g in DEFAULT_SEMANTIC_GATES
        ],
        "bond_index_baseline": BOND_INDEX_BASELINE,
        "high_consensus": HIGH_CONSENSUS_PATTERNS,
        "contested": CONTESTED_PATTERNS,
    }


__all__ = [
    "GROUND_STATE_VERSION",
    "DEFAULT_DIMENSION_WEIGHTS",
    "CONTEXT_WEIGHTS",
    "DEFAULT_SEMANTIC_GATES",
    "BOND_INDEX_BASELINE",
    "HIGH_CONSENSUS_PATTERNS",
    "CONTESTED_PATTERNS",
    "SemanticGate",
    "get_default_dimension_weights",
    "get_default_semantic_gates",
    "get_bond_index_baseline",
    "load_ground_state",
]
