"""
bond_invariance_demo.py

Bond Invariance Principle (BIP) demo script in the same style as:
  - triage_ethics_provenance_demo.py
  - greek_tragedy_pantheon_demo.py

What this demo illustrates (max-impact edition):
  1) Bond-preserving representation changes SHOULD NOT change the outcome:
     - reorder options
     - relabel option identifiers (names/IDs) without changing the underlying facts
     - unit / scale changes (with explicit canonicalization)
     - equivalent redescriptions at the evidence layer (toy paraphrase)

  2) Bond-changing changes MAY change the outcome:
     - counterfactual: remove protected-attribute discrimination evidence
     - (demo is tuned so Patient C becomes best AFTER the constraint is removed)

  3) Declared lens change MAY change the outcome (and that's OK):
     - run the same case under a second stakeholder profile (consequences-first tilt)
     - (demo is tuned so the consequences-first lens prefers B over A)

It also:
  - prints a compact scoreboard of per-module judgements and (when available) aggregated option scores
  - writes a machine-readable JSON audit artifact (suitable for CI/benchmarks)
  - includes a "composed transforms" check (reorder ∘ relabel ∘ unit-scale)

Usage (from repo root, after copying this file to erisml/examples/):

  python -m erisml.examples.bond_invariance_demo
  python -m erisml.examples.bond_invariance_demo --profile deme_profile_v03.json
  python -m erisml.examples.bond_invariance_demo --no-lens
  python -m erisml.examples.bond_invariance_demo --no-scoreboard
  python -m erisml.examples.bond_invariance_demo --audit-out bip_audit.json

Notes:
- This is an *ethical structure* demo. It's not medical guidance.
- If an invariance check fails (verdict flips under a bond-preserving transform),
  that’s a BIP violation worth investigating.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Iterable, Callable, Mapping

# --- erisml imports ---
try:
    from erisml.ethics import (
        AutonomyAndAgency,
        Consequences,
        EpistemicStatus,
        EthicalFacts,
        EthicalJudgement,
        JusticeAndFairness,
        PrivacyAndDataGovernance,
        ProceduralAndLegitimacy,
        RightsAndDuties,
        SocietalAndEnvironmental,
    )
    from erisml.ethics.governance.aggregation import DecisionOutcome, select_option
    from erisml.ethics.interop.profile_adapters import build_triage_ems_and_governance
    from erisml.ethics.modules import EM_REGISTRY
    from erisml.ethics.profile_v03 import DEMEProfileV03, deme_profile_v03_from_dict
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "Could not import erisml. This script is meant to run inside the erisml repo.\n"
        "Copy it to erisml/examples/ and run from the repo root via:\n"
        "  python -m erisml.examples.bond_invariance_demo\n\n"
        f"Import error: {e}"
    )


# ---------------------------------------------------------------------------
# Provenance (minimal; optional printing)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactProvenance:
    fact_path: str
    source_type: str
    rule_id: str
    confidence: float
    evidence_snippet: str
    model_id: Optional[str] = None
    notes: Optional[str] = None


def _clip(text: str, n: int = 110) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _set_attr(obj: Any, attr: str, value: Any) -> None:
    """Best-effort attribute set that works for (some) frozen dataclasses too."""
    try:
        setattr(obj, attr, value)
    except Exception:
        try:
            object.__setattr__(obj, attr, value)
        except Exception:
            # If this fails, we just can't mutate this object; caller must handle.
            pass


# ---------------------------------------------------------------------------
# Audit artifact types
# ---------------------------------------------------------------------------


@dataclass
class BIPAuditEntry:
    transform: str
    transform_kind: str  # "bond_preserving" | "bond_changing" | "lens_change" | "illustrative_violation"
    baseline_selected: Optional[str]
    transformed_selected_raw: Optional[str]
    transformed_selected_canonical: Optional[str]
    passed: Optional[
        bool
    ]  # None for non-check entries (e.g., lens change, bond change)
    notes: str = ""
    mapping: Optional[Dict[str, str]] = None
    unit_scale: Optional[float] = None
    bond_signature_baseline: Optional[Dict[str, Dict[str, Any]]] = None
    bond_signature_canonical: Optional[Dict[str, Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # keep output lean
        if not self.mapping:
            d.pop("mapping", None)
        if self.unit_scale is None:
            d.pop("unit_scale", None)
        if not self.bond_signature_baseline:
            d.pop("bond_signature_baseline", None)
        if not self.bond_signature_canonical:
            d.pop("bond_signature_canonical", None)
        return d


# ---------------------------------------------------------------------------
# Profile loading + a simple second stakeholder ("lens") variant
# ---------------------------------------------------------------------------


def load_profile(path: Path) -> DEMEProfileV03:
    data = json.loads(path.read_text(encoding="utf-8"))
    return deme_profile_v03_from_dict(data)


def make_second_stakeholder_profile(base_profile_path: Path) -> DEMEProfileV03:
    """Create a second stakeholder profile with an aggressively consequences-first tilt."""
    data = json.loads(base_profile_path.read_text(encoding="utf-8"))
    data = copy.deepcopy(data)

    data["name"] = (data.get("name") or "Stakeholder") + "-UtilitarianVariant"
    data["stakeholder_label"] = "utilitarian_stakeholder"
    data["override_mode"] = "consequences_first"

    # Heavily downweight equity/autonomy to encourage a different optimum.
    dims = dict(data.get("deme_dimensions", {}))
    if dims:
        dims.update(
            {
                "safety": 0.55,
                "priority_for_vulnerable": 0.01,
                "fairness_equity": 0.02,
                "autonomy_respect": 0.02,
                "privacy_confidentiality": 0.05,
                "rule_following_legality": 0.10,
                "environment_societal": 0.08,
                "trust_relationships": 0.17,
            }
        )
        total = sum(float(v) for v in dims.values())
        if total > 0:
            dims = {k: float(v) / total for k, v in dims.items()}
        data["deme_dimensions"] = dims

    # If present, push principlism strongly toward beneficence/non-maleficence.
    prin = dict(data.get("principlism", {}))
    if prin:
        prin.update(
            {
                "beneficence": 0.75,
                "non_maleficence": 0.20,
                "autonomy": 0.03,
                "justice": 0.02,
            }
        )
        total = sum(float(v) for v in prin.values())
        if total > 0:
            prin = {k: float(v) / total for k, v in prin.items()}
        data["principlism"] = prin

    return deme_profile_v03_from_dict(data)


# ---------------------------------------------------------------------------
# Evidence -> facts (small, deterministic extractor)
# ---------------------------------------------------------------------------

_DISCRIM_RX = re.compile(
    r"\b(race|ethnicity|gender|religion|protected attribute|protected class)\b", re.I
)


def discrimination_classifier_stub(text: str) -> Tuple[bool, float, str]:
    """Deterministic stand-in for a discrimination classifier."""
    m = _DISCRIM_RX.search(text or "")
    if not m:
        return False, 0.08, ""
    return True, 0.93, m.group(0)


def transform_paraphrase_evidence(evidence_by_option: Dict[str, str]) -> Dict[str, str]:
    """Bond-preserving semantic re-description at the evidence layer (toy paraphrase).

    The point here is *not* NLP quality; it’s to show the pipeline can tolerate
    equivalent natural-language redescriptions when the extracted ethical facts are unchanged.
    """
    out: Dict[str, str] = {}
    for k, v in evidence_by_option.items():
        if k.endswith("_C") or "patient_C" in k or k == "allocate_to_patient_C":
            # IMPORTANT: keep 'race'/'protected attribute' so the deterministic stub extracts the same fact.
            out[k] = (
                "Staff report (rephrased): triage assignment is proposed using race (a protected attribute) "
                "instead of clinical indicators. No other breach is noted."
            )
        elif k == "allocate_to_patient_A":
            out[k] = (
                "Scenario (rephrased): urgent patient, disadvantaged status; informed consent is valid."
            )
        elif k == "allocate_to_patient_B":
            out[k] = (
                "Scenario (rephrased): higher total welfare across many affected people; consent is valid."
            )
        else:
            out[k] = f"Rephrased: {v}"
    return out


def build_facts_for_demo(
    evidence_by_option: Dict[str, str],
) -> Tuple[Dict[str, EthicalFacts], Dict[str, Dict[str, FactProvenance]]]:
    """Create EthicalFacts for three triage options A/B/C."""
    prov_by_option: Dict[str, Dict[str, FactProvenance]] = {}

    # --- Option A: rights-first should prefer this (urgent + disadvantaged) ---
    a = EthicalFacts(
        option_id="allocate_to_patient_A",
        consequences=Consequences(
            expected_benefit=0.55,
            expected_harm=0.45,
            urgency=1.00,
            affected_count=1,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=True,
            distributive_pattern="maximin",
            exploits_vulnerable_population=False,
            exacerbates_power_imbalance=False,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=True,
            coercion_or_undue_influence=False,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.2,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.1,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.1,
            long_term_societal_risk=0.2,
            benefits_to_future_generations=0.6,
            burden_on_vulnerable_groups=0.2,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.30,
            evidence_quality="high",
            novel_situation_flag=False,
        ),
    )
    prov_by_option[a.option_id] = {
        "justice_and_fairness.prioritizes_most_disadvantaged": FactProvenance(
            fact_path="justice_and_fairness.prioritizes_most_disadvantaged",
            source_type="human",
            rule_id="MANUAL-SCENARIO",
            confidence=0.90,
            evidence_snippet=_clip(evidence_by_option.get(a.option_id, "")),
            notes="Scenario asserts vulnerability status.",
        )
    }

    # --- Option B: consequences-first should prefer this (big welfare gain + more lives affected) ---
    b = EthicalFacts(
        option_id="allocate_to_patient_B",
        consequences=Consequences(
            expected_benefit=1.00,
            expected_harm=0.00,
            urgency=0.20,
            affected_count=30,  # IMPORTANT: makes utilitarian lens noticeably prefer B
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=False,
            has_valid_consent=True,
            violates_explicit_rule=False,
            role_duty_conflict=False,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=False,
            prioritizes_most_disadvantaged=False,
            distributive_pattern="utilitarian",
            exploits_vulnerable_population=False,
            exacerbates_power_imbalance=False,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=True,
            coercion_or_undue_influence=False,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.2,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.1,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.1,
            long_term_societal_risk=0.25,
            benefits_to_future_generations=0.6,
            burden_on_vulnerable_groups=0.25,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.35,
            evidence_quality="medium",
            novel_situation_flag=False,
        ),
    )
    prov_by_option[b.option_id] = {
        "consequences.affected_count": FactProvenance(
            fact_path="consequences.affected_count",
            source_type="human",
            rule_id="MANUAL-SCENARIO",
            confidence=0.85,
            evidence_snippet=_clip(evidence_by_option.get(b.option_id, "")),
            notes="Scenario asserts broader impact (affected_count).",
        )
    }

    # --- Option C: tuned so it becomes BEST once discrimination is removed ---
    ev_c = evidence_by_option.get("allocate_to_patient_C", "")
    is_discrim, conf, tok = discrimination_classifier_stub(ev_c)

    fairness = JusticeAndFairness(
        discriminates_on_protected_attr=is_discrim,
        prioritizes_most_disadvantaged=True,  # once allowed, this should score well for rights-first too
        distributive_pattern="maximin",
        exploits_vulnerable_population=False,
        exacerbates_power_imbalance=False,
    )
    rights = RightsAndDuties(
        violates_rights=bool(
            is_discrim
        ),  # demo: treat discrimination as rights trigger
        has_valid_consent=True,
        violates_explicit_rule=False,
        role_duty_conflict=False,
    )

    c = EthicalFacts(
        option_id="allocate_to_patient_C",
        consequences=Consequences(
            expected_benefit=1.00,
            expected_harm=0.00,
            urgency=0.97,
            affected_count=1,
        ),
        rights_and_duties=rights,
        justice_and_fairness=fairness,
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=True,
            coercion_or_undue_influence=False,
            can_withdraw_without_penalty=True,
            manipulative_design_present=False,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=0.2,
            data_minimization_respected=True,
            secondary_use_without_consent=False,
            data_retention_excessive=False,
            reidentification_risk=0.1,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=0.1,
            long_term_societal_risk=0.25,
            benefits_to_future_generations=0.6,
            burden_on_vulnerable_groups=0.25,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=True,
            stakeholders_consulted=True,
            decision_explainable_to_public=True,
            contestation_available=True,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=0.35,
            evidence_quality="medium",
            novel_situation_flag=False,
        ),
    )

    prov_by_option[c.option_id] = {
        "justice_and_fairness.discriminates_on_protected_attr": FactProvenance(
            fact_path="justice_and_fairness.discriminates_on_protected_attr",
            source_type="classifier",
            rule_id="GNV-FAIR-001",
            confidence=conf if is_discrim else (1.0 - conf),
            evidence_snippet=_clip(ev_c),
            model_id="discrim_clf_stub_v0.1",
            notes=f"Matched token='{tok}'" if tok else "No protected-attr token match.",
        ),
        "rights_and_duties.violates_rights": FactProvenance(
            fact_path="rights_and_duties.violates_rights",
            source_type="hybrid",
            rule_id="RIGHTS-DERIVE-010",
            confidence=0.90 if is_discrim else 0.20,
            evidence_snippet=_clip(ev_c),
            notes="Derived: discrimination implies rights violation (demo).",
        ),
    }

    return {a.option_id: a, b.option_id: b, c.option_id: c}, prov_by_option


# ---------------------------------------------------------------------------
# Evaluation (profile -> EMs -> select_option)
# ---------------------------------------------------------------------------


def evaluate_under_profile(
    profile: DEMEProfileV03,
    facts_by_option: Dict[str, EthicalFacts],
) -> Tuple[DecisionOutcome, Dict[str, List[Tuple[str, EthicalJudgement]]]]:
    triage_em, rights_em, gov_cfg = build_triage_ems_and_governance(profile)

    ems: Dict[str, Any] = {
        "case_study_1_triage": triage_em,
        "rights_first_compliance": rights_em,
    }

    for base_id in getattr(gov_cfg, "base_em_ids", []):
        em_cls = EM_REGISTRY.get(base_id)
        if em_cls is None:
            print(f"[warn] base_em_id '{base_id}' not found in EM_REGISTRY.")
            continue
        ems[base_id] = em_cls()

    all_judgements: Dict[str, List[Tuple[str, EthicalJudgement]]] = defaultdict(list)
    for oid, facts in facts_by_option.items():
        for em_id, em in ems.items():
            all_judgements[oid].append((em_id, em.judge(facts)))

    decision: DecisionOutcome = select_option(
        {oid: [j for (_, j) in js] for oid, js in all_judgements.items()},
        gov_cfg,
    )
    return decision, all_judgements


# ---------------------------------------------------------------------------
# Scoreboard printing (robust to internal schema changes)
# ---------------------------------------------------------------------------


def _safe_get(obj: Any, *names: str) -> Any:
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return None


def _fmt_score(x: Any) -> str:
    if x is None:
        return "—"
    try:
        return f"{float(x):.3f}"
    except Exception:
        return str(x)


def extract_aggregated_scores(decision: DecisionOutcome) -> Optional[Dict[str, float]]:
    """Best-effort extraction of aggregated per-option scores from DecisionOutcome."""
    candidates = [
        "scores_by_option",
        "option_scores",
        "aggregated_scores",
        "score_by_option",
        "option_score_map",
        "normalized_scores",
    ]
    for attr in candidates:
        val = getattr(decision, attr, None)
        if isinstance(val, dict) and val:
            out: Dict[str, float] = {}
            ok = False
            for k, v in val.items():
                try:
                    out[str(k)] = float(v)
                    ok = True
                except Exception:
                    continue
            if ok and out:
                return out
    return None


def print_scoreboard(
    decision: DecisionOutcome,
    judgements: Dict[str, List[Tuple[str, EthicalJudgement]]],
) -> None:
    agg = extract_aggregated_scores(decision)
    ranked = set(
        getattr(decision, "ranked_options", getattr(decision, "ranked_option_ids", []))
        or []
    )
    forbidden = set(
        getattr(
            decision, "forbidden_options", getattr(decision, "forbidden_option_ids", [])
        )
        or []
    )

    print("\n--- Scoreboard (per option) ---")
    hdr = (
        "option_id".ljust(30)
        + "status".ljust(10)
        + "agg".ljust(8)
        + "module judgements"
    )
    print(hdr)
    print("-" * len(hdr))

    for oid, js in judgements.items():
        status = "ALLOW" if oid in ranked else ("FORBID" if oid in forbidden else "—")
        agg_s = _fmt_score(agg.get(oid)) if agg else "—"
        parts: List[str] = []
        for em_id, j in js:
            verdict = _safe_get(j, "verdict", "decision", "outcome")
            score = _safe_get(j, "normative_score", "score", "satisfaction", "value")
            parts.append(f"{em_id}:{verdict}/{_fmt_score(score)}")
        print(
            oid.ljust(30) + status.ljust(10) + agg_s.ljust(8) + "  " + "; ".join(parts)
        )


def print_outcome(
    label: str,
    decision: DecisionOutcome,
    judgements: Optional[Dict[str, List[Tuple[str, EthicalJudgement]]]] = None,
    show_scoreboard: bool = True,
) -> None:
    print(f"\n=== {label} ===")
    print(f"selected_option_id: {decision.selected_option_id}")
    ranked = getattr(
        decision, "ranked_options", getattr(decision, "ranked_option_ids", [])
    )
    forbidden = getattr(
        decision, "forbidden_options", getattr(decision, "forbidden_option_ids", [])
    )
    print(f"ranked_options (eligible): {ranked}")
    print(f"forbidden_options:         {forbidden if forbidden else 'none'}")
    print(f"rationale:                 {decision.rationale}")
    if show_scoreboard and judgements is not None:
        print_scoreboard(decision, judgements)


# ---------------------------------------------------------------------------
# Bond signatures (for audit artifacts)
# ---------------------------------------------------------------------------


def bond_signature(
    facts_by_option: Dict[str, EthicalFacts]
) -> Dict[str, Dict[str, Any]]:
    """A small, stable signature of ethically salient structure for audit artifacts.

    This is *not* meant to be exhaustive; it’s a quick way to show that a purported
    bond-preserving transform did (or did not) change extracted structure.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for oid, f in facts_by_option.items():
        cons = _safe_get(f, "consequences") or object()
        rights = _safe_get(f, "rights_and_duties") or object()
        justice = _safe_get(f, "justice_and_fairness") or object()
        epi = _safe_get(f, "epistemic_status") or object()
        out[oid] = {
            "benefit": _safe_get(cons, "expected_benefit"),
            "harm": _safe_get(cons, "expected_harm"),
            "urgency": _safe_get(cons, "urgency"),
            "affected_count": _safe_get(cons, "affected_count"),
            "violates_rights": _safe_get(rights, "violates_rights"),
            "consent": _safe_get(rights, "has_valid_consent"),
            "discriminates": _safe_get(justice, "discriminates_on_protected_attr"),
            "prioritizes_disadvantaged": _safe_get(
                justice, "prioritizes_most_disadvantaged"
            ),
            "evidence_quality": _safe_get(epi, "evidence_quality"),
            "uncertainty": _safe_get(epi, "uncertainty_level"),
        }
    return out


