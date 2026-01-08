# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
# Contact: agi.hpc@gmail.com
#
# Licensed under the AGI-HPC Responsible AI License v1.0.
# You may obtain a copy of the License at the root of this repository,
# or by contacting the author(s).
#
# You may use, modify, and distribute this file for non-commercial
# research and educational purposes, subject to the conditions in
# the License. Commercial use, high-risk deployments, and autonomous
# operation in safety-critical domains require separate written
# permission and must include appropriate safety and governance controls.
#
# Unless required by applicable law or agreed to in writing, this
# software is provided "AS IS", without warranties or conditions
# of any kind. See the License for the specific language governing
# permissions and limitations.

"""
ErisML AST definitions.

Supports DEME 2.0 with MoralVector dimensions, tier configs, and ethics modules.

Version: 2.0.0 (DEME 2.0)
"""

from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class TypeExpr(BaseModel):
    kind: Literal["base", "mapping"]
    base: str
    key_object_type: Optional[str] = None


class StateVarDecl(BaseModel):
    name: str
    type: TypeExpr


class EnvDecl(BaseModel):
    name: str
    object_types: List[str]
    state_vars: List[StateVarDecl]


class AgentDecl(BaseModel):
    name: str
    capabilities: List[str]
    beliefs: List[str] = []
    intents: List[str] = []
    constraints: List[str] = []


class NormRuleDecl(BaseModel):
    kind: Literal["prohibition", "obligation", "sanction"]
    expr: str


class NormsDecl(BaseModel):
    name: str
    rules: List[NormRuleDecl]


# ============================================================================
# DEME 2.0 Ethics AST Nodes
# ============================================================================


class MoralVectorDecl(BaseModel):
    """MoralVector dimension weights declaration."""

    physical_harm: float = 1.0
    rights_respect: float = 1.0
    fairness_equity: float = 1.0
    autonomy_respect: float = 1.0
    legitimacy_trust: float = 1.0
    epistemic_quality: float = 0.5


class TierConfigDecl(BaseModel):
    """Configuration for an EM tier."""

    tier: int
    enabled: bool = True
    weight: float = 1.0
    veto_enabled: bool = True


class EMDecl(BaseModel):
    """Ethics Module declaration."""

    name: str
    tier: int = 2
    weight: float = 1.0
    veto_capable: bool = False
    tags: List[str] = Field(default_factory=list)


class VetoRuleDecl(BaseModel):
    """Reflex layer veto rule declaration."""

    condition_expr: str
    flag: str
    reason: Optional[str] = None


class EthicsDecl(BaseModel):
    """DEME 2.0 ethics configuration block."""

    name: str
    moral_vector: Optional[MoralVectorDecl] = None
    tier_configs: List[TierConfigDecl] = Field(default_factory=list)
    ems: List[EMDecl] = Field(default_factory=list)
    veto_rules: List[VetoRuleDecl] = Field(default_factory=list)


# ============================================================================
# Model AST
# ============================================================================


class ModelAST(BaseModel):
    environment: EnvDecl
    agents: List[AgentDecl]
    norms: Optional[NormsDecl] = None
    ethics: Optional[EthicsDecl] = None  # DEME 2.0
