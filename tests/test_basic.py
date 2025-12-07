from erisml.core.engine import ErisEngine
from erisml.core.norms import NormViolation
from erisml.core.types import ActionInstance
from erisml.examples.tiny_home import build_tiny_home_model, demo_tiny_home_run


def test_tiny_home_norm_violation():
    model = build_tiny_home_model()
    engine = ErisEngine(model)

    state = {
        "location_human": "r1",
        "location_robot": "r1",
        "light_on_r1": False,
        "light_on_r2": False,
    }

    a1 = ActionInstance(
        agent="Robot",
        name="toggle_light",
        params={"room": "r1"},
    )
    state = engine.step(state, a1)

    a2 = ActionInstance(
        agent="Robot",
        name="move_robot",
        params={"from": "r1", "to": "r2"},
    )

    raised = False
    try:
        engine.step(state, a2)
    except NormViolation:
        raised = True

    assert raised, "Moving into r2 should violate norms"


def test_demo_runs():
    demo_tiny_home_run()