# ---------------------------------------------------------------------------
# BIP transforms
# ---------------------------------------------------------------------------


def transform_reorder(
    facts_by_option: Dict[str, EthicalFacts]
) -> Dict[str, EthicalFacts]:
    """Bond-preserving transform: reorder option presentation."""
    keys = list(facts_by_option.keys())
    if len(keys) <= 1:
        return dict(facts_by_option)
    return OrderedDict([(k, facts_by_option[k]) for k in reversed(keys)])


def transform_relabel(
    facts_by_option: Dict[str, EthicalFacts],
    suffix: str = "_renamed",
) -> Tuple[Dict[str, EthicalFacts], Dict[str, str]]:
    """Bond-preserving transform: relabel option IDs without changing the underlying facts."""
    out: Dict[str, EthicalFacts] = OrderedDict()
    mapping: Dict[str, str] = {}
    for old_id, facts in facts_by_option.items():
        new_id = f"{old_id}{suffix}"
        nf = copy.deepcopy(facts)
        _set_attr(nf, "option_id", new_id)
        out[new_id] = nf
        mapping[old_id] = new_id
    return out, mapping


def transform_unit_scale(
    facts_by_option: Dict[str, EthicalFacts],
    *,
    scale: float = 100.0,
) -> Tuple[Dict[str, EthicalFacts], float]:
    """Bond-preserving transform: reparameterize numeric features by a unit/scale change.

    We treat this as a *representation-level* change. Canonicalization must divide by `scale`
    before the governance engine runs. This demonstrates "Scale Normalization" in a way
    that can be plugged into CI.
    """
    out: Dict[str, EthicalFacts] = OrderedDict()
    for oid, f in facts_by_option.items():
        nf = copy.deepcopy(f)
        cons = copy.deepcopy(_safe_get(nf, "consequences"))
        if cons is not None:
            for field in ("expected_benefit", "expected_harm", "urgency"):
                if hasattr(cons, field):
                    val = getattr(cons, field)
                    if isinstance(val, (int, float)):
                        _set_attr(cons, field, float(val) * float(scale))
            _set_attr(nf, "consequences", cons)
        out[_safe_get(nf, "option_id") or oid] = nf
    return out, float(scale)


