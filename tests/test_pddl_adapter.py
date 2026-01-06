from __future__ import annotations

import pytest

from erisml.interop.pddl_adapter import erisml_to_tarski


# Dummy ErisModel and environment for testing
class DummyObjectType:
    def __init__(self, instances):
        self.instances = instances


class DummyEnv:
    object_types = {
        "robot": DummyObjectType(["r1", "r2"]),
        "location": DummyObjectType(["loc1", "loc2"]),
    }


class DummyModel:
    env = DummyEnv()


# ------------------------
# Tests
# ------------------------


def test_erisml_to_tarski_import_error(monkeypatch):
    """Should raise ImportError if tarski is not installed."""
    monkeypatch.setattr("erisml.interop.pddl_adapter.tarski", None)
    monkeypatch.setattr("erisml.interop.pddl_adapter.fs", None)

    model = DummyModel()
    with pytest.raises(ImportError):
        erisml_to_tarski(model)


@pytest.mark.skipif(
    erisml_to_tarski.__defaults__ is None, reason="tarski not installed"
)
def test_erisml_to_tarski_creates_problem(monkeypatch):
    """Check that the problem is created with correct sorts and constants."""

    try:
        import importlib.util

        def tarski_available():
            return importlib.util.find_spec("tarski") is not None

    except ImportError:
        pytest.skip("tarski not installed")

    model = DummyModel()
    problem = erisml_to_tarski(model)

    # type check
    assert problem.__class__.__name__ == "Problem"

    # verify object types are added as sorts
    for obj_type in model.env.object_types:
        assert obj_type in problem.language.sorts

    # verify constants
    for obj_type, type_obj in model.env.object_types.items():
        for inst in type_obj.instances:
            assert inst in problem.language.constants
