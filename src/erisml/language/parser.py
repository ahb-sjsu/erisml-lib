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

from pathlib import Path
from typing import Any, Dict, List

from lark import Lark, Transformer, Token

from .ast import (
    AgentDecl,
    EnvDecl,
    ModelAST,
    NormRuleDecl,
    NormsDecl,
    StateVarDecl,
    TypeExpr,
)


def _grammar_text() -> str:
    grammar_path = Path(__file__).with_name("grammar.lark")
    return grammar_path.read_text(encoding="utf-8")


_PARSER = Lark(_grammar_text(), start="model", parser="lalr")


class ASTBuilder(Transformer):
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
        raise ValueError("Invalid type_expr items")

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

    def norms_block(self, items: List[Any]) -> NormsDecl:
        name_token: Token = items[0]
        rules: List[NormRuleDecl] = items[1:]
        return NormsDecl(name=name_token.value, rules=rules)

    def prohibition_rule(self, items: List[Any]) -> NormRuleDecl:
        expr_str = self._expr_to_str(items[0])
        return NormRuleDecl(kind="prohibition", expr=expr_str)

    def obligation_rule(self, items: List[Any]) -> NormRuleDecl:
        expr_str = self._expr_to_str(items[0])
        return NormRuleDecl(kind="obligation", expr=expr_str)

    def sanction_rule(self, items: List[Any]) -> NormRuleDecl:
        expr_str = self._expr_to_str(items[0])
        return NormRuleDecl(kind="sanction", expr=expr_str)

    def expr(self, items: List[Any]) -> Any:
        if len(items) == 1:
            return items[0]
        if len(items) == 3:
            return (items[1].value, items[0], items[2])
        return items[0]

    def CNAME(self, token: Token) -> Token:
        return token

    def _expr_to_str(self, node: Any) -> str:
        if isinstance(node, Token):
            return str(node.value)
        if isinstance(node, tuple) and len(node) == 3:
            op, left, right = node
            return f"({self._expr_to_str(left)} {op} {self._expr_to_str(right)})"
        return str(node)

    def model(self, items: List[Any]) -> ModelAST:
        env: EnvDecl | None = None
        agents: List[AgentDecl] = []
        norms: NormsDecl | None = None
        for item in items:
            if isinstance(item, EnvDecl):
                env = item
            elif isinstance(item, AgentDecl):
                agents.append(item)
            elif isinstance(item, NormsDecl):
                norms = item
        assert env is not None, "Model must have an environment"
        return ModelAST(environment=env, agents=agents, norms=norms)


def parse_erisml(source: str) -> ModelAST:
    # Parse ErisML source code into a typed AST.
    tree = _PARSER.parse(source)
    ast = ASTBuilder().transform(tree)
    assert isinstance(ast, ModelAST)
    return ast
