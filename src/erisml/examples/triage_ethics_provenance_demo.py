"""
triage_ethics_provenance_demo.py

New demo that extends the canonical triage example with:

1) Fact provenance: show where key facts (e.g., violates_rights) came from
   (rule ID, classifier confidence, evidence snippet, etc.) in the rationale.

2) Counterfactual test: flip one key fact by changing one piece of evidence
   ("remove discrimination") and show the verdict changes as expected.

3) Multi-stakeholder merge: run the same scenario under two stakeholder
   profiles and resolve conflicts transparently.

This file is designed to sit next to erisml/examples/triage_ethics_demo.py and
reuse the same runtime wiring (DEMEProfileV03 -> build_triage_ems_and_governance
-> select_option). See triage_ethics_demo.py for the baseline structure.
"""

from __future__ import annotations

import copy
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

# --- erisml imports (same core set as the existing triage_ethics_demo) ---
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

FACT_EXTRACTOR_VERSION = "prov_extractor_v0.1"


# ---------------------------------------------------------------------------
# Provenance model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactProvenance:
    """Minimal audit payload you can carry alongside EthicalFacts."""

    fact_path: str  # e.g. "rights_and_duties.violates_rights"
    source_type: str  # e.g. "rule", "classifier", "human", "hybrid"
    rule_id: str  # e.g. "GNV-FAIR-001"
    confidence: float  # 0..1
    evidence_snippet: str  # short excerpt
    model_id: str | None = None  # e.g. "discrim_clf_v0.1"
    notes: str | None = None


def _clip(text: str, n: int = 140) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _renormalize(d: Dict[str, float]) -> Dict[str, float]:
    total = sum(float(v) for v in d.values())
    if total <= 0:
        return d
    return {k: float(v) / total for k, v in d.items()}


# ---------------------------------------------------------------------------
# Profile loading + a synthetic second stakeholder
# ---------------------------------------------------------------------------


def load_profile(path: Path) -> DEMEProfileV03:
    data = json.loads(path.read_text(encoding="utf-8"))
    return deme_profile_v03_from_dict(data)


def make_second_stakeholder_profile(base_profile_path: Path) -> DEMEProfileV03:
    """
    Create a second stakeholder profile by cloning the JSON and shifting emphasis
    toward welfare/consequences (so we can demonstrate a transparent conflict).
    """
    data = json.loads(base_profile_path.read_text(encoding="utf-8"))
    data = copy.deepcopy(data)

    data["name"] = (data.get("name") or "Stakeholder") + "-UtilitarianVariant"
    data["stakeholder_label"] = "utilitarian_stakeholder"

    # NOTE: OverrideMode.CONSEQUENCES_FIRST exists in ethical_dialogue_cli_v04.py.
    # If your profile schema only accepts certain strings, adjust this value.
    data["override_mode"] = "consequences_first"

    # Shift DEME dimension weights
    dims = dict(data.get("deme_dimensions", {}))
    dims.update(
        {
            "safety": 0.42,
            "priority_for_vulnerable": 0.02,
            "fairness_equity": 0.08,
            "autonomy_respect": 0.06,
            "privacy_confidentiality": 0.08,
            "rule_following_legality": 0.10,
            "environment_societal": 0.10,
            "trust_relationships": 0.14,
        }
    )
    data["deme_dimensions"] = _renormalize(dims)

    # Shift principlism
    prin = dict(data.get("principlism", {}))
    prin.update(
        {
            "beneficence": 0.50,
            "non_maleficence": 0.30,
            "autonomy": 0.10,
            "justice": 0.10,
        }
    )
    data["principlism"] = _renormalize(prin)

    # Keep hard vetoes on: we want conflict within the allowed set, not over illegal/rights violations.
    return deme_profile_v03_from_dict(data)


# ---------------------------------------------------------------------------
# Evidence -> facts (with provenance)
# ---------------------------------------------------------------------------

