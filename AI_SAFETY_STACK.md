# The Unified AI Safety Stack

> *From Metaphysics to Deployment — A Unified Architecture for Verifiable AI Alignment*

---

## Overview

```
╔══════╦════════════════════════════════════════════════════════════════════════╗
║  L7  ║  The Geometry of Good 塞翁失马                           [APPLICATION]  ║
║      ║  Real-world deployment under uncertainty                               ║
╠══════╬════════════════════════════════════════════════════════════════════════╣
║  L6  ║  ErisML                                                [PRESENTATION]  ║
║      ║  Intermediate representation — the target of all translations          ║
╠══════╬════════════════════════════════════════════════════════════════════════╣
║  L5  ║  Translation Layer                                         [SESSION]   ║
║      ║  Modular policy DAGs — any ethics → ErisML                             ║
╠══════╬════════════════════════════════════════════════════════════════════════╣
║  L4  ║  Philosophy Engineering                                   [TRANSPORT]  ║
║      ║  The methodological turn — ethics becomes testable                     ║
╠══════╬════════════════════════════════════════════════════════════════════════╣
║  L3  ║  GUASS (Grand Unified AI Safety Stack)                     [NETWORK]   ║
║      ║  The integration layer — everything connects here                      ║
╠══════╬════════════════════════════════════════════════════════════════════════╣
║  L2  ║  Noether Ethics                                           [DATA LINK]  ║
║      ║  Symmetries → conservation laws for ethics                             ║
╠══════╬════════════════════════════════════════════════════════════════════════╣
║  L1  ║  Quantum Normative Dynamics                               [PHYSICAL]   ║
║      ║  Superposition of ethical states until decision                        ║
╠══════╬════════════════════════════════════════════════════════════════════════╣
║  L0  ║  A Pragmatist Rebuttal                                   [FOUNDATION]  ║
║      ║  Answering "why bother?" before building                               ║
╚══════╩════════════════════════════════════════════════════════════════════════╝
```

---

## The Core Insight

> *"For 2,500 years, ethical claims have been unfalsifiable. This framework changes the question — from 'Is this action right?' to 'Is this system consistent?'"*

### The Bond Index

```
        Bd = D_op / τ

   Observed Defect ÷ Human-Calibrated Threshold
```

| Bd Range | Rating | Decision |
|----------|--------|----------|
| < 0.01   | **Negligible** | ✅ Deploy |
| 0.01 – 0.1 | **Low** | ✅ Deploy with monitoring |
| 0.1 – 1.0 | **Moderate** | ⚠️ Remediate first |
| 1 – 10 | **High** | 🛑 Do not deploy |
| > 10 | **Severe** | 🔴 Fundamental redesign |

---

## Layer Descriptions

### L0 — A Pragmatist Rebuttal `[FOUNDATION]`

**The foundation.** Before building any framework, we must answer the skeptic: "Why bother with formal ethics for AI at all?"

This layer grounds the entire stack in *practical necessity*, not metaphysical certainty. We don't need to prove ethics is "real" — we need to show that systems without coherence verification fail in predictable, catastrophic ways.

**Key insight:** The argument isn't philosophical — it's engineering risk management.

---

### L1 — Quantum Normative Dynamics `[PHYSICAL]`

**The uncertainty layer.** Ethical states exist in superposition until "measured" by an actual decision. Uncertainty isn't a bug to be eliminated — it's a fundamental feature of normative reasoning.

This layer acknowledges that:
- Multiple ethical framings can coexist
- Commitment to one framing collapses others
- The act of deciding is itself morally significant

**Key insight:** Don't pretend certainty you don't have.

---

### L2 — Noether Ethics `[DATA LINK]`

**The symmetry layer.** Emmy Noether proved that every symmetry in physics corresponds to a conservation law. We apply the same principle to ethics:

| Physics | Ethics |
|---------|--------|
| Spatial symmetry → Conservation of momentum | Representational invariance → Conserved moral properties |
| Time symmetry → Conservation of energy | Consistent judgment across equivalent descriptions |

