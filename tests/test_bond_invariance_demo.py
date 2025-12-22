"""
pytest smoke tests for bond_invariance_demo_upgraded.py

These tests are intentionally simple:
- They verify that bond-preserving transforms do NOT change the selected option
  (after canonicalization where applicable).
- They verify that the "illustrative violation" is detected (i.e., fails invariance).

Run (from repo root):
  pytest -q

If your repo uses a different default profile path, set:
  DEME_PROFILE_PATH=/path/to/deme_profile_v03.json pytest -q
"""

from __future__ import annotations

from pathlib import Path
import os
import pytest


def _profile_path() -> Path:
    env = os.environ.get("DEME_PROFILE_PATH")
    if env:
        return Path(env)
    return Path("deme_profile_v03.json")


@pytest.mark.smoke
def test_bip_bond_preserving_transforms_invariant():
    try:
        # If you copy the upgraded script into erisml/examples/, import from there.
        from erisml.examples.bond_invariance_demo_upgraded import run_bip_suite
    except Exception:
        # Fallback: allow running tests directly from this file location (dev convenience).
        import importlib.util

        here = Path(__file__).resolve().parent
        demo = here / "bond_invariance_demo_upgraded.py"
        if not demo.exists():
            pytest.skip(
                "Demo script not found; copy bond_invariance_demo_upgraded.py next to this test or into erisml/examples/."
            )
        spec = importlib.util.spec_from_file_location(
            "bond_invariance_demo_upgraded", demo
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        assert spec and spec.loader
        spec.loader.exec_module(mod)  # type: ignore
        run_bip_suite = mod.run_bip_suite  # type: ignore

    profile = _profile_path()
    if not profile.exists():
        pytest.skip(
            f"Profile JSON not found at {profile}. Set DEME_PROFILE_PATH or run from repo root."
        )

    audit = run_bip_suite(
        profile,
        run_lens=False,
        show_scoreboard=False,
        show_violation=True,
        unit_scale=100.0,
    )
    baseline = audit["baseline_selected"]
    entries = {e["transform"]: e for e in audit["entries"]}

    # Bond-preserving transforms must PASS
    assert entries["reorder_options"]["passed"] is True
    assert entries["relabel_option_ids"]["passed"] is True
    assert entries["unit_scale"]["passed"] is True
    assert entries["paraphrase_evidence"]["passed"] is True
    assert entries["compose_relabel_reorder_unit_scale"]["passed"] is True

    # The illustrative violation must FAIL
    assert entries["illustrative_order_bug"]["passed"] is False

    # Sanity check: canonical comparisons were made against baseline
    assert entries["reorder_options"]["baseline_selected"] == baseline


@pytest.mark.smoke
def test_bip_counterfactual_is_not_marked_as_invariance_check():
    try:
        from erisml.examples.bond_invariance_demo_upgraded import run_bip_suite
    except Exception:
        pytest.skip(
            "Cannot import demo; copy bond_invariance_demo_upgraded.py into erisml/examples/."
        )

    profile = _profile_path()
    if not profile.exists():
        pytest.skip(
            "Profile JSON missing; run from repo root or set DEME_PROFILE_PATH."
        )

    audit = run_bip_suite(
        profile,
        run_lens=False,
        show_scoreboard=False,
        show_violation=False,
        unit_scale=100.0,
    )
    entries = {e["transform"]: e for e in audit["entries"]}

    # Counterfactual is bond-changing, so it is not asserted as pass/fail invariance.
    assert entries["remove_discrimination_counterfactual"]["passed"] is None