_DISCRIM_RX = re.compile(
    r"\b(race|ethnicity|gender|religion|protected attribute|protected class)\b", re.I
)
_POLICY_VIOLATION_RX = re.compile(
    r"\b(breach|violat(e|es|ed)|noncompliant|against policy)\b", re.I
)
_CONSENT_RX = re.compile(r"\b(without consent|no consent|coercion|forced)\b", re.I)


def _discrimination_classifier_stub(text: str) -> Tuple[bool, float, str]:
    """
    A deterministic stand-in for a fairness classifier. Replace with your real model call.
    Returns: (is_discrimination, confidence, matched_snippet)
    """
    m = _DISCRIM_RX.search(text or "")
    if not m:
        return False, 0.08, ""
    # "confidence" for demo purposes
    return True, 0.93, m.group(0)


def extract_rights_and_fairness_facts(
    evidence_text: str,
) -> Tuple[RightsAndDuties, JusticeAndFairness, Dict[str, FactProvenance]]:
    """
    Extract a couple of key facts from evidence_text and return provenance entries
    that explain *why* those facts were set.

    The specific rule IDs are placeholders (demonstration); swap them for your internal IDs.
    """
    prov: Dict[str, FactProvenance] = {}

    is_discrim, conf, snippet = _discrimination_classifier_stub(evidence_text)

    # Fact 1: discrimination on protected attributes
    fact_path_discrim = "justice_and_fairness.discriminates_on_protected_attr"
    prov[fact_path_discrim] = FactProvenance(
        fact_path=fact_path_discrim,
        source_type="classifier",
        rule_id="GNV-FAIR-001",
        confidence=conf if is_discrim else (1.0 - conf),
        evidence_snippet=_clip(evidence_text),
        model_id="discrim_clf_stub_v0.1",
        notes=(
            f"Matched token='{snippet}'"
            if snippet
            else "No protected-attr token match."
        ),
    )

    # Fact 2: explicit policy breach (optional)
    violates_policy = bool(_POLICY_VIOLATION_RX.search(evidence_text or ""))
    fact_path_rule = "rights_and_duties.violates_explicit_rule"
    prov[fact_path_rule] = FactProvenance(
        fact_path=fact_path_rule,
        source_type="rule",
        rule_id="INST-POL-007",
        confidence=0.80 if violates_policy else 0.80,
        evidence_snippet=_clip(evidence_text),
        model_id=None,
        notes="Keyword-based policy breach detector (demo).",
    )

    # Fact 3: consent violation (optional)
    no_consent = bool(_CONSENT_RX.search(evidence_text or ""))
    fact_path_consent = "rights_and_duties.has_valid_consent"
    prov[fact_path_consent] = FactProvenance(
        fact_path=fact_path_consent,
        source_type="rule",
        rule_id="CONSENT-001",
        confidence=0.85,
        evidence_snippet=_clip(evidence_text),
        model_id=None,
        notes="Keyword-based consent detector (demo).",
    )

    # *Missing axiom / spec note*
    # We intentionally *derive* violates_rights from a small set of "rights triggers"
    # (here: discrimination OR explicit policy breach OR no consent), rather than setting
    # it by hand. This makes the provenance story coherent.
    violates_rights = bool(is_discrim or violates_policy or no_consent)
    fact_path_rights = "rights_and_duties.violates_rights"
    trigger_list = []
    if is_discrim:
        trigger_list.append("protected-attr discrimination")
    if violates_policy:
        trigger_list.append("explicit policy breach")
    if no_consent:
        trigger_list.append("no valid consent")
    prov[fact_path_rights] = FactProvenance(
        fact_path=fact_path_rights,
        source_type="hybrid",
        rule_id="RIGHTS-DERIVE-010",
        confidence=min(0.95, 0.55 + 0.20 * len(trigger_list)),
        evidence_snippet=_clip(evidence_text),
        model_id=None,
        notes=(
            ("Derived from: " + ", ".join(trigger_list))
            if trigger_list
            else "No trigger matched."
        ),
    )

    rights = RightsAndDuties(
        violates_rights=violates_rights,
        has_valid_consent=(not no_consent),
        violates_explicit_rule=violates_policy,
        role_duty_conflict=False,
    )
    fairness = JusticeAndFairness(
        discriminates_on_protected_attr=is_discrim,
        prioritizes_most_disadvantaged=False,
        distributive_pattern="other",
        exploits_vulnerable_population=False,
        exacerbates_power_imbalance=False,
    )
    return rights, fairness, prov


