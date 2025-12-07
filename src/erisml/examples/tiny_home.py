from __future__ import annotations

from typing import Any, Dict

from erisml.core.engine import ErisEngine
from erisml.core.model import AgentModel, EnvironmentModel, ErisModel
from erisml.core.norms import NormRule, NormSystem, NormViolation
from erisml.core.types import (
    ActionInstance,
    ActionSchema,
    BaseType,
    EnvironmentRule,
    StateVarDomain,
)


def build_tiny_home_model() -> ErisModel:
    env = EnvironmentModel(name="TinyHome")
    env.add_object_type("Room", ["r1", "r2"])

    env.add_state_var("location_human", StateVarDomain(BaseType.STR))
    env.add_state_var("location_robot", StateVarDomain(BaseType.STR))
    env.add_state_var("light_on_r1", StateVarDomain(BaseType.BOOL))
    env.add_state_var("light_on_r2", StateVarDomain(BaseType.BOOL))

    def move_robot_rule(
        state: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        from_room = params["from"]
        to_room = params["to"]
        new_state = dict(state)
        if state["location_robot"] == from_room:
            new_state["location_robot"] = to_room
        return new_state

    def toggle_light_rule(
        state: Dict[str, Any],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        room = params["room"]
        new_state = dict(state)
        key = f"light_on_{room}"
        new_state[key] = not state[key]
        return new_state

    env.add_rule(
        EnvironmentRule("move_robot", ["from", "to"], move_robot_rule)
    )
    env.add_rule(
        EnvironmentRule("toggle_light", ["room"], toggle_light_rule)
    )

    robot = AgentModel(name="Robot")
    robot.add_capability(ActionSchema("move_robot", ["from", "to"]))
    robot.add_capability(ActionSchema("toggle_light", ["room"]))

    agents = {"Robot": robot}

    norms = NormSystem(name="Safety")

    def prohibition_move_to_r2(
        state: Dict[str, Any],
        action: ActionInstance,
    ) -> bool:
        return (
            action.agent == "Robot"
            and action.name == "move_robot"
            and action.params.get("to") == "r2"
        )

    norms.add_rule(
        NormRule("no_move_into_r2", "prohibition", prohibition_move_to_r2)
    )

    def obligation_light_on_human_room(
        state: Dict[str, Any],
        action: ActionInstance,
    ) -> bool:
        room = state["location_human"]
        key = f"light_on_{room}"
        return not state[key]

    norms.add_rule(
        NormRule(
            "keep_human_room_lit",
            "obligation",
            obligation_light_on_human_room,
        )
    )

    model = ErisModel(env=env, agents=agents, norms=norms)
    return model


def demo_tiny_home_run() -> None:
    model = build_tiny_home_model()
    engine = ErisEngine(model)

    state: Dict[str, Any] = {
        "location_human": "r1",
        "location_robot": "r1",
        "light_on_r1": False,
        "light_on_r2": False,
    }

    print("Initial state:", state)

    a1 = ActionInstance(
        agent="Robot",
        name="toggle_light",
        params={"room": "r1"},
    )
    state = engine.step(state, a1)
    print("After toggle_light(r1):", state)

    a2 = ActionInstance(
        agent="Robot",
        name="move_robot",
        params={"from": "r1", "to": "r2"},
    )
    try:
        state = engine.step(state, a2)
    except NormViolation as exc:
        print("Blocked action:", a2)
        print("Reason:", exc)

    print("Final state:", state)
    print("Metrics: steps =", engine.metrics.steps, "NVR =", engine.metrics.nvr)


if __name__ == "__main__":
    demo_tiny_home_run()
