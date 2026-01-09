# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
Default Ethics Configuration.

Empirically-derived ethical defaults from the Dear Abby Ground State.
These weights represent 32 years of accumulated moral wisdom (1985-2017).
"""

from erisml.ethics.defaults.ground_state_loader import (
    load_ground_state,
    get_default_dimension_weights,
    get_default_semantic_gates,
    get_bond_index_baseline,
    GROUND_STATE_VERSION,
)

__all__ = [
    "load_ground_state",
    "get_default_dimension_weights",
    "get_default_semantic_gates",
    "get_bond_index_baseline",
    "GROUND_STATE_VERSION",
]
