import os
import re
import subprocess
import sys


def _run_pantheon_demo() -> str:
    """
    Integration-style test: run the pantheon demo as a module and capture stdout.

    Note on Windows:
      The demo prints provenance arrows like "←". If the child process inherits a
      non-UTF8 console encoding (e.g., cp1252), printing may raise UnicodeEncodeError.
      We force UTF-8 for the child via PYTHONUTF8 / PYTHONIOENCODING.
    """
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    proc = subprocess.run(
        [sys.executable, "-m", "erisml.examples.greek_tragedy_pantheon_demo"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "Pantheon demo failed.\n"
            f"returncode={proc.returncode}\n"
            f"--- stdout ---\n{proc.stdout}\n"
            f"--- stderr ---\n{proc.stderr}\n"
        )
    return proc.stdout


def test_greek_tragedy_pantheon_demo_expected_outcomes():
    out = _run_pantheon_demo()

    # 1) Sanity: the new EM ran and printed output for each option.
    # 8 cases × 3 options each = 24 (should be exactly 24 unless you add/remove cases/options).
    assert out.count("[EM=tragic_conflict") >= 24

    # 2) Sanity: the tragic_conflict EM should NEVER hard-veto / forbid on its own.
    assert re.search(r"\[EM=tragic_conflict\s+\]\s+verdict=forbid", out) is None

    # 3) Canonical expected selections (stable behavioral contract).
    # We assert using the final summary lines to avoid fragile per-case parsing.
    expected = {
        "aulis": "aulis_delay",
        "antigone": "antigone_petition",
        "ajax": "ajax_merit_award",
        "iphigenia": "iphigenia_alternative",
        "hippolytus": "hippolytus_confidential",
        "prometheus": "prometheus_governed",
        "thebes": "thebes_public_inquiry",
        "oedipus": "oedipus_gather_evidence",
    }

    # Example summary line:
    #   - aulis        [Consequences            ] -> aulis_delay
    for case_id, selected in expected.items():
        pat = (
            rf"^\s*-\s*{re.escape(case_id)}\s+\[.*?\]\s+->\s+{re.escape(selected)}\s*$"
        )
        assert re.search(
            pat, out, flags=re.MULTILINE
        ), f"Missing/changed summary for {case_id}"

    # 4) The EM should detect at least one high-conflict option in the suite.
    indices = [
        float(x) for x in re.findall(r"Tragic conflict index=([0-9]+\.[0-9]+)", out)
    ]
    assert indices, "No tragic conflict indices found in output."
    assert (
        max(indices) >= 0.55
    ), f"Expected at least one high conflict (>=0.55). got max={max(indices):.2f}"

    # 5) Ensure at least one trigger explanation was printed.
    assert "Trigger(s):" in out

    # 6) Ensure at least one high-conflict flag is present (human-facing rationale contract).
    assert "• tragic_conflict_high = True" in out