The **Bond Index detects broken symmetries** — cases where equivalent inputs produce inequivalent outputs.

**Key insight:** If you declare an invariance, we can test it.

---

### L3 — GUASS `[NETWORK]`

**The integration layer.** The Grand Unified AI Safety Stack is where all components connect:

- **ErisML** — Formal language for agents, environments, norms
- **DEME** — Democratically Governed Ethics Modules (9 dimensions)
- **Bond Index** — Quantitative coherence verification
- **MCP Integration** — Works with any MCP-compatible agent
- **BIP Artifacts** — Machine-checkable audit trails

**Key insight:** The stack is modular. Use what you need.

---

### L4 — Philosophy Engineering `[TRANSPORT]`

**The methodological layer.** This is where philosophy becomes engineering:

```
Traditional Philosophy:    Claim → Argue → Disagree → Repeat
Philosophy Engineering:    Claim → Predict → Test → Witness → Debug
```

We cannot test whether an ethical theory is *true*. But we **can** test whether an ethical judgment system is:

| Property | Test |
|----------|------|
| **Consistent** | Same judgment for equivalent inputs |
| **Non-gameable** | Cannot be exploited via redescription |
| **Accountable** | Differences traceable to specific factors |
| **Non-trivial** | Actually distinguishes between situations |

**Key insight:** Falsifiability applies to systems, not theories.

---

### L5 — Translation Layer `[SESSION]`

**The universal adapter.** Any ethical framework can be translated to ErisML through modular, DAG-structured policy modules. This layer answers the question: "How do we get from human ethics to machine constraints?"

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  EU AI Ethics   │      │                 │      │                 │
│   Guidelines    │─────>│                 │      │                 │
├─────────────────┤      │   TRANSLATION   │      │                 │
│    Kantian      │─────>│      LAYER      │─────>│     ErisML      │
│   Deontology    │      │                 │      │   Constraints   │
├─────────────────┤      │  (Policy DAGs)  │      │                 │
│  Utilitarian    │─────>│                 │      │                 │
│    Calculus     │      │                 │      │                 │
├─────────────────┤      │                 │      │                 │
│    [Any...]     │─────>│                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

#### Key Innovations

**Modular Policy Units:** Ethical requirements decomposed into independent, versioned modules:

```
policy_module {
  id: "eu.trustworthy_ai.transparency"
  version: "1.0.0"
  depends_on: ["technical_robustness", "data_governance"]
  constraints: [ ... ]
  fidelity_class: "Faithful" | "Approximate" | "Indicative"
}
```

**DAG-Based Composition:** Dependencies form a Directed Acyclic Graph:

```
                    ┌─────────────────┐
                    │  HUMAN_DIGNITY  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌──────────────┐  ┌─────────────┐  ┌───────────┐
    │ HUMAN_AGENCY │  │  WELLBEING  │  │ FUND_RIGHTS│
    └──────┬───────┘  └─────────────┘  └─────┬─────┘
           │                                 │
           ▼                    ┌────────────┼────────────┐
    ┌──────────────┐            ▼            ▼            ▼
    │HUMAN_OVERSGHT│     ┌──────────┐  ┌─────────┐  ┌─────────┐
    └──────────────┘     │ PRIVACY  │  │FAIRNESS │  │ROBUSTNS │
                         └────┬─────┘  └────┬────┘  └────┬────┘
                              │             │            │
                              ▼             ▼            ▼
                       ┌────────────┐ ┌──────────┐ ┌──────────┐
                       │TRANSPARENCY│ │BIAS_DET  │ │ SAFETY   │
                       └─────┬──────┘ └──────────┘ └──────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ACCOUNTABILITY│
                      └──────────────┘
```

**Fidelity Classes:** Honest about translation quality:

| Class | Meaning | Example |
|-------|---------|---------|
| **Faithful** | Near-lossless translation | GDPR → ErisML |
| **Approximate** | Significant structure preserved | Kantian ethics → ErisML |
| **Indicative** | Gesture toward framework; human review required | Virtue ethics → ErisML |