def canonicalize_units(
    facts_by_option: Dict[str, EthicalFacts],
    *,
    unit_scale: Optional[float] = None,
) -> Dict[str, EthicalFacts]:
    """Convert unit-scaled representations back to canonical units before evaluation."""
    if unit_scale is None or unit_scale == 1.0:
        return facts_by_option
    inv = 1.0 / float(unit_scale)
    out: Dict[str, EthicalFacts] = OrderedDict()
    for oid, f in facts_by_option.items():
        nf = copy.deepcopy(f)
        cons = copy.deepcopy(_safe_get(nf, "consequences"))
        if cons is not None:
            for field in ("expected_benefit", "expected_harm", "urgency"):
                if hasattr(cons, field):
                    val = getattr(cons, field)
                    if isinstance(val, (int, float)):
                        _set_attr(cons, field, float(val) * inv)
            _set_attr(nf, "consequences", cons)
        out[oid] = nf
    return out


def canonicalize_selected(
    selected_option_id: Optional[str], inverse_map: Mapping[str, str]
) -> Optional[str]:
    if selected_option_id is None:
        return None
    return inverse_map.get(selected_option_id, selected_option_id)


def print_mapping_summary(mapping: Dict[str, str], *, title: str = "mapping") -> None:
    items = list(mapping.items())
    print(f"[{title}] {len(items)} ids")
    for k, v in items:
        print(f"  {k}  ->  {v}")


