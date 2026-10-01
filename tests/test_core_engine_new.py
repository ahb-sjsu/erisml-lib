import pytest
from erisml.core.engine import ErisEngine
from erisml.core.model import ErisModel, EnvironmentModel, AgentModel, NormSystem
from erisml.core.types import ActionInstance, EnvironmentRule


def simple_update(state, params):
    return {"count": state.get("count", 0) + 1}


@pytest.fixture
def minimal_model():
    env = EnvironmentModel(name="TestEnv")
    env.add_rule(EnvironmentRule("tick", [], simple_update))
    agents = {"a1": AgentModel("a1")}
    return ErisModel(env, agents, NormSystem("Empty"))


def test_engine_lifecycle(minimal_model):
    engine = ErisEngine(minimal_model)
    state = engine.reset(seed=42)
    assert engine._seed == 42
    assert engine.metrics.steps == 0

    # Step
    action = ActionInstance("a1", "tick", {})
    new_state = engine.step(state, action)
    assert new_state["count"] == 1
    assert engine.metrics.steps == 1


def test_hooks(minimal_model):
    engine = ErisEngine(minimal_model)
    state = engine.reset()

    pre_called = False
    post_called = False

    def pre_hook(s, a):
        nonlocal pre_called
        pre_called = True

    def post_hook(s, a, ns):
        nonlocal post_called
        post_called = True

    engine.register_pre_step_hook(pre_hook)
    engine.register_post_step_hook(post_hook)

    action = ActionInstance("a1", "tick", {})
    engine.step(state, action)

    assert pre_called
    assert post_called
