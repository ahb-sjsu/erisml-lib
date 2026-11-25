# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
# Contact: agi.hpc@gmail.com
#
# Licensed under the MIT License. See LICENSE.txt at the root of this repository.
"""ErisML source text to a typed AST.

    from erisml.language import parse_erisml
    model = parse_erisml(source)

Every block of the grammar reaches the AST: environment, agents, norms, ethics and dynamics.
A source that does not parse raises ``ParsingError`` with the line and column.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from lark import Lark, Token, Transformer
from lark.exceptions import LarkError, VisitError

from .ast import (
    AgentDecl,
    DynamicsDecl,
    EMDecl,
    EnvDecl,
    EthicsDecl,
    Expr,
    JointTermDecl,
    ModelAST,
    MoralVectorDecl,
    NormRuleDecl,
    NormsDecl,
    RewardTermDecl,
    StateVarDecl,
    TierConfigDecl,
    TypeExpr,
    VetoRuleDecl,
)


def _grammar_text() -> str:
    grammar_path = Path(__file__).with_name("grammar.lark")
    return grammar_path.read_text(encoding="utf-8")


_PARSER = Lark(_grammar_text(), start="model", parser="lalr")


class ParsingError(ValueError):
    pass


def _unquote(token: Token) -> str:
    return str(token.value)[1:-1]


def _expr(node: Any) -> Expr:
    if isinstance(node, Expr):
        return node
    raise ParsingError(f"Invalid expression node: {node!r}")


class ASTBuilder(Transformer):
    # ------------------------------------------------------------ environment
    def environment_block(self, items: List[Any]) -> EnvDecl:
        name_token: Token = items[0]
        env_body: Dict[str, Any] = items[1]
        return EnvDecl(
            name=name_token.value,
            object_types=env_body.get("object_types", []),
            state_vars=env_body.get("state_vars", []),
        )

    def env_body(self, items: List[Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {"object_types": [], "state_vars": []}
        for item in items:
            if isinstance(item, dict) and "object_types" in item:
                out["object_types"] = item["object_types"]
            elif isinstance(item, list):
                out["state_vars"] = item
        return out

    def objects_decl(self, items: List[Token]) -> Dict[str, Any]:
        return {"object_types": [tok.value for tok in items]}

    def state_decl(self, items: List[StateVarDecl]) -> List[StateVarDecl]:
        return items

    def state_var_decl(self, items: List[Any]) -> StateVarDecl:
        name_token: Token = items[0]
        texpr: TypeExpr = items[1]
        return StateVarDecl(name=name_token.value, type=texpr)

    def base_type(self, items: List[Any]) -> Token:
        if len(items) == 1 and isinstance(items[0], Token):
            return items[0]
        raise ParsingError("Tuple type expressions are not supported")

    def type_expr(self, items: List[Any]) -> TypeExpr:
        if len(items) == 1:
            base = items[0].value
            return TypeExpr(kind="base", base=base)
        if len(items) == 2:
            key_type: Token = items[0]
            base_type: Token = items[1]
            return TypeExpr(
                kind="mapping",
                base=base_type.value,
                key_object_type=key_type.value,
            )
        raise ParsingError(
            "Invalid type expression: expected a base type or mapping type"
        )

    # ------------------------------------------------------------ agents
    def agent_block(self, items: List[Any]) -> AgentDecl:
        name_token: Token = items[0]
        body: Dict[str, Any] = items[1]
        return AgentDecl(
            name=name_token.value,
            capabilities=body.get("capabilities", []),
            beliefs=body.get("beliefs", []),
            intents=body.get("intents", []),
            constraints=body.get("constraints", []),
        )

    def agent_body(self, items: List[Any]) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "capabilities": [],
            "beliefs": [],
            "intents": [],
            "constraints": [],
        }
        for item in items:
            if isinstance(item, dict):
                data.update(item)
        return data

    def capabilities_decl(self, items: List[Token]) -> Dict[str, Any]:
        return {"capabilities": [tok.value for tok in items]}

    def beliefs_decl(self, items: List[Token]) -> Dict[str, Any]:
        return {"beliefs": [tok.value for tok in items]}

    def intents_decl(self, items: List[Token]) -> Dict[str, Any]:
        return {"intents": [tok.value for tok in items]}

    def constraints_decl(self, items: List[Token]) -> Dict[str, Any]:
        return {"constraints": [tok.value for tok in items]}

    # ------------------------------------------------------------ norms
    def norms_block(self, items: List[Any]) -> NormsDecl:
        name_token: Token = items[0]
        rules: List[NormRuleDecl] = list(items[1:])
        return NormsDecl(name=name_token.value, rules=rules)

    def _rule(self, kind: str, items: List[Any]) -> NormRuleDecl:
        tree = _expr(items[0])
        return NormRuleDecl(kind=kind, expr=tree.text(), tree=tree)

    def prohibition_rule(self, items: List[Any]) -> NormRuleDecl:
        return self._rule("prohibition", items)

    def obligation_rule(self, items: List[Any]) -> NormRuleDecl:
        return self._rule("obligation", items)

    def sanction_rule(self, items: List[Any]) -> NormRuleDecl:
        return self._rule("sanction", items)

    # ------------------------------------------------------------ expressions
    def name(self, items: List[Token]) -> Expr:
        return Expr(kind="name", value=".".join(tok.value for tok in items))

    def number(self, items: List[Token]) -> Expr:
        return Expr(kind="number", value=float(items[0].value))

    def string(self, items: List[Token]) -> Expr:
        return Expr(kind="string", value=_unquote(items[0]))

    def boolean(self, items: List[Token]) -> Expr:
        return Expr(kind="boolean", value=items[0].value == "true")

    def negation(self, items: List[Any]) -> Expr:
        return Expr(kind="not", args=[_expr(items[1])])

    def binary(self, items: List[Any]) -> Expr:
        left, op, right = items
        return Expr(kind="binary", op=str(op.value), args=[_expr(left), _expr(right)])

    # ------------------------------------------------------------ ethics
    def dimension_weight(self, items: List[Token]) -> Dict[str, float]:
        return {items[0].value: float(items[1].value)}

    def moral_vector_decl(self, items: List[Dict[str, float]]) -> MoralVectorDecl:
        weights: Dict[str, float] = {}
        for item in items:
            for dim in item:
                if dim in weights:
                    raise ParsingError(f"moral_vector gives {dim} twice")
            weights.update(item)
        return MoralVectorDecl(weights=weights)

    def tier_enabled(self, items: List[Token]) -> Dict[str, Any]:
        return {"enabled": items[0].value == "true"}

    def tier_weight(self, items: List[Token]) -> Dict[str, Any]:
        return {"weight": float(items[0].value)}

    def tier_veto(self, items: List[Token]) -> Dict[str, Any]:
        return {"veto_enabled": items[0].value == "true"}

    def tier_body(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for item in items:
            out.update(item)
        return out

    def tier_config_decl(self, items: List[Any]) -> TierConfigDecl:
        return TierConfigDecl(tier=int(items[0].value), **items[1])

    def em_tier(self, items: List[Token]) -> Dict[str, Any]:
        return {"tier": int(items[0].value)}

    def em_weight(self, items: List[Token]) -> Dict[str, Any]:
        return {"weight": float(items[0].value)}

    def em_veto_capable(self, items: List[Token]) -> Dict[str, Any]:
        return {"veto_capable": items[0].value == "true"}

    def string_list(self, items: List[Token]) -> List[str]:
        return [_unquote(tok) for tok in items]

    def em_tags(self, items: List[List[str]]) -> Dict[str, Any]:
        return {"tags": items[0]}

    def em_body(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for item in items:
            out.update(item)
        return out

    def em_decl(self, items: List[Any]) -> EMDecl:
        return EMDecl(name=items[0].value, **items[1])

    def veto_flag(self, items: List[Token]) -> Dict[str, Any]:
        return {"flag": _unquote(items[0])}

    def veto_reason(self, items: List[Token]) -> Dict[str, Any]:
        return {"reason": _unquote(items[0])}

    def veto_body(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for item in items:
            out.update(item)
        return out

    def veto_rule(self, items: List[Any]) -> VetoRuleDecl:
        tree = _expr(items[0])
        return VetoRuleDecl(condition_expr=tree.text(), tree=tree, **items[1])

    def ethics_body(self, items: List[Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "moral_vector": None,
            "tier_configs": [],
            "ems": [],
            "veto_rules": [],
        }
        for item in items:
            if isinstance(item, MoralVectorDecl):
                out["moral_vector"] = item
            elif isinstance(item, TierConfigDecl):
                if any(t.tier == item.tier for t in out["tier_configs"]):
                    raise ParsingError(f"tier {item.tier} is configured twice")
                out["tier_configs"].append(item)
            elif isinstance(item, EMDecl):
                if any(e.name == item.name for e in out["ems"]):
                    raise ParsingError(f"em {item.name} is declared twice")
                out["ems"].append(item)
            elif isinstance(item, VetoRuleDecl):
                out["veto_rules"].append(item)
        return out

    def ethics_block(self, items: List[Any]) -> EthicsDecl:
        return EthicsDecl(name=items[0].value, **items[1])

    # ------------------------------------------------------------ dynamics
    def joint_term(self, items: List[Token]) -> JointTermDecl:
        return JointTermDecl(
            agent=items[0].value, action=items[1].value, cost=float(items[2].value)
        )

    def joint_action_decl(self, items: List[JointTermDecl]) -> List[JointTermDecl]:
        return list(items)

    def reward_term(self, items: List[Any]) -> RewardTermDecl:
        tree = _expr(items[1])
        return RewardTermDecl(name=items[0].value, expr=tree.text(), tree=tree)

    def reward_decl(self, items: List[RewardTermDecl]) -> List[RewardTermDecl]:
        return list(items)

    def dynamics_block(self, items: List[Any]) -> DynamicsDecl:
        return DynamicsDecl(joint_actions=items[0], rewards=items[1])

    # ------------------------------------------------------------ model
    def model(self, items: List[Any]) -> ModelAST:
        env: EnvDecl | None = None
        agents: List[AgentDecl] = []
        norms: NormsDecl | None = None
        ethics: EthicsDecl | None = None
        dynamics: DynamicsDecl | None = None
        for item in items:
            if isinstance(item, EnvDecl):
                env = item
            elif isinstance(item, AgentDecl):
                agents.append(item)
            elif isinstance(item, NormsDecl):
                norms = item
            elif isinstance(item, EthicsDecl):
                ethics = item
            elif isinstance(item, DynamicsDecl):
                dynamics = item
        if env is None:
            raise ParsingError("Model must have an environment")
        names = [a.name for a in agents]
        for n in names:
            if names.count(n) > 1:
                raise ParsingError(f"agent {n} is declared twice")
        return ModelAST(
            environment=env,
            agents=agents,
            norms=norms,
            ethics=ethics,
            dynamics=dynamics,
        )


def parse_erisml(source: str) -> ModelAST:
    """Parse ErisML source text into a typed AST."""
    try:
        tree = _PARSER.parse(source)
    except LarkError as e:
        raise ParsingError(str(e)) from e
    try:
        ast = ASTBuilder().transform(tree)
    except VisitError as e:
        if isinstance(e.orig_exc, ParsingError):
            raise e.orig_exc from e
        raise ParsingError(f"{e.rule}: {e.orig_exc}") from e
    if not isinstance(ast, ModelAST):
        raise ParsingError("Parser produced an invalid ModelAST")
    return ast
