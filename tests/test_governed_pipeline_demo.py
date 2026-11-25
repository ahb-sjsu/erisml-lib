"""The 3.2 tutorial example decides what its text says it decides, and the tutorial notebooks
are the example scripts they claim to be."""

import os
import subprocess
import sys

from erisml.examples import (
    bond_invariance_demo,
    governed_pipeline_demo,
    triage_ethics_demo,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_the_demo_shows_veto_escalation_shell_and_party_judging(capsys):
    results = governed_pipeline_demo.run()
    capsys.readouterr()
    acts, parties = results["acts"], results["parties"]

    assert acts.composition == "hard_shell"
    assert acts.selected_option_id == "call_for_help"
    # a deception is vetoed by the gate; an act without consent and with grave harm by the shell
    assert set(acts.forbidden_options) == {
        "tell_visitor_all_is_well",
        "lift_her_unasked",
    }
    # a deception whose purpose is to protect is a conflict of duties: escalated, not forbidden
    assert list(acts.escalations) == ["understate_the_fall_to_calm_her"]
    assert "understate_the_fall_to_calm_her" not in acts.forbidden_options
    assert [s["stage"] for s in acts.stages] == ["shell", "inner"]
    assert acts.proof is not None

    # per party: the visitor consents, the resident does not, and the act is forbidden for her
    assert parties.forbidden_options == ["lift_her_as_visitor_asks"]
    verdicts = parties.party_verdicts["lift_her_as_visitor_asks"]["autonomy_consent"]
    assert verdicts["resident"] == "veto" and verdicts["visitor"] != "veto"


def test_main_runs(capsys):
    governed_pipeline_demo.main()
    out = capsys.readouterr().out
    assert "escalated" in out and "call_for_help" in out


def test_the_profile_demos_find_the_shipped_profile_from_any_directory(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)  # no deme_profile_v03.json here, as in a notebook
    for demo in (triage_ethics_demo, bond_invariance_demo):
        path = demo.default_profile_path()
        assert path.exists() and path.name == "deme_profile_v03.json"


def test_the_tutorial_notebooks_are_built_from_the_current_scripts():
    r = subprocess.run(
        [
            sys.executable,
            os.path.join(ROOT, "scripts", "build_tutorial_notebooks.py"),
            "--check",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