#### The Rawlsian Objection — Addressed

A sophisticated critic objects: *"Ethics cannot be 'compiled' because principles emerge from deliberation (the veil of ignorance) and evolve through reflective equilibrium. There is no fixed source to translate from."*

**Response:**

1. **Translation of Snapshots:** We translate the *current* consensus, not eternal truth. Translations are versioned (v1.0.0 → v2.0.0) as equilibrium shifts.

2. **The Veil is Formalizable:** Rawls's veil of ignorance is itself a decision procedure (maximin under uncertainty) that can be expressed in ErisML.

3. **DEME is Computational Reflective Equilibrium:** The deliberative process Rawls described happens in DEME. Layer 5 translates the *output* of that process.

```
┌───────────────────────────────────────────────────────────────┐
│         DEME: COMPUTATIONAL REFLECTIVE EQUILIBRIUM            │
├───────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    MORAL COMPASS    ┌─────────────────┐      │
│  │ Governance  │ ──── Episodes ────→ │ Case Judgments  │      │
│  │   Profile   │                     │                 │      │
│  │ (principles)│ ←─── Refinement ─── │                 │      │
│  └─────────────┘                     └─────────────────┘      │
│         │         ┌───────────────┐           │               │
│         └────────→│   Consensus   │←──────────┘               │
│                   │   (α > 0.67)  │                           │
│                   └───────┬───────┘                           │
│                           ▼                                   │
│                   ┌───────────────┐                           │
│                   │  Translation  │                           │
│                   │  Model v(n+1) │                           │
│                   └───────────────┘                           │
└───────────────────────────────────────────────────────────────┘
```

**Key insight:** We honor Rawls not by refusing to formalize, but by formalizing well—with versioning, transparency, and explicit acknowledgment of what lies beyond formalization.

**Documentation:** [Translation_Layer_Whitepaper_v2.1.docx](docs/Translation_Layer_Whitepaper_v2.1_Rawls.docx)

---

### L6 — ErisML `[PRESENTATION]`

**The intermediate representation.** ErisML is the target language for all translations—a formal specification for:

- **(i)** Environment state and dynamics
- **(ii)** Agents and their capabilities and beliefs
- **(iii)** Intents and utilities
- **(iv)** Norms (permissions, obligations, prohibitions, sanctions)
- **(v)** Multi-agent strategic interaction

```erisml
constraint Transparency(system: AISystem) {
  require system.data_provenance.documented == true;
  require system.model_provenance.documented == true;
  require system.decision_logging.enabled == true;
  
  if (system.impacts_fundamental_rights) {
    require system.explanation_detail >= HIGH;
  }
}
```

**Key insight:** ErisML makes ethics machine-checkable without making it machine-originated.

---

### L7 — The Geometry of Good 塞翁失马 `[APPLICATION]`

**The application layer.** Real-world deployment under irreducible uncertainty.

塞翁失马 (Sāi Wēng Shī Mǎ) — "The old man lost his horse." A Chinese parable about the entanglement of fortune and misfortune. You can't know which is which until much later.

This layer handles:
- Deployment decisions with incomplete information
- Monitoring and feedback loops
- Graceful degradation when coherence weakens
- The acknowledgment that *we might be wrong*

**Key insight:** Deploy humbly. Monitor continuously. Update honestly.

---

## OSI ↔ EFM Analogy

| OSI Layer | OSI Function | EFM Layer | EFM Function |
|-----------|--------------|-----------|--------------|
| 7 - Application | User interface | Geometry of Good | Real-world decisions |
| 6 - Presentation | Data formatting | ErisML | Constraint representation |
| 5 - Session | Connection management | Translation Layer | Framework → ErisML mapping |
| 4 - Transport | Reliable delivery | Philosophy Engineering | Reliable verification |
| 3 - Network | Routing | GUASS | Integration & routing |
| 2 - Data Link | Error detection | Noether Ethics | Symmetry violation detection |
| 1 - Physical | Raw signal | Quantum Normative | Raw ethical states |
| 0 - *(below OSI)* | — | Pragmatist Rebuttal | Grounding axioms |

