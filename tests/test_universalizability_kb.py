"""The deontic gate's sets follow from the one universalizability knowledge base.

Before 3.2 the gate kept a copy of erisml-compiler's table, and the copies could drift.
"""

from erisml.ethics import deontic_gate as gate
from erisml.ethics.facts import Maxim
from erisml.ethics.universalizability import DEFAULT_INSTITUTION_DEPENDENCIES as KB
from erisml.ethics.universalizability import test_universalizability as universalize


def test_the_gate_s_sets_are_the_knowledge_base_s():
    assert gate.PROHIBITIONS == {k for k, v in KB.items() if not v.passes}
    assert gate.PERMISSIBLE == {k for k, v in KB.items() if v.passes}
    assert gate.IMPERFECT_DUTIES <= gate.PERMISSIBLE


def test_the_gate_and_the_knowledge_base_agree_on_every_kind_and_polarity():
    for kind in KB:
        for polarity in ("affirmed", "negated"):
            verdict = gate.evaluate_maxim(Maxim(action_kind=kind, polarity=polarity))
            assert verdict.vetoed is (
                not universalize(kind, polarity=polarity).passes
            ), (
                kind,
                polarity,
            )
