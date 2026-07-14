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

## Why This Project Matters

Current AI safety tooling operates at the system boundary — input filters see prompts, output filters see generations — and cannot answer the only question that matters: **what is the model actually doing inside?** RLHF shapes training. Constitutional AI prompts. Activation steering modifies. None of these enforce at inference time, on internal state, under democratic governance.

The I-EIP Monitor does. It is one of the only deployable safety frameworks that:

- **Sees inside** — probes internal activations during every forward pass
- **Enforces in real time** — gates the forward pass, not after-the-fact review
- **Honors stakeholders** — the DEME profile is authored by the governance body, not the engineers
- **Produces verifiable evidence** — cryptographically signed audit artifacts a regulator can verify offline
- **Is honest about limitations** — §7 of the whitepaper explicitly catalogs what it cannot detect

If you work on this, you are building the runtime half of AI alignment — the half that actually runs in production next to the model. The theoretical half already exists (Geometric Ethics, GUASS-SAI, the 6-patent portfolio). Your job is to make it execute.

**Concrete things you will have on your CV after contributing:**

- Hands-on experience with mechanistic interpretability (probes, activation patching, ρ estimation via Procrustes)
- Production PyTorch / transformer hooks at a level rare in most ML coursework
- Applied cryptography (ECDSA, Merkle trees, audit-artifact schemas)
- Formal-methods-adjacent work (o-minimal decidability, property-based testing, stratified spaces)
- Co-authorship on the I-EIP Monitor Whitepaper for substantial contributions

---

## Getting Started: First Week

The goal of your first week is to **ship one tiny thing** that proves your environment works, not to absorb the entire framework. Here is a concrete day-by-day:

### Day 1 — Orientation

- Read the **I-EIP Monitor Whitepaper** end-to-end (475 lines, ~90 minutes). Do not skip §7 "What I-EIP Does NOT Detect" — it is the most important section.
- Skim **GUASS-SAI §16** (30 minutes). This is the criterion `h_ℓ(g·x) ≈ ρ_ℓ(g) · h_ℓ(x)`. If the math is unfamiliar, that's fine — you will build intuition by writing code.
- Skim the **Dear Abby EM-DAG document** (30 minutes). You do not need to memorize the domain breakdown; you need to understand the *shape*: structural layer → nullifiers → domain router → per-domain EMs.
- Set up your workstation: clone `erisml-lib`, verify CI runs locally.

### Day 2 — Environment

Follow the Environment Setup block below. Goal by end of day: `pytest tests/` passes and you can attach a probe to a tiny model (e.g., Qwen 0.5B or GPT-2 small) and print an activation.

### Day 3 — Pick a starter task

From the **First-Week Starter Tasks** list below, claim one by commenting on its tracking issue (see "Communication and Mentorship"). Read the dependencies and referenced whitepaper sections.

### Days 4–5 — Ship it

Write the smallest version that passes tests. Push a draft PR. Request review from your workstream lead. Iterate on feedback. Merge before the week ends.

**If you are not merged by end of week 1**, that is a signal to **ask for help earlier** next time — not a signal to work longer hours. Early contributors consistently underestimate how much talking-to-the-lead beats solo-debugging.

---

## Environment Setup

**Required tools:**

```bash
# Python 3.11+
python --version  # should be >= 3.11

# Clone
git clone https://github.com/ahb-sjsu/erisml-lib.git
cd erisml-lib

# Create venv
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
# .venv\Scripts\activate          # Windows

# Install (editable) with dev extras
pip install -e ".[dev,ieip]"

# Verify
pytest tests/            # should pass
mypy src/                # should be clean
```

**GPU setup (optional for Phase A probes, required for Phase D red-team):**

If you have an NVIDIA GPU, follow the `feedback_atlas_pytorch` pattern from our prior experience: always `pip install torch` *inside* the venv, and synchronize PyTorch and CUDA versions. Do not `pip install --user`; it creates subtle path collisions with the venv.

**Transformer models for testing:**

For CI / local dev, use a small open-weights model. Recommended sequence:

1. **Qwen 0.5B** (fast, CPU-viable, best for iteration)
2. **GPT-2 small** (classic interpretability testbed; `transformer_lens` has first-class support)
3. **Llama 3.1 8B** (realistic deployment scale; needs GPU)

Download with `huggingface-cli download` — do not commit model weights to the repo.

**Atlas HPC cluster:**

