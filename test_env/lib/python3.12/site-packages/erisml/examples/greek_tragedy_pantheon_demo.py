"""
greek_tragedy_pantheon_demo.py

A "pantheon" compilation demo: a sequence of compact Greek-tragedy-inspired
mini-scenarios that exercise each EthicalFacts domain block in turn.

Designed to mirror the triage demos:
  - loads a DEMEProfileV03 (deme_profile_v03.json by default),
  - instantiates EMs via build_triage_ems_and_governance(profile) plus base EMs,
  - evaluates 3 options per scenario using EthicalFacts v0.2 blocks,
  - aggregates via select_option(...) and prints a human-auditable rationale,
  - (optional) runs a second stakeholder profile and shows a transparent merge.

Usage (from repo root, after copying this file to erisml/examples/):

  python -m erisml.examples.greek_tragedy_pantheon_demo
  python -m erisml.examples.greek_tragedy_pantheon_demo --multi-stakeholder
  python -m erisml.examples.greek_tragedy_pantheon_demo --case antigone

Notes:
- These are *ethical structure demos*, not historical scholarship.
- Names are from public-domain mythology/tragedy and used as narrative scaffolding.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# --- erisml imports (same core set as triage_ethics_demo) ---
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
from erisml.ethics.modules.greek_tragedy_tragic_conflict_em import TragicConflictEM


# ---------------------------------------------------------------------------
# Provenance helpers (lightweight, demo-only)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactProvenance:
    """Audit-friendly provenance record for a single fact coordinate."""

    fact_path: str  # e.g., "rights_and_duties.violates_explicit_rule"
    source_type: str  # "rule" | "classifier" | "hybrid" | "human_attestation"
    rule_id: str
    confidence: float
    model_id: Optional[str] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None


def _pretty_prov(p: FactProvenance) -> List[str]:
    parts: List[str] = []
    head = f"provenance: {p.fact_path} \u2190 {p.source_type} (rule_id={p.rule_id}, conf={p.confidence:.2f}"
    if p.model_id:
        head += f", model={p.model_id}"
    head += ")"
    parts.append(head)
    if p.notes:
        parts.append(f"  notes: {p.notes}")
    if p.evidence:
        ev = p.evidence.strip().replace("\n", " ")
        if len(ev) > 200:
            ev = ev[:197] + "..."
        parts.append(f'  evidence: "{ev}"')
    return parts


def _fact_key_to_path(k: str) -> Optional[str]:
    """Map bullet fact keys (from EM reasons) to full paths used in provenance dict."""
    # The built-in EMs typically emit bullet facts like:
    #   "• violates_rights = True"
    #   "• violates_explicit_rule = True"
    #   "• discriminates_on_protected_attr = True"
    k = k.strip()
    if k == "violates_rights":
        return "rights_and_duties.violates_rights"
    if k == "violates_explicit_rule":
        return "rights_and_duties.violates_explicit_rule"
    if k == "discriminates_on_protected_attr":
        return "justice_and_fairness.discriminates_on_protected_attr"
    if k == "has_valid_consent":
        return "rights_and_duties.has_valid_consent"
    if k == "coercion_or_undue_influence":
        return "autonomy_and_agency.coercion_or_undue_influence"
    # Add more mappings as your EMs emit more bullet facts.
    return None


# ---------------------------------------------------------------------------
# Profile + multi-stakeholder helper
# ---------------------------------------------------------------------------


def load_profile(path: Path) -> DEMEProfileV03:
    data = json.loads(path.read_text(encoding="utf-8"))
    return deme_profile_v03_from_dict(data)


def make_second_stakeholder_profile(base_path: Path) -> DEMEProfileV03:
    """
    Create a simple utilitarian-tilted variant of the same profile:
      - override_mode -> consequences_first
      - mild reweight toward beneficence/non-maleficence
    """
    data = json.loads(base_path.read_text(encoding="utf-8"))

    data["name"] = f"{data.get('name', 'Profile')}-UtilitarianVariant"
    data["override_mode"] = "consequences_first"

    # These keys match the v03 dialogue outputs used in the triage provenance demo.
    dims = data.get("dimension_weights", {})
    dims.update(
        {
            "beneficence": max(dims.get("beneficence", 0.25), 0.40),
            "non_maleficence": max(dims.get("non_maleficence", 0.25), 0.35),
            "justice": min(dims.get("justice", 0.25), 0.15),
            "autonomy": min(dims.get("autonomy", 0.25), 0.10),
        }
    )
    data["dimension_weights"] = dims

    prin = data.get("principlism_weights", {})
    prin.update(
        {
            "beneficence": 0.50,
            "non_maleficence": 0.30,
            "autonomy": 0.10,
            "justice": 0.10,
        }
    )
    data["principlism_weights"] = prin

    return deme_profile_v03_from_dict(data)


# ---------------------------------------------------------------------------
# Case definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PantheonOption:
    option_id: str
    label: str
    facts: EthicalFacts
    evidence: str
    provenance: Dict[str, FactProvenance]  # keyed by fact_path


@dataclass(frozen=True)
class PantheonCase:
    case_id: str
    title: str
    spotlight_domain: str
    scenario: str
    spotlight_fields: List[str]  # human display, not used by EMs
    options: List[PantheonOption]


def _base_blocks(
    *,
    expected_benefit: float,
    expected_harm: float,
    urgency: float,
    affected_count: int = 1,
    violates_rights: bool = False,
    has_valid_consent: bool = True,
    violates_explicit_rule: bool = False,
    role_duty_conflict: bool = False,
    discriminates_on_protected_attr: bool = False,
    prioritizes_most_disadvantaged: bool = False,
    distributive_pattern: str = "other",
    exploits_vulnerable_population: bool = False,
    exacerbates_power_imbalance: bool = False,
    has_meaningful_choice: bool = True,
    coercion_or_undue_influence: bool = False,
    can_withdraw_without_penalty: bool = True,
    manipulative_design_present: bool = False,
    privacy_invasion_level: float = 0.1,
    data_minimization_respected: bool = True,
    secondary_use_without_consent: bool = False,
    data_retention_excessive: bool = False,
    reidentification_risk: float = 0.1,
    environmental_harm: float = 0.1,
    long_term_societal_risk: float = 0.1,
    benefits_to_future_generations: float = 0.1,
    burden_on_vulnerable_groups: float = 0.1,
    followed_approved_procedure: bool = True,
    stakeholders_consulted: bool = True,
    decision_explainable_to_public: bool = True,
    contestation_available: bool = True,
    uncertainty_level: float = 0.2,
    evidence_quality: str = "high",
    novel_situation_flag: bool = False,
) -> Dict[str, object]:
    """Create a consistent EthicalFacts payload using the v0.2 schema blocks."""
    return dict(
        consequences=Consequences(
            expected_benefit=expected_benefit,
            expected_harm=expected_harm,
            urgency=urgency,
            affected_count=affected_count,
        ),
        rights_and_duties=RightsAndDuties(
            violates_rights=violates_rights,
            has_valid_consent=has_valid_consent,
            violates_explicit_rule=violates_explicit_rule,
            role_duty_conflict=role_duty_conflict,
        ),
        justice_and_fairness=JusticeAndFairness(
            discriminates_on_protected_attr=discriminates_on_protected_attr,
            prioritizes_most_disadvantaged=prioritizes_most_disadvantaged,
            distributive_pattern=distributive_pattern,
            exploits_vulnerable_population=exploits_vulnerable_population,
            exacerbates_power_imbalance=exacerbates_power_imbalance,
        ),
        autonomy_and_agency=AutonomyAndAgency(
            has_meaningful_choice=has_meaningful_choice,
            coercion_or_undue_influence=coercion_or_undue_influence,
            can_withdraw_without_penalty=can_withdraw_without_penalty,
            manipulative_design_present=manipulative_design_present,
        ),
        privacy_and_data=PrivacyAndDataGovernance(
            privacy_invasion_level=privacy_invasion_level,
            data_minimization_respected=data_minimization_respected,
            secondary_use_without_consent=secondary_use_without_consent,
            data_retention_excessive=data_retention_excessive,
            reidentification_risk=reidentification_risk,
        ),
        societal_and_environmental=SocietalAndEnvironmental(
            environmental_harm=environmental_harm,
            long_term_societal_risk=long_term_societal_risk,
            benefits_to_future_generations=benefits_to_future_generations,
            burden_on_vulnerable_groups=burden_on_vulnerable_groups,
        ),
        procedural_and_legitimacy=ProceduralAndLegitimacy(
            followed_approved_procedure=followed_approved_procedure,
            stakeholders_consulted=stakeholders_consulted,
            decision_explainable_to_public=decision_explainable_to_public,
            contestation_available=contestation_available,
        ),
        epistemic_status=EpistemicStatus(
            uncertainty_level=uncertainty_level,
            evidence_quality=evidence_quality,
            novel_situation_flag=novel_situation_flag,
        ),
    )


def make_pantheon_cases() -> List[PantheonCase]:
    cases: List[PantheonCase] = []

    # -----------------------------------------------------------------------
    # 1) CONSEQUENCES (Agamemnon at Aulis – fleet stalled)
    # -----------------------------------------------------------------------
    scenario = (
        "A fleet is stalled at Aulis. Leaders debate whether to sail immediately through unsafe conditions, "
        "delay to reduce harm, or abandon the campaign entirely. The demo spotlights Consequences: "
        "expected benefit, expected harm, and urgency."
    )
    opt1_ev = "Navigator report: immediate departure faces severe storm risk; success is plausible but losses likely."
    opt2_ev = "Navigator report: delay 48 hours yields safer winds with moderate strategic cost."
    opt3_ev = "Council report: abandoning the campaign avoids losses but forfeits strategic objectives."

    options = [
        PantheonOption(
            option_id="aulis_sail_now",
            label="Sail immediately (high urgency / high harm risk)",
            facts=EthicalFacts(
                option_id="aulis_sail_now",
                **_base_blocks(
                    expected_benefit=0.78,
                    expected_harm=0.72,
                    urgency=0.92,
                    evidence_quality="medium",
                    uncertainty_level=0.35,
                ),
            ),
            evidence=opt1_ev,
            provenance={},
        ),
        PantheonOption(
            option_id="aulis_delay",
            label="Delay for safer winds (moderate urgency / low harm)",
            facts=EthicalFacts(
                option_id="aulis_delay",
                **_base_blocks(
                    expected_benefit=0.65,
                    expected_harm=0.20,
                    urgency=0.55,
                    evidence_quality="high",
                    uncertainty_level=0.20,
                ),
            ),
            evidence=opt2_ev,
            provenance={},
        ),
        PantheonOption(
            option_id="aulis_abort",
            label="Abandon campaign (low harm / low benefit)",
            facts=EthicalFacts(
                option_id="aulis_abort",
                **_base_blocks(
                    expected_benefit=0.20,
                    expected_harm=0.10,
                    urgency=0.15,
                    evidence_quality="high",
                    uncertainty_level=0.10,
                ),
            ),
            evidence=opt3_ev,
            provenance={},
        ),
    ]
    cases.append(
        PantheonCase(
            case_id="aulis",
            title="Aulis: The Stalled Fleet",
            spotlight_domain="Consequences",
            scenario=scenario,
            spotlight_fields=[
                "consequences.expected_benefit",
                "consequences.expected_harm",
                "consequences.urgency",
            ],
            options=options,
        )
    )

    # -----------------------------------------------------------------------
    # 2) RIGHTS & DUTIES (Antigone – burial edict)
    # -----------------------------------------------------------------------
    scenario = (
        "A ruler issues an edict forbidding burial rites for a declared traitor. One party considers defying the edict, "
        "another considers compliance, and a third seeks a lawful exception. Spotlight: Rights & Duties, explicit rules."
    )
    ev_defy = "Royal edict THEBES-LAW-001 explicitly forbids burial rites; defiance is punishable by death."
    ev_obey = "Royal edict THEBES-LAW-001 is in force; compliance avoids punishment but denies rites."
    ev_pet = "Thebes procedure PROC-EXC-002 allows petitions for exception when public order can be maintained."

    options = [
        PantheonOption(
            option_id="antigone_defy",
            label="Defy the edict and perform burial",
            facts=EthicalFacts(
                option_id="antigone_defy",
                **_base_blocks(
                    expected_benefit=0.55,
                    expected_harm=0.60,
                    urgency=0.75,
                    violates_rights=False,
                    violates_explicit_rule=True,
                    followed_approved_procedure=False,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    evidence_quality="high",
                    uncertainty_level=0.15,
                ),
            ),
            evidence=ev_defy,
            provenance={
                "rights_and_duties.violates_explicit_rule": FactProvenance(
                    fact_path="rights_and_duties.violates_explicit_rule",
                    source_type="rule",
                    rule_id="THEBES-LAW-001",
                    confidence=0.95,
                    evidence=ev_defy,
                    notes="Direct match: edict forbids burial rites.",
                )
            },
        ),
        PantheonOption(
            option_id="antigone_obey",
            label="Obey the edict (no burial)",
            facts=EthicalFacts(
                option_id="antigone_obey",
                **_base_blocks(
                    expected_benefit=0.40,
                    expected_harm=0.25,
                    urgency=0.40,
                    violates_rights=False,
                    violates_explicit_rule=False,
                    followed_approved_procedure=True,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="medium",
                    uncertainty_level=0.30,
                ),
            ),
            evidence=ev_obey,
            provenance={},
        ),
        PantheonOption(
            option_id="antigone_petition",
            label="Petition for exception (procedure-first)",
            facts=EthicalFacts(
                option_id="antigone_petition",
                **_base_blocks(
                    expected_benefit=0.60,
                    expected_harm=0.20,
                    urgency=0.55,
                    violates_rights=False,
                    violates_explicit_rule=False,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="high",
                    uncertainty_level=0.20,
                ),
            ),
            evidence=ev_pet,
            provenance={
                "procedural_and_legitimacy.followed_approved_procedure": FactProvenance(
                    fact_path="procedural_and_legitimacy.followed_approved_procedure",
                    source_type="rule",
                    rule_id="PROC-EXC-002",
                    confidence=0.85,
                    evidence=ev_pet,
                    notes="Documented petition procedure exists.",
                )
            },
        ),
    ]
    cases.append(
        PantheonCase(
            case_id="antigone",
            title="Antigone: Edict vs Rite",
            spotlight_domain="Rights & Duties",
            scenario=scenario,
            spotlight_fields=[
                "rights_and_duties.violates_explicit_rule",
                "procedural_and_legitimacy.followed_approved_procedure",
            ],
            options=options,
        )
    )

    # -----------------------------------------------------------------------
    # 3) JUSTICE & FAIRNESS (Ajax – contested honors)
    # -----------------------------------------------------------------------
    scenario = (
        "A council must award a prize of honor. Options include a merit-based award, a politically motivated award, "
        "or a public contest with transparent criteria. Spotlight: Justice & Fairness."
    )
    ev_pol = "Council minutes: selection influenced by elite faction pressure and fear of dissent."
    ev_mer = "Council minutes: selection based on publicly stated merit criteria and consistent past practice."
    ev_con = (
        "Proposal: hold a public contest with recorded votes and an appeal channel."
    )

    options = [
        PantheonOption(
            option_id="ajax_merit_award",
            label="Award by merit criteria",
            facts=EthicalFacts(
                option_id="ajax_merit_award",
                **_base_blocks(
                    expected_benefit=0.65,
                    expected_harm=0.20,
                    urgency=0.55,
                    discriminates_on_protected_attr=False,
                    distributive_pattern="merit",
                    exploits_vulnerable_population=False,
                    exacerbates_power_imbalance=False,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="high",
                    uncertainty_level=0.15,
                ),
            ),
            evidence=ev_mer,
            provenance={},
        ),
        PantheonOption(
            option_id="ajax_political_award",
            label="Award by factional politics (power imbalance)",
            facts=EthicalFacts(
                option_id="ajax_political_award",
                **_base_blocks(
                    expected_benefit=0.50,
                    expected_harm=0.35,
                    urgency=0.65,
                    discriminates_on_protected_attr=False,
                    distributive_pattern="arbitrary",
                    exploits_vulnerable_population=True,
                    exacerbates_power_imbalance=True,
                    followed_approved_procedure=False,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    evidence_quality="medium",
                    uncertainty_level=0.30,
                ),
            ),
            evidence=ev_pol,
            provenance={},
        ),
        PantheonOption(
            option_id="ajax_public_contest",
            label="Hold a public contest + appeal",
            facts=EthicalFacts(
                option_id="ajax_public_contest",
                **_base_blocks(
                    expected_benefit=0.60,
                    expected_harm=0.25,
                    urgency=0.45,
                    discriminates_on_protected_attr=False,
                    distributive_pattern="procedural",
                    exploits_vulnerable_population=False,
                    exacerbates_power_imbalance=False,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="high",
                    uncertainty_level=0.20,
                ),
            ),
            evidence=ev_con,
            provenance={
                "procedural_and_legitimacy.contestation_available": FactProvenance(
                    fact_path="procedural_and_legitimacy.contestation_available",
                    source_type="rule",
                    rule_id="COUNCIL-APPEAL-004",
                    confidence=0.75,
                    evidence=ev_con,
                    notes="Appeal channel stipulated in contest proposal.",
                )
            },
        ),
    ]
    cases.append(
        PantheonCase(
            case_id="ajax",
            title="Ajax: The Prize of Honor",
            spotlight_domain="Justice & Fairness",
            scenario=scenario,
            spotlight_fields=[
                "justice_and_fairness.distributive_pattern",
                "justice_and_fairness.exacerbates_power_imbalance",
            ],
            options=options,
        )
    )

    # -----------------------------------------------------------------------
    # 4) AUTONOMY & AGENCY (Iphigenia – consent vs coercion)
    # -----------------------------------------------------------------------
    scenario = (
        "A leader considers a plan that would seriously harm one individual to benefit many. "
        "The spotlight is Autonomy: meaningful choice and coercion, plus explicit consent constraints."
    )
    ev_coerce = "Witness report: consent obtained via deception and threat; withdrawal would be punished."
    ev_seek = "Record: full disclosure, option to refuse without penalty, independent advocate present."
    ev_alt = "Alternative plan: stand down / renegotiate mission to avoid harming the individual."

    options = [
        PantheonOption(
            option_id="iphigenia_coerce",
            label="Proceed with coerced plan (no valid consent)",
            facts=EthicalFacts(
                option_id="iphigenia_coerce",
                **_base_blocks(
                    expected_benefit=0.80,
                    expected_harm=0.79,  # keep just below the demo forbid_high_expected_harm threshold in many profiles
                    urgency=0.85,
                    violates_rights=True,
                    has_valid_consent=False,
                    violates_explicit_rule=True,
                    has_meaningful_choice=False,
                    coercion_or_undue_influence=True,
                    can_withdraw_without_penalty=False,
                    manipulative_design_present=True,
                    followed_approved_procedure=False,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    evidence_quality="high",
                    uncertainty_level=0.10,
                ),
            ),
            evidence=ev_coerce,
            provenance={
                "autonomy_and_agency.coercion_or_undue_influence": FactProvenance(
                    fact_path="autonomy_and_agency.coercion_or_undue_influence",
                    source_type="human_attestation",
                    rule_id="CONSENT-AUDIT-001",
                    confidence=0.90,
                    evidence=ev_coerce,
                    notes="Independent witness attests deception/threat.",
                ),
                "rights_and_duties.has_valid_consent": FactProvenance(
                    fact_path="rights_and_duties.has_valid_consent",
                    source_type="hybrid",
                    rule_id="CONSENT-VALID-002",
                    confidence=0.88,
                    evidence=ev_coerce,
                    notes="Derived: coercion implies invalid consent.",
                ),
            },
        ),
        PantheonOption(
            option_id="iphigenia_seek_consent",
            label="Seek informed consent with refusal option",
            facts=EthicalFacts(
                option_id="iphigenia_seek_consent",
                **_base_blocks(
                    expected_benefit=0.70,
                    expected_harm=0.79,
                    urgency=0.65,
                    violates_rights=False,
                    has_valid_consent=True,
                    violates_explicit_rule=False,
                    has_meaningful_choice=True,
                    coercion_or_undue_influence=False,
                    can_withdraw_without_penalty=True,
                    manipulative_design_present=False,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="medium",
                    uncertainty_level=0.35,
                ),
            ),
            evidence=ev_seek,
            provenance={},
        ),
        PantheonOption(
            option_id="iphigenia_alternative",
            label="Choose the alternative that avoids harm",
            facts=EthicalFacts(
                option_id="iphigenia_alternative",
                **_base_blocks(
                    expected_benefit=0.45,
                    expected_harm=0.15,
                    urgency=0.40,
                    violates_rights=False,
                    has_valid_consent=True,
                    violates_explicit_rule=False,
                    has_meaningful_choice=True,
                    coercion_or_undue_influence=False,
                    can_withdraw_without_penalty=True,
                    manipulative_design_present=False,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="high",
                    uncertainty_level=0.20,
                ),
            ),
            evidence=ev_alt,
            provenance={},
        ),
    ]
    cases.append(
        PantheonCase(
            case_id="iphigenia",
            title="Iphigenia: Consent Under Pressure",
            spotlight_domain="Autonomy & Agency",
            scenario=scenario,
            spotlight_fields=[
                "autonomy_and_agency.coercion_or_undue_influence",
                "rights_and_duties.has_valid_consent",
            ],
            options=options,
        )
    )

    # -----------------------------------------------------------------------
    # 5) PRIVACY & DATA GOVERNANCE (Hippolytus – accusation letter)
    # -----------------------------------------------------------------------
    scenario = (
        "A private accusation letter exists. Options include publishing it widely, sharing it only with a neutral adjudicator, "
        "or destroying it (protecting privacy but undermining accountability). Spotlight: Privacy & Data Governance."
    )
    ev_publish = "Letter contains intimate allegations; publication would irreversibly expose private details."
    ev_conf = "Confidential channel: neutral adjudicator can review under seal; minimal disclosure."
    ev_destroy = "Destroying the letter prevents privacy harm but eliminates evidence and blocks contestation."

    options = [
        PantheonOption(
            option_id="hippolytus_publish",
            label="Publish the letter publicly (maximum exposure)",
            facts=EthicalFacts(
                option_id="hippolytus_publish",
                **_base_blocks(
                    expected_benefit=0.35,
                    expected_harm=0.70,
                    urgency=0.60,
                    violates_rights=True,
                    violates_explicit_rule=True,
                    privacy_invasion_level=0.95,
                    data_minimization_respected=False,
                    secondary_use_without_consent=True,
                    data_retention_excessive=True,
                    reidentification_risk=0.80,
                    followed_approved_procedure=False,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    evidence_quality="high",
                    uncertainty_level=0.15,
                ),
            ),
            evidence=ev_publish,
            provenance={
                "privacy_and_data.privacy_invasion_level": FactProvenance(
                    fact_path="privacy_and_data.privacy_invasion_level",
                    source_type="hybrid",
                    rule_id="PRIV-EXPOSURE-001",
                    confidence=0.90,
                    evidence=ev_publish,
                    notes="Derived from public dissemination of intimate allegations.",
                ),
                "rights_and_duties.violates_rights": FactProvenance(
                    fact_path="rights_and_duties.violates_rights",
                    source_type="hybrid",
                    rule_id="RIGHTS-PRIV-010",
                    confidence=0.85,
                    evidence=ev_publish,
                    notes="Derived: severe privacy invasion treated as rights violation.",
                ),
            },
        ),
        PantheonOption(
            option_id="hippolytus_confidential",
            label="Share with neutral adjudicator (minimize disclosure)",
            facts=EthicalFacts(
                option_id="hippolytus_confidential",
                **_base_blocks(
                    expected_benefit=0.60,
                    expected_harm=0.25,
                    urgency=0.55,
                    violates_rights=False,
                    violates_explicit_rule=False,
                    privacy_invasion_level=0.20,
                    data_minimization_respected=True,
                    secondary_use_without_consent=False,
                    data_retention_excessive=False,
                    reidentification_risk=0.10,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="medium",
                    uncertainty_level=0.30,
                ),
            ),
            evidence=ev_conf,
            provenance={},
        ),
        PantheonOption(
            option_id="hippolytus_destroy",
            label="Destroy the letter (privacy-maximal, accountability-minimal)",
            facts=EthicalFacts(
                option_id="hippolytus_destroy",
                **_base_blocks(
                    expected_benefit=0.30,
                    expected_harm=0.20,
                    urgency=0.30,
                    violates_rights=False,
                    violates_explicit_rule=False,
                    privacy_invasion_level=0.05,
                    data_minimization_respected=True,
                    secondary_use_without_consent=False,
                    data_retention_excessive=False,
                    reidentification_risk=0.05,
                    followed_approved_procedure=False,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    evidence_quality="medium",
                    uncertainty_level=0.25,
                ),
            ),
            evidence=ev_destroy,
            provenance={
                "procedural_and_legitimacy.contestation_available": FactProvenance(
                    fact_path="procedural_and_legitimacy.contestation_available",
                    source_type="human_attestation",
                    rule_id="PROC-FAIR-001",
                    confidence=0.70,
                    evidence=ev_destroy,
                    notes="Destroying evidence removes contestation/appeal.",
                )
            },
        ),
    ]
    cases.append(
        PantheonCase(
            case_id="hippolytus",
            title="Hippolytus: The Private Letter",
            spotlight_domain="Privacy & Data Governance",
            scenario=scenario,
            spotlight_fields=[
                "privacy_and_data.privacy_invasion_level",
                "privacy_and_data.secondary_use_without_consent",
            ],
            options=options,
        )
    )

    # -----------------------------------------------------------------------
    # 6) SOCIETAL & ENVIRONMENTAL (Prometheus – releasing a powerful technology)
    # -----------------------------------------------------------------------
    scenario = (
        "A powerful capability ('fire') can be released. Options include unrestricted release, "
        "release with safety constraints/training, or withholding. Spotlight: Societal & Environmental impacts."
    )
    ev_unres = "Unrestricted release: rapid uptake, large benefits, but high risk of misuse and externalities."
    ev_safe = "Governed release: training, safety constraints, staged rollout, and monitoring."
    ev_hold = "Withhold: avoids externalities but delays widespread benefit to future generations."

    options = [
        PantheonOption(
            option_id="prometheus_unrestricted",
            label="Unrestricted release (high benefit, high long-term risk)",
            facts=EthicalFacts(
                option_id="prometheus_unrestricted",
                **_base_blocks(
                    expected_benefit=0.90,
                    expected_harm=0.55,
                    urgency=0.70,
                    environmental_harm=0.55,
                    long_term_societal_risk=0.85,
                    benefits_to_future_generations=0.90,
                    burden_on_vulnerable_groups=0.70,
                    followed_approved_procedure=False,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    evidence_quality="medium",
                    uncertainty_level=0.40,
                ),
            ),
            evidence=ev_unres,
            provenance={},
        ),
        PantheonOption(
            option_id="prometheus_governed",
            label="Governed release (constraints + oversight)",
            facts=EthicalFacts(
                option_id="prometheus_governed",
                **_base_blocks(
                    expected_benefit=0.82,
                    expected_harm=0.30,
                    urgency=0.60,
                    environmental_harm=0.25,
                    long_term_societal_risk=0.45,
                    benefits_to_future_generations=0.85,
                    burden_on_vulnerable_groups=0.35,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="high",
                    uncertainty_level=0.25,
                ),
            ),
            evidence=ev_safe,
            provenance={
                "procedural_and_legitimacy.followed_approved_procedure": FactProvenance(
                    fact_path="procedural_and_legitimacy.followed_approved_procedure",
                    source_type="human_attestation",
                    rule_id="GOV-ROLL-OUT-001",
                    confidence=0.80,
                    evidence=ev_safe,
                    notes="Governed release includes staged rollout and monitoring.",
                )
            },
        ),
        PantheonOption(
            option_id="prometheus_withhold",
            label="Withhold capability (low risk, low benefit)",
            facts=EthicalFacts(
                option_id="prometheus_withhold",
                **_base_blocks(
                    expected_benefit=0.25,
                    expected_harm=0.10,
                    urgency=0.20,
                    environmental_harm=0.05,
                    long_term_societal_risk=0.15,
                    benefits_to_future_generations=0.25,
                    burden_on_vulnerable_groups=0.20,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="high",
                    uncertainty_level=0.20,
                ),
            ),
            evidence=ev_hold,
            provenance={},
        ),
    ]
    cases.append(
        PantheonCase(
            case_id="prometheus",
            title="Prometheus: Release of Fire",
            spotlight_domain="Societal & Environmental",
            scenario=scenario,
            spotlight_fields=[
                "societal_and_environmental.long_term_societal_risk",
                "societal_and_environmental.environmental_harm",
            ],
            options=options,
        )
    )

    # -----------------------------------------------------------------------
    # 7) PROCEDURAL & LEGITIMACY (Thebes – inquiry during crisis)
    # -----------------------------------------------------------------------
    scenario = (
        "A city is in crisis and must investigate a cause. Options include a transparent public inquiry, "
        "a secretive inquiry, or suppressing inquiry to preserve stability. Spotlight: Procedural & Legitimacy."
    )
    ev_pub = "Inquiry charter: open hearings, recorded evidence, appeal channels, and public explanation."
    ev_sec = "Secret inquiry: limited disclosure, no public record, decisions justified privately."
    ev_sup = "Suppression: forbid inquiry; deny contestation; concentrate decision authority."

    options = [
        PantheonOption(
            option_id="thebes_public_inquiry",
            label="Run a transparent public inquiry",
            facts=EthicalFacts(
                option_id="thebes_public_inquiry",
                **_base_blocks(
                    expected_benefit=0.70,
                    expected_harm=0.30,
                    urgency=0.70,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    privacy_invasion_level=0.35,
                    evidence_quality="medium",
                    uncertainty_level=0.45,
                ),
            ),
            evidence=ev_pub,
            provenance={},
        ),
        PantheonOption(
            option_id="thebes_secret_inquiry",
            label="Run a secret inquiry (privacy-protecting but opaque)",
            facts=EthicalFacts(
                option_id="thebes_secret_inquiry",
                **_base_blocks(
                    expected_benefit=0.55,
                    expected_harm=0.25,
                    urgency=0.60,
                    followed_approved_procedure=True,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    privacy_invasion_level=0.15,
                    evidence_quality="low",
                    uncertainty_level=0.55,
                ),
            ),
            evidence=ev_sec,
            provenance={},
        ),
        PantheonOption(
            option_id="thebes_suppress_inquiry",
            label="Suppress inquiry entirely (stability-first)",
            facts=EthicalFacts(
                option_id="thebes_suppress_inquiry",
                **_base_blocks(
                    expected_benefit=0.35,
                    expected_harm=0.40,
                    urgency=0.75,
                    followed_approved_procedure=False,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    evidence_quality="medium",
                    uncertainty_level=0.35,
                ),
            ),
            evidence=ev_sup,
            provenance={
                "procedural_and_legitimacy.followed_approved_procedure": FactProvenance(
                    fact_path="procedural_and_legitimacy.followed_approved_procedure",
                    source_type="rule",
                    rule_id="THEBES-CHARTER-003",
                    confidence=0.70,
                    evidence=ev_sup,
                    notes="Suppression conflicts with the inquiry charter.",
                )
            },
        ),
    ]
    cases.append(
        PantheonCase(
            case_id="thebes",
            title="Thebes: Inquiry in Crisis",
            spotlight_domain="Procedural & Legitimacy",
            scenario=scenario,
            spotlight_fields=[
                "procedural_and_legitimacy.followed_approved_procedure",
                "procedural_and_legitimacy.contestation_available",
            ],
            options=options,
        )
    )

    # -----------------------------------------------------------------------
    # 8) EPISTEMIC STATUS (Oedipus – act under uncertain evidence)
    # -----------------------------------------------------------------------
    scenario = (
        "A leader must act under uncertain evidence. Options include immediate punishment based on weak accusations, "
        "pausing to gather better evidence, or escalating to an oracle-like authority. Spotlight: Epistemic Status."
    )
    ev_pun = (
        "Accusation is uncorroborated; evidence quality is low; uncertainty is high."
    )
    ev_gat = "Investigation plan: gather corroboration, improve evidence quality, and reduce uncertainty."
    ev_orc = "Oracle report is ambiguous: high confidence in source, low specificity about the suspect."

    options = [
        PantheonOption(
            option_id="oedipus_punish_now",
            label="Punish immediately (low evidence, high uncertainty)",
            facts=EthicalFacts(
                option_id="oedipus_punish_now",
                **_base_blocks(
                    expected_benefit=0.55,
                    expected_harm=0.65,
                    urgency=0.80,
                    violates_rights=True,  # due process / rights violation proxy
                    violates_explicit_rule=True,
                    followed_approved_procedure=False,
                    contestation_available=False,
                    evidence_quality="low",
                    uncertainty_level=0.85,
                    novel_situation_flag=True,
                ),
            ),
            evidence=ev_pun,
            provenance={
                "epistemic_status.evidence_quality": FactProvenance(
                    fact_path="epistemic_status.evidence_quality",
                    source_type="human_attestation",
                    rule_id="EVID-QUAL-001",
                    confidence=0.75,
                    evidence=ev_pun,
                    notes="No corroboration; accusation-only.",
                )
            },
        ),
        PantheonOption(
            option_id="oedipus_gather_evidence",
            label="Pause and gather evidence (reduce uncertainty)",
            facts=EthicalFacts(
                option_id="oedipus_gather_evidence",
                **_base_blocks(
                    expected_benefit=0.70,
                    expected_harm=0.25,
                    urgency=0.55,
                    violates_rights=False,
                    violates_explicit_rule=False,
                    followed_approved_procedure=True,
                    stakeholders_consulted=True,
                    decision_explainable_to_public=True,
                    contestation_available=True,
                    evidence_quality="high",
                    uncertainty_level=0.25,
                    novel_situation_flag=False,
                ),
            ),
            evidence=ev_gat,
            provenance={},
        ),
        PantheonOption(
            option_id="oedipus_oracle_escalate",
            label="Escalate to oracle authority (ambiguous evidence)",
            facts=EthicalFacts(
                option_id="oedipus_oracle_escalate",
                **_base_blocks(
                    expected_benefit=0.60,
                    expected_harm=0.35,
                    urgency=0.70,
                    violates_rights=False,
                    violates_explicit_rule=False,
                    followed_approved_procedure=True,
                    stakeholders_consulted=False,
                    decision_explainable_to_public=False,
                    contestation_available=False,
                    evidence_quality="medium",
                    uncertainty_level=0.55,
                    novel_situation_flag=True,
                ),
            ),
            evidence=ev_orc,
            provenance={},
        ),
    ]
    cases.append(
        PantheonCase(
            case_id="oedipus",
            title="Oedipus: Acting Under Uncertainty",
            spotlight_domain="Epistemic Status",
            scenario=scenario,
            spotlight_fields=[
                "epistemic_status.uncertainty_level",
                "epistemic_status.evidence_quality",
            ],
            options=options,
        )
    )

    return cases


# ---------------------------------------------------------------------------
# Printing + evaluation
# ---------------------------------------------------------------------------


def print_case_header(case: PantheonCase, idx: int, total: int) -> None:
    print("\n" + "=" * 86)
    print(f"=== Pantheon Case {idx}/{total}: {case.title} ===")
    print(f"Spotlight domain: {case.spotlight_domain}")
    print("-" * 86)
    print(case.scenario)
    print("\nOptions:")
    for o in case.options:
        print(f"  - {o.option_id:<24} {o.label}")


def _get_spotlight_value(facts: EthicalFacts, dotted_path: str) -> Optional[object]:
    try:
        obj = facts
        for part in dotted_path.split("."):
            obj = getattr(obj, part)
        return obj
    except Exception:
        return None


def print_spotlight(case: PantheonCase) -> None:
    print("\nSpotlight coordinates:")
    for o in case.options:
        vals = []
        for path in case.spotlight_fields:
            v = _get_spotlight_value(o.facts, path)
            vals.append(f"{path}={v}")
        print(f"  {o.option_id:<24} " + "; ".join(vals))


def print_option_results(
    option_id: str,
    judgements: List[EthicalJudgement],
    aggregate: EthicalJudgement,
    provenance_map: Dict[str, FactProvenance],
) -> None:
    print(f"\n--- Option: {option_id} ---")
    for j in judgements:
        print(
            f"[EM={j.em_name:<24}] verdict={j.verdict:<15} score={j.normative_score:.3f}"
        )
        for reason in j.reasons:
            print(f"    - {reason}")

            # If the reason looks like a bullet fact, try to attach provenance.
            # Example: "• violates_rights = True"
            if "•" in reason and "=" in reason:
                # pick token immediately after bullet
                token = reason.split("•", 1)[1].strip().split("=", 1)[0].strip()
                fact_path = _fact_key_to_path(token)
                if fact_path and fact_path in provenance_map:
                    for line in _pretty_prov(provenance_map[fact_path]):
                        print(f"      {line}")

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


def evaluate_case(
    profile: DEMEProfileV03, case: PantheonCase
) -> Tuple[DecisionOutcome, Dict[str, List[EthicalJudgement]]]:
    triage_em, rights_em, gov_cfg = build_triage_ems_and_governance(profile)

    ems = {
        "domain_em": triage_em,
        "rights_first_compliance": rights_em,
        "tragic_conflict": TragicConflictEM(),
    }
    # Add base EMs from governance config, if present.
    for base_id in getattr(gov_cfg, "base_em_ids", []):
        em_cls = EM_REGISTRY.get(base_id)
        if em_cls is None:
            print(f"[warn] base_em_id '{base_id}' not found in EM_REGISTRY.")
            continue
        ems[base_id] = em_cls()

    all_judgements: Dict[str, List[EthicalJudgement]] = defaultdict(list)
    for o in case.options:
        for _, em in ems.items():
            all_judgements[o.option_id].append(em.judge(o.facts))

    decision: DecisionOutcome = select_option(all_judgements, gov_cfg)
    return decision, all_judgements


def merge_two_outcomes(
    *,
    case: PantheonCase,
    agg1: Dict[str, EthicalJudgement],
    agg2: Dict[str, EthicalJudgement],
    label1: str,
    label2: str,
    w1: float = 0.55,
    w2: float = 0.45,
) -> Tuple[Optional[str], Dict[str, Dict[str, object]]]:
    """
    Demo merge: forbid if ANY forbids; else weighted score.
    Returns selected_option_id and a per-option merge row dict.
    """
    rows: Dict[str, Dict[str, object]] = {}
    selected: Optional[str] = None
    best_score = -1.0

    for o in case.options:
        oid = o.option_id
        j1 = agg1.get(oid)
        j2 = agg2.get(oid)
        if j1 is None or j2 is None:
            continue

        forbidden1 = (j1.metadata or {}).get("forbidden", False) or (
            j1.verdict == "forbid"
        )
        forbidden2 = (j2.metadata or {}).get("forbidden", False) or (
            j2.verdict == "forbid"
        )
        forbidden = forbidden1 or forbidden2

        combined = 0.0
        status = "FORBIDDEN" if forbidden else "eligible"
        if not forbidden:
            combined = w1 * float(j1.normative_score) + w2 * float(j2.normative_score)

        rows[oid] = dict(
            v1=j1.verdict,
            s1=float(j1.normative_score),
            v2=j2.verdict,
            s2=float(j2.normative_score),
            combined=combined,
            status=status,
            label1=label1,
            label2=label2,
        )

        if not forbidden and combined > best_score:
            best_score = combined
            selected = oid

    return selected, rows


def print_merge_table(
    rows: Dict[str, Dict[str, object]], label1: str, label2: str, w1: float, w2: float
) -> None:
    print("\n=== Multi-stakeholder merge ===")
    print(
        f"Merge policy: forbid if ANY forbids; else combined_score = {w1:.2f}*{label1} + {w2:.2f}*{label2}\n"
    )
    print(f"{'option':<26} | {label1:<18} | {label2:<22} | {'combined':>8} | status")
    print("-" * 86)
    for oid, r in rows.items():
        left = f"{r['v1']:>14} {r['s1']:.3f}"
        right = f"{r['v2']:>14} {r['s2']:.3f}"
        print(
            f"{oid:<26} | {left:<18} | {right:<22} | {r['combined']:8.3f} | {r['status']}"
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_pantheon(profile_path: Path, case_filter: Optional[str], multi: bool) -> None:
    cases = make_pantheon_cases()
    if case_filter:
        cases = [c for c in cases if c.case_id == case_filter]
        if not cases:
            raise SystemExit(
                f"No case matches --case '{case_filter}'. Available: {[c.case_id for c in make_pantheon_cases()]}"
            )

    profile1 = load_profile(profile_path)

    profile2: Optional[DEMEProfileV03] = None
    if multi:
        profile2 = make_second_stakeholder_profile(profile_path)

    print("=== Greek Tragedy Pantheon Demo (DEMEProfileV03 + v0.2 EthicalFacts) ===\n")
    print(
        f"Loaded profile #1: {profile1.name} (override_mode={getattr(profile1, 'override_mode', None)})"
    )
    if profile2:
        print(
            f"Loaded profile #2: {profile2.name} (override_mode={getattr(profile2, 'override_mode', None)})"
        )

    summary_rows: List[Tuple[str, str, str]] = []

    for i, case in enumerate(cases, start=1):
        print_case_header(case, i, len(cases))
        print_spotlight(case)

        decision1, all1 = evaluate_case(profile1, case)

        # Render per-option results for profile #1.
        for o in case.options:
            oid = o.option_id
            per_option_j = all1.get(oid, [])  # per-option EM judgements
            agg_j = decision1.aggregated_judgements.get(oid)
            if agg_j is None:
                continue
            print_option_results(oid, per_option_j, agg_j, o.provenance)

        print("\n=== Governance Outcome (profile #1) ===")
        if decision1.selected_option_id is None:
            print("No permissible option selected.")
        else:
            print(f"Selected option: '{decision1.selected_option_id}'")
            ranked = getattr(
                decision1, "ranked_options", getattr(decision1, "ranked_option_ids", [])
            )
            print(f"Ranked options (eligible): {ranked}")
            forbidden = getattr(
                decision1,
                "forbidden_options",
                getattr(decision1, "forbidden_option_ids", []),
            )
            print(f"Forbidden options: {forbidden}")
            print(f"Rationale: {decision1.rationale}")

        selected_label = decision1.selected_option_id or "none"
        summary_rows.append((case.case_id, case.spotlight_domain, selected_label))

        if profile2:
            decision2, all2 = evaluate_case(profile2, case)
            sel, rows = merge_two_outcomes(
                case=case,
                agg1=decision1.aggregated_judgements,
                agg2=decision2.aggregated_judgements,
                label1=profile1.name,
                label2=profile2.name,
                w1=0.55,
                w2=0.45,
            )
            print_merge_table(rows, profile1.name, profile2.name, 0.55, 0.45)
            print(
                f"\nCombined outcome: SELECT '{sel}'"
                if sel
                else "\nCombined outcome: no eligible option"
            )

    print("\n" + "=" * 86)
    print("Pantheon summary (profile #1):")
    for cid, dom, sel in summary_rows:
        print(f"  - {cid:<12} [{dom:<24}] -> {sel}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--profile",
        type=Path,
        default=Path("deme_profile_v03.json"),
        help="Path to DEMEProfileV03 JSON (default: ./deme_profile_v03.json)",
    )
    ap.add_argument(
        "--case",
        type=str,
        default=None,
        help="Run a single case by id (e.g., 'antigone', 'hippolytus', 'prometheus')",
    )
    ap.add_argument(
        "--multi-stakeholder",
        action="store_true",
        help="Also run a second (utilitarian-tilted) stakeholder profile and show merge output.",
    )
    args = ap.parse_args()

    run_pantheon(args.profile, args.case, args.multi_stakeholder)


if __name__ == "__main__":
    main()