def check_invariance(
    label: str,
    baseline: Optional[str],
    transformed_canonical: Optional[str],
    *,
    use_symbols: bool = True,
) -> bool:
    ok = baseline == transformed_canonical
    if use_symbols:
        status = "PASS ✓" if ok else "FAIL ✗"
    else:
        status = "PASS" if ok else "FAIL"
    print(f"[BIP invariance check] {label}: {status}")
    if not ok:
        print(f"  baseline:    {baseline}")
        print(f"  transformed: {transformed_canonical}")
        print(
            "  - This would indicate a bug: the system responded to syntax, not structure."
        )
    return ok


def highlight_change(title: str, before: Optional[str], after: Optional[str]) -> None:
    if before == after:
        print(f"[{title}] selected option unchanged: {before}")
        print(
            "  (This can happen if options remain similarly ranked under this governance config; see scoreboard.)"
        )
    else:
        print(f"[{title}] selected option CHANGED: {before}  ->  {after}")


def simulate_order_dependent_bug_selected_id(
    decision: DecisionOutcome, baseline_selected: Optional[str]
) -> Optional[str]:
    """Return a DIFFERENT eligible option id to simulate an order-dependent bug.

    This does NOT reflect erisml behavior; it's an intentional illustration of what a BIP failure
    would look like in logs.
    """
    ranked = (
        getattr(decision, "ranked_options", getattr(decision, "ranked_option_ids", []))
        or []
    )
    for oid in ranked:
        if oid != baseline_selected:
            return oid
    return ranked[0] if ranked else baseline_selected