For anything involving real calibration corpora (>1k inputs) or large models, use Atlas. Instructions in `docs/ATLAS_OPERATIONS.md`. Always cache intermediates to `/archive/ieip/...` (cf. guardrail #5 below) — do **not** leave activation caches on scratch disks.

---

## First-Week Starter Tasks

These are tasks specifically chosen to be achievable in 1–5 days by a contributor new to the project, without blocking anyone else. Order is roughly easiest → hardest.

| Task ID | Name | Skill | Est. Hours | Why It's a Good Starter |
|---|---|---|---|---|
| **A.1.1** | Design `ProbeSpec` struct | L3–L5 | 12 | Pure design. Read the whitepaper §2.2, write a Pydantic model, add tests. No ML knowledge needed. |
| **B.1.1** | `EthicalFacts` dataclass | L3 | 8 | Smallest possible task. Type the whitepaper §5 JSON schema into Python. Get a review on PR style. |
| **B.1.2** | `EthicalJudgment` dataclass | L3 | 8 | Same shape as above. Often picked as a pair with B.1.1. |
| **C.1.1** | Audit-artifact JSON schema | L3 | 8 | Copy the whitepaper §5 schema to JSON Schema, add validator, write 5 examples. |
| **A.4.5** | DAG serialization with content-hashed version ID | L3 | 16 | Serialize the `EMDAG` data structure to JSON, hash it, round-trip test. |
| **D.1.2** | Nullifier trigger tests | L3 | 24 | Each nullifier (abuse, danger, impossibility, illegality, estrangement) gets a test. Use the Dear Abby examples as ground truth. |
| **X.5** | FAQ: when does gating fail open vs. fail closed | L3 | 16 | Writing task. Read whitepaper §2.3 and §7, produce a 1-page FAQ. Gives you deep familiarity with the trust model. |
| **A.1.6** | Benchmark probe overhead at L=12/32/80 | L3 | 16 | Once A.1.2 is merged, measure overhead on GPT-2/Llama/Qwen. Produce a report. |

**Avoid as first tasks** (these need more context):

- A.3.2 (SAE domain discovery) — L5 work, research-grade
- B.3.6 (out-of-model trust boundary test) — security-critical, requires mentorship
- C.2.6 (logical-consistency decider) — formal-methods heavy
- D.2.x (red-team) — requires deep familiarity with the framework first

---

## Picking Your First Task by Skill Level

Expanding the earlier list with context:

### If you are L2 (early-career or learning)

Start with **documentation** (X.1, X.2, X.6) or a **dataclass task** (B.1.1, B.1.2, C.1.1). These let you engage with the framework's semantics without deep implementation. Pair with an L3 or L4 mentor for your first PR.

### If you are L3 (2–5 years experience)

You are the target audience for most of the plan. Start with one of the First-Week Starter Tasks, then graduate to:

- **Spec-driven implementation:** A.3.4 (cluster review UI), A.4.1 (EMDAG data structure), B.1.3 (EM base class), B.2.5 (DecisionOutcome emission), C.1.2 (artifact serialization)
- **Testing infrastructure:** D.1.1 (regression corpus), D.1.2 (nullifier tests)

If you want to push into L4 territory, claim B.3.4 (redirect path) or C.1.5 (Merkle hash chain) after your first L3 task is merged.

### If you are L4 (5+ years experience, system design)

Claim a **pipeline task**:

- A.1.2 (PyTorch probe hooks) — foundational; many downstream tasks wait on this
- A.2.3 (transform application pipeline) — integration across calibration corpus + probes
- B.2.3 (governance aggregation function) — stakeholder weighting + lexical priority, needs careful testing
- B.3.1 (`GatedForward` wrapper) — the runtime integration that ties everything together
- C.1.4 (ECDSA signing in the audit path) — crypto-adjacent, needs careful implementation

### If you are L5 (research or deep specialist)

Take a **research task**:

- A.3.2 (SAE-based domain discovery) — requires judgment about cluster quality
- B.1.4 (EM evaluation from activations) — connects mechanistic interpretability to governance; core research question
- C.2.6 (logical-consistency decider via SGE Thm 6.4) — formal-methods heavy, o-minimal structures
- D.2.1–D.2.5 (red-team) — characterizes what the framework cannot detect; findings update whitepaper §7

L5 contributors also lead design reviews for L3/L4 PRs in their area.

---

## What "Done" Looks Like

A merged task has, at minimum:

1. **Code passes CI** — `pytest`, `mypy`, and ruff/black style all green.
2. **Tests that exercise the acceptance criterion** — not just smoke tests. For a dataclass, the test checks field constraints. For an algorithm, the test checks the mathematical property (e.g., equivariance preserved). Property-based tests (Hypothesis) strongly preferred for anything with a theorem attached.
3. **Documentation updated** — if you added a public API, it shows up in `docs/`. If you changed a core invariant, the whitepaper or sprint plan reflects it.
4. **PR description references the task ID** — e.g., "Implements A.1.2" so reviewers can cross-check.
5. **At least one reviewer approval** — from your workstream lead for new subsystems; peer review acceptable for isolated additions.
6. **Large data goes to `/archive`** (guardrail #5), not the repo.

Concrete acceptance example for **A.1.1** (`ProbeSpec` struct):

```python
# src/erisml_ieip/probes/spec.py
from pydantic import BaseModel, Field

class ProbeSpec(BaseModel):
    target_layer: int = Field(..., ge=0)
    activation_site: Literal["residual", "attn_out", "mlp_out"]
    sampling_rate: float = Field(1.0, gt=0, le=1.0)  # fraction of inferences probed
    shape: tuple[int, ...]  # expected activation shape

# tests/ieip/probes/test_spec.py
def test_probe_spec_rejects_negative_layer():
    with pytest.raises(ValidationError):
        ProbeSpec(target_layer=-1, activation_site="residual", shape=(768,))

def test_probe_spec_sampling_rate_bounds():
    with pytest.raises(ValidationError):
        ProbeSpec(target_layer=0, activation_site="residual", sampling_rate=1.5, shape=(768,))
```

If your PR looks like that — even at L2 — it's merge-ready.

---

## Communication and Mentorship

**Where to ask:**

- **Technical questions** (how does this work, what should I do here) — GitHub Discussions on `erisml-lib` under the `I-EIP Monitor` category.
- **Task-specific questions** (stuck on implementing X) — comment on the tracking issue for your task.
- **Urgent blockers** (CI broken, credentials lost, unsure if this is destructive) — tag `@ahb-sjsu` directly on the issue.
- **Governance questions** (can we change this EM, is this profile change OK) — governance-body channel; not your call to make unilaterally (guardrail #7).

**Mentorship:**

Each workstream has a **lead** (L5 or senior L4) who is responsible for reviewing PRs and answering design questions. Current leads:

- Workstream #5 (I-EIP core): TBD — see `docs/teams/WORKSTREAM_LEADS.md` for current assignments
- Workstream #9 (Domain modules): TBD
- Workstream #4 (Cryptographic): TBD
- Workstream #8 (Testing): TBD
- Workstream #11 (Documentation): TBD

**Pair programming:**

Recommended for L2 / L3 first tasks. Pair up with someone at the same level ("study group" pairing — you learn together) or one level up ("apprenticeship" pairing — they explain while you drive). Both are valuable; neither is wasted time.

**Code review expectations:**

- Reviewers respond within 2 business days
- Aim for **small PRs** (<300 lines diff). Larger PRs get split on request.
- "Nitpick" comments are prefixed `nit:` and are non-blocking
- Blocking comments explain *why* and suggest a fix
- "Approved with suggestions" is a valid review state; do not rewrite work that was merged with notes

---

## FAQ

**Q: I'm not familiar with the ErisML / DEME governance framework. Do I need to read all of GUASS-SAI first?**

No. Read §16 of GUASS-SAI (30 minutes, the only strictly required part) and the I-EIP Monitor Whitepaper (90 minutes). For other sections, read-on-demand as you encounter dependencies. The whitepaper cites specific sections for specific concepts.

**Q: I don't have a GPU. Can I still contribute?**

Yes. Most of Phase A (probe infrastructure, data structures, serialization) and Phase C (attestation, verifier) are CPU work. Phase B runtime gating can be developed against Qwen 0.5B on CPU. GPUs mainly matter for Phase D red-team work with large models.

**Q: How much math do I need?**

- L2/L3: basic linear algebra (matrix multiply, projections). You'll pick up Procrustes and regularized least squares from the GUASS §16 snippet as needed.
- L4: comfortable with linear algebra and basic probability.
- L5: differential geometry intuition helps (stratified spaces), but is not required unless you claim SGE-theorem tasks.

**Q: What's the difference between a "probe" and "activation steering"?**

A probe is **read-only**. Activation steering **writes**. I-EIP uses only probes. Writing to activations is explicitly out of scope — it changes the model's behavior in ways the monitor cannot audit.

**Q: Can I use this for my thesis / research?**

Yes, with citation. See the whitepaper's reference list. If your contribution is substantial, you are eligible for co-authorship on the whitepaper v2.0 or subsequent publications.

**Q: I found a bug in the whitepaper (math error, typo, inconsistency). What do I do?**

Open an issue with the tag `whitepaper:correction`. Math errors get priority. If you want to propose a fix, include a suggested diff.

**Q: I disagree with a design decision. How do I argue for a change?**

GitHub Discussion under `I-EIP Monitor: design`. Frame as (a) what's wrong with the current design, (b) what you propose instead, (c) what evidence supports your proposal. Design debates are welcome; drive-by objections without alternatives less so.

**Q: A guardrail seems overly restrictive for my task. Can I relax it?**

No — not without a design review. The guardrails exist because earlier failure modes produced them. If a guardrail blocks you, that is the signal to open a discussion, not the signal to work around it. "Guardrail #3 made me do a weird thing to avoid leaking gating state" is a valid design conversation. Silently bypassing it is not.

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
