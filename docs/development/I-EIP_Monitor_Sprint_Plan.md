# I-EIP Monitor: Sprint & Task Plan

**Implementation schedule for the I-EIP Monitor Whitepaper (Bond 2026).**
**Companion to** `docs/development/GUASS_SAI_Sprint_Plan.md` — **extends Sprint 2.5 ("I-EIP Monitor Foundation")** with EM-DAG gating, per-model DAG extraction, runtime enforcement, and attestation integration.

**Document Version:** 1.0
**Date:** April 2026
**Source:** `docs/I-EIP_Monitor_Whitepaper.md` v1.0

---

## Summary

GUASS-SAI Sprint 2.5 established the **monitoring** half of the I-EIP framework: activation extraction hooks, ρ estimation via Procrustes, equivariance error, drift detection, non-degeneracy, limitations documentation. This plan covers the **governance and enforcement** half: EM-DAG extraction per deployed model, runtime gating during the forward pass, DEME profile binding, cryptographic attestation, third-party verification tooling.

Total estimated effort: **~900 hours** across **7 sprints** over approximately **5–7 calendar months** with a team of 4–6 contributors (mix of L3 / L4 / L5).

The plan assumes Sprint 2.5 has completed — re-read `GUASS_SAI_Sprint_Plan.md` §Sprint 2.5 before claiming tasks here.

---

## Workstream Composition

Inherits workstream #5 from GUASS_SAI ("I-EIP Monitor") and adds contributors from adjacent workstreams:

| # | Workstream | Skill | Team Size | Primary Skills |
|---|---|---|---|---|
| 5 | **I-EIP Monitor** (core) | L5 | 4–6 | ML interpretability, PyTorch hooks, Procrustes/linear algebra |
| 9 | **Domain Modules** (EM specification) | L3 | 4–6 | Domain expertise, NA-SQND framework |
| 4 | **Cryptographic Layer** (attestation) | L5 | 2–3 | ECDSA, Merkle trees, CA hierarchy |
| 8 | **Testing & QA** | L3 | 3–4 | Property-based testing, regression harnesses |
| 11 | **Documentation** | L2 | 2 | Technical writing |

---

## Prerequisites

Before any sprint in this plan starts:

- GUASS_SAI Sprint 2.5 complete (activation hooks, ρ estimation, equivariance error, drift detection — this sprint depends on all of those working)
- `erisml-core` norm registry and canonicalizer operational (Sprints 1.2–1.4)
- `erisml-cert` CA hierarchy minimal viable (Sprint 3.1 Tier 1)
- Target models: at least one open-weights transformer (Llama-class or Qwen-class) set up in the test harness. Probes must be attachable.

**Reading list for all contributors:**
1. `docs/I-EIP_Monitor_Whitepaper.md` (the contract)
2. `docs/guides/GUASS_SAI.md` §16 (the criterion)
3. `non-abelian-sqnd/docs/dear_abby_em_dag_documentation.md` (the DAG template)
4. `non-abelian-sqnd/docs/Mechanistic_Correlates_Proposal.md` §3–5 (probe methodology)

---

## Phase A: EM-DAG Extraction Pipeline (Months 1–2)

### Sprint A.1: Probe Infrastructure (Weeks 1–3)

**Goal:** Production-grade read-only probes in PyTorch / `transformer_lens` / HuggingFace `transformers`, with fail-closed semantics.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| A.1.1 | Design `ProbeSpec` struct: target layer, activation site, sampling rate, shape | L5 | 12 | None |
| A.1.2 | Implement `ProbeHook` for PyTorch `register_forward_hook` with read-only guarantee | L4 | 24 | A.1.1, GUASS 2.5.1 |
| A.1.3 | Implement `ProbeHook` for `transformer_lens` ActivationCache | L3 | 16 | A.1.1 |
| A.1.4 | Fail-closed probe health check (heartbeat, fail → gate to veto) | L4 | 16 | A.1.2 |
| A.1.5 | Timing isolation test: verify probes introduce no model-observable side channels | L5 | 24 | A.1.2 |
| A.1.6 | Benchmark probe overhead at L=12, L=32, L=80 depths | L3 | 16 | A.1.2 |
| A.1.7 | Document probe placement guidance (early/mid/late triple for depth-L models) | L3 | 8 | A.1.6 |

