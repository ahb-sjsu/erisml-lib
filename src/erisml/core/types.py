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

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class BaseType(Enum):
    BOOL = "bool"
    INT = "int"
    REAL = "real"
    STR = "str"


@dataclass
class ObjectType:
    name: str
    instances: List[str]


@dataclass
class StateVarDomain:
    base_type: BaseType
    key_object_type: Optional[str] = None

    @property
    def is_mapping(self) -> bool:
        return self.key_object_type is not None


@dataclass
class StateVar:
    name: str
    domain: StateVarDomain


@dataclass
class EnvironmentRule:
    name: str
    param_names: List[str]
    update_fn: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


@dataclass
class ActionSchema:
    name: str
    param_names: List[str]


@dataclass
class ActionInstance:
    agent: str
    name: str
    params: Dict[str, Any]

    def __repr__(self) -> str:
        param_str = ", ".join(f"{k}={v!r}" for k, v in self.params.items())
        return f"{self.agent}.{self.name}({param_str})"
