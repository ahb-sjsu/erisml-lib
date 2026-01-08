# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Reflex Layer: Fast veto checks (<100μs target).

The reflex layer provides hard constraint enforcement with minimal latency.
In production FPGA deployments, this layer runs in hardware. This Python
implementation serves as a reference and software fallback.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from erisml.ethics.facts import EthicalFacts


class VetoCategory(str, Enum):
    """Categories of veto conditions."""

    RIGHTS_VIOLATION = "rights_violation"
    DISCRIMINATION = "discrimination"
    CATASTROPHIC_HARM = "catastrophic_harm"
    CONSENT_ABSENT = "consent_absent"
    RULE_VIOLATION = "rule_violation"
    CUSTOM = "custom"


@dataclass
class VetoResult:
    """Result of a reflex layer veto check."""

    vetoed: bool
    """Whether the option was vetoed."""

    category: Optional[VetoCategory] = None
    """Category of veto if triggered."""

    rule_name: Optional[str] = None
    """Name of the rule that triggered the veto."""

    reason: str = ""
    """Human-readable reason for the veto."""

    latency_us: int = 0
    """Execution latency in microseconds."""


@dataclass
class VetoRule:
    """
    A single veto rule for the reflex layer.

    Rules should be fast (target <10μs per rule) and stateless.
    """

    name: str
    """Unique name for this rule."""

    category: VetoCategory
    """Category of violation this rule checks."""

    check: Callable[[EthicalFacts], bool]
    """
    Function that returns True if veto should be triggered.

    Should be as fast as possible (<10μs).
    """

    reason_template: str = "Veto triggered by {name}"
    """Template for veto reason. {name} will be substituted."""

    enabled: bool = True
    """Whether this rule is active."""


@dataclass
class ReflexLayerConfig:
    """Configuration for the reflex layer."""

    enabled: bool = True
    """Whether reflex layer is active."""

    timeout_us: int = 100
    """Target timeout in microseconds (for monitoring, not enforcement)."""

    fail_open: bool = False
    """
    If True, allow options when reflex check times out or errors.
    If False (default), veto on any reflex layer failure.
    """

    veto_rules: List[VetoRule] = field(default_factory=list)
    """List of veto rules to apply."""


class ReflexLayer:
    """
    Fast veto checks for hard constraint enforcement.

    Designed for <100μs total latency. In production, this would be
    implemented in FPGA hardware. This Python version is a reference
    implementation.
    """

    def __init__(self, config: Optional[ReflexLayerConfig] = None) -> None:
        """
        Initialize the reflex layer.

        Args:
            config: Layer configuration. Defaults to standard config
                   with built-in rules.
        """
        if config is None:
            config = ReflexLayerConfig()
            config.veto_rules = self._default_rules()
        self.config = config

    def _default_rules(self) -> List[VetoRule]:
        """Create default veto rules for standard constraints."""
        return [
            VetoRule(
                name="rights_violation",
                category=VetoCategory.RIGHTS_VIOLATION,
                check=lambda f: f.rights_and_duties.violates_rights,
                reason_template="Rights violation detected",
            ),
            VetoRule(
                name="discrimination",
                category=VetoCategory.DISCRIMINATION,
                check=lambda f: f.justice_and_fairness.discriminates_on_protected_attr,
                reason_template="Discrimination on protected attributes",
            ),
            VetoRule(
                name="rule_violation",
                category=VetoCategory.RULE_VIOLATION,
                check=lambda f: f.rights_and_duties.violates_explicit_rule,
                reason_template="Explicit rule violation",
            ),
        ]

    def check(self, facts: EthicalFacts) -> VetoResult:
        """
        Run all reflex veto checks.

        Args:
            facts: The EthicalFacts to check.

        Returns:
            VetoResult indicating whether option was vetoed.
        """
        if not self.config.enabled:
            return VetoResult(vetoed=False, latency_us=0)

        start_time = time.perf_counter_ns()

        try:
            for rule in self.config.veto_rules:
                if not rule.enabled:
                    continue

                try:
                    if rule.check(facts):
                        latency_us = (time.perf_counter_ns() - start_time) // 1000
                        return VetoResult(
                            vetoed=True,
                            category=rule.category,
                            rule_name=rule.name,
                            reason=rule.reason_template.format(name=rule.name),
                            latency_us=latency_us,
                        )
                except Exception:
                    # Rule check failed - treat as veto if not fail_open
                    if not self.config.fail_open:
                        latency_us = (time.perf_counter_ns() - start_time) // 1000
                        return VetoResult(
                            vetoed=True,
                            category=VetoCategory.CUSTOM,
                            rule_name=rule.name,
                            reason=f"Rule {rule.name} check failed",
                            latency_us=latency_us,
                        )

            # All rules passed
            latency_us = (time.perf_counter_ns() - start_time) // 1000
            return VetoResult(vetoed=False, latency_us=latency_us)

        except Exception:
            # Layer-level failure
            latency_us = (time.perf_counter_ns() - start_time) // 1000
            if self.config.fail_open:
                return VetoResult(vetoed=False, latency_us=latency_us)
            else:
                return VetoResult(
                    vetoed=True,
                    category=VetoCategory.CUSTOM,
                    reason="Reflex layer failure",
                    latency_us=latency_us,
                )

    def check_batch(self, facts_list: List[EthicalFacts]) -> List[VetoResult]:
        """
        Check multiple options in batch.

        Args:
            facts_list: List of EthicalFacts to check.

        Returns:
            List of VetoResults, one per input.
        """
        return [self.check(facts) for facts in facts_list]

    def add_rule(self, rule: VetoRule) -> None:
        """Add a veto rule to the layer."""
        self.config.veto_rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """
        Remove a rule by name.

        Returns:
            True if rule was found and removed.
        """
        original_len = len(self.config.veto_rules)
        self.config.veto_rules = [r for r in self.config.veto_rules if r.name != name]
        return len(self.config.veto_rules) < original_len

    def enable_rule(self, name: str, enabled: bool = True) -> bool:
        """
        Enable or disable a rule by name.

        Returns:
            True if rule was found.
        """
        for rule in self.config.veto_rules:
            if rule.name == name:
                rule.enabled = enabled
                return True
        return False


__all__ = [
    "VetoCategory",
    "VetoResult",
    "VetoRule",
    "ReflexLayerConfig",
    "ReflexLayer",
]
