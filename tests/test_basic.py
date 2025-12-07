# ruff: noqa: E402
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

"""
Basic smoke tests for the ErisML engine and the tiny_home example.

These tests assert a few useful properties:

- The tiny_home model can be built and stepped without crashing.
- Norm violations are raised as NormViolation exceptions.
- The demo helper runs end-to-end without raising.

They also emit logging so you can see what the engine is doing when
running interactively (e.g. with `pytest -vv --log-cli-level=INFO`).
"""

from __future__ import annotations

import logging
import pathlib
import sys

import pytest

# ---------------------------------------------------------------------------
# Ensure we can import `erisml` when running pytest from the repo root,
# without requiring `pip install -e .`.
# Layout is:
#   <project_root>/
#       src/erisml/...
#       tests/test_basic.py
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from erisml.core.engine import ErisEngine
from erisml.core.norms import NormViolation
from erisml.core.types import ActionInstance
from erisml.examples.tiny_home import build_tiny_home_model, demo_tiny_home_run

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _make_engine_and_state():
    """Helper to create a tiny_home engine and a canonical initial state."""
    logger.info("Building tiny_home model and ErisEngine instance")
    model = build_tiny_home_model()
    engine = ErisEngine(model)

    state = {
        "location_human": "r1",
        "location_robot": "r1",
        "light_on_r1": False,
        "light_on_r2": False,
    }
    logger.info("Initial state: %s", state)
    return engine, state


def test_tiny_home_toggle_light_updates_state():
    """Toggling the light in r1 should update the state as expected."""
    engine, state = _make_engine_and_state()

    action = ActionInstance(
        agent="Robot",
        name="toggle_light",
        params={"room": "r1"},
    )
    logger.info("Running action: %s", action)

    new_state = engine.step(state, action)
    logger.info("State after toggle_light: %s", new_state)

    # State should be a new mapping with r1 light turned on
    assert new_state is not state, "Engine.step() should return a new state object"
    assert new_state["light_on_r1"] is True
    assert new_state["light_on_r2"] is False
    assert new_state["location_robot"] == "r1"
    assert new_state["location_human"] == "r1"


def test_tiny_home_norm_violation_on_forbidden_move():
    """
    After toggling the light in r1, moving the robot into r2 in the default
    tiny_home setup is expected to violate a norm and raise NormViolation.
    """
    engine, state = _make_engine_and_state()

    # First action: allowed toggle in r1
    a1 = ActionInstance(
        agent="Robot",
        name="toggle_light",
        params={"room": "r1"},
    )
    logger.info("Running action a1 (expected allowed): %s", a1)
    state_after_toggle = engine.step(state, a1)
    logger.info("State after a1: %s", state_after_toggle)

    # Second action: move into r2, which the example is designed
    # to treat as a norm violation.
    a2 = ActionInstance(
        agent="Robot",
        name="move_robot",
        params={"from": "r1", "to": "r2"},
    )
    logger.info("Running action a2 (expected norm violation): %s", a2)

    with pytest.raises(NormViolation):
        engine.step(state_after_toggle, a2)
    logger.info("NormViolation raised as expected for forbidden move")


def test_demo_runs_without_error():
    """
    The tiny_home demo should run end-to-end without raising.
    This is a basic smoke test for wiring between model, engine, and demo code.
    """
    logger.info("Starting demo_tiny_home_run()")
    demo_tiny_home_run()
    logger.info("demo_tiny_home_run() completed without error")
