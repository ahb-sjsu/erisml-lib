"""
Configuration for democratic governance over ethics modules.

The GovernanceConfig encapsulates how multiple EthicalJudgement objects
(from different EMs and stakeholders) are aggregated into a final decision.

Version: 0.3 (EthicalDomains + base EMs / 'Geneva' layer)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from erisml.ethics.profile_v03 import BaseEMEnforcementMode


@dataclass
class GovernanceConfig:
    """
    Configuration for aggregating EthicalJudgement outputs.

    This structure is intentionally simple but expressive enough to capture
    many governance patterns mentioned in the whitepaper:

    - weighted voting over EMs / stakeholders,
    - veto powers for specific EMs,
    - minimum score thresholds before an option can be selected,
    - basic tie-breaking preferences,
    - treatment of foundational ("base") EMs that sit at the top of the
      EM DAG (e.g., a Geneva-convention-style module).

    The aggregation logic that uses this config is implemented in
    `erisml.ethics.governance.aggregation`.
    """

    stakeholder_weights: Dict[str, float] = field(default_factory=dict)
    """
    Optional weights for stakeholder perspectives, keyed by stakeholder name.

    Example:
        {
            "patients_and_public": 1.0,
            "clinicians": 0.8,
            "regulator": 1.2,
            "environment": 1.0,
        }

    If empty, all stakeholders are treated as weight 1.0 by default.
    """

    em_weights: Dict[str, float] = field(default_factory=dict)
    """
    Optional per-EM weights, keyed by em_name.

    Example:
        {
            "rights_first_compliance": 2.0,
            "case_study_1_triage": 1.0,
            "fairness_em": 1.0,
        }

    If a specific em_name is not present, a default of 1.0 is assumed.
    """

    veto_ems: List[str] = field(default_factory=list)
    """
    Names of EMs (em_name) that hold veto power.

    If any such EM issues a verdict of "forbid" for an option, the
    aggregation logic will (by default) mark that option as ineligible,
    regardless of other scores.
    """

    min_score_threshold: float = 0.0
    """
    Minimum aggregated normative_score required for an option to be
    considered selectable. Options below this threshold are filtered out.

    This can be used to encode "do nothing" / status-quo preferences when
    all options score poorly.
    """

    require_non_forbidden: bool = True
    """
    If True (default), options that are forbidden by *any* EM
    (regardless of veto status) are excluded from selection.

    If False, only EMs listed in `veto_ems` have strict forbidding power.
    """

    tie_breaker: Optional[str] = None
    """
    Strategy for breaking ties between options with identical aggregated
    scores. Supported values (by the default aggregator) may include:

    - None: leave ties unresolved and let the caller decide.
    - "first": choose the first in a deterministic iteration order.
    - "random": break ties randomly (not deterministic).
    - "status_quo": prefer a designated baseline option if present.

    The exact behavior is defined in the aggregation implementation.
    """

    prefer_higher_uncertainty: bool = False
    """
    Optional tweak for experiments: if True, in tie situations the
    aggregator may favor options with *higher* epistemic uncertainty,
    to encourage exploration. If False, lower-uncertainty options are
    preferred in tie-breaking, where applicable.
    """

    # ------------------------------------------------------------------
    # Foundational / "base" EMs (Geneva-convention-style layer)
    # ------------------------------------------------------------------

    base_em_ids: List[str] = field(default_factory=list)
    """
    EM names (em_name) that should be treated as foundational.

    These EMs are intended to sit at the root of the EM-level DAG and
    may be given special treatment by the aggregator, such as:

      - being evaluated first,
      - having non-overridable veto power,
      - or occupying a dedicated top lexical layer.

    The precise semantics are controlled by `base_em_enforcement`.
    """

    base_em_enforcement: BaseEMEnforcementMode = BaseEMEnforcementMode.HARD_VETO
    """
    How the judgements from base EMs are enforced:

      - HARD_VETO:
          Any option that a base EM forbids is removed from consideration
          before other EMs are aggregated.

      - LEXICAL_SUPERIOR:
          Base EM scores are fed into a top lexical layer with hard_stop
          semantics; they influence aggregation via lexical priority rather
          than an explicit pre-pass.

      - ADVISORY:
          Base EM judgements are logged and surfaced but do not themselves
          veto options. Intended mainly for experimentation.
    """

    def weight_for_em(self, em_name: str, stakeholder: Optional[str] = None) -> float:
        """
        Compute the effective weight for an EM judgement given this config.

        The default policy is multiplicative:
            stakeholder_weight(stakeholder) * em_weight(em_name)

        Missing entries default to 1.0.
        """
        sw = 1.0
        if stakeholder is not None and stakeholder in self.stakeholder_weights:
            sw = self.stakeholder_weights[stakeholder]

        ew = self.em_weights.get(em_name, 1.0)
        return sw * ew

    def clone_with_overrides(self, **overrides: object) -> "GovernanceConfig":
        """
        Shallow clone this config with the given field overrides.

        Useful for scenario experiments where only a few parameters change.
        """
        return dataclasses.replace(self, **changes)  # type: ignore


__all__ = [
    "GovernanceConfig",
]
