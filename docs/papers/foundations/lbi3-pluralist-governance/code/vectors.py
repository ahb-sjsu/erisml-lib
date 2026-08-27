"""The 31 preregistered constructed vectors for RQ1/E1.

Ground truth is *definitional*: each record is built so that the
expected gate outcome follows from its construction, not from a
judgment call about a real case. Expectations are written here, next
to the construction, so a reader can check them by inspection.

Expectation vocabulary per gate: "pass" | "fire" | "undet".
"""

from __future__ import annotations

from doctrinal import (
    PERMISSIVE_CONTROL,
    WI_2016_LOOMIS,
    DecisionRecord,
    JurisdictionProfile,
)

GATES = (
    "required_warnings_present",
    "not_determinative",
    "group_to_individual_inference",
    "validated_for_population",
    "purpose_fit",
    "contestability",
    "attribute_policy",
)

ALL_WARNINGS = WI_2016_LOOMIS.required_warnings

# A fully-specified, fully-compliant record. Every vector below is a
# deviation from this one, which keeps the ground truth legible.
COMPLIANT = dict(
    instrument="RAI-X",
    score=5.0,
    decision_point="post_sentencing_corrections",
    instrument_inputs=("age", "priors_count", "sex"),
    warnings_given=ALL_WARNINGS,
    stated_basis=("risk_score", "offence_history", "judicial_assessment"),
    asserts_individual_prediction=False,
    defendant_notified=True,
    contest_opportunity=True,
    validated_populations=("broward_county",),
    deployment_population="broward_county",
)


def _rec(record_id: str, **overrides) -> DecisionRecord:
    return DecisionRecord(record_id=record_id, **{**COMPLIANT, **overrides})


class Vector:
    def __init__(
        self,
        vid: str,
        klass: str,
        record: DecisionRecord,
        expect: dict[str, str],
        profile: JurisdictionProfile = WI_2016_LOOMIS,
        expect_verdict: str | None = None,
        note: str = "",
    ):
        self.vid, self.klass, self.record = vid, klass, record
        self.profile, self.note = profile, note
        # unspecified gates default to "pass"
        self.expect = {g: expect.get(g, "pass") for g in GATES}
        self.expect_verdict = expect_verdict


VECTORS: list[Vector] = []

# ---------------------------------------------------------------- V-P (7)
# One per gate: the MINIMAL record that satisfies it — only that gate's
# required fields are present, so the target gate passes and the other
# six go undetermined. This isolates each gate's pass path (seven copies
# of one fully-compliant record would test almost nothing).
_GATE_FIELDS: dict[str, tuple[str, ...]] = {
    "required_warnings_present": ("warnings_given",),
    "not_determinative": ("stated_basis",),
    "group_to_individual_inference": ("asserts_individual_prediction",),
    "validated_for_population": ("validated_populations", "deployment_population"),
    "purpose_fit": ("decision_point",),
    "contestability": ("defendant_notified", "contest_opportunity"),
    "attribute_policy": ("instrument_inputs",),
}

for i, gate in enumerate(GATES, start=1):
    fields = {f: COMPLIANT[f] for f in _GATE_FIELDS[gate]}
    VECTORS.append(
        Vector(
            f"V-P{i}", "V-P",
            DecisionRecord(record_id=f"V-P{i}", instrument="RAI-X", **fields),
            {g: ("pass" if g == gate else "undet") for g in GATES},
            expect_verdict="requires_review",
            note=f"isolates the pass path of {gate}; all other gates undetermined",
        )
    )

# ---------------------------------------------------------------- V-F (7)
# One per gate: minimal violation. That gate fires; others pass.
VECTORS += [
    Vector("V-F1", "V-F",
           _rec("V-F1", warnings_given=ALL_WARNINGS[:-1]),
           {"required_warnings_present": "fire"}, expect_verdict="forbidden",
           note="one required warning omitted"),
    Vector("V-F2", "V-F",
           _rec("V-F2", stated_basis=("risk_score",)),
           {"not_determinative": "fire"}, expect_verdict="forbidden",
           note="score is the sole stated basis"),
    Vector("V-F3", "V-F",
           _rec("V-F3", asserts_individual_prediction=True),
           {"group_to_individual_inference": "fire"}, expect_verdict="forbidden",
           note="group statistic asserted as individual prediction"),
    Vector("V-F4", "V-F",
           _rec("V-F4", deployment_population="other_county"),
           {"validated_for_population": "fire"}, expect_verdict="requires_review",
           note="deployed outside validated population (moderate only)"),
    Vector("V-F5", "V-F",
           _rec("V-F5", decision_point="pretrial_release"),
           {"purpose_fit": "fire"}, expect_verdict="forbidden",
           note="off-label decision point"),
    Vector("V-F6", "V-F",
           _rec("V-F6", contest_opportunity=False),
           {"contestability": "fire"}, expect_verdict="forbidden",
           note="no opportunity to contest inputs"),
    Vector("V-F7", "V-F",
           _rec("V-F7", instrument_inputs=("age", "race")),
           {"attribute_policy": "fire"}, expect_verdict="forbidden",
           note="foreclosed attribute among instrument inputs"),
]