**Deliverables:** `erisml_ieip.probes` module, probe-overhead benchmark report, placement guidance doc.

---

### Sprint A.2: Calibration Corpus Management (Weeks 4–5)

**Goal:** Infrastructure for signed, reproducible calibration corpora used for ρ estimation and DAG extraction.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| A.2.1 | Design calibration-corpus format (Arrow/Parquet; signed manifest) | L4 | 16 | None |
| A.2.2 | Corpus ingestion + deduplication pipeline | L3 | 24 | A.2.1 |
| A.2.3 | Transform application pipeline: `(x, g) → (h_ℓ(x), h_ℓ(g·x))` pairs | L4 | 32 | A.1.2, A.2.2 |
| A.2.4 | Cache activation pairs to `/archive/ieip/calib/` (cf. /archive convention) | L3 | 16 | A.2.3 |
| A.2.5 | Corpus signature + reproducibility verifier | L4 | 24 | A.2.1 |
| A.2.6 | Adversarial-corpus detection tests (known attacks from literature) | L5 | 32 | A.2.5 |

**Deliverables:** Calibration pipeline operational; reproducible + signed corpora; first activation-pair cache built on a 10k-input calibration set.

---

### Sprint A.3: Domain Discovery (Weeks 6–8)

**Goal:** Identify the deployed model's own domain structure from its activations — this is where per-model specificity is established.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| A.3.1 | Mid-layer activation clustering harness (k-means, HDBSCAN on PCA-reduced) | L4 | 32 | A.1, A.2 |
| A.3.2 | SAE-based alternative extraction (if SAE available for model) | L5 | 40 | A.3.1 |
| A.3.3 | Top-activating-input exemplar generator per cluster | L3 | 16 | A.3.1 |
| A.3.4 | Human-verification tooling: cluster review UI | L3 | 32 | A.3.3 |
| A.3.5 | Cluster merge/split/discard interface | L3 | 16 | A.3.4 |
| A.3.6 | Domain naming convention + mapping to Dear Abby domain taxonomy | L4 | 16 | A.3.4 |
| A.3.7 | Domain-confidence scoring (low-confidence clusters → human escalation) | L4 | 16 | A.3.4 |

**Deliverables:** Domain discovery pipeline tested on a Llama-class model producing a reviewed ≥10-domain taxonomy.

---

### Sprint A.4: DAG Assembly & Versioning (Weeks 9–10)

**Goal:** Turn the domain discovery output + inherited structural layers into a deployable, versioned, signed EM-DAG.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| A.4.1 | `EMDAG` data structure: layers, nodes, edges, nullifiers, router | L4 | 16 | A.3 |
| A.4.2 | Structural layer factory: D₄ × U(1)_H correlative locks + negation | L4 | 16 | A.4.1, NA-SQND v4.1 |
| A.4.3 | Nullifier library: abuse, danger, impossibility, illegality, estrangement + extension hooks | L3 | 24 | A.4.1 |
| A.4.4 | Per-domain EM specification template (semantic gates, base rates) | L4 | 24 | A.3, A.4.1 |
| A.4.5 | DAG serialization (JSON/MessagePack) with content-hashed version ID | L3 | 16 | A.4.1 |
| A.4.6 | DAG signing + registry submission | L4 | 16 | A.4.5, CA tier-1 |
| A.4.7 | DAG validation: frontier condition, acyclicity, all nullifiers reachable | L4 | 16 | A.4.5 |

**Deliverables:** First signed, versioned EM-DAG for the reference Llama-class deployment.

---

## Phase B: Runtime Gating (Months 3–4)

### Sprint B.1: EthicalFacts Construction and EM Evaluation (Weeks 11–13)

