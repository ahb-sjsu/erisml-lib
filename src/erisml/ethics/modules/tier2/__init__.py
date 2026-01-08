# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tier 2: Rights and Fairness Ethics Modules.

These EMs encode rights-based and fairness-based reasoning including
autonomy, consent, and allocation fairness.

Tier 2 EMs:
- Moderate default weights
- Can have veto capability for severe violations
- Focus on autonomy, consent, and fair treatment

Version: 2.0.0 (DEME 2.0)
"""

from erisml.ethics.modules.tier2.autonomy_consent_em import AutonomyConsentEMV2

__all__ = [
    "AutonomyConsentEMV2",
]
