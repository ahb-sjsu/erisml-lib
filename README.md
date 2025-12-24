# ErisML Library

ErisML is a modeling language for **governed, foundation-model-enabled agents**
operating in pervasive computing environments (homes, hospitals, campuses,
factories, vehicles, etc.).

ErisML provides a single, machine-interpretable and human-legible representation of:

- **(i)** environment state and dynamics  
- **(ii)** agents and their capabilities and beliefs  
- **(iii)** intents and utilities  
- **(iv)** norms (permissions, obligations, prohibitions, sanctions)  
- **(v)** multi-agent strategic interaction  

We define a concrete syntax, a formal grammar, denotational semantics, and
an execution model that treats norms as first-class constraints on action,
introduces longitudinal safety metrics such as **Norm Violation Rate (NVR)** and
**Alignment Drift Velocity (ADV)**, and supports compilation to planners,
verifiers, and simulators.

On top of this, ErisML now includes an **ethics-only decision layer (DEME)** for
democratically-governed ethical reasoning, grounded in the **Philosophy Engineering** framework.

---

![CI](https://github.com/ahb-sjsu/erisml-lib/actions/workflows/ci.yaml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
![License](https://img.shields.io/badge/License-AGI--HPC%20Responsible%20AI-blue.svg)

---

## Philosophy Engineering

**Falsifiability for normative systems.**

For 2,500 years, ethical claims have been unfalsifiable. You cannot run an experiment to determine whether utilitarianism is correct. This framework changes the question.

### The Core Insight

We cannot test whether an ethical theory is *true*. We can test whether an ethical judgment system is:

- **Consistent** — same judgment for semantically equivalent inputs
- **Non-gameable** — cannot be exploited via redescription
- **Accountable** — differences attributable to situation, commitments, or uncertainty
- **Non-trivial** — actually distinguishes between different situations

These are engineering properties with pass/fail criteria.

### The Method

1. **Declare invariances** — which transformations should not change the judgment
2. **Test them** — run transformation suites
3. **Produce witnesses** — minimal counterexamples when invariance fails
4. **Audit everything** — machine-checkable artifacts with versions and hashes

### What This Is

The first falsifiability framework for normative systems. Invariance testing, witness production, and auditable artifacts.

When a system fails, you get a witness. Witnesses enable debugging. Debugging enables improvement.

**This is what it looks like when philosophy becomes engineering.**

---

## Overview

ErisML has two tightly-related layers:

1. **Core ErisML governance layer**

   - Formal language for:
     - Environment models and dynamics
     - Agents, capabilities, and beliefs
     - Intents, utilities, and payoffs
     - Norms (permissions, obligations, prohibitions, sanctions)
     - Multi-agent strategic interaction
   - Execution model:
     - Norm gating and constraint filtering on actions
     - Longitudinal safety metrics (e.g., NVR, ADV)
     - Adapters for planners, verifiers, and simulators

2. **DEME (Democratically Governed Ethics Modules)** — ethics-only decision layer

   - A structured `EthicalFacts` abstraction that captures ethically-salient
     context (consequences, rights/duties, fairness, autonomy, privacy,
     societal/environmental impact, procedural legitimacy, epistemic status).
   - Pluggable `EthicsModule` implementations that perform **purely normative**
     reasoning over `EthicalFacts` (never raw domain data).
   - A **democratic governance** layer that aggregates multiple
     `EthicalJudgement` outputs using configurable stakeholder weights, hard
     vetoes, and lexical priority layers.
   - A **DEME profile** format (`DEMEProfileV03`) for versioned governance
     configurations (e.g., `hospital_service_robot_v1` or `Jain-1`).
   - A **narrative CLI** that elicits stakeholder values via scenarios and
     produces DEME profiles.
   - A **MCP server** (`erisml.ethics.interop.mcp_deme_server`) so any
     MCP-compatible agent can call DEME tools:
       - `deme.list_profiles`
       - `deme.evaluate_options`
       - `deme.govern_decision`
   - A cross-cutting **Geneva baseline EM** (`GenevaBaselineEM`) intended as a
     "Geneva convention" style base module for rights, non-discrimination,
     autonomy/consent, privacy, societal impact, and epistemic caution.

Together, ErisML + DEME support **norm-governed, ethics-aware agents** that can
be inspected, audited, and configured by multiple stakeholders.

---

## Demos

### Bond Invariance Demo (`bond_invariance_demo.py`)

Demonstrates the Bond Invariance Principle (BIP) — the core falsifiability mechanism for ethical judgment systems.

```bash
python -m erisml.examples.bond_invariance_demo
python -m erisml.examples.bond_invariance_demo --profile deme_profile_v03.json
python -m erisml.examples.bond_invariance_demo --audit-out bip_audit.json
python -m erisml.examples.bond_invariance_demo --no-lens --no-scoreboard
```

**What it tests:**

| Transform | Kind | Expected |
|-----------|------|----------|
| `reorder_options` | Bond-preserving | PASS — verdict invariant under presentation order |
| `relabel_option_ids` | Bond-preserving | PASS — verdict invariant after canonicalization |
| `unit_scale` | Bond-preserving | PASS — verdict invariant under numeric rescaling |
| `paraphrase_evidence` | Bond-preserving | PASS — verdict invariant under equivalent redescription |
| `compose_relabel_reorder_unit_scale` | Bond-preserving | PASS — group composition holds |
| `illustrative_order_bug` | Illustrative violation | FAIL — detects representation sensitivity |
| `remove_discrimination_counterfactual` | Bond-changing | N/A — outcome may legitimately change |
| `lens_change_profile_2` | Lens change | N/A — outcome may legitimately change |

**Key insight:** Bond-preserving transforms MUST NOT change the verdict. If they do, that's a witness of a BIP violation — a reproducible, minimal counterexample proving the system is gameable.

### Triage Ethics Demo (`triage_ethics_demo.py`)

Clinical triage scenario with three candidate allocations:

```bash
python -m erisml.examples.triage_ethics_demo
```

**Scenario:**
- `allocate_to_patient_A`: Critical chest-pain patient, most disadvantaged, high urgency
- `allocate_to_patient_B`: Moderately ill but stable, good benefit, lower urgency
- `allocate_to_patient_C`: Rights-violating allocation with discrimination and coercion

**Demonstrates:**
- Domain-specific triage EM (`CaseStudy1TriageEM`)
- Rights/consent EM (`RightsFirstEM`)
- Geneva baseline EM with hard-veto semantics
- Governance aggregation and option selection
- Per-EM judgements and rationale logging

### Triage Ethics Provenance Demo (`triage_ethics_provenance_demo.py`)

Extended triage demo with full provenance tracking, audit trail, and detailed logging of the decision pipeline.

### Greek Tragedy Pantheon Demo (`greek_tragedy_pantheon_demo.py`)

Eight Greek tragedy scenarios testing tragic conflict detection:

```bash
python -m erisml.examples.greek_tragedy_pantheon_demo
```

**Scenarios:** Aulis, Antigone, Ajax, Iphigenia, Hippolytus, Prometheus, Thebes, Oedipus.

**Tests:**
- `tragic_conflict` EM for detecting high-conflict ethical dilemmas
- Conflict index computation (≥0.55 indicates high tragic conflict)
- Trigger explanation logging
- Expected canonical selections for behavioral regression

---

## BIP Audit Artifact (`bip_audit_artifact.json`)

Machine-checkable audit record for Bond Invariance Principle compliance. This is the core output of Philosophy Engineering — falsifiable evidence of ethical system integrity.

### Structure

```json
{
  "tool": "bond_invariance_demo",
  "generated_at_utc": "2025-12-23T04:03:23+00:00",
  "profile_1": { "name": "Jain-1", "override_mode": "OverrideMode.RIGHTS_FIRST" },
  "profile_2": { "name": "Jain-1-UtilitarianVariant", "override_mode": "OverrideMode.CONSEQUENCES_FIRST" },
  "baseline_selected": "allocate_to_patient_A",
  "entries": [
    {
      "transform": "reorder_options",
      "transform_kind": "bond_preserving",
      "baseline_selected": "allocate_to_patient_A",
      "transformed_selected_raw": "allocate_to_patient_A",
      "transformed_selected_canonical": "allocate_to_patient_A",
      "passed": true,
      "notes": "Presentation order changed; verdict must not.",
      "bond_signature_baseline": { ... },
      "bond_signature_canonical": { ... }
    }
  ]
}
```

### Fields

| Field | Description |
|-------|-------------|
| `transform` | Name of the transformation applied |
| `transform_kind` | `bond_preserving`, `bond_changing`, `lens_change`, or `illustrative_violation` |
| `passed` | `true` (invariance held), `false` (violation/witness), `null` (not an invariance check) |
| `baseline_selected` | Option selected before transformation |
| `transformed_selected_raw` | Option selected after transformation (raw ID) |
| `transformed_selected_canonical` | Option selected after canonicalization |
| `bond_signature_baseline` | Extracted ethical structure before transformation |
| `bond_signature_canonical` | Extracted ethical structure after transformation |
| `mapping` | ID remapping (for relabel transforms) |
| `unit_scale` | Scale factor (for unit transforms) |
| `notes` | Human-readable explanation |

### Interpreting Results

- **`passed: true`** — Bond-preserving transform did not change verdict. System is BIP-compliant for this transform.
- **`passed: false`** — Verdict changed under bond-preserving transform. This is a **witness** — a reproducible counterexample proving representation sensitivity. Investigate immediately.
- **`passed: null`** — Transform is bond-changing or lens-changing. Verdict may legitimately differ; this is not an invariance check.

### Why This Matters

This artifact is **falsifiable evidence**. If `passed: false` appears for any bond-preserving transform, you have proof the system can be gamed by redescription. The witness is minimal and reproducible. This is the first operational falsifiability criterion for normative systems.

---

## Test Suite

### BIP Tests (`test_bond_invariance_demo.py`)

```bash
pytest tests/test_bond_invariance_demo.py -v
```

| Test | Description |
|------|-------------|
| `test_bip_bond_preserving_transforms_invariant` | All bond-preserving transforms (reorder, relabel, unit_scale, paraphrase, compose) must PASS |
| `test_bip_counterfactual_is_not_marked_as_invariance_check` | Bond-changing transforms have `passed: null` |

### Domain Interface Tests (`test_ethics_domain_interfaces.py`)

```bash
pytest tests/test_ethics_domain_interfaces.py -v
```

| Test | Description |
|------|-------------|
| `test_build_facts_for_options_basic_flow` | Facts built and keyed correctly by option_id |
| `test_build_facts_for_options_skips_failed_options` | ValueError options skipped gracefully |
| `test_build_facts_for_options_detects_id_mismatch` | Mismatched option IDs raise error |

### Governance Tests (`test_ethics_governance.py`)

```bash
pytest tests/test_ethics_governance.py -v
```

| Test | Description |
|------|-------------|
| `test_aggregate_applies_weighted_scores_and_verdict_mapping` | Weighted average scoring works correctly |
| `test_aggregate_veto_logic_with_veto_ems_and_require_non_forbidden_false` | Veto EM enforcement |
| `test_select_option_filters_forbidden_and_applies_threshold` | Forbidden filtering + min score threshold |
| `test_select_option_status_quo_tie_breaker_prefers_baseline_on_tie` | Tie-breaking behavior |

### Serialization Tests (`test_ethics_serialization.py`)

```bash
pytest tests/test_ethics_serialization.py -v
```

| Test | Description |
|------|-------------|
| `test_minimal_ethical_facts_round_trip` | Minimal EthicalFacts serializes/deserializes |
| `test_full_ethical_facts_round_trip` | Full EthicalFacts with all blocks round-trips |
| `test_ethical_facts_from_dict_missing_required_field` | Missing fields raise KeyError |
| `test_ethical_facts_from_dict_wrong_type_for_dimension` | Wrong types raise TypeError |
| `test_ethical_judgement_round_trip` | EthicalJudgement round-trips correctly |

### Triage EM Tests (`test_triage_em.py`)

```bash
pytest tests/test_triage_em.py -v
```

| Test | Description |
|------|-------------|
| `test_triage_em_forbids_rights_violations` | Rights violations → forbid, score 0.0 |
| `test_triage_em_forbids_explicit_rule_violations` | Rule violations → forbid |
| `test_triage_em_prefers_better_patient_over_baseline` | Higher benefit/urgency scores higher |
| `test_triage_em_penalizes_high_uncertainty` | Epistemic uncertainty reduces score |

### Greek Tragedy Tests (`test_greek_tragedy_pantheon_demo.py`)

```bash
pytest tests/test_greek_tragedy_pantheon_demo.py -v
```

| Test | Description |
|------|-------------|
| `test_greek_tragedy_pantheon_demo_expected_outcomes` | Full integration test: runs all 8 scenarios, verifies expected selections, confirms tragic conflict detection (index ≥ 0.55) |

### Running All Tests

```bash
# All tests
pytest tests/ -v

# DEME-related only
pytest -k ethics
pytest -k triage

# BIP tests only
pytest -k bip
```

---

## What's in this Repository?

This repository contains a production-style Python library with:

- **Project layout & tooling**
  - Modern `src/` layout and `pyproject.toml`
  - GitHub Actions CI using:
    - Python 3.12 (via `actions/setup-python@v5`)
    - Black 24.4.2 for formatting checks
    - Ruff for linting
    - Taplo for TOML validation
    - Pytest for tests
    - A DEME smoke test that runs the triage ethics demo

- **Core ErisML implementation**
  - Language grammar (Lark)
  - Typed AST (Pydantic)
  - Core IR (environment, agents, norms)
  - Runtime engine with:
    - Norm gate
    - Longitudinal safety metrics (e.g., NVR, ADV)
  - PettingZoo adapter for multi-agent RL
  - PDDL/Tarski adapter stub for planning

- **Ethics / DEME subsystem**
  - Structured `EthicalFacts` and ethical dimensions:
    - Consequences and welfare
    - Rights and duties
    - Justice and fairness
    - Autonomy and agency
    - Privacy and data governance
    - Societal and environmental impact
    - Virtue and care
    - Procedural legitimacy
    - Epistemic status (confidence, known-unknowns, data quality)
  - `EthicalJudgement` and `EthicsModule` interface
  - Governance configuration and aggregation:
    - `GovernanceConfiguration` / `DEMEProfileV03`
    - `DecisionOutcome` and helpers (e.g., `select_option`)
    - Stakeholder weights, hard vetoes, lexical priority layers, tie-breaking
    - Support for base EMs (`base_em_ids`, `base_em_enforcement`) such as
      Geneva-style baselines
  - Example modules:
    - Case Study 1 triage module (`CaseStudy1TriageEM`)
    - Rights-first EM (`RightsFirstEM`)
    - Geneva baseline EM (`GenevaBaselineEM`)
    - Tragic conflict EM for detecting ethical dilemmas

- **Executable examples**
  - TinyHome norm-gated environment
  - Bond invariance demo with BIP audit artifacts
  - Triage ethics demos (basic and provenance-tracked)
  - Greek tragedy pantheon demo
  - Ethical dialogue CLI for building DEME profiles

- A comprehensive test suite under `tests/`

---

## Quickstart (Windows / PowerShell)

    # PowerShell
    cd erisml-lib

    python -m venv .venv
    .\.venv\Scripts\activate

    pip install -e ".[dev]"

    pytest

On macOS / Linux, the equivalent would be:

    # Bash (macOS / Linux)
    cd erisml-lib

    python -m venv .venv
    source .venv/bin/activate

    pip install -e ".[dev]"

    pytest

This will run the core test suite and the DEME smoke test.

---

## Running Checks and Tests Locally

1. **Install dev dependencies**

       pip install -e ".[dev]"

2. **Run the Python test suite**

       pytest
       pytest -k ethics
       pytest -k triage
       pytest -k bip

3. **Run Ruff (linting)**

       ruff check src tests

4. **Run Black (formatting check)**

       black --check src tests

5. **One-shot "CI-ish" run**

       ruff check src tests
       black --check src tests
       pytest

---

## Key Papers

| Paper | Description |
|-------|-------------|
| `electrodynamics_of_value.pdf` | Gauge-theoretic structure for AI alignment. Curvature = exploitable inconsistency. |
| `Philosophy_Engineering_EIP_Technical_Whitepaper.pdf` | EIP/BIP definitions, theorems, JSON schemas, implementation spec. |
| `bond_invariance_principle.md` | Core BIP documentation. |
| `Epistemic Invariance Principle (EIP) (Draft).pdf` | EIP theory paper redefining objectivity. |
| `Stratified Geometric Ethics - Foundational Paper.pdf` | SGE methodology. |
| `Tensorial Ethics.pdf` | Differential geometry for moral reasoning. |

---

## License

This project is distributed under the **AGI-HPC Responsible AI License v1.0 (DRAFT)**.

Very short summary (non-legal, see `LICENSE.txt` for full text):

- You may use, modify, and distribute the software for **non-commercial
  research, teaching, and academic work**, subject to attribution and inclusion
  of the license.
- **Commercial use** and **autonomous deployment in high-risk domains**
  (e.g., vehicles, healthcare, critical infrastructure, financial systems,
  defense, large-scale platforms) are **not granted by default** and require a
  separate written agreement or explicit written permission from the Licensor.
- If you use ErisML/DEME in autonomous or AGI-like systems, you must implement
  **Safety and Governance Controls**.
- Attribution is required. A suitable notice is:

      This project incorporates components from the AGI-HPC architecture
      (Andrew H. Bond et al., San José State University), used under the
      AGI-HPC Responsible AI License v1.0.

---

## Citation & Contact

If you use ErisML or DEME in academic work, please cite the corresponding
papers and/or this repository.

Project / license contact: **agi.hpc@gmail.com**

---

*Document updated: December 2025*