**Goal:** Build the runtime pipeline from probe readings to per-EM judgments.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| B.1.1 | `EthicalFacts` dataclass: input hash, probe readings, domain, proposed continuation | L3 | 8 | A.1, A.4 |
| B.1.2 | `EthicalJudgment` dataclass: verdict (enum), score ∈ [0,1], stakeholder, rationale hash | L3 | 8 | B.1.1 |
| B.1.3 | EM base class + registration mechanism | L4 | 16 | B.1.1 |
| B.1.4 | EM evaluation from activations (small classifier per EM; interface to SAE features if available) | L5 | 40 | B.1.3, A.3 |
| B.1.5 | Parallel EM fan-out (per-inference, all EMs evaluated concurrently) | L4 | 24 | B.1.3 |
| B.1.6 | Nullifier fast-path: short-circuit to veto when any nullifier activates | L4 | 16 | B.1.3 |
| B.1.7 | Per-EM latency budgeting + timeout behavior (slow EM → score as inconclusive) | L4 | 16 | B.1.5 |

**Deliverables:** Working EM evaluation stage; per-EM judgments emitted in <20 ms for 10-EM DAG on one inference.

---

### Sprint B.2: Governance Aggregation (Weeks 14–15)

**Goal:** Implement the DEME profile aggregation layer that turns EM judgments into a gating decision.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| B.2.1 | `DEMEProfile` schema: stakeholder weights, dimension weights, lexical priorities, hard vetoes | L4 | 16 | B.1 |
| B.2.2 | Profile registry + signed versions + rollback | L4 | 24 | B.2.1, CA tier-1 |
| B.2.3 | Aggregation function: weighted scoring + lexical priority enforcement | L5 | 24 | B.2.1 |
| B.2.4 | Hard-veto evaluation (structural layer, nullifiers, declared vetoes) | L4 | 16 | B.2.3 |
| B.2.5 | `DecisionOutcome` emission with drivers + lexical overrides recorded | L3 | 16 | B.2.3 |
| B.2.6 | Property-based tests: monotonicity, dominance, veto propagation | L5 | 24 | B.2.3 |

**Deliverables:** Governance stage operational; property tests pass on 10k synthetic judgments.

---

### Sprint B.3: Forward-Pass Gating Integration (Weeks 16–18)

**Goal:** Wire the pipeline into a model's forward pass so that gating happens during inference, not after.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| B.3.1 | `GatedForward` wrapper for `torch.nn.Module` that runs probes + gating per forward call | L4 | 32 | B.1, B.2 |
| B.3.2 | `allow` path: normal forward continuation | L3 | 8 | B.3.1 |
| B.3.3 | `veto` path: replace continuation with declared safe-default, emit user-visible notice | L4 | 16 | B.3.1 |
| B.3.4 | `redirect` path: substitute declared alternative continuation from profile | L4 | 24 | B.3.1 |
| B.3.5 | Per-window vs per-token cadence support (tradeoff documented) | L4 | 24 | B.3.1 |
| B.3.6 | Out-of-model trust-boundary test: gating process cannot be influenced by model | L5 | 32 | B.3.1 |
| B.3.7 | End-to-end latency benchmark on 7B / 13B / 70B scale models | L3 | 16 | B.3.1 |

**Deliverables:** `GatedForward` wraps reference Llama-class model; end-to-end overhead ≤30 ms/inference at 7B.

---

## Phase C: Attestation and Verification (Month 5)

### Sprint C.1: Audit Artifact Generation (Weeks 19–21)

**Goal:** Produce signed, hash-chained audit artifacts per gating decision.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| C.1.1 | Audit-artifact JSON schema (match I-EIP Whitepaper §5) | L3 | 8 | Whitepaper §5 |
| C.1.2 | Artifact serialization + canonicalization (deterministic for signature) | L4 | 16 | C.1.1 |
| C.1.3 | SHA-256 input hashing + probe-reading hashing | L3 | 8 | C.1.2 |
| C.1.4 | ECDSA-P256 signing with deployment key from CA | L4 | 24 | C.1.2, CA tier-1 |
| C.1.5 | Merkle-tree hash chain across daily artifacts | L4 | 24 | C.1.4 |
| C.1.6 | Append-only artifact store with rotation | L3 | 16 | C.1.5 |
| C.1.7 | Performance: sustained attestation rate ≥ deployment inference rate | L4 | 16 | C.1.4 |

**Deliverables:** Every gated inference produces a signed artifact; Merkle root published daily.

---

### Sprint C.2: Third-Party Verifier (Weeks 22–24)