# ---------------------------------------------------------------------------
# Suite runner (callable from pytest/CI)
# ---------------------------------------------------------------------------


def run_bip_suite(
    profile_path: Path,
    *,
    run_lens: bool = True,
    show_scoreboard: bool = True,
    show_violation: bool = True,
    unit_scale: float = 100.0,
) -> Dict[str, Any]:
    """Run the full demo suite and return a JSON-serializable audit dict."""
    audit_entries: List[BIPAuditEntry] = []

    profile_1 = load_profile(profile_path)
    profile_2: Optional[DEMEProfileV03] = (
        make_second_stakeholder_profile(profile_path) if run_lens else None
    )

    # Evidence texts are used for provenance + discrimination detection for C.
    evidence_baseline = {
        "allocate_to_patient_A": "Manual scenario: urgent disadvantaged patient; consent OK.",
        "allocate_to_patient_B": "Manual scenario: higher welfare gain across multiple affected people; consent OK.",
        "allocate_to_patient_C": (
            "Nurse note: allocate triage slot based on race (protected attribute) rather than clinical need. "
            "No other policy breach is recorded."
        ),
    }

    # --- baseline ---
    facts_base, _ = build_facts_for_demo(evidence_baseline)
    dec_base, js_base = evaluate_under_profile(profile_1, facts_base)
    print_outcome(
        "Baseline (canonical representation)",
        dec_base,
        js_base,
        show_scoreboard=show_scoreboard,
    )
    baseline_sel = dec_base.selected_option_id
    sig_base = bond_signature(facts_base)

    # --- bond-preserving: reorder ---
    facts_reordered = transform_reorder(facts_base)
    dec_reorder, js_reorder = evaluate_under_profile(profile_1, facts_reordered)
    print_outcome(
        "Bond-preserving transform: reorder options",
        dec_reorder,
        js_reorder,
        show_scoreboard=show_scoreboard,
    )
    ok_reorder = check_invariance(
        "reorder", baseline_sel, dec_reorder.selected_option_id
    )
    audit_entries.append(
        BIPAuditEntry(
            transform="reorder_options",
            transform_kind="bond_preserving",
            baseline_selected=baseline_sel,
            transformed_selected_raw=dec_reorder.selected_option_id,
            transformed_selected_canonical=dec_reorder.selected_option_id,
            passed=ok_reorder,
            notes="Presentation order changed; verdict must not.",
            bond_signature_baseline=sig_base,
            bond_signature_canonical=bond_signature(facts_reordered),
        )
    )

    # --- illustrative violation ---
    if show_violation:
        print("\n=== BIP VIOLATION (intentional, for illustration) ===")
        print("[Simulated bug: outcome depends on option presentation order]")
        bug_selected = simulate_order_dependent_bug_selected_id(
            dec_reorder, baseline_sel
        )
        print(f"selected_option_id: {bug_selected}  \u2190 DIFFERENT!")
        ok_bug = check_invariance(
            "reorder", baseline_sel, bug_selected, use_symbols=True
        )
        audit_entries.append(
            BIPAuditEntry(
                transform="illustrative_order_bug",
                transform_kind="illustrative_violation",
                baseline_selected=baseline_sel,
                transformed_selected_raw=bug_selected,
                transformed_selected_canonical=bug_selected,
                passed=ok_bug,
                notes="Intentional failure: demonstrates the audit detects representation sensitivity.",
            )
        )

    # --- bond-preserving: relabel IDs (canonicalize the answer back) ---
    facts_relabeled, mapping = transform_relabel(facts_base)
    inv_map = {v: k for k, v in mapping.items()}
    print("\n[relabel] option-id mapping:")
    print_mapping_summary(mapping, title="relabel mapping")
    dec_relabel, js_relabel = evaluate_under_profile(profile_1, facts_relabeled)
    canon_sel_relabel = canonicalize_selected(dec_relabel.selected_option_id, inv_map)
    print_outcome(
        "Bond-preserving transform: relabel option IDs",
        dec_relabel,
        js_relabel,
        show_scoreboard=show_scoreboard,
    )
    print(
        f"[relabel] selected_option_id canonicalized: {dec_relabel.selected_option_id} -> {canon_sel_relabel}"
    )
    ok_relabel = check_invariance(
        "relabel (canonicalized)", baseline_sel, canon_sel_relabel
    )
    audit_entries.append(
        BIPAuditEntry(
            transform="relabel_option_ids",
            transform_kind="bond_preserving",
            baseline_selected=baseline_sel,
            transformed_selected_raw=dec_relabel.selected_option_id,
            transformed_selected_canonical=canon_sel_relabel,
            passed=ok_relabel,
            mapping=mapping,
            notes="IDs renamed; compare after canonicalization.",
            bond_signature_baseline=sig_base,
            bond_signature_canonical=bond_signature(facts_relabeled),
        )
    )

    # --- bond-preserving: unit/scale change (canonicalize units before evaluation) ---
    facts_scaled, scale = transform_unit_scale(facts_base, scale=unit_scale)
    facts_scaled_canon = canonicalize_units(facts_scaled, unit_scale=scale)
    dec_scaled, js_scaled = evaluate_under_profile(profile_1, facts_scaled_canon)
    print_outcome(
        f"Bond-preserving transform: unit/scale change (scale={scale:g})",
        dec_scaled,
        js_scaled,
        show_scoreboard=show_scoreboard,
    )
    ok_scale = check_invariance(
        f"unit_scale (canonicalized, scale={scale:g})",
        baseline_sel,
        dec_scaled.selected_option_id,
    )
    audit_entries.append(
        BIPAuditEntry(
            transform="unit_scale",
            transform_kind="bond_preserving",
            baseline_selected=baseline_sel,
            transformed_selected_raw=dec_scaled.selected_option_id,
            transformed_selected_canonical=dec_scaled.selected_option_id,
            passed=ok_scale,
            unit_scale=scale,
            notes="Numeric features rescaled; canonicalization must undo before governance.",
            bond_signature_baseline=sig_base,
            bond_signature_canonical=bond_signature(facts_scaled_canon),
        )
    )

    # --- bond-preserving: equivalent redescription at evidence layer (paraphrase) ---
    evidence_para = transform_paraphrase_evidence(evidence_baseline)
    facts_para, _ = build_facts_for_demo(evidence_para)
    dec_para, js_para = evaluate_under_profile(profile_1, facts_para)
    print_outcome(
        "Bond-preserving transform: equivalent redescription (toy paraphrase)",
        dec_para,
        js_para,
        show_scoreboard=show_scoreboard,
    )
    ok_para = check_invariance(
        "paraphrase_evidence", baseline_sel, dec_para.selected_option_id
    )
    audit_entries.append(
        BIPAuditEntry(
            transform="paraphrase_evidence",
            transform_kind="bond_preserving",
            baseline_selected=baseline_sel,
            transformed_selected_raw=dec_para.selected_option_id,
            transformed_selected_canonical=dec_para.selected_option_id,
            passed=ok_para,
            notes="Evidence text rephrased; extracted facts unchanged => verdict invariant.",
            bond_signature_baseline=sig_base,
            bond_signature_canonical=bond_signature(facts_para),
        )
    )

    # --- composed bond-preserving transforms: reorder ∘ relabel ∘ unit-scale ---
    facts_comp, map_comp = transform_relabel(facts_base, suffix="_X")
    facts_comp = transform_reorder(facts_comp)
    facts_comp, scale_comp = transform_unit_scale(facts_comp, scale=unit_scale)
    facts_comp_canon = canonicalize_units(facts_comp, unit_scale=scale_comp)
    inv_comp = {v: k for k, v in map_comp.items()}

    print("\n[compose] applied: relabel('_X') ∘ reorder ∘ unit_scale")
    print_mapping_summary(map_comp, title="compose relabel mapping")
    dec_comp, js_comp = evaluate_under_profile(profile_1, facts_comp_canon)
    canon_sel_comp = canonicalize_selected(dec_comp.selected_option_id, inv_comp)
    print_outcome(
        "Bond-preserving transform: composed (relabel ∘ reorder ∘ unit_scale)",
        dec_comp,
        js_comp,
        show_scoreboard=show_scoreboard,
    )
    print(
        f"[compose] selected_option_id canonicalized: {dec_comp.selected_option_id} -> {canon_sel_comp}"
    )
    ok_comp = check_invariance("compose (canonicalized)", baseline_sel, canon_sel_comp)
    audit_entries.append(
        BIPAuditEntry(
            transform="compose_relabel_reorder_unit_scale",
            transform_kind="bond_preserving",
            baseline_selected=baseline_sel,
            transformed_selected_raw=dec_comp.selected_option_id,
            transformed_selected_canonical=canon_sel_comp,
            passed=ok_comp,
            mapping=map_comp,
            unit_scale=scale_comp,
            notes="Composition check: invariance should hold under group action, not just one-off transforms.",
            bond_signature_baseline=sig_base,
            bond_signature_canonical=bond_signature(facts_comp_canon),
        )
    )

    # --- bond-changing counterfactual: remove discrimination evidence ---
    evidence_cf = dict(evidence_baseline)
    evidence_cf["allocate_to_patient_C"] = (
        "Counterfactual note: allocate triage slot based on clinical urgency and expected benefit only. "
        "No protected-attribute discrimination is recorded."
    )
    facts_cf, _ = build_facts_for_demo(evidence_cf)
    dec_cf, js_cf = evaluate_under_profile(profile_1, facts_cf)
    print_outcome(
        "Bond-changing counterfactual: remove discrimination",
        dec_cf,
        js_cf,
        show_scoreboard=show_scoreboard,
    )
    highlight_change(
        "Bond-change effect (expected)", baseline_sel, dec_cf.selected_option_id
    )
    audit_entries.append(
        BIPAuditEntry(
            transform="remove_discrimination_counterfactual",
            transform_kind="bond_changing",
            baseline_selected=baseline_sel,
            transformed_selected_raw=dec_cf.selected_option_id,
            transformed_selected_canonical=dec_cf.selected_option_id,
            passed=None,
            notes="Bond changed (non-discrimination / rights trigger removed), so outcome may change.",
            bond_signature_baseline=sig_base,
            bond_signature_canonical=bond_signature(facts_cf),
        )
    )

    print("\n[BIP interpretation]")
    print(
        "  - Outcome changes under reorder/relabel/unit/paraphrase are NOT expected: those are BIP tests."
    )
    print(
        "  - Outcome changes under the counterfactual ARE expected: bond-relevant evidence changed."
    )

    # --- lens change (stakeholder #2) ---
    if profile_2 is not None:
        dec_lens, js_lens = evaluate_under_profile(profile_2, facts_base)
        print_outcome(
            "Declared lens change: stakeholder #2",
            dec_lens,
            js_lens,
            show_scoreboard=show_scoreboard,
        )
        highlight_change(
            "Lens-change effect (allowed)", baseline_sel, dec_lens.selected_option_id
        )
        print("\n[BIP interpretation]")
        print(
            "  - Lens changes may change outcomes, but must be declared and auditable."
        )
        audit_entries.append(
            BIPAuditEntry(
                transform="lens_change_profile_2",
                transform_kind="lens_change",
                baseline_selected=baseline_sel,
                transformed_selected_raw=dec_lens.selected_option_id,
                transformed_selected_canonical=dec_lens.selected_option_id,
                passed=None,
                notes="Lens change is allowed (and should be explicit).",
            )
        )

    # summary
    return {
        "tool": "bond_invariance_demo",
        "generated_at_utc": _utc_now_iso(),
        "profile_1": {
            "name": profile_1.name,
            "override_mode": str(getattr(profile_1, "override_mode", None)),
        },
        "profile_2": (
            None
            if profile_2 is None
            else {
                "name": profile_2.name,
                "override_mode": str(getattr(profile_2, "override_mode", None)),
            }
        ),
        "baseline_selected": baseline_sel,
        "entries": [e.to_dict() for e in audit_entries],
    }