# ---------------------------------------------------------------- V-U (7)
# One per gate: required field(s) removed -> undetermined, never fired.
VECTORS += [
    Vector("V-U1", "V-U", _rec("V-U1", warnings_given=None),
           {"required_warnings_present": "undet"}, expect_verdict="requires_review"),
    Vector("V-U2", "V-U", _rec("V-U2", stated_basis=None),
           {"not_determinative": "undet"}, expect_verdict="requires_review"),
    Vector("V-U3", "V-U", _rec("V-U3", asserts_individual_prediction=None),
           {"group_to_individual_inference": "undet"}, expect_verdict="requires_review"),
    Vector("V-U4", "V-U", _rec("V-U4", validated_populations=None),
           {"validated_for_population": "undet"}, expect_verdict="requires_review"),
    Vector("V-U5", "V-U", _rec("V-U5", decision_point=None),
           {"purpose_fit": "undet"}, expect_verdict="requires_review"),
    Vector("V-U6", "V-U", _rec("V-U6", defendant_notified=None),
           {"contestability": "undet"}, expect_verdict="requires_review"),
    Vector("V-U7", "V-U", _rec("V-U7", instrument_inputs=None),
           {"attribute_policy": "undet"}, expect_verdict="requires_review"),
]

# --------------------------------------------------------------- V-N1 (1)
# THE ANTI-VACUITY VECTOR: nothing observable. Everything undetermined,
# and the verdict must NOT be permissible — an empty record cannot
# certify compliance.
VECTORS.append(
    Vector(
        "V-N1", "V-N",
        DecisionRecord(record_id="V-N1", instrument="RAI-X"),
        {g: "undet" for g in GATES},
        expect_verdict="requires_review",
        note="fully stripped record; silence must not read as compliance",
    )
)

# ------------------------------------------------------------ V-J1/J2 (2)
# One record, two profiles: doctrine lives in data, not code.
_race_input = _rec("V-J", instrument_inputs=("age", "race"))
VECTORS += [
    Vector("V-J1", "V-J", _race_input, {"attribute_policy": "fire"},
           profile=WI_2016_LOOMIS, expect_verdict="forbidden",
           note="race foreclosed under the Loomis profile"),
    Vector("V-J2", "V-J", _race_input, {},
           profile=PERMISSIVE_CONTROL, expect_verdict="permissible",
           note="same record, permissive control profile: gate does not fire"),
]

# ---------------------------------------------------------------- V-C (4)
# Combinations: severity roll-up and fire/undetermined mixing.
VECTORS += [
    Vector("V-C1", "V-C",
           _rec("V-C1", stated_basis=("risk_score",), instrument_inputs=("race",)),
           {"not_determinative": "fire", "attribute_policy": "fire"},
           expect_verdict="forbidden", note="two catastrophic fires"),
    Vector("V-C2", "V-C",
           _rec("V-C2", deployment_population="other_county", warnings_given=None),
           {"validated_for_population": "fire", "required_warnings_present": "undet"},
           expect_verdict="requires_review",
           note="moderate fire + one undetermined"),
    Vector("V-C3", "V-C",
           _rec("V-C3", contest_opportunity=False, stated_basis=None,
                asserts_individual_prediction=None),
           {"contestability": "fire", "not_determinative": "undet",
            "group_to_individual_inference": "undet"},
           expect_verdict="forbidden",
           note="grave fire dominates undetermined gates"),
    Vector("V-C4", "V-C",
           _rec("V-C4", warnings_given=(), decision_point="pretrial_release"),
           {"required_warnings_present": "fire", "purpose_fit": "fire"},
           expect_verdict="forbidden", note="two grave fires"),
]

# ---------------------------------------------------------------- V-A (3)
# Adversarial near-misses that must NOT fire (over-firing check).
VECTORS += [
    Vector("V-A1", "V-A",
           _rec("V-A1", stated_basis=("risk_score", "judicial_assessment")),
           {}, expect_verdict="permissible",
           note="score present but not the sole basis"),
    Vector("V-A2", "V-A",
           _rec("V-A2", instrument_inputs=("age", "sex")),
           {}, expect_verdict="permissible",
           note="sex is permitted-with-justification, not foreclosed"),
    Vector("V-A3", "V-A",
           _rec("V-A3", warnings_given=ALL_WARNINGS + ("extra_local_caution",)),
           {}, expect_verdict="permissible",
           note="superset of required warnings still satisfies"),
]

assert len(VECTORS) == 31, f"expected 31 vectors, built {len(VECTORS)}"
assert len({v.vid for v in VECTORS}) == 31, "vector ids must be unique"