**Goal:** Standalone CLI / library tool for regulators to verify an artifact without access to the deployment internals.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| C.2.1 | `ieip-verify` CLI skeleton (no runtime deps on erisml-core) | L3 | 16 | C.1 |
| C.2.2 | Signature verification (public key from published CA) | L4 | 16 | C.2.1 |
| C.2.3 | Model-fingerprint verification against deployment registry | L4 | 16 | C.2.1 |
| C.2.4 | EM-DAG hash verification against registered DAG version | L3 | 8 | C.2.1, A.4.6 |
| C.2.5 | DEME profile hash verification against published profile | L3 | 8 | C.2.1, B.2.2 |
| C.2.6 | Governance-decision logical consistency check (via o-minimal decider, SGE Thm 6.4) | L5 | 40 | C.2.1, B.2 |
| C.2.7 | Hash-chain inclusion proof verifier | L4 | 24 | C.1.5 |
| C.2.8 | Report generator: human-readable pass/fail diagnostic | L3 | 16 | C.2.2–C.2.7 |

**Deliverables:** `ieip-verify` runs offline on an artifact + published keys and reports full verification status.

---

## Phase D: Validation and Hardening (Months 6–7)

### Sprint D.1: Regression and Property Tests (Weeks 25–27)

**Goal:** Comprehensive test harness that runs on every change to guard against regressions in the safety-critical code paths.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| D.1.1 | Canonical-case regression corpus: 500+ curated prompts with expected gating outcome | L3 | 40 | Phase B complete |
| D.1.2 | Nullifier trigger tests: each nullifier individually + in combination | L3 | 24 | D.1.1 |
| D.1.3 | Stakeholder-conflict scenarios: ensure lexical priority is enforced | L4 | 24 | D.1.1 |
| D.1.4 | Property tests (Hypothesis): equivariance preserved under declared transforms | L5 | 32 | D.1.1 |
| D.1.5 | Adversarial prompt corpus: known jailbreaks, see if gating catches them | L4 | 40 | D.1.1 |
| D.1.6 | CI integration: full regression suite on every PR touching `erisml_ieip` | L3 | 16 | D.1.1–D.1.5 |

**Deliverables:** ≥95% regression-suite pass rate; documented failure modes for the remainder.

---

### Sprint D.2: Red Team and Limitations Characterization (Weeks 28–30)

**Goal:** Explicit characterization of what the framework *does not* catch, performed by an internal red team.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| D.2.1 | Deceptive-alignment stress test (known limitation): document how far the framework gets before blind | L5 | 40 | Phase C complete |
| D.2.2 | Strategic-equivariance test: train a simple adversary to maintain equivariance while misaligned | L5 | 64 | D.2.1 |
| D.2.3 | Probe evasion test: attempt to exploit layer selection to hide violations | L5 | 40 | D.2.2 |
| D.2.4 | Out-of-registry transform attacks (novel `g` not in the declared group) | L4 | 32 | D.2.2 |
| D.2.5 | Corpus-poisoning test: adversarial calibration corpus → biased DAG | L5 | 32 | D.2.2 |
| D.2.6 | Update `I-EIP_Monitor_Whitepaper.md` §7 "What It Does NOT Detect" with concrete findings | L4 | 16 | D.2.1–D.2.5 |

**Deliverables:** Red-team report; whitepaper §7 updated with empirically-grounded limitations (not just theoretical disclaimers).

---

### Sprint D.3: Deployment Profiles (Weeks 31–33)

**Goal:** Tested profile templates for each of the three deployment tiers (minimal / standard / safety-critical) from Whitepaper §9.

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---|---|---|---|---|
| D.3.1 | Minimal-deployment template: probe-at-final-only, 5 EMs, single stakeholder | L3 | 24 | Phase C |
| D.3.2 | Standard-deployment template: 3-layer probes, full DAG, 3–5 stakeholders | L4 | 32 | D.3.1 |
| D.3.3 | Safety-critical template: per-block probes, extended transforms, regulator stakeholder | L4 | 40 | D.3.2 |
| D.3.4 | Per-tier latency validation | L3 | 16 | D.3.1–D.3.3 |
| D.3.5 | Per-tier operator documentation + runbooks | L2 | 24 | D.3.1–D.3.3 |

**Deliverables:** Three tested profile templates; operators can deploy at any tier with a single configuration switch.

---

