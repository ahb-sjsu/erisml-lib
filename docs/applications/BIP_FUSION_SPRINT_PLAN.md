# BIP Fusion Implementation — Project Brief

**Reference implementation of the BIP Fusion framework described in [*Physics-Invariant Density Control for Tokamak Plasmas*](https://github.com/ahb-sjsu/erisml-lib/blob/main/docs/applications/BIP_Fusion_Theory_Whitepaper.md) (Bond, v2.0, April 2026).**

---

## What this project is

We are building the software (and eventually hardware) reference implementation of a formally verifiable control framework for tokamak plasma physics. Tokamaks are the leading candidate technology for commercial fusion power. The core engineering problem is regulating plasma density up against hard safety limits — push too close to the Greenwald limit and you get a disruption; stay too far away and the reactor never becomes economical.

Existing approaches (PID, MPC, deep RL) all fail for the same structural reason: they project a multi-dimensional feasibility tensor onto a scalar reward and optimize that. The *Reward Irrecoverability Theorem* (Bond 2026k, Vol 11 of the Geometric Series) proves this projection is not recoverable — information critical to safe behavior near stratum boundaries is irreversibly lost.

The Bond Invariance Principle (BIP) keeps the tensor-valued structure and evaluates candidate control actions directly on a stratified manifold. This project implements that framework end-to-end:

1. **Core BIP in software** — canonicalization, grounding, satisfaction
2. **Stratified Geometric Ethics** — five formal theorems from USPTO Provisional Patent 63/945,667 (Minimality, Representation, Finite Approximation, Decidability, Sample Complexity), encoded as executable code
3. **I-EIP verifier** — checks that control decisions are invariant under declared transformations (units, coordinates, machine scaling)
4. **DIII-D historical replay** — validate against ~10,000 archived tokamak shots
5. **Latency & FPGA co-simulation** — prove the pipeline fits a 1 kHz plasma control loop
6. **Multi-machine tensor & cryptographic attestation** — coordination across reactor fleets, signed audit artifacts for regulatory compliance

Everything is grounded in peer-reviewable theorems and matches the structure of six USPTO provisional patents filed December 2025.

---

## Why this is good work

**Scientific.** Fusion power is one of the defining engineering problems of the century. Every serious fusion program — ITER, DIII-D, JET, SPARC, JT-60SA — needs solved control problems before producing net energy becomes routine.

**Formal.** Unlike typical ML / control work, the correctness criterion is a theorem, not a benchmark. You write code, prove it satisfies an invariance property, and the result is formally verifiable. This is a very different kind of engineering, and it's rare to get to do it on a real application.

**Cross-domain.** The framework here is one of eleven domain instantiations of a unified geometric theory that also covers AI alignment (Vol 11), medical triage (Vol 8), legal reasoning (Vol 5), and economic equilibrium (Vol 4). The mathematical core you work with on fusion transfers directly.

**Concrete deliverables.** Every sprint has executable code, tests, and a result you can point to — not a paper that goes in a drawer. The work also feeds back into the whitepaper, so your contribution is cited.

---

## Prerequisites

You do **not** need fusion physics background — we will explain everything from the plasma side as we go. You **do** need:

**Required**
- Python 3.11+ comfort, including NumPy and some form of typed code (dataclasses, mypy, or similar)
- Ability to read a mathematical definition and turn it into a data structure
- Git workflow: branches, PRs, code review

**Helpful for specific sprints**
- Sprint 1–3: property-based testing (Hypothesis), numerical stability, linear algebra
- Sprint 2: a little differential geometry intuition (stratified space = "disjoint smooth pieces glued along boundaries") — we will supply reading
- Sprint 4: time-series processing, scientific data formats (MDSplus, Arrow, Parquet)
- Sprint 5: benchmarking (`pytest-benchmark`, `pyperf`); Vivado / RTL / `cocotb` for the FPGA track
- Sprint 6: applied crypto (SHA-256, ECDSA-P256, Merkle trees)

**Not required**
- Fusion physics — we'll explain
- Hardware engineering — only the FPGA co-sim issue needs this, and it's an optional track

---

## The Geometric Series context

This project sits inside an 11-volume mathematical series. Students who want the full theoretical picture should read, in priority order:

1. [Whitepaper](https://github.com/ahb-sjsu/erisml-lib/blob/main/docs/applications/BIP_Fusion_Theory_Whitepaper.md) — the single document that matters most for this project. Read §§1–6 and §7a.
2. *Geometric Ethics* v1.0.2g (Bond 2026c, Vol 3) — the foundational text. Ch. 4–6 cover the stratified space formalism you will implement.
3. *Geometric AI* (Bond 2026k, Vol 11) — source of the Reward Irrecoverability Theorem. Worth reading even if you don't work on the AI side because it explains *why* the scalar approach fails.
4. USPTO Provisional 63/945,667 (Stratified Geometric Ethics) — the five theorems we turn into code in Sprint 2.

You do not need to read all of these before starting. Read the whitepaper, pick a first issue, read the sections relevant to that issue.

---

## Sprint plan

Tracked at [github.com/users/ahb-sjsu/projects/4](https://github.com/users/ahb-sjsu/projects/4). All issues are in the `agi-hpc` repo, labelled `fusion`.

### Sprint 1 — BIP Core (software reference)

Foundational. Everything else depends on this.

- **#45** Scaffold `bip_fusion` package (structure, CI, typing)
- **#46** Canonicalization library
- **#47** Grounding Ψ and satisfaction Σ = χ_hard · Σ_soft
- **#48** Formal verification of Theorems 4.1–4.3 as executable property tests

### Sprint 2 — Stratified Geometric Ethics

Turns the five SGE theorems into code.

- **#49** `StratifiedSpace` data structure and frontier-condition validator
- **#50** Stratum classifier (L / H / ELMy / detached) with hysteresis
- **#51** O-minimal decidability checker for constraint specifications (Thm 6.4)
- **#52** Finite-graph approximation of stratified plasma space (Thm 6.3)

### Sprint 3 — I-EIP Verifier & Cross-Machine Transfer

The invariance engine. Proves control decisions don't depend on arbitrary unit / coordinate / machine-scale choices.

- **#53** Transformation-group library for declared invariances
- **#54** I-EIP invariance checker (software equivalent of the FPGA Stage 5)
- **#55** Dimensionless mapping Ψ ↔ Ψ* and cross-machine transfer harness

### Sprint 4 — DIII-D Historical-Data Replay

Where theory meets real plasma data. Depends on Sprints 1–3 being usable.

- **#56** Acquire / mirror DIII-D shot archive and licensing review (start here — it has the longest lead time)
- **#57** Ψ(t) reconstructor from archived diagnostics
- **#58** Replay harness: BIP controller vs archived controller with scoring
- **#59** Synthetic shot generator for CI (no DUA-dependent tests in CI)

### Sprint 5 — Latency & Hardware Co-Simulation

Validates the §7a latency budget (~12–15 μs) and builds the bridge to the FPGA patent.

- **#60** Latency profiler (software pipeline vs hardware budget)
- **#61** FPGA co-simulation harness (Vivado / `cocotb`) for HW/SW equivalence
- **#62** DeepMind RL baseline reproduction for head-to-head comparison

### Sprint 6 — Multi-Machine Tensor & Cryptographic Attestation

Coordination and regulatory-grade auditability.

- **#63** Rank-4 tensor Σ[i, j, k, l] for multi-machine coordination
- **#64** Cryptographic attestation: SHA-256 + ECDSA audit artifacts per control cycle
- **#65** Third-party audit-artifact verifier (standalone CLI)

---

## How to pick your first issue

1. **Read the whitepaper.** Sections 1, 4, 5, 6, 7a are the essential parts.
2. **Look at Sprint 1 first.** If any of #45–#48 are open and unassigned, those are the best starting points — they don't depend on anything else and they set up the scaffolding everyone else will use.
3. **If Sprint 1 is claimed**, skim the Sprint 2 and Sprint 3 issues. These depend on Sprint 1 but can be developed in parallel against a mocked interface.
4. **If you have a specific skill**, look at the sprint that matches:
   - Formal methods / theorem proving → Sprints 1–2
   - Numerics / linear algebra → Sprints 2–3
   - Data engineering → Sprint 4
   - Performance / RTL → Sprint 5
   - Applied crypto → Sprint 6
5. **Comment on the issue** to claim it before starting work. This prevents duplicate work.

---

## Workflow

**Branches:** `fusion/sprint-N/issue-description` — e.g. `fusion/sprint-1/canonicalization-library`.

**Commits:** Descriptive messages. Each commit should compile and pass tests if possible.

**Pull requests:**
- One PR per issue. Small is good.
- Reference the issue: "Fixes #47"
- CI must be green before merge.
- Tests are required for all new code. Property-based tests (Hypothesis) where the correctness criterion is a theorem.
- Math-heavy code should have comments citing the whitepaper / patent section being implemented, so reviewers can check fidelity to the source theorem.

**Reviews:**
- Andrew (`@ahb-sjsu`) reviews everything touching the formal theorems or the I-EIP pipeline.
- Peer review welcome for everything else; Andrew approves merge.

**Questions:**
- Open a GitHub discussion or tag the issue with `question`
- Or reach out on the project Discord

---

## Non-obvious pitfalls

These are things past contributors on related projects hit; flagged here to save you time.

1. **Don't "improve" the canonicalization ordering.** Stages are ordered to match the hardware pipeline (Patent 6). If Python and hardware drift apart on stage order, the co-simulation in Sprint 5 will fail in hard-to-debug ways. If you think an ordering is wrong, discuss before changing.

2. **Don't collapse tensor-valued objectives to scalars for "simplicity".** That's exactly the failure mode the Reward Irrecoverability Theorem describes. If you find yourself wanting to sum the dimensions of Σ into one number, stop and re-read §1.2.1 of the whitepaper.

3. **All large data goes to `/archive`, not into the repo.** DIII-D shot data, cached embeddings, replay results — `/archive/diii-d/`, `/archive/results_fusion/`, etc. Compute on the HPC cluster, cache intermediates. Don't commit anything >10 MB.

4. **Don't mock in integration tests.** Unit tests can mock. Integration tests must exercise the real pipeline — on synthetic data (Sprint 4 issue #59), not mocked data.

5. **Pre-registered negative results are preserved.** If something doesn't work (like the v1 aesthetics formula that failed at scale), document the failure. Don't delete or retcon it.

---

## Timeline sketch

- **Sprint 1** — 2–3 weeks (4 issues, small to medium)
- **Sprint 2** — 3–4 weeks (4 issues, one of them — Thm 6.4 decidability — is substantial)
- **Sprint 3** — 2 weeks
- **Sprint 4** — 4–6 weeks *plus DUA lead time* (start #56 immediately; the rest can proceed on synthetic data meanwhile)
- **Sprint 5** — 2–3 weeks (FPGA co-sim is the only hard part)
- **Sprint 6** — 2–3 weeks

These overlap. Sprint 4 can start in parallel with Sprint 2. Sprint 5 depends on Sprint 3 being done.

---

## Contact

**Andrew H. Bond** — andrew.bond@sjsu.edu  
Department of Computer Engineering, San José State University

For project questions: open a GitHub issue or discussion.  
For theoretical questions: see the whitepaper and cited volumes first; open a discussion if still unclear.
