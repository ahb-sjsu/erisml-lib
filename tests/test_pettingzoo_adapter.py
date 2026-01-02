from __future__ import annotations

import pytest
from types import SimpleNamespace

from erisml.interop.pettingzoo_adapter import ErisPettingZooEnv
from erisml.core.model import ErisModel
from erisml.core.types import ActionInstance


# ---------------------------
# Dummy classes for testing
# ---------------------------


class DummyEngine:
    """Fake engine to track calls."""

    def __init__(self, model):
        self.model = model
        self.step_called_with = []

    def step(self, state, action):
        self.step_called_with.append((state, action))
        return {"dummy_state": True}


class DummyModel(ErisModel):
    """Fake ErisModel with agents only."""

    def __init__(self):
        self.agents = {"agent1": None, "agent2": None}
        self.env = SimpleNamespace(object_types={})


# ---------------------------
# Tests
# ---------------------------


def test_env_initialization(monkeypatch):
    """Check initialization of agents, action/obs spaces, and state."""
    model = DummyModel()
    monkeypatch.setattr("erisml.interop.pettingzoo_adapter.ErisEngine", DummyEngine)
    env = ErisPettingZooEnv(model)

    assert env.agents == ["agent1", "agent2"]
    assert env.possible_agents == ["agent1", "agent2"]
    assert isinstance(env.action_spaces["agent1"], type(env.action_spaces["agent2"]))
    assert env._agent_index == 0
    assert env._cumulative_rewards["agent1"] == 0.0


def test_env_reset(monkeypatch):
    """Reset should restore internal state and cumulative rewards."""
    model = DummyModel()
    monkeypatch.setattr("erisml.interop.pettingzoo_adapter.ErisEngine", DummyEngine)
    env = ErisPettingZooEnv(model)

    env._state = {"some": "state"}
    env._cumulative_rewards["agent1"] = 5.0
    env._agent_index = 1

    env.reset()
    assert env._state == {}
    assert env._agent_index == 0
    assert env._cumulative_rewards["agent1"] == 0.0


def test_env_step(monkeypatch):
    """Step should call engine.step and cycle _agent_index."""
    model = DummyModel()
    engine_instance = DummyEngine(model)
    monkeypatch.setattr(
        "erisml.interop.pettingzoo_adapter.ErisEngine", lambda m: engine_instance
    )

    env = ErisPettingZooEnv(model)
    env.reset()

    env.step(0)
    # Check engine.step called with decoded action
    state, action = engine_instance.step_called_with[0]
    assert isinstance(action, ActionInstance)
    assert env._agent_index == 1


def test_env_step_multiple_agents(monkeypatch):
    """_agent_index cycles correctly over multiple steps."""
    model = DummyModel()
    engine_instance = DummyEngine(model)
    monkeypatch.setattr(
        "erisml.interop.pettingzoo_adapter.ErisEngine", lambda m: engine_instance
    )

    env = ErisPettingZooEnv(model)
    env.reset()

    env.step(0)
    env.step(1)
    env.step(2)  # Should wrap around to first agent
    assert env._agent_index == 1


def test_env_observe(monkeypatch):
    """Observe returns empty dict."""
    model = DummyModel()
    monkeypatch.setattr("erisml.interop.pettingzoo_adapter.ErisEngine", DummyEngine)
    env = ErisPettingZooEnv(model)

    obs = env.observe("agent1")
    assert obs == {}


def test_env_render_close(monkeypatch):
    """Render and close run without errors."""
    model = DummyModel()
    monkeypatch.setattr("erisml.interop.pettingzoo_adapter.ErisEngine", DummyEngine)
    env = ErisPettingZooEnv(model)

    env.render()  # prints state
    env.close()  # no-op