# ---------------------------------------------------------------------------
# CLI runner (thin wrapper around run_bip_suite)
# ---------------------------------------------------------------------------


def run(
    profile_path: Path,
    run_lens: bool,
    show_scoreboard: bool,
    show_violation: bool,
    audit_out: Optional[Path],
    unit_scale: float,
) -> None:
    print("=== Bond Invariance Principle (BIP) Demo ===\n")
    audit = run_bip_suite(
        profile_path,
        run_lens=run_lens,
        show_scoreboard=show_scoreboard,
        show_violation=show_violation,
        unit_scale=unit_scale,
    )
    if audit_out is not None:
        audit_out.write_text(
            json.dumps(audit, indent=2, sort_keys=False), encoding="utf-8"
        )
        print(f"\n[audit] wrote JSON artifact: {audit_out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--profile",
        type=Path,
        default=Path("deme_profile_v03.json"),
        help="Path to DEMEProfileV03 JSON (default: ./deme_profile_v03.json)",
    )
    ap.add_argument(
        "--no-lens",
        action="store_true",
        help="Skip the second stakeholder profile (lens-change) portion.",
    )
    ap.add_argument(
        "--no-scoreboard",
        action="store_true",
        help="Do not print the detailed per-option scoreboard.",
    )
    ap.add_argument(
        "--no-violation",
        action="store_true",
        help="Skip the intentional BIP-violation illustration block.",
    )
    ap.add_argument(
        "--audit-out",
        type=Path,
        default=Path("bip_audit_artifact.json"),
        help="Write a JSON audit artifact to this path (default: ./bip_audit_artifact.json). Use --no-audit to disable.",
    )
    ap.add_argument(
        "--no-audit",
        action="store_true",
        help="Do not write a JSON audit artifact.",
    )
    ap.add_argument(
        "--unit-scale",
        type=float,
        default=100.0,
        help="Scale factor used for the unit/scale reparameterization transform (default: 100.0).",
    )
    args = ap.parse_args()

    run(
        args.profile,
        run_lens=(not args.no_lens),
        show_scoreboard=(not args.no_scoreboard),
        show_violation=(not args.no_violation),
        audit_out=(None if args.no_audit else args.audit_out),
        unit_scale=float(args.unit_scale),
    )


if __name__ == "__main__":
    main()