def make_demo_facts_with_provenance(
    evidence_by_option: Dict[str, str],
) -> Tuple[Dict[str, EthicalFacts], Dict[str, Dict[str, FactProvenance]]]:
    """
    Construct EthicalFacts for options A/B manually, and for option C using a tiny
    "extractor" that also emits provenance.
    """
    provenance_by_option: Dict[str, Dict[str, FactProvenance]] = {}

    # Option A: lower overall benefit than B, but urgent and most disadvantaged (tradeoff case).
    opt_a = EthicalFacts(
        option_id="allocate_to_patient_A",
        consequences=Consequences(
            expected_benefit=0.70, expected_harm=0.30, urgency=0.95, affected_count=1
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
            uncertainty_level=0.30, evidence_quality="high", novel_situation_flag=False
        ),
    )
    provenance_by_option[opt_a.option_id] = {
        "rights_and_duties.violates_rights": FactProvenance(
            fact_path="rights_and_duties.violates_rights",
            source_type="human",
            rule_id="MANUAL-SCENARIO",
            confidence=0.90,
            evidence_snippet=_clip(
                evidence_by_option.get(opt_a.option_id, "manual scenario")
            ),
            model_id=None,
            notes="Scenario author asserts no rights violations.",
        )
    }

    # Option B: higher benefit, less urgent, not most disadvantaged.
    opt_b = EthicalFacts(
        option_id="allocate_to_patient_B",
        consequences=Consequences(
            expected_benefit=0.98, expected_harm=0.10, urgency=0.55, affected_count=1
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
    provenance_by_option[opt_b.option_id] = {
        "rights_and_duties.violates_rights": FactProvenance(
            fact_path="rights_and_duties.violates_rights",
            source_type="human",
            rule_id="MANUAL-SCENARIO",
            confidence=0.90,
            evidence_snippet=_clip(
                evidence_by_option.get(opt_b.option_id, "manual scenario")
            ),
            model_id=None,
            notes="Scenario author asserts no rights violations.",
        )
    }

    # Option C: build rights/fairness facts from evidence and keep other blocks reasonable.
    ev_c = evidence_by_option.get("allocate_to_patient_C", "")
    rights, fairness, prov = extract_rights_and_fairness_facts(ev_c)

    opt_c = EthicalFacts(
        option_id="allocate_to_patient_C",
        consequences=Consequences(
            expected_benefit=0.85, expected_harm=0.30, urgency=0.80, affected_count=1
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
    provenance_by_option[opt_c.option_id] = prov

    return {
        opt_a.option_id: opt_a,
        opt_b.option_id: opt_b,
        opt_c.option_id: opt_c,
    }, provenance_by_option


# ---------------------------------------------------------------------------
# Printing helpers (provenance-aware)
# ---------------------------------------------------------------------------


def _lookup_prov(
    prov: Dict[str, FactProvenance], fact_name_or_path: str
) -> FactProvenance | None:
    """
    Map an EM-reported fact token like 'violates_rights' to our provenance keys
    like 'rights_and_duties.violates_rights'.
    """
    if fact_name_or_path in prov:
        return prov[fact_name_or_path]

    # Try suffix match (e.g. "violates_rights" -> "...violates_rights")
    for k, v in prov.items():
        if k.endswith("." + fact_name_or_path) or k == fact_name_or_path:
            return v
    return None


_FACT_TOKEN_RX = re.compile(r"•\s*([a-zA-Z0-9_\.]+)\s*=\s*(True|False)", re.I)


def print_option_results_with_provenance(
    option_id: str,
    judgements: List[EthicalJudgement],
    aggregate: EthicalJudgement,
    provenance_for_option: Dict[str, FactProvenance],
) -> None:
    print(f"\n--- Option: {option_id} ---")
    for j in judgements:
        print(
            f"[EM={j.em_name:<24}] verdict={j.verdict:<15} score={j.normative_score:.3f}"
        )
        for reason in j.reasons:
            print(f"    - {reason}")

            # If the reason includes bullet facts, attach provenance.
            # (This is intentionally lightweight: it doesn't require changing EM implementations.)
            m = _FACT_TOKEN_RX.search(reason)
            if m:
                fact_token = m.group(1)
                p = _lookup_prov(provenance_for_option, fact_token)
                if p is not None:
                    print(
                        "      provenance: "
                        f"{p.fact_path} ← {p.source_type} "
                        f"(rule_id={p.rule_id}, conf={p.confidence:.2f}"
                        + (f", model={p.model_id}" if p.model_id else "")
                        + f")"
                    )
                    if p.notes:
                        print(f"        notes: {p.notes}")
                    if p.evidence_snippet:
                        print(f'        evidence: "{p.evidence_snippet}"')

    print(
        f"[AGG governance] verdict={aggregate.verdict:<15} score={aggregate.normative_score:.3f}"
    )

    meta = aggregate.metadata or {}
    forbidden = meta.get("forbidden", False)
    forbidden_by = meta.get("forbidden_by", [])
    vetoed_by = meta.get("vetoed_by", [])

    if forbidden:
        print("    * Marked FORBIDDEN by governance.")
    if forbidden_by:
        print("    * Forbidden by EM(s): " + ", ".join(sorted(set(forbidden_by))))
    if vetoed_by:
        print("    * Veto EM(s): " + ", ".join(sorted(set(vetoed_by))))


# ---------------------------------------------------------------------------
# Core eval routine (profile -> EMs -> select_option)
# ---------------------------------------------------------------------------


def evaluate_under_profile(
    profile: DEMEProfileV03,
    facts_by_option: Dict[str, EthicalFacts],
) -> Tuple[DecisionOutcome, Dict[str, List[EthicalJudgement]]]:
    triage_em, rights_em, gov_cfg = build_triage_ems_and_governance(profile)

    ems = {
        "case_study_1_triage": triage_em,
        "rights_first_compliance": rights_em,
    }

    # Add base EMs requested by governance config (often geneva_baseline).
    for base_id in getattr(gov_cfg, "base_em_ids", []):
        em_cls = EM_REGISTRY.get(base_id)
        if em_cls is None:
            print(f"[warn] base_em_id '{base_id}' not found in EM_REGISTRY.")
            continue
        ems[base_id] = em_cls()

    all_judgements: Dict[str, List[EthicalJudgement]] = defaultdict(list)

    for oid, facts in facts_by_option.items():
        for _, em in ems.items():
            all_judgements[oid].append(em.judge(facts))

    decision: DecisionOutcome = select_option(all_judgements, gov_cfg)
    return decision, all_judgements


# ---------------------------------------------------------------------------
# Multi-stakeholder merge (transparent)
# ---------------------------------------------------------------------------


def merge_two_stakeholder_decisions(
    decision_a: DecisionOutcome,
    decision_b: DecisionOutcome,
    weights: Tuple[float, float] = (0.5, 0.5),
    stakeholder_names: Tuple[str, str] = ("stakeholder_A", "stakeholder_B"),
) -> str:
    """
    Produce a human-readable merge report and a combined selection.

    Policy (demo):
      - If either stakeholder forbids an option -> combined forbids it.
      - Otherwise, combined_score = wA*scoreA + wB*scoreB.
      - Pick max combined_score.
    """
    w_a, w_b = weights
    name_a, name_b = stakeholder_names

    # Build option universe
    all_option_ids = set(decision_a.aggregated_judgements.keys()) | set(
        decision_b.aggregated_judgements.keys()
    )

    forbidden_union = set(decision_a.forbidden_options) | set(
        decision_b.forbidden_options
    )

    def get_j(dec: DecisionOutcome, oid: str) -> EthicalJudgement | None:
        return dec.aggregated_judgements.get(oid)

    rows = []
    for oid in sorted(all_option_ids):
        ja = get_j(decision_a, oid)
        jb = get_j(decision_b, oid)
        sa = ja.normative_score if ja else 0.0
        sb = jb.normative_score if jb else 0.0
        va = ja.verdict if ja else "missing"
        vb = jb.verdict if jb else "missing"
        combined = w_a * sa + w_b * sb
        rows.append((oid, va, sa, vb, sb, combined, oid in forbidden_union))

    eligible = [r for r in rows if not r[6]]
    selected = max(eligible, key=lambda r: r[5], default=None)

    # Pretty print
    out = []
    out.append("=== Multi-stakeholder merge ===")
    out.append(
        f"Merge policy: forbid if ANY forbids; else combined_score = {w_a:.2f}*{name_a} + {w_b:.2f}*{name_b}"
    )
    out.append("")
    out.append(f"{'option':<24} | {name_a:<14} | {name_b:<14} | combined | status")
    out.append("-" * 78)
    for oid, va, sa, vb, sb, combined, is_forbidden in rows:
        status = "FORBIDDEN" if is_forbidden else "eligible"
        out.append(
            f"{oid:<24} | {va:>7} {sa:>5.3f} | {vb:>7} {sb:>5.3f} | {combined:>7.3f} | {status}"
        )

    out.append("")
    if selected is None:
        out.append("Combined outcome: no eligible option.")
    else:
        out.append(
            f"Combined outcome: SELECT '{selected[0]}' (combined_score={selected[5]:.3f})"
        )
        out.append(
            "Rationale: selected the eligible option maximizing the weighted combined score;"
        )
        out.append("          forbiddances are treated as non-negotiable in this demo.")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Demo runner
# ---------------------------------------------------------------------------


def run_demo(profile_path: Path) -> None:
    print(
        "=== Triage Ethics Demo: Provenance + Counterfactual + Multi-stakeholder ===\n"
    )
    print(f"Extractor version: {FACT_EXTRACTOR_VERSION}\n")

    profile_1 = load_profile(profile_path)
    profile_2 = make_second_stakeholder_profile(profile_path)

    print(
        f"Loaded profile #1: {profile_1.name} (override_mode={profile_1.override_mode})"
    )
    print(
        f"Loaded profile #2: {profile_2.name} (override_mode={profile_2.override_mode})\n"
    )

    # ------------------------------------------------------------------
    # Evidence packs (baseline vs counterfactual)
    # ------------------------------------------------------------------
    evidence_baseline = {
        "allocate_to_patient_A": "Manual scenario: urgent disadvantaged patient; no discrimination, consent OK.",
        "allocate_to_patient_B": "Manual scenario: higher expected benefit; no discrimination, consent OK.",
        "allocate_to_patient_C": (
            "Nurse note: allocate triage slot based on race (protected attribute) rather than clinical need. "
            "No other policy breach is recorded."
        ),
    }
    evidence_counterfactual = copy.deepcopy(evidence_baseline)
    evidence_counterfactual["allocate_to_patient_C"] = (
        "Counterfactual note: allocate triage slot based on clinical urgency and expected benefit only. "
        "No protected-attribute discrimination is recorded."
    )

    # ------------------------------------------------------------------
    # 1) Fact provenance demo (baseline evidence)
    # ------------------------------------------------------------------
    print("=== Demo 1: Fact provenance in rationale (baseline evidence) ===")
    facts_1, prov_1 = make_demo_facts_with_provenance(evidence_baseline)
    decision_1, all_judgements_1 = evaluate_under_profile(profile_1, facts_1)

    for oid in facts_1.keys():
        agg = decision_1.aggregated_judgements.get(oid)
        if not agg:
            continue
        print_option_results_with_provenance(
            oid,
            all_judgements_1.get(oid, []),
            agg,
            prov_1.get(oid, {}),
        )

    print("\nGovernance outcome (profile #1):")
    print(f"  selected_option_id: {decision_1.selected_option_id}")
    print(f"  ranked_options:     {decision_1.ranked_options}")
    print(f"  forbidden_options:  {decision_1.forbidden_options}")
    print(f"  rationale:          {decision_1.rationale}")

    # ------------------------------------------------------------------
    # 2) Counterfactual demo (remove discrimination from option C evidence)
    # ------------------------------------------------------------------
    print("\n=== Demo 2: Counterfactual test (flip one key fact) ===")
    facts_cf, prov_cf = make_demo_facts_with_provenance(evidence_counterfactual)
    decision_cf, _ = evaluate_under_profile(profile_1, facts_cf)

    oid = "allocate_to_patient_C"
    before = decision_1.aggregated_judgements.get(oid)
    after = decision_cf.aggregated_judgements.get(oid)

    print(f"Counterfactual target: {oid}")
    if before and after:
        print(
            f"  before: verdict={before.verdict:<15} score={before.normative_score:.3f}"
        )
        print(
            f"  after:  verdict={after.verdict:<15} score={after.normative_score:.3f}"
        )
    else:
        print(
            "  [warn] could not find aggregated judgements for option C in one of the runs."
        )

    # Show the exact fact flips (from provenance)
    p_before = prov_1.get(oid, {})
    p_after = prov_cf.get(oid, {})
    for key in [
        "justice_and_fairness.discriminates_on_protected_attr",
        "rights_and_duties.violates_rights",
    ]:
        b = p_before.get(key)
        a = p_after.get(key)
        if b and a:
            print(f"  flip: {key}")
            print(f'        baseline evidence:      "{b.evidence_snippet}"')
            print(f'        counterfactual evidence: "{a.evidence_snippet}"')

    # ------------------------------------------------------------------
    # 3) Multi-stakeholder merge demo (same baseline scenario)
    # ------------------------------------------------------------------
    print("\n=== Demo 3: Multi-stakeholder merge ===")
    decision_s1, _ = evaluate_under_profile(profile_1, facts_1)
    decision_s2, _ = evaluate_under_profile(profile_2, facts_1)

    print("\nStakeholder #1 outcome:")
    print(f"  selected_option_id: {decision_s1.selected_option_id}")
    print(f"  ranked_options:     {decision_s1.ranked_options}")
    print(f"  forbidden_options:  {decision_s1.forbidden_options}")

    print("\nStakeholder #2 outcome:")
    print(f"  selected_option_id: {decision_s2.selected_option_id}")
    print(f"  ranked_options:     {decision_s2.ranked_options}")
    print(f"  forbidden_options:  {decision_s2.forbidden_options}")

    merge_report = merge_two_stakeholder_decisions(
        decision_s1,
        decision_s2,
        weights=(0.55, 0.45),
        stakeholder_names=(profile_1.name, profile_2.name),
    )
    print()
    print(merge_report)


def main() -> None:
    profile_path = Path("deme_profile_v03.json")
    if not profile_path.exists():
        raise SystemExit(
            "No deme_profile_v03.json found in current directory.\n"
            "Copy/symlink your profile JSON here, then run:\n"
            "  python -m erisml.examples.triage_ethics_provenance_demo"
        )
    run_demo(profile_path)


if __name__ == "__main__":
    main()
