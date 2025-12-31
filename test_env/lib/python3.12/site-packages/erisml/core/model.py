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

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from erisml.core.norms import NormSystem

from .types import ActionSchema, EnvironmentRule, ObjectType, StateVar, StateVarDomain


@dataclass
class EnvironmentModel:
    name: str
    object_types: Dict[str, ObjectType] = field(default_factory=dict)
    state_vars: Dict[str, StateVar] = field(default_factory=dict)
    rules: Dict[str, EnvironmentRule] = field(default_factory=dict)

    def add_object_type(self, name: str, instances: List[str]) -> None:
        self.object_types[name] = ObjectType(name, instances)

    def add_state_var(self, name: str, domain: StateVarDomain) -> None:
        self.state_vars[name] = StateVar(name, domain)

    def add_rule(self, rule: EnvironmentRule) -> None:
        self.rules[rule.name] = rule


@dataclass
class AgentModel:
    name: str
    capabilities: Dict[str, ActionSchema] = field(default_factory=dict)

    def add_capability(self, schema: ActionSchema) -> None:
        self.capabilities[schema.name] = schema


@dataclass
class ErisModel:
    env: EnvironmentModel
    agents: Dict[str, AgentModel]
    norms: Optional["NormSystem"] = None  # defined in norms.py

    def agent(self, name: str) -> AgentModel:
        return self.agents[name]
