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

from __future__ import annotations

from typing import List, Optional, Literal

from pydantic import BaseModel


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


class ModelAST(BaseModel):
    environment: EnvDecl
    agents: List[AgentDecl]
    norms: Optional[NormsDecl] = None
