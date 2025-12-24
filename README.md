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
democratically-governed ethical reasoning.

---

![CI](https://github.com/ahb-sjsu/erisml-lib/actions/workflows/ci.yaml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
![License](https://img.shields.io/badge/License-AGI--HPC%20Responsible%20AI-blue.svg)

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
     “Geneva convention” style base module for rights, non-discrimination,
     autonomy/consent, privacy, societal impact, and epistemic caution.

Together, ErisML + DEME support **norm-governed, ethics-aware agents** that can
be inspected, audited, and configured by multiple stakeholders.

---

## What’s in this Repository?

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
    - Geneva baseline EM (`GenevaBaselineEM`) as a cross-cutting,
      “Geneva convention” style base EM
    - Additional simple EMs for safety, fairness, etc. (in progress)

- **Executable examples**
  - TinyHome norm-gated environment
  - Triage ethics demo (`erisml.examples.triage_ethics_demo`) combining:
    - Domain-specific triage EM (`CaseStudy1TriageEM`)
    - Rights/consent EM (`RightsFirstEM`)
    - Geneva baseline EM (`GenevaBaselineEM`) configured as a base EM in
      `DEMEProfileV03` with hard-veto semantics
  - Ethical dialogue CLI that interactively builds DEME profiles from
    narrative scenarios (see `scripts/ethical_dialogue_cli_v03.py`)

- A basic test suite under `tests/`

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

To reproduce (most of) what CI does on your machine:

1. **Install dev dependencies**

       pip install -e ".[dev]"

2. **Run the Python test suite**

   From the repo root:

       pytest

   To run only the DEME-related tests:

       pytest -k ethics
       pytest -k triage

3. **Run Ruff (linting)**

       ruff check src tests

4. **Run Black (formatting check)**

       black --check src tests

   To auto-format instead:

       black src tests

5. **Run Taplo (TOML validation)**

   Depending on your Taplo version:

       taplo fmt --check
   or

       taplo check

6. **One-shot “CI-ish” run**

       ruff check src tests
       black --check src tests
       taplo fmt --check
       pytest

---

## Running the DEME Triage Demo

The DEME triage demo shows how multiple Ethics Modules and a governance
configuration interact to produce an ethically-justified decision, including
a Geneva-style base EM.

### 1. Create a DEME profile via the dialogue CLI

From the repo root:

    cd scripts

    python ethical_dialogue_cli_v03.py ^
      --config ethical_dialogue_questions.yaml ^
      --output deme_profile_v03.json

On macOS / Linux, drop the `^` line continuations as usual:

    cd scripts
    python ethical_dialogue_cli_v03.py \
      --config ethical_dialogue_questions.yaml \
      --output deme_profile_v03.json

This walks you through a narrative questionnaire and writes a
`deme_profile_v03.json` profile (e.g., `Jain-1`).

Copy or symlink that profile into the directory where you’ll run the demo
(often the repo root):

    cp deme_profile_v03.json ..
    cd ..

You should now have `deme_profile_v03.json` in the project root.

### 2. Run the triage ethics demo

From the repo root:

    python -m erisml.examples.triage_ethics_demo

The demo will:

1. Load `deme_profile_v03.json` as a `DEMEProfileV03` (including any configured
   `base_em_ids` such as `"geneva_baseline"`).
2. Construct `EthicalFacts` for three triage options:
   - `allocate_to_patient_A`: critical chest-pain patient, most disadvantaged.  
   - `allocate_to_patient_B`: moderately ill but more stable patient.  
   - `allocate_to_patient_C`: rights-violating / discriminatory option.
3. Instantiate Ethics Modules:
   - `CaseStudy1TriageEM` (domain-specific triage EM)  
   - `RightsFirstEM` (rights/consent / explicit rules)  
   - `GenevaBaselineEM` (Geneva-style baseline, added via `base_em_ids`)
4. Evaluate all options with all EMs, logging per-EM verdicts and scores.
5. Aggregate via the DEME governance layer (respecting base-EM hard vetoes).
6. Print:
   - Per-option per-EM judgements  
   - Governance aggregate per option  
   - The final selected option and rationale  
   - Which options were forbidden, and by which EM(s) and veto rules  

This demo is the canonical example of the current DEME `EthicalFacts` schema
wired to a fully-configured `DEMEProfileV03` with base EMs.

---

## DEME MCP Server (Experimental)

The DEME subsystem can be exposed as an MCP server:

- MCP Server ID: `erisml.ethics.interop.mcp_deme_server`

It provides (at minimum) the following MCP tools:

- `deme.list_profiles` — enumerate available DEME profiles and metadata  
- `deme.evaluate_options` — run Ethics Modules on candidate options given
  their `EthicalFacts`  
- `deme.govern_decision` — aggregate EM outputs and select an option under a
  chosen profile  

Any MCP-compatible client (agent frameworks, IDE copilots, or custom agents)
can use this server to add ethical oversight to planning and action selection.
See `erisml/ethics/interop/` and the examples for details.

---

## Writing Your Own Ethics Module (EM)

ErisML’s DEME subsystem is designed so that **any stakeholder** can plug in their
own ethical perspective as a small, testable module.

An EM is a Python object that implements the `EthicsModule` protocol (or
subclasses `BaseEthicsModule`) and only looks at `EthicalFacts`, never at raw
domain data (ICD codes, sensor traces, etc.).

### 1. Basic structure

A minimal EM looks like this:

    from dataclasses import dataclass

    from erisml.ethics import (
        EthicalFacts,
        EthicalJudgement,
        EthicsModule,
    )


    @dataclass
    class SimpleSafetyEM(EthicsModule):
        """
        Example EM that only cares about expected harm.

        verdict mapping (based on normative_score):
          [0.8, 1.0] -> strongly_prefer
          [0.6, 0.8) -> prefer
          [0.4, 0.6) -> neutral
          [0.2, 0.4) -> avoid
          [0.0, 0.2) -> forbid
        """

        em_name: str = "simple_safety"
        stakeholder: str = "safety_officer"

        def judge(self, facts: EthicalFacts) -> EthicalJudgement:
            # Use only EthicalFacts – no direct access to ICD codes, sensors, etc.
            harm = facts.consequences.expected_harm

            # Simple scoring: less harm -> higher score
            score = 1.0 - harm

            # Map score to a discrete verdict
            if score >= 0.8:
                verdict = "strongly_prefer"
            elif score >= 0.6:
                verdict = "prefer"
            elif score >= 0.4:
                verdict = "neutral"
            elif score >= 0.2:
                verdict = "avoid"
            else:
                verdict = "forbid"

            reasons = [
                f"Expected harm={harm:.2f}, computed safety score={score:.2f}.",
            ]

            metadata = {
                "harm": harm,
                "score_components": {"harm_component": score},
            }

            return EthicalJudgement(
                option_id=facts.option_id,
                em_name=self.em_name,
                stakeholder=self.stakeholder,
                verdict=verdict,
                normative_score=score,
                reasons=reasons,
                metadata=metadata,
            )

From there you can:

- Add additional features (e.g., use `facts.epistemic_status` to downweight
  low-confidence scenarios).  
- Compose multiple EMs and wire them into a `GovernanceConfiguration` /
  `DEMEProfileV03` profile.  
- Write unit tests to ensure your EM behaves as intended over important
  corner cases.

---

## Relationship Between ErisML and DEME

- **ErisML** handles:
  - World modeling (environments, agents, capabilities, norms)
  - Strategic interaction and norm-governed behavior
  - Longitudinal safety metrics and simulation/integration with RL/planning

- **DEME** handles:
  - Ethics-only reasoning over `EthicalFacts`
  - Multi-stakeholder governance (multiple EMs)
  - Configurable profiles and decision aggregation
  - Structured audit logs and explainable rationales

In many deployments:

- ErisML provides the normative environment model and constraint gate.  
- Domain services convert raw state/plan information into `EthicalFacts`.  
- DEME evaluates candidate options and recommends (or vetoes) actions.  

---
# ErisML Library
## Complete Documentation Index

This document provides a comprehensive index of all documentation files in the ErisML library repository. Files are organized by category for easy navigation. Click any filename to view the document on GitHub.

**Repository:** [ahb-sjsu/erisml-lib](https://github.com/ahb-sjsu/erisml-lib)

---

## Core Documentation

1. **[README.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/README.md)**  
   Main repository documentation providing overview, quickstart guide, and installation instructions for ErisML library.

2. **[LICENSE.txt](https://github.com/ahb-sjsu/erisml-lib/blob/main/LICENSE.txt)**  
   MIT License file specifying usage terms and conditions.

3. **[CITATION.cff](https://github.com/ahb-sjsu/erisml-lib/blob/main/CITATION.cff)**  
   Citation file format for proper academic attribution of the ErisML library.

4. **[pyproject.toml](https://github.com/ahb-sjsu/erisml-lib/blob/main/pyproject.toml)**  
   Python project configuration file defining dependencies and build settings.

5. **[insert_header.py](https://github.com/ahb-sjsu/erisml-lib/blob/main/insert_header.py)**  
   Python utility script for adding headers to source files.

---

## ErisML Foundation Papers

1. **[erisml.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/erisml.md)**  
   Core ErisML language specification in markdown format detailing syntax, semantics, and execution model.

2. **[erisml.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/erisml.pdf)**  
   Comprehensive PDF documentation of ErisML language specification, formal grammar, and denotational semantics.

3. **[ErisML_Vision.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/ErisML_Vision.md)**  
   Vision document outlining ErisML goals, architecture, and philosophy for governed AI agents in pervasive computing.

4. **[ErisML Vision Paper.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/ErisML%20Vision%20Paper.pdf)**  
   Academic vision paper presenting theoretical foundations and challenges of creating governed AI agents.

5. **[ErisML_IEEE.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/ErisML_IEEE.pdf)**  
   IEEE-formatted publication documenting technical aspects including concrete syntax and execution semantics.

6. **[ErisML_IEEE.tex](https://github.com/ahb-sjsu/erisml-lib/blob/main/ErisML_IEEE.tex)**  
   LaTeX source code for the IEEE publication.

7. **[ErisML - Comparison with Related Normative Frameworks.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/ErisML%20-%20Comparison%20with%20Related%20Normative%20Frameworks.md)**  
   Comparative analysis of ErisML against other normative and governance frameworks in AI.

---

## DEME (Democratic Ethics Module Engine) 2.0

1. **[DEME_2.0_Vision_Paper.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/DEME_2.0_Vision_Paper.md)**  
   Vision paper for DEME 2.0 architecture introducing democratic governance for AI ethics modules.

2. **[DEME 2.0 - NMI Manuscript - Dec 2025.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/DEME%202.0%20-%20NMI%20Manuscript%20-%20Dec%202025.pdf)**  
   Recent manuscript on DEME 2.0 Normative Module Integration (NMI) architecture and implementation.

3. **[DEME 2.0 - Three tier architecture.svg](https://github.com/ahb-sjsu/erisml-lib/blob/main/DEME%202.0%20-%20Three%20tier%20architecture.svg)**  
   SVG diagram illustrating the three-tier architectural design of DEME 2.0 system.

4. **[DEME Advanced Architectural Roadmap.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/DEME%20Advanced%20Architectural%20Roadmap.md)**  
   Technical roadmap detailing advanced architectural features and mobile agent hardware integration for DEME.

5. **[DEME_EFM_Design_Guide_v0.1.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/DEME_EFM_Design_Guide_v0.1.md)**  
   Design guide for Ethical Facts Modules (EFM) in DEME, covering implementation patterns and best practices.

6. **[DEME–ErisML Governance Plugin for Gazebo.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/DEME%E2%80%93ErisML%20Governance%20Plugin%20for%20Gazebo.pdf)**  
   Documentation for integrating DEME-ErisML governance into Gazebo robotics simulator.

7. **[deme_profile_v03.json](https://github.com/ahb-sjsu/erisml-lib/blob/main/deme_profile_v03.json)**  
   JSON configuration profile for DEME deployment, including ethics module settings and governance parameters.

8. **[deme_whitepaper_nist.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/deme_whitepaper_nist.md)**  
   NIST-oriented whitepaper on DEME system architecture and compliance with AI governance standards.

9. **[SGE DEME2 Nontechnical Summary.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/SGE%20DEME2%20Nontechnical%20Summary.pdf)**  
   Non-technical summary of Stratified Geometric Ethics integration with DEME 2.0 for general audiences.

10. **[SGE+DEME_2.0_Nontechnical_Summary.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/SGE%2BDEME_2.0_Nontechnical_Summary.pdf)**  
    Combined non-technical overview of SGE and DEME 2.0 collaboration and capabilities.

---

## DEME 3.0 & Tensorial Ethics

1. **[DEME_3.0_Tensorial_Ethics_Vision.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/DEME_3.0_Tensorial_Ethics_Vision.md)**  
   Vision document for DEME 3.0 introducing tensorial ethics framework for multi-dimensional moral reasoning.

2. **[Tensorial Ethics.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/Tensorial%20Ethics.md)**  
   Markdown documentation of tensorial ethics theory applying differential geometry to ethical decision-making.

3. **[Tensorial Ethics.docx](https://github.com/ahb-sjsu/erisml-lib/blob/main/Tensorial%20Ethics.docx)**  
   Word document version of tensorial ethics framework with detailed mathematical formulations.

4. **[Tensorial Ethics.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/Tensorial%20Ethics.pdf)**  
   PDF publication on tensorial ethics combining geometric algebra with ethical reasoning.

5. **[tensorial_ethics_chapter_2.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/tensorial_ethics_chapter_2.md)**  
   Chapter 2 of tensorial ethics series covering mathematical foundations and tensor representations.

6. **[tensorial_ethics_chapter_3.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/tensorial_ethics_chapter_3.md)**  
   Chapter 3 exploring ethical manifolds and geometric structures in moral decision spaces.

7. **[tensorial_ethics_chapter_4.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/tensorial_ethics_chapter_4.md)**  
   Chapter 4 detailing practical applications and computational methods for tensorial ethics.

8. **[The Inevitability of Tensorial Manifolds in Multi-Agent Ethics.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/The%20Inevitability%20of%20Tensorial%20Manifolds%20in%20Multi-Agent%20Ethics.pdf)**  
   Theoretical paper arguing for necessity of tensorial manifolds in representing multi-agent ethical interactions.

---

## Stratified Geometric Ethics (SGE)

1. **[geometric_ethics.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/geometric_ethics.pdf)**  
   Introduction to geometric ethics framework using differential geometry for moral analysis.

3. **[Stratified Geometric Ethics - Foundational Paper - Bond - Dec 2025.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/Stratified%20Geometric%20Ethics%20-%20Foundational%20Paper%20-%20Bond%20-%20Dec%202025.pdf)**  
   Foundational paper on Stratified Geometric Ethics methodology (December 2025 version).

7. **[The_Geometry_of_Good_塞翁失马.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/The_Geometry_of_Good_%E5%A1%9E%E7%BF%81%E5%A4%B1%E9%A9%AC.pdf)**  
   Philosophical exploration of geometric ethics with cross-cultural perspectives (塞翁失马 - Sàiwēngshīmǎ).

8. **[geometry_of_good_whitepaper.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/geometry_of_good_whitepaper.pdf)**  
   Whitepaper on geometric approaches to defining and computing ethical good in AI systems.

9. **[sge_section_9_4_6_bip_verification.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/sge_section_9_4_6_bip_verification.md)**  
   Technical section documenting Bond Invariance Principle verification methods in SGE framework.

---

## Invariance Principles & Mathematical Foundations

1. **[bond_invariance_principle.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/bond_invariance_principle.md)**  
   Core document defining the Bond Invariance Principle for consistent ethical reasoning across contexts.

2. **[bond_invariance_principle.md.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/bond_invariance_principle.md.pdf)**  
   PDF version of Bond Invariance Principle documentation for easy distribution.

3. **[Epistemic Invariance Principle (EIP) (Draft).pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/Epistemic%20Invariance%20Principle%20%28EIP%29%20%28Draft%29.pdf)**  
   Draft paper introducing Epistemic Invariance Principle redefining objectivity in AI systems.

4. **[I-EIP_Monitor_Whitepaper.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/I-EIP_Monitor_Whitepaper.pdf)**  
   Whitepaper on implementing EIP monitoring systems for foundation models and AI agents.

5. **[Internal_EIP_Research_Proposal.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/Internal_EIP_Research_Proposal.pdf)**  
   Internal research proposal for advancing EIP theory and practical implementation.

6. **[Technical Brief - The Invariance Framework for Verifiable AI Governance.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/Technical%20Brief%20-%20The%20Invariance%20Framework%20for%20Verifiable%20AI%20Governance.pdf)**  
   Technical brief outlining invariance-based framework for verifying AI governance compliance.

7. **[Philosophy_Engineering_EIP_Technical_Whitepaper_v0.01.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/Philosophy_Engineering_EIP_Technical_Whitepaper_v0.01.pdf)**  
   Early version technical whitepaper bridging philosophy and engineering in EIP implementation.

8. **[Differential Geometry for Moral Alignment -The Mathematical Foundations of DEME 3.0.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/Differential%20Geometry%20for%20Moral%20Alignment%20-The%20Mathematical%20Foundations%20of%20DEME%203.0.pdf)**  
   Mathematical foundations paper applying differential geometry to moral alignment in DEME 3.0.

---

## Gauge Theory & Physics-Inspired Ethics

1. **[gauge_theory_control.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/gauge_theory_control.pdf)**  
   Paper on applying gauge theory principles to ethical control systems and constraint management.

2. **[stratified_gauge_theory.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/stratified_gauge_theory.pdf)**  
   Stratified approach to gauge theory in ethical reasoning, combining topology with normative frameworks.

3. **[electrodynamics_of_value.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/electrodynamics_of_value.pdf)**  
   Novel framework treating ethical values through electrodynamics-inspired field theory.

4. **[BIP_Fusion_Theory_Whitepaper.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/BIP_Fusion_Theory_Whitepaper.md)**  
   Whitepaper on fusion theory integrating Bond Invariance Principle across multiple ethical frameworks.

5. **[foundations_paper.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/foundations_paper.pdf)**  
   Foundational paper establishing theoretical basis for physics-inspired approaches to AI ethics.

6. **[ruling_ring_synthesis.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/ruling_ring_synthesis.pdf)**  
   Synthesis paper on ruling ring structures in ethical governance and constraint propagation.

---

## Mathematical Containment & Safety

1. **[No_Escape_Mathematical_Containment_for_AI.pdf](https://github.com/ahb-sjsu/erisml-lib/blob/main/No_Escape_Mathematical_Containment_for_AI.pdf)**  
   Paper on mathematical methods for ensuring AI systems cannot escape ethical constraints.

2. **[bip_audit_artifact.json](https://github.com/ahb-sjsu/erisml-lib/blob/main/bip_audit_artifact.json)**  
   JSON artifact containing Bond Invariance Principle audit trail and verification data.

---

## Data & Configuration Files

1. **[Item-1.jsonl](https://github.com/ahb-sjsu/erisml-lib/blob/main/Item-1.jsonl)**  
   JSONL data file containing structured items for DEME system testing and evaluation.

2. **[top_10_domains_analysis.md](https://github.com/ahb-sjsu/erisml-lib/blob/main/top_10_domains_analysis.md)**  
   Analysis document ranking and evaluating top 10 application domains for ErisML and DEME deployment.

---

## Summary

**Total Categories:** 9  
**Total Documentation Files:** 57

For the latest updates and to contribute, visit the [GitHub repository](https://github.com/ahb-sjsu/erisml-lib).

---

*Document generated: December 24, 2024*



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
  **Safety and Governance Controls**, including:
  - Explicit normative constraints / environment modeling (e.g., ErisML or
    equivalent),
  - Pluralistic, auditable ethical decision modules (e.g., DEME-style EMs),
  - Logging and audit trails with tamper-evident protections,
  - Safe fallback behaviors and reasonable testing.
- You must not use the software to build:
  - Weapons systems designed primarily to harm or destroy,
  - Coercive surveillance or systems aimed at suppressing fundamental rights,
  - Systems that intentionally or recklessly cause serious harm or large-scale
    rights violations.
- Attribution is required. A suitable notice is:

      This project incorporates components from the AGI-HPC architecture
      (Andrew H. Bond et al., San José State University), used under the
      AGI-HPC Responsible AI License v1.0.

For full details, this README is not legal advice — please see the
`LICENSE.txt` file and consult legal counsel before adopting this license for
production or commercial use.

---

## Citation & Contact

If you use ErisML or DEME in academic work, please cite the corresponding
papers and/or this repository.

Project / license contact: **agi.hpc@gmail.com**