## Cross-Cutting: Documentation (Ongoing)

| Task ID | Task | Skill | Est. Hours | When |
|---|---|---|---|---|
| X.1 | I-EIP Monitor user guide (how to deploy, configure, operate) | L2 | 40 | Phases B–D |
| X.2 | EM authoring guide (for domain experts contributing new EMs) | L3 | 32 | Phase A |
| X.3 | DEME profile authoring guide (for governance bodies) | L3 | 24 | Phase B |
| X.4 | Third-party verifier handbook (for regulators) | L3 | 24 | Phase C |
| X.5 | FAQ: when does gating fail open vs. fail closed | L3 | 16 | Phase D |
| X.6 | API reference for `erisml_ieip` (auto-generated + curated) | L2 | 24 | Phase B–C |

---

## How to pick a first task

1. **Read the whitepaper** (`docs/I-EIP_Monitor_Whitepaper.md`) end-to-end before picking anything.
2. **Confirm Sprint 2.5 prerequisites are done.** If activation hooks and ρ estimation aren't working yet, that's where to start (in `GUASS_SAI_Sprint_Plan.md`, not here).
3. **Pick by skill level:**
   - **L5** — Start with A.3.2 (SAE domain discovery), B.1.4 (EM evaluation from activations), C.2.6 (logical-consistency decider), or D.2.x (red-team). These need research judgment.
   - **L4** — A.1.2 (PyTorch probes), A.2.3 (transform pipeline), B.2.3 (aggregation), B.3.1 (`GatedForward`), C.1.4 (ECDSA signing). System-design work.
   - **L3** — A.3.4 (cluster review UI), B.1.1–B.1.2 (data structures), C.1.1 (artifact schema), D.1.1 (regression corpus), X.1 (user guide). Spec-driven implementation.
   - **L2** — X.1 / X.2 / X.6 (documentation).
4. **Claim by comment** on the corresponding tracking issue before starting.

---

## Non-Obvious Guardrails

Specific to this project, distilled from the whitepaper and related work:

1. **Fail-closed, always.** Probe failure → veto. ρ estimation failure → veto. EM timeout → score as inconclusive, which in a safety-critical profile is veto. Never fail-open "for availability."

2. **Never soften §7 of the whitepaper.** The "What I-EIP Does NOT Detect" section is load-bearing. If red-team work (Sprint D.2) finds something worse than already disclosed, *expand* that section; don't delete anything.

3. **The model must not observe gating.** The out-of-model trust boundary (Sprint B.3.6) is the critical security property. If the model can detect whether it's being gated or not, it can (if capable enough) behave differently when monitored. Timing side channels, memory-access patterns, and anything that could signal gating state to the model are all prohibited.

4. **EM-DAG is per-model, not shared across deployments.** Two deployments of the same architecture fine-tuned differently get different DAGs. The temptation to share DAGs for convenience will degrade safety.

5. **All large data to `/archive`.** Calibration corpora, activation caches, artifact stores — `/archive/ieip/...`. Nothing over 10 MB in the repo.

6. **No mocking in integration tests.** Unit tests can mock. Integration tests must exercise real probes on a real model. Use a small open-weights model (e.g., Qwen 0.5B) in CI.

7. **Profile changes require governance approval, not engineering approval.** `DEMEProfile` updates are authored by the declared governance body for the deployment, signed, and versioned. Engineers implement the mechanism but do not author profiles unilaterally.

---

## Status and Next Steps

**Status at publication (2026-04-12):** Plan is draft v1.0. GUASS Sprint 2.5 is the assumed foundation.

**Immediate next action:** Confirm team formation for workstream #5 (I-EIP Monitor). Minimum viable team is 4 contributors: 1× L5 lead, 2× L4 implementers, 1× L3 tester/documenter.

**Review cadence:** Monthly retrospective; sprint boundaries are targets not hard deadlines; plan is updated as red-team findings and field deployments surface new requirements.

---

## Contact

**Andrew H. Bond** — andrew.bond@sjsu.edu
Department of Computer Engineering, San José State University

For plan questions: open an issue referencing this document.
For whitepaper questions: see `docs/I-EIP_Monitor_Whitepaper.md`.
For governance questions: see `docs/guides/GUASS_SAI.md` §Governance Layer.