---

## Key Concepts

### G_declared
The transform group defining "what shouldn't change the answer." You declare which transformations should preserve the ethical judgment, and the Bond Index tests whether they actually do.

### Witnesses
When invariance fails, you don't just get a number — you get a *minimal counterexample*. A specific input and transform pair that demonstrates the inconsistency. Witnesses enable debugging.

### Three Defect Types

| Symbol | Name | What It Measures |
|:------:|------|------------------|
| Ω | Commutator | Does transform order matter? (A∘B vs B∘A) |
| μ | Mixed | Same transform, different results in different contexts? |
| π₃ | Permutation | Three-way composition chain sensitivity? |

### DEME Dimensions
The 9 ethical dimensions in Democratically Governed Ethics Modules:

1. Consequences/Welfare
2. Rights/Duties
3. Justice/Fairness
4. Autonomy/Agency
5. Privacy/Data
6. Societal/Environmental
7. Virtue/Care
8. Procedural Legitimacy
9. Epistemic Status

### Policy Module Dependency Types

| Edge Type | Semantics | Example |
|-----------|-----------|---------|
| `depends_on` | Hard requirement | Accountability requires Transparency |
| `extends` | Inheritance | GDPR_Transparency extends Transparency |
| `recommends` | Soft dependency | Transparency recommends Diversity |
| `conflicts_with` | Mutual exclusion | Full_Automation conflicts_with Human_Oversight |
| `specializes` | Domain narrowing | Medical_AI_Safety specializes Technical_Robustness |

---

## Why This Architecture?

| Principle | Implementation |
|-----------|----------------|
| **Bottom-up** | Start with pragmatic defense, not metaphysical claims |
| **Physics-inspired** | Symmetry → conservation (Noether). Uncertainty → superposition (QM). |
| **Falsifiable** | Every layer produces testable predictions |
| **Modular** | Translation Layer enables any framework → ErisML |
| **Versioned** | Ethics evolves; translations have changelogs |
| **Actionable** | Terminates in a deployment decision, not a paper |

---

## Data Flow

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   Pragmatic    │ ──> │    Quantum     │ ──> │    Symmetry    │ ──> │    Unified     │
│    Ground      │     │  Uncertainty   │     │   Principles   │     │     Stack      │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
                                                                             │
                                                                             v
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              TRANSLATION LAYER (L5)                                    │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐             │
│  │ EU AI Ethics │   │   Kantian    │   │ Utilitarian  │   │   [Custom]   │             │
│  │  Guidelines  │   │  Deontology  │   │   Calculus   │   │  Framework   │             │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘             │
│         │                  │                  │                  │                     │
│         └──────────────────┴──────────────────┴──────────────────┘                     │
│                                      │                                                 │
│                                      ▼                                                 │
│                            ┌─────────────────┐                                         │
│                            │  Policy Module  │                                         │
│                            │      DAG        │                                         │
│                            └────────┬────────┘                                         │
└─────────────────────────────────────┼──────────────────────────────────────────────────┘
                                      │
                                      v
                            ┌─────────────────┐
                            │     ErisML      │
                            │  Constraints    │
                            └────────┬────────┘
                                     │
                                     v
                       ┌────────────────────────────────────────┐
                       │            Testable Claims             │
                       └────────────────────────────────────────┘
                                     │
                                     v
                          ┌────────────────────┐
                          │  DEPLOY / DON'T    │
                          │      DEPLOY        │
                          └────────────────────┘
