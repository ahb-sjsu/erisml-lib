# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Tier 0: Constitutional Ethics Modules.

These EMs encode non-removable constraints based on fundamental
principles like Geneva conventions, basic human rights, and
non-discrimination requirements.

Tier 0 EMs:
- Cannot be disabled by governance profiles
- Always have veto capability
- Highest default weights

Version: 2.0.0 (DEME 2.0)
"""

from erisml.ethics.modules.tier0.geneva_em import GenevaEMV2

__all__ = [
    "GenevaEMV2",
]
