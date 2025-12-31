"""
Judgements produced by ethics modules.

Ethics modules (EMs) consume EthicalFacts and emit EthicalJudgement objects,
which are then aggregated by the democratic governance layer.

Version: 0.2 (EthicalDomains update)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal


# Canonical verdict labels used across EMs and governance.
Verdict = Literal["strongly_prefer", "prefer", "neutral", "avoid", "forbid"]


@dataclass
class EthicalJudgement:
    """
    A single ethics module's normative assessment of one candidate option.

    Each EthicalJudgement is:

    - local to one EM (identified by em_name and stakeholder), and
    - tied to a specific option_id (matching an EthicalFacts.option_id).
    """

    option_id: str
    """
    Identifier for the candidate option being judged.
    Must match the EthicalFacts.option_id used as input.
    """

    em_name: str
    """
    Name or identifier of the ethics module that produced this judgement,
    e.g. "case_study_1_triage" or "rights_first_compliance".
    """

    stakeholder: str
    """
    Stakeholder whose perspective this EM is intended to represent,
    e.g. "patients_and_public", "crew", "regulator", "environment".
    """

    verdict: Verdict
    """
    Categorical verdict expressing the module's normative stance:

    - "strongly_prefer": option is strongly recommended
    - "prefer": option is acceptable and preferable to neutral
    - "neutral": no strong preference for or against the option
    - "avoid": option is disfavored but not strictly forbidden
    - "forbid": option should not be chosen under this module's view
    """

    normative_score: float
    """
    Scalar measure of ethical preferability in [0.0, 1.0].

    This is suitable for aggregation (e.g., weighted voting) but SHOULD NOT
    be interpreted without the accompanying verdict and reasons.
    """

    reasons: List[str]
    """
    Human-readable explanations for the verdict and score.

    These should reference EthicalFacts dimensions (e.g., rights violations,
    unfair discrimination, high environmental harm) in a way suitable for
    audit and external review.
    """

    metadata: Dict[str, Any]
    """
    Machine-readable metadata for downstream analysis and governance.

    Examples:
    - internal weight vectors
    - flags for which constraints were triggered
    - intermediate scores by dimension (e.g., "rights_score", "env_score")
    """


# Optional convenience helpers. These are small and safe to expose.
def is_forbidden(j: EthicalJudgement) -> bool:
    """Return True if this judgement marks the option as forbidden."""
    return j.verdict == "forbid"


def is_strongly_preferred(j: EthicalJudgement) -> bool:
    """Return True if this judgement strongly prefers the option."""
    return j.verdict == "strongly_prefer"


__all__ = [
    "Verdict",
    "EthicalJudgement",
    "is_forbidden",
    "is_strongly_preferred",
]
