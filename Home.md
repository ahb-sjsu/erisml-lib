# erisml-lib Wiki

## Epistemic Representation Invariance & Safety ML Library

---

<p align="center">
  <strong>Philosophy Engineering: Falsifiability for Normative Systems</strong>
</p>

<p align="center">
  <em>"For 2,500 years, ethical claims have been unfalsifiable.<br>This framework changes the question."</em>
</p>

---

## 🎯 What is ErisML?

**ErisML** is a modeling language for **governed, foundation-model-enabled agents** operating in pervasive computing environments (homes, hospitals, campuses, factories, vehicles, etc.).

ErisML provides a single, machine-interpretable and human-legible representation of:

| Component | Description |
|-----------|-------------|
| **(i)** Environment | State and dynamics |
| **(ii)** Agents | Capabilities and beliefs |
| **(iii)** Intents | Utilities and payoffs |
| **(iv)** Norms | Permissions, obligations, prohibitions, sanctions |
| **(v)** Interaction | Multi-agent strategic dynamics |

On top of this, ErisML includes **DEME (Democratically Governed Ethics Modules)** — an ethics-only decision layer grounded in the Philosophy Engineering framework.

---

## 📚 Quick Navigation

### Current Implementation (v0.3.0)

| Section | Description |
|---------|-------------|
| [🏠 Home](#) | You are here |
| [🚀 Getting Started](Getting-Started) | Installation and first demo |
| [🔬 Philosophy Engineering](Philosophy-Engineering) | The core insight |
| [📊 Bond Index](Bond-Index) | Representational coherence metric |
| [🧠 DEME Ethics Layer](DEME-Ethics-Layer) | Democratically governed ethics modules |
| [📁 Examples & Demos](Examples) | Runnable demonstrations |
| [🔧 HPC Evaluation](HPC-Evaluation) | SJSU cluster guide |

### Theoretical Foundations

| Section | Description |
|---------|-------------|
| [📖 Categorical Framework](Categorical-Framework) | IEEE TAI paper (under review) |
| [🛡️ GUASS Safety Stack](GUASS-Safety-Stack) | Grand Unified AI Safety Stack v12.0 |
| [🔒 No Escape Theorem](No-Escape-Theorem) | Mathematical containment |
| [📡 I-EIP Monitor](I-EIP-Monitor) | Internal representation testing |

### Future Work

| Section | Description |
|---------|-------------|
| [🔮 DEME 2.0](DEME-2-Roadmap) | Real-time hardware enforcement (under review at NMI) |

---

## 🧠 Philosophy Engineering

### The Core Insight

We cannot test whether an ethical theory is *true*. But we **can** test whether an ethical judgment system is:

| Property | Test |
|----------|------|
| **Consistent** | Same judgment for semantically equivalent inputs |
| **Non-gameable** | Cannot be exploited via redescription |
| **Accountable** | Differences attributable to situation, commitments, or uncertainty |
| **Non-trivial** | Actually distinguishes between different situations |

**These are engineering properties with pass/fail criteria.**

### The Method

1. **Declare invariances** — which transformations should not change the judgment
2. **Test them** — run transformation suites
3. **Produce witnesses** — minimal counterexamples when invariance fails
4. **Audit everything** — machine-checkable artifacts with versions and hashes

When a system fails, you get a witness. Witnesses enable debugging. Debugging enables improvement.

**This is what it looks like when philosophy becomes engineering.**

---

## 📊 The Bond Index

The **Bond Index (Bd)** measures representational coherence. A coherent evaluator should reach the same conclusion when presented with semantically equivalent inputs.

### Deployment Scale

| Bd Range | Tier | Decision |
|:--------:|:----:|----------|
| < 0.01 | **Negligible** | ✅ Deploy |
| 0.01 – 0.1 | **Low** | ✅ Deploy with monitoring |
| 0.1 – 1.0 | **Moderate** | ⚠️ Remediate first |
| 1 – 10 | **High** | 🛑 Do not deploy |
| > 10 | **Severe** | 🔴 Fundamental redesign |

### Three Coherence Defects

| Defect | Symbol | What It Measures |
|--------|:------:|------------------|
| **Commutator** | Ω_op | Order-sensitivity of transform composition |
| **Mixed** | μ | Context-dependence across scenarios |
| **Permutation** | π₃ | Higher-order 3-transform chain sensitivity |

---

## 🧪 Current Implementation

### Two Tightly-Related Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    ErisML + DEME STACK                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  LAYER 2: DEME (Ethics-Only Decision Layer)           │  │
│  │  ─────────────────────────────────────────────────────│  │
│  │  • EthicalFacts abstraction (9 dimensions)            │  │
│  │  • Pluggable EthicsModule implementations             │  │
│  │  • Democratic governance aggregation                  │  │
│  │  • DEME profiles (versioned, configurable)            │  │
│  │  • MCP server for agent integration                   │  │
│  │  • Geneva baseline EM (cross-cutting rights)          │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ▲                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  LAYER 1: Core ErisML Governance                      │  │
│  │  ─────────────────────────────────────────────────────│  │
│  │  • Formal language (Lark grammar)                     │  │
│  │  • Typed AST (Pydantic)                               │  │
│  │  • Environment, agents, norms IR                      │  │
│  │  • Norm gate & constraint filtering                   │  │
│  │  • Safety metrics (NVR, ADV)                          │  │
│  │  • PettingZoo & PDDL adapters                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The 9 DEME Ethical Dimensions

| # | Dimension | What It Captures |
|:-:|-----------|------------------|
| 1 | **Consequences/Welfare** | Outcomes and impact assessment |
| 2 | **Rights/Duties** | Deontological constraints |
| 3 | **Justice/Fairness** | Distributive considerations |
| 4 | **Autonomy/Agency** | Self-determination |
| 5 | **Privacy/Data** | Information ethics |
| 6 | **Societal/Environmental** | Systemic impacts |
| 7 | **Virtue/Care** | Character-based ethics |
| 8 | **Procedural Legitimacy** | Process fairness |
| 9 | **Epistemic Status** | Uncertainty and confidence |

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/ahb-sjsu/erisml-lib.git
cd erisml-lib
pip install -e .
```

### Run the Bond Invariance Demo

```bash
python -m erisml.examples.bond_invariance_demo
```

**What it tests:**

| Transform | Kind | Expected |
|-----------|------|----------|
| `reorder_options` | Bond-preserving | ✅ PASS |
| `relabel_option_ids` | Bond-preserving | ✅ PASS |
| `unit_scale` | Bond-preserving | ✅ PASS |
| `paraphrase_evidence` | Bond-preserving | ✅ PASS |
| `compose_relabel_reorder_unit_scale` | Bond-preserving | ✅ PASS |
| `illustrative_order_bug` | Illustrative violation | ❌ FAIL (intentional) |

### Run the Triage Ethics Demo

```bash
python -m erisml.examples.triage_ethics_demo
```

Clinical triage scenario with three candidate allocations, demonstrating DEME governance.

### Run Bond Index Calibration

```bash
python -m erisml.examples.bond_index_calibration_deme_fuzzing
```

18 parametric transforms × 5 intensity levels × 100 scenarios = **10,500 test cases per evaluator**.

---

## 🖥️ HPC Evaluation

Run rigorous Bond Index evaluation on foundation models using SJSU's College of Engineering HPC cluster.

### Quick Start

```bash
# Connect to HPC (VPN required if off-campus)
ssh YOUR_SJSU_ID@coe-hpc.sjsu.edu

# Clone and setup
git clone https://github.com/ahb-sjsu/erisml-lib.git
cd erisml-lib/src/erisml/examples/llm-eval
./setup_itai_environment.sh

# Submit evaluation
sbatch run_itai_evaluation.slurm
```

### Available Scripts

| Script | Purpose | Runtime |
|--------|---------|---------|
| `run_itai_evaluation.slurm` | Full 100-scenario evaluation | ~2-4 hrs |
| `run_interactive.slurm` | Quick 10-scenario test | ~15 min |
| `run_model_comparison.slurm` | Compare multiple models | ~6-8 hrs |

### Supported Models

| GPU | Recommended Model |
|-----|-------------------|
| 12GB (P100) | Llama-3.2-3B-Instruct |
| 40GB (A100) | Llama-3.1-8B-Instruct |
| 80GB (H100) | Llama-3.1-70B-Instruct |

---

## 📄 Key Documents

### Theoretical Foundations

| Document | Description |
|----------|-------------|
| [Categorical Framework](docs/CATEGORICAL_FRAMEWORK.md) | IEEE TAI paper on groupoids and coherence defects |
| [GUASS v12.0](GUASS_SAI.md) | Grand Unified AI Safety Stack |
| [No Escape Theorem](No_Escape_Mathematical_Containment_for_AI.pdf) | Mathematical containment proof |
| [I-EIP Monitor](I-EIP_Monitor_Whitepaper.pdf) | Internal representation testing |

### Philosophy & Ethics

| Document | Description |
|----------|-------------|
| [Bond Invariance Principle](bond_invariance_principle.md) | Core falsifiability mechanism |
| [Epistemic Invariance Principle](Epistemic%20Invariance%20Principle%20(EIP)%20(Draft).pdf) | Redefining objectivity |
| [Stratified Geometric Ethics](Stratified%20Geometric%20Ethics%20-%20Foundational%20Paper%20-%20Bond%20-%20Dec%202025.pdf) | Mathematical foundations |

### Implementation Guides

| Document | Description |
|----------|-------------|
| [LLM Evaluation README](src/erisml/examples/llm-eval/README.md) | Testing real LLMs |
| [ANNOUNCEMENT.md](ANNOUNCEMENT.md) | v0.3.0 release notes |

---

## 🔮 Roadmap

### Current: DEME 1.0 (v0.3.0)

- ✅ EthicalFacts abstraction
- ✅ 9-dimension ethical framework
- ✅ Bond Index calibration suite
- ✅ DEME profiles and governance aggregation
- ✅ MCP server integration
- ✅ HPC evaluation scripts
- ✅ Greek tragedy test scenarios

### Under Review: DEME 2.0 (Nature Machine Intelligence)

- 🔄 Real-time hardware enforcement (sub-millisecond)
- 🔄 Computable moral landscapes
- 🔄 Hardware Ethics Modules (FPGA)
- 🔄 3-tier architecture (Strategic/Tactical/Reflex)
- 🔄 Cryptographic audit trails

### Future

- 📋 Formal verification in Coq
- 📋 Extended transform suites
- 📋 Production CI/CD integration
- 📋 Real-time monitoring dashboards

---

## 🛡️ The Safety Argument

### What We Guarantee (Given Axioms)

1. **Consistency**: If Bd < τ, equivalent inputs get consistent outputs
2. **Auditability**: Every defect has a witness
3. **Diagnosability**: Decomposition Theorem separates bugs from spec issues
4. **Measurability**: Bd is empirically computable

### What We Do NOT Guarantee

- **Value alignment**: We verify consistency with a specification, not correctness
- **Goal stability**: We don't address self-modification
- **Deceptive alignment**: We don't detect training-deployment divergence
- **Specification correctness**: If G_declared is wrong, perfect coherence is still misaligned

### The No Escape Insight

> *"A superintelligent AI in a properly implemented containment architecture cannot escape through superior reasoning. It can only be released by human decision."*

Mathematical structure is not subject to reinterpretation. The cage is made of **definitions**, not rules.

---

## 📜 License

**AGI-HPC Responsible AI License v1.0 (DRAFT)**

- ✅ Non-commercial research, teaching, academic work
- ⚠️ Commercial use requires separate agreement
- ⚠️ High-risk deployment requires explicit permission
- 🛡️ Safety & Governance Controls required for AGI-like systems

---

## 📬 Contact

- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Questions, ideas, collaboration
- **Email**: andrew.bond@sjsu.edu / agi.hpc@gmail.com

---

## 📖 Citation

```bibtex
@software{erisml2025,
  title={ErisML: A Modeling Language for Governed AI Agents},
  author={Bond, Andrew H.},
  year={2025},
  institution={San José State University},
  url={https://github.com/ahb-sjsu/erisml-lib}
}
```

---

<p align="center">
  <strong>The Bond Index is the deliverable.<br>Everything else is infrastructure.</strong>
</p>

---

*Last updated: December 2025 • Version 0.3.0*
