from __future__ import annotations

import logging

from prometheus_client import Counter

logger = logging.getLogger("erisml")

NORM_VIOLATIONS = Counter(
    "erisml_norm_violations_total",
    "Total norm violations observed by ErisEngine",
)
STEPS = Counter(
    "erisml_steps_total",
    "Total simulation steps in ErisEngine",
)


def log_step(violated: bool) -> None:
    STEPS.inc()
    if violated:
        NORM_VIOLATIONS.inc()
    logger.info("step", extra={"norm_violated": violated})
