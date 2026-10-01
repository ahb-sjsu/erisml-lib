from types import SimpleNamespace

from erisml.examples.adversarial_fuzzer import fuzz_numerical, make_safe_baseline


class _HarmThresholdEM:
    """Stub module: 'avoid' when expected_harm is below 0.1, else 'prefer'."""

    em_name = "harm_threshold_stub"

    def judge(self, facts):
        harm = facts.consequences.expected_harm
        verdict = "avoid" if harm < 0.1 else "prefer"
        return SimpleNamespace(verdict=verdict, normative_score=harm)


def _harm_witnesses():
    baseline = make_safe_baseline()  # expected_harm = 0.1
    witnesses = fuzz_numerical(_HarmThresholdEM(), baseline, "prefer", 0.1)
    return [w for w in witnesses if w.field_path == "consequences.expected_harm"]


def test_first_step_flip_reports_the_baseline_value():
    first = _harm_witnesses()[0]
    # the sweep starts at 0.0, so the value before the flip is the baseline's own
    assert first.baseline_value == 0.1
    assert first.mutated_value == 0.0
    assert (first.baseline_verdict, first.flipped_verdict) == ("prefer", "avoid")


def test_later_flip_reports_the_previous_probe():
    second = _harm_witnesses()[1]
    assert second.baseline_value == 0.05
    assert second.mutated_value == 0.1
    assert (second.baseline_verdict, second.flipped_verdict) == ("avoid", "prefer")


def test_every_witness_value_is_a_probed_value_in_range():
    for w in _harm_witnesses():
        assert 0.0 <= w.baseline_value <= 1.0
        assert w.baseline_value != w.mutated_value
