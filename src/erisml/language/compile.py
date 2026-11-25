# ErisML is a modeling layer for governed, foundation-model-enabled agents
# Copyright (c) 2025 Andrew H. Bond
# Contact: agi.hpc@gmail.com
#
# Licensed under the MIT License. See LICENSE.txt at the root of this repository.
"""From a parsed ErisML model to objects that run.

``build_model`` turns the environment, agents and norms of a ``ModelAST`` into an
``erisml.core.model.ErisModel`` whose norm rules are evaluated by the engine.
``ethics_profile`` turns the ethics block into a ``DEMEProfileV04`` that
``pipeline_from_profile`` executes.

What a norm condition can read
------------------------------
A norm rule's condition is evaluated against the current state and the action proposed:

    action.agent        the acting agent's name
    action.name         the action's name
    action.<param>      a parameter of the action (None when the action has none by that name)
    <state variable>    a state variable declared in the environment
    <other name>        a bare identifier that is not a state variable stands for itself, as a
                        symbol: ``action.agent == Robot`` compares with the string "Robot"

A dotted name that does not start with ``action.`` is an error, found when the model is built.

What the language does not express
----------------------------------
How an action changes the state. Those transition functions are Python callables, passed to
``build_model`` as ``rules``. The object instances of each object type are data too
(``instances``). The dynamics block's costs and reward terms are kept in the AST and are not
compiled here.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from erisml.core.model import AgentModel, EnvironmentModel, ErisModel
from erisml.core.norms import NormRule, NormSystem
from erisml.core.types import (
    ActionInstance,
    ActionSchema,
    BaseType,
    EnvironmentRule,
    StateVarDomain,
)

from .ast import EthicsDecl, Expr, ModelAST


class CompileError(ValueError):
    pass


_COMPARE: Dict[str, Callable[[Any, Any], bool]] = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


def evaluate(
    expr: Expr, state: Mapping[str, Any], action: Optional[ActionInstance]
) -> Any:
    """The value of an expression in a state, for a proposed action (see the module text)."""
    if expr.kind in ("number", "string", "boolean"):
        return expr.value
    if expr.kind == "name":
        name = str(expr.value)
        if name.startswith("action."):
            if action is None:
                return None
            field = name[len("action.") :]
            if field == "agent":
                return action.agent
            if field == "name":
                return action.name
            return action.params.get(field)
        if name in state:
            return state[name]
        return name
    if expr.kind == "not":
        return not evaluate(expr.args[0], state, action)
    left, right = expr.args
    if expr.op == "&&":
        return bool(evaluate(left, state, action)) and bool(
            evaluate(right, state, action)
        )
    if expr.op == "||":
        return bool(evaluate(left, state, action)) or bool(
            evaluate(right, state, action)
        )
    a, b = evaluate(left, state, action), evaluate(right, state, action)
    if expr.op in ("<", ">", "<=", ">=") and (a is None or b is None):
        return False  # an absent parameter is not less or greater than anything
    return _COMPARE[str(expr.op)](a, b)


def _check_names(expr: Expr, where: str) -> None:
    for name in expr.names():
        if "." in name and not name.startswith("action."):
            raise CompileError(
                f"{where}: '{name}' is a dotted name, and only action.<field> may be dotted"
            )
        if name.startswith("action.") and name.count(".") != 1:
            raise CompileError(
                f"{where}: '{name}' has more than one field after action"
            )


def build_model(
    ast: ModelAST,
    instances: Optional[Mapping[str, Iterable[str]]] = None,
    rules: Optional[Mapping[str, EnvironmentRule]] = None,
) -> ErisModel:
    """The runnable model of a parsed source.

    instances  object type name -> its instance names. A type with no entry has no instances.
    rules      action name -> the EnvironmentRule that applies it. Each agent capability with a
               rule takes the rule's parameter names; one without takes none.
    """
    instances = instances or {}
    rules = rules or {}

    env = EnvironmentModel(name=ast.environment.name)
    for t in ast.environment.object_types:
        env.add_object_type(t, list(instances.get(t, [])))
    unknown = sorted(set(instances) - set(ast.environment.object_types))
    if unknown:
        raise CompileError(f"instances given for undeclared object types: {unknown}")
    for sv in ast.environment.state_vars:
        if sv.type.key_object_type and sv.type.key_object_type not in env.object_types:
            raise CompileError(
                f"state variable {sv.name} is keyed by undeclared object type "
                f"{sv.type.key_object_type}"
            )
        env.add_state_var(
            sv.name, StateVarDomain(BaseType(sv.type.base), sv.type.key_object_type)
        )
    for rule in rules.values():
        env.add_rule(rule)

    agents: Dict[str, AgentModel] = {}
    capabilities = set()
    for a in ast.agents:
        agent = AgentModel(name=a.name)
        for cap in a.capabilities:
            params = list(rules[cap].param_names) if cap in rules else []
            agent.add_capability(ActionSchema(cap, params))
            capabilities.add(cap)
        agents[a.name] = agent
    stray = sorted(set(rules) - capabilities)
    if stray:
        raise CompileError(f"rules given for actions no agent can take: {stray}")

    norms: Optional[NormSystem] = None
    if ast.norms is not None:
        norms = NormSystem(name=ast.norms.name)
        counts: Dict[str, int] = {}
        for decl in ast.norms.rules:
            if decl.tree is None:
                raise CompileError(f"norm rule '{decl.expr}' has no expression tree")
            counts[decl.kind] = counts.get(decl.kind, 0) + 1
            name = f"{decl.kind}_{counts[decl.kind]}"
            _check_names(decl.tree, f"{ast.norms.name}.{name}")
            norms.add_rule(NormRule(name, decl.kind, _predicate(decl.tree)))

    return ErisModel(env=env, agents=agents, norms=norms)


def _predicate(tree: Expr) -> Callable[[Dict[str, object], ActionInstance], bool]:
    def predicate(state: Dict[str, object], action: ActionInstance) -> bool:
        return bool(evaluate(tree, state, action))

    predicate.__doc__ = tree.text()
    return predicate


def ethics_profile(
    ethics: EthicsDecl,
    *,
    description: str = "",
    stakeholder_label: str = "",
    composition: str = "flat",
) -> Any:
    """The DEMEProfileV04 an ethics block declares.

    Each ``moral_vector`` weight must name a read-out the governance weights hold
    (``erisml.ethics.governance.config_v2.DimensionWeights``); a name it does not hold is an
    error that lists the names it does. Read-outs the block leaves out keep their defaults.
    Each ``tier`` sets that tier's enabled flag, weight multiplier and veto right. Each ``em``
    names an ethics module to activate, which must be registered. Veto rules stay in the AST:
    the reflex layer's rules are Python objects and are not built from text.
    """
    from dataclasses import fields

    from erisml.ethics.governance.config_v2 import DimensionWeights
    from erisml.ethics.profile_v04 import DEMEProfileV04, EMTierConfig

    profile = DEMEProfileV04(
        name=ethics.name,
        description=description or f"ErisML ethics block {ethics.name}",
        stakeholder_label=stakeholder_label or ethics.name,
        composition=composition,
    )
    if ethics.moral_vector is not None:
        known = [f.name for f in fields(DimensionWeights)]
        bad = [n for n in ethics.moral_vector.weights if n not in known]
        if bad:
            raise CompileError(
                f"moral_vector names read-outs the governance weights do not hold: {bad}. "
                f"They hold: {known}"
            )
        for name, weight in ethics.moral_vector.weights.items():
            setattr(profile.moral_dimension_weights, name, weight)
    for t in ethics.tier_configs:
        profile.tier_configs[t.tier] = EMTierConfig(
            enabled=t.enabled, weight_multiplier=t.weight, veto_enabled=t.veto_enabled
        )
    profile.active_em_names = [em.name for em in ethics.ems]
    return profile


def norm_texts(ast: ModelAST) -> List[str]:
    """Each norm rule as ``kind: condition``, for logs and proofs."""
    if ast.norms is None:
        return []
    return [f"{r.kind}: {r.expr}" for r in ast.norms.rules]
