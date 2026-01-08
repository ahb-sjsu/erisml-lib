# Copyright (c) 2026 Andrew H. Bond and Claude Opus 4.5
# Department of Computer Engineering, San Jose State University
# Licensed under the AGI-HPC Responsible AI License v1.0.

"""
DEME 2.0 Three-Layer Architecture.

Provides the layered decision infrastructure:
- Reflex Layer: Fast veto checks (<100μs target)
- Tactical Layer: Full MoralVector reasoning (10-100ms)
- Strategic Layer: Policy optimization (seconds-hours)
- Pipeline: Orchestrates all layers for complete decisions

Version: 2.0.0 (DEME 2.0)
"""

from erisml.ethics.layers.reflex import (
    ReflexLayer,
    ReflexLayerConfig,
    VetoRule,
    VetoResult,
)
from erisml.ethics.layers.tactical import (
    TacticalLayer,
    TacticalLayerConfig,
)
from erisml.ethics.layers.strategic import (
    StrategicLayer,
    StrategicLayerConfig,
)
from erisml.ethics.layers.pipeline import (
    DEMEPipeline,
    PipelineConfig,
)

__all__ = [
    # Reflex
    "ReflexLayer",
    "ReflexLayerConfig",
    "VetoRule",
    "VetoResult",
    # Tactical
    "TacticalLayer",
    "TacticalLayerConfig",
    # Strategic
    "StrategicLayer",
    "StrategicLayerConfig",
    # Pipeline
    "DEMEPipeline",
    "PipelineConfig",
]