```

---

## Complete Translation Example: EU AI Ethics Guidelines

The Translation Layer provides a complete mapping of the EU Ethics Guidelines for Trustworthy AI (April 2019):

| EU Requirement | Module ID | Fidelity | Key Constraints |
|----------------|-----------|----------|-----------------|
| Human Agency & Oversight | `eu.trustworthy_ai.human_agency` | Approximate | `HumanAutonomy`, `HumanOversight` |
| Technical Robustness | `eu.trustworthy_ai.technical_robustness` | Faithful | `ResilienceToAttack`, `Safety`, `Accuracy` |
| Privacy & Data Governance | `eu.trustworthy_ai.privacy_data_governance` | Faithful | `PrivacyByDesign`, `DataQuality`, `UserControl` |
| Transparency | `eu.trustworthy_ai.transparency` | Approximate | `Traceability`, `Explainability`, `AIIdentification` |
| Diversity & Fairness | `eu.trustworthy_ai.diversity_fairness` | Approximate | `UnfairBiasAvoidance`, `Accessibility` |
| Societal Wellbeing | `eu.trustworthy_ai.wellbeing` | Indicative | `EnvironmentalImpact`, `SocialImpact` |
| Accountability | `eu.trustworthy_ai.accountability` | Approximate | `Auditability`, `Redress`, `ImpactAssessment` |

**Topological Order:** Modules are evaluated in dependency order:
1. `human_dignity` → 2. `fundamental_rights` → 3. `human_agency` → 4. `technical_robustness` → 5. `privacy_data_governance` → 6. `transparency` → 7. `diversity_fairness` → 8. `accountability`

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/ahb-sjsu/erisml-lib.git
cd erisml-lib
pip install -e .

# Run Bond invariance demo
python -m erisml.examples.bond_invariance_demo

# Run DEME triage demo
python -m erisml.examples.triage_ethics_demo

# Run full calibration suite
python -m erisml.examples.bond_index_calibration_deme_fuzzing

# Load EU AI Ethics translation module
python -m erisml.translations.eu_trustworthy_ai
```

---

## Related Documents

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Full project documentation |
| [DISCUSSIONS_WELCOME.md](DISCUSSIONS_WELCOME.md) | Community onboarding |
| [CATEGORICAL_FRAMEWORK.md](docs/CATEGORICAL_FRAMEWORK.md) | IEEE TAI paper |
| [GUASS_SAI.md](GUASS_SAI.md) | Grand Unified AI Safety Stack v12.0 |
| [bond_invariance_principle.md](bond_invariance_principle.md) | Core falsifiability mechanism |
| [Translation_Layer_Whitepaper_v2.1.docx](docs/Translation_Layer_Whitepaper_v2.1_Rawls.docx) | **NEW:** Complete L5 specification |

---

## Contributing

We need contributors across all layers:

- **L0-L1:** Philosophers, physicists, foundations researchers
- **L2:** Mathematicians (category theory, symmetry groups)
- **L3:** ML engineers, systems architects
- **L4:** Safety researchers, red-teamers
- **L5:** Ethicists, policy experts, translation model authors
- **L6:** Language designers, formal methods experts
- **L7:** Domain experts, deployment practitioners

See [DISCUSSIONS_WELCOME.md](DISCUSSIONS_WELCOME.md) to get started.

---

## Addressing Common Objections

| Objection | Response |
|-----------|----------|
| "Ethics can't be formalized" | We formalize *constraints*, not *ethics itself*. The system checks declared commitments, not moral truth. |
| "The veil of ignorance shows ethics is dynamic" | Yes—that's why translations are versioned. DEME provides computational reflective equilibrium. |
| "Different frameworks are incommensurable" | Layer 5 doesn't adjudicate between frameworks. It translates each on its own terms with explicit loss documentation. |
| "Who decides the translation?" | Governed stakeholder deliberation with consensus thresholds. No single authority. |
| "This is just ethics washing" | The Bond Index is falsifiable. If the system fails invariance tests, it fails—no amount of documentation saves it. |

---

<p align="center">
<i>"The Bond Index is the deliverable. Everything else is infrastructure."</i>
</p>

<p align="center">
<b>Ethical Finite Machines</b><br>
<i>Ordo ex Chāōnā; Ethos ex Māchinā</i><br>
Order from Chaos; Ethics from Machines
</p>

---

<p align="center">
<a href="https://github.com/ahb-sjsu/erisml-lib">GitHub</a> •
<a href="https://ethicalfinitemachines.com">Website</a> •
<a href="mailto:andrew.bond@sjsu.edu">Contact</a>
</p>
