# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
# Contact: agi.hpc@gmail.com
#
# Licensed under the MIT License. See LICENSE.txt at the root of this repository.
"""
ErisML AST definitions.

Every block of the grammar has a node here: environment, agents, norms, the ethics block
(MoralVector weights, tier configuration, ethics modules, veto rules) and dynamics.

An expression is kept twice: as a tree (``Expr``), which is what gets evaluated, and as its
canonical text, fully parenthesised, which is what gets shown and logged.

Version: 2.1.0
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union

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


# ============================================================================
# Expressions
# ============================================================================


class Expr(BaseModel):
    """One node of an expression tree.

    kind      value                              args
    name      the dotted name, "action.name"     none
    number    a float                            none
    string    the text, without quotes           none
    boolean   True or False                      none
    not       None                               one operand
    binary    None, with ``op`` set              left and right
    """

    kind: Literal["name", "number", "string", "boolean", "not", "binary"]
    value: Union[bool, float, str, None] = None
    op: Optional[Literal["||", "&&", "==", "!=", "<", ">", "<=", ">="]] = None
    args: List["Expr"] = Field(default_factory=list)

    def text(self) -> str:
        """The canonical text: binary operations fully parenthesised."""
        if self.kind == "name":
            return str(self.value)
        if self.kind == "number":
            v = float(self.value)  # type: ignore[arg-type]
            return str(int(v)) if v.is_integer() else repr(v)
        if self.kind == "string":
            return f'"{self.value}"'
        if self.kind == "boolean":
            return "true" if self.value else "false"
        if self.kind == "not":
            return f"!{self.args[0].text()}"
        return f"({self.args[0].text()} {self.op} {self.args[1].text()})"

    def names(self) -> List[str]:
        """Every name the expression reads, in order of first appearance."""
        out: List[str] = []
        stack = [self]
        while stack:
            node = stack.pop(0)
            if node.kind == "name" and node.value not in out:
                out.append(str(node.value))
            stack = list(node.args) + stack
        return out


Expr.model_rebuild()


class NormRuleDecl(BaseModel):
    kind: Literal["prohibition", "obligation", "sanction"]
    expr: str
    """The condition's canonical text."""
    tree: Optional[Expr] = None
    """The condition as a tree. None only for a rule built by hand from text."""


class NormsDecl(BaseModel):
    name: str
    rules: List[NormRuleDecl]


# ============================================================================
# Ethics block (DEME)
# ============================================================================


class MoralVectorDecl(BaseModel):
    """Weights on named read-outs of the moral evaluation, in the order written.

    The names are not fixed by the language. A read-out the source does not mention has no
    entry here, and whatever consumes the declaration supplies its own default for it.
    """

    weights: Dict[str, float] = Field(default_factory=dict)


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
    tree: Optional[Expr] = None


class EthicsDecl(BaseModel):
    """The ethics configuration block."""

    name: str
    moral_vector: Optional[MoralVectorDecl] = None
    tier_configs: List[TierConfigDecl] = Field(default_factory=list)
    ems: List[EMDecl] = Field(default_factory=list)
    veto_rules: List[VetoRuleDecl] = Field(default_factory=list)


# ============================================================================
# Dynamics block
# ============================================================================


class JointTermDecl(BaseModel):
    """``Agent.action -> cost N;``: what an agent's action costs."""

    agent: str
    action: str
    cost: float


class RewardTermDecl(BaseModel):
    """``name: expr;``: a named reward term."""

    name: str
    expr: str
    tree: Optional[Expr] = None


class DynamicsDecl(BaseModel):
    joint_actions: List[JointTermDecl] = Field(default_factory=list)
    rewards: List[RewardTermDecl] = Field(default_factory=list)


# ============================================================================
# Model AST
# ============================================================================


class ModelAST(BaseModel):
    environment: EnvDecl
    agents: List[AgentDecl]
    norms: Optional[NormsDecl] = None
    ethics: Optional[EthicsDecl] = None
    dynamics: Optional[DynamicsDecl] = None
