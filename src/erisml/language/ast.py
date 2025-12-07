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
