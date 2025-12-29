# GUASS-SAI Project Sprint & Task Breakdown

## For Distributed Volunteer Team (50-100 Contributors)

**Document Version:** 1.0  
**Date:** December 2025  
**Source:** GUASS_SAI.md v12.0 Whitepaper

---

## Executive Summary

The Grand Unified AI Safety Stack (GUASS-SAI) is a comprehensive 10-layer architecture for building safe, auditable AI systems. This document decomposes the ~4,700 line technical whitepaper into manageable sprints and tasks suitable for a distributed team of 50-100 part-time volunteers with varying skill levels.

**Estimated Total Effort:** 18-24 months  
**Team Structure:** ~12 workstreams with 4-8 contributors each

---

## Team Structure & Skill Mapping

### Skill Level Definitions

| Level | Description | Typical Background | Hours/Week |
|-------|-------------|-------------------|------------|
| **L1 - Intern** | Learning fundamentals | CS undergrad, bootcamp | 5-10 |
| **L2 - Junior** | Can implement specs | Early career dev | 10-15 |
| **L3 - Mid** | Independent problem-solving | 2-5 years experience | 10-20 |
| **L4 - Senior** | System design capability | 5+ years, domain expertise | 10-15 |
| **L5 - PhD/Expert** | Research & architecture | Research background | 5-15 |

### Workstreams

| # | Workstream | Lead Skill | Team Size | Primary Skills |
|---|------------|------------|-----------|----------------|
| 1 | **ErisML Core** | L5 | 6-8 | PL theory, parsing, Coq |
| 2 | **Transpiler** | L4 | 8-10 | ML/NLP, Python |
| 3 | **TCB Infrastructure** | L4 | 6-8 | Systems, security |
| 4 | **Cryptographic Layer** | L5 | 4-6 | Crypto, blockchain |
| 5 | **I-EIP Monitor** | L5 | 4-6 | ML interpretability |
| 6 | **Capability Bounds** | L4 | 4-6 | Security, containers |
| 7 | **Audit & Attestation** | L3 | 6-8 | Backend, databases |
| 8 | **Testing & QA** | L3 | 8-10 | Testing, automation |
| 9 | **Domain Modules** | L3 | 8-12 | Domain expertise |
| 10 | **DevOps & Infra** | L4 | 4-6 | K8s, cloud, CI/CD |
| 11 | **Documentation** | L2 | 6-8 | Technical writing |
| 12 | **Human Studies** | L4 | 4-6 | HCI, statistics |

---

## Phase 1: Foundation (Months 1-3)

### Sprint 1.1: Project Bootstrap (Weeks 1-2)

**Goal:** Establish infrastructure and team onboarding

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 1.1.1 | Set up monorepo structure | L3 | 16 | None |
| 1.1.2 | Configure CI/CD pipeline (GitHub Actions) | L3 | 24 | 1.1.1 |
| 1.1.3 | Create contribution guidelines | L2 | 8 | None |
| 1.1.4 | Set up documentation site (MkDocs/Docusaurus) | L2 | 16 | 1.1.1 |
| 1.1.5 | Create onboarding tutorial for each skill level | L2 | 24 | 1.1.3 |
| 1.1.6 | Set up Discord/Slack with workstream channels | L1 | 8 | None |
| 1.1.7 | Define coding standards per language | L3 | 16 | None |
| 1.1.8 | Create issue templates and project boards | L2 | 8 | 1.1.1 |

**Deliverables:** Repository ready, CI/CD working, team can contribute

---

### Sprint 1.2: ErisML Parser Foundation (Weeks 3-6)

**Goal:** Implement the ErisML grammar and basic parser (§8)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 1.2.1 | Define ErisML EBNF grammar specification | L5 | 40 | None |
| 1.2.2 | Implement lexer in Python (reference impl) | L3 | 32 | 1.2.1 |
| 1.2.3 | Implement recursive descent parser | L4 | 48 | 1.2.2 |
| 1.2.4 | Define AST node types and interfaces | L4 | 24 | 1.2.1 |
| 1.2.5 | Implement AST builder from parse tree | L3 | 32 | 1.2.3, 1.2.4 |
| 1.2.6 | Create parser test suite (100+ cases) | L2 | 40 | 1.2.3 |
| 1.2.7 | Document grammar with examples | L2 | 16 | 1.2.1 |
| 1.2.8 | Implement error recovery and reporting | L3 | 24 | 1.2.3 |

**Deliverables:** Working ErisML parser, test suite, grammar docs

---

### Sprint 1.3: Normalizer Implementation (Weeks 5-8)

**Goal:** Implement deterministic normalization (N1-N7, §8.2)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 1.3.1 | N1: Implement field sorting (lexicographic) | L2 | 8 | 1.2.5 |
| 1.3.2 | N2: Implement canonical entity ID assignment | L3 | 16 | 1.2.5 |
| 1.3.3 | N3: Implement enum variant collapsing | L2 | 12 | 1.2.5 |
| 1.3.4 | N4: Implement default value removal | L2 | 12 | 1.2.5 |
| 1.3.5 | N5: Implement numeric precision normalization | L3 | 16 | 1.2.5 |
| 1.3.6 | N6: Implement collection sorting | L2 | 12 | 1.2.5 |
| 1.3.7 | N7: Implement canonical serialization | L3 | 24 | 1.3.1-1.3.6 |
| 1.3.8 | Create Normalizer class with full pipeline | L3 | 16 | 1.3.1-1.3.7 |
| 1.3.9 | Write determinism tests (same input → same output) | L2 | 24 | 1.3.8 |
| 1.3.10 | Document normalization rules | L2 | 8 | 1.3.1-1.3.7 |

**Deliverables:** Normalizer producing deterministic canonical forms

---

### Sprint 1.4: Loop Test Harness (Weeks 7-10)

**Goal:** Implement transform testing infrastructure (§10-11)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 1.4.1 | Define Transform interface/protocol | L4 | 16 | 1.2.4 |
| 1.4.2 | Implement commutator defect calculation (Ω_op) | L4 | 24 | 1.4.1 |
| 1.4.3 | Implement delta distance function (§10.2) | L3 | 16 | 1.3.8 |
| 1.4.4 | Implement Bond index (Bd = Ω_op / τ) | L3 | 8 | 1.4.2 |
| 1.4.5 | Create batch loop test runner | L3 | 24 | 1.4.2, 1.4.4 |
| 1.4.6 | Implement test result aggregation/reporting | L2 | 16 | 1.4.5 |
| 1.4.7 | Create sample transform suite (G_test) | L3 | 24 | 1.4.1 |
| 1.4.8 | Implement chain consistency testing (§12.4) | L4 | 32 | 1.4.5 |
| 1.4.9 | Create visualization for Bd distributions | L2 | 16 | 1.4.6 |

**Deliverables:** Loop test harness, sample transforms, Bd metrics

---

### Sprint 1.5: Basic Audit Artifacts (Weeks 9-12)

**Goal:** Implement audit artifact generation (§42)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 1.5.1 | Define AuditArtifact schema (JSON/Protobuf) | L3 | 16 | None |
| 1.5.2 | Implement artifact generation from pipeline | L3 | 24 | 1.3.8, 1.5.1 |
| 1.5.3 | Add state_id (SHA-256) computation | L2 | 8 | 1.3.7 |
| 1.5.4 | Implement artifact signing (Ed25519) | L3 | 16 | 1.5.2 |
| 1.5.5 | Create artifact validation utilities | L2 | 16 | 1.5.1 |
| 1.5.6 | Implement append-only local audit log | L3 | 24 | 1.5.2 |
| 1.5.7 | Create artifact versioning (v6.0 schema) | L2 | 8 | 1.5.1 |
| 1.5.8 | Write artifact schema documentation | L2 | 8 | 1.5.1 |

**Deliverables:** Audit artifacts generated, signed, logged locally

---

## Phase 2: Hardening (Months 4-6)

### Sprint 2.1: Transpiler MVP (Weeks 13-18)

**Goal:** Build LLM-based natural language to ErisML transpiler (§9)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 2.1.1 | Design transpiler prompt templates | L4 | 32 | 1.2.1 |
| 2.1.2 | Implement single-model transpiler wrapper | L3 | 24 | 2.1.1 |
| 2.1.3 | Create training/eval dataset (500+ examples) | L2-L3 | 80 | 1.2.7 |
| 2.1.4 | Implement temperature=0 determinism | L3 | 8 | 2.1.2 |
| 2.1.5 | Add input preprocessing/sanitization | L3 | 16 | 2.1.2 |
| 2.1.6 | Implement output post-processing | L3 | 16 | 2.1.2 |
| 2.1.7 | Create transpiler evaluation metrics | L4 | 24 | 2.1.3 |
| 2.1.8 | Build transpiler test suite | L2 | 32 | 2.1.3 |
| 2.1.9 | Document prompt engineering guidelines | L3 | 16 | 2.1.1 |

**Deliverables:** Working single-model transpiler, eval framework

---

### Sprint 2.2: Transpiler Ensemble (Weeks 17-22)

**Goal:** Implement Protocol T-1 ensemble disagreement detection (§9.1)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 2.2.1 | Design ensemble architecture (3+ models) | L4 | 24 | 2.1.2 |
| 2.2.2 | Implement parallel transpiler execution | L3 | 24 | 2.2.1 |
| 2.2.3 | Implement canonical form comparison | L3 | 16 | 2.2.2, 1.3.8 |
| 2.2.4 | Implement disagreement detection logic | L3 | 16 | 2.2.3 |
| 2.2.5 | Create DisagreementWitness recording | L2 | 8 | 2.2.4 |
| 2.2.6 | Implement escalation routing | L3 | 16 | 2.2.4 |
| 2.2.7 | Add ensemble performance monitoring | L2 | 16 | 2.2.2 |
| 2.2.8 | Tune disagreement thresholds | L4 | 24 | 2.2.4 |

**Deliverables:** 3-model ensemble with disagreement handling

---

### Sprint 2.3: OOD Detection (Weeks 19-24)

**Goal:** Implement Protocol T-3 distribution shift detection (§9.3)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 2.3.1 | Implement embedding extraction | L3 | 16 | 2.1.3 |
| 2.3.2 | Build training distribution profile | L4 | 24 | 2.3.1, 2.1.3 |
| 2.3.3 | Implement distance-to-training metric | L3 | 16 | 2.3.1, 2.3.2 |
| 2.3.4 | Calibrate OOD threshold (2σ) | L4 | 24 | 2.3.3 |
| 2.3.5 | Implement OOD detection in pipeline | L3 | 16 | 2.3.4 |
| 2.3.6 | Create OOD test cases (synthetic drift) | L3 | 24 | 2.3.5 |
| 2.3.7 | Add OOD metrics to audit artifacts | L2 | 8 | 2.3.5, 1.5.2 |

**Deliverables:** OOD detection integrated, threshold calibrated

---

### Sprint 2.4: TCB Process Isolation (Weeks 21-26)

**Goal:** Implement Trusted Computing Base isolation (§2)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 2.4.1 | Design TCB process architecture | L5 | 32 | None |
| 2.4.2 | Implement IPC protocol (gRPC/Unix sockets) | L4 | 32 | 2.4.1 |
| 2.4.3 | Configure seccomp syscall filtering | L4 | 24 | 2.4.1 |
| 2.4.4 | Implement namespace isolation (PID, net, mount) | L4 | 24 | 2.4.1 |
| 2.4.5 | Configure cgroups resource limits | L3 | 16 | 2.4.1 |
| 2.4.6 | Implement read-only model weights mount | L3 | 8 | 2.4.1 |
| 2.4.7 | Create isolation verification tests | L3 | 32 | 2.4.2-2.4.6 |
| 2.4.8 | Document TCB boundaries and guarantees | L3 | 16 | 2.4.1 |
| 2.4.9 | Implement fail-closed behavior (TCB-3) | L4 | 24 | 2.4.2 |

**Deliverables:** TCB isolation working, verified, documented

---

### Sprint 2.5: I-EIP Monitor Foundation (Weeks 23-26)

**Goal:** Implement internal equivariance monitoring (§16)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 2.5.1 | Design activation extraction hooks | L5 | 24 | None |
| 2.5.2 | Implement activation logging infrastructure | L4 | 32 | 2.5.1 |
| 2.5.3 | Implement ρ estimation (Procrustes) | L5 | 40 | 2.5.2 |
| 2.5.4 | Implement equivariance error computation | L4 | 24 | 2.5.3 |
| 2.5.5 | Create I-EIP metrics dashboard | L3 | 24 | 2.5.4 |
| 2.5.6 | Implement drift detection baseline | L4 | 24 | 2.5.4 |
| 2.5.7 | Create non-degeneracy checks | L4 | 16 | 2.5.4 |
| 2.5.8 | Document I-EIP limitations honestly | L3 | 8 | 2.5.1 |

**Deliverables:** I-EIP monitoring operational, metrics visible

---

## Phase 3: Cryptographic Layer (Months 5-8)

### Sprint 3.1: Certificate Authority Hierarchy (Weeks 25-30)

**Goal:** Implement 3-tier CA structure (§38)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 3.1.1 | Design CA hierarchy architecture | L5 | 24 | None |
| 3.1.2 | Implement Root CA (offline HSM simulation) | L4 | 32 | 3.1.1 |
| 3.1.3 | Implement Intermediate CA | L4 | 24 | 3.1.2 |
| 3.1.4 | Implement deployment certificate issuance | L3 | 24 | 3.1.3 |
| 3.1.5 | Implement certificate revocation (CRL/OCSP) | L4 | 32 | 3.1.3 |
| 3.1.6 | Create key ceremony procedures | L5 | 24 | 3.1.2 |
| 3.1.7 | Implement certificate validation chain | L3 | 24 | 3.1.4 |
| 3.1.8 | Create CA administration tools | L3 | 24 | 3.1.2-3.1.5 |
| 3.1.9 | Document key rotation procedures | L3 | 16 | 3.1.6 |

**Deliverables:** 3-tier CA operational, keys generated

---

### Sprint 3.2: Blockchain Attestation (Weeks 29-34)

**Goal:** Implement hybrid attestation (§39, §4.2)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 3.2.1 | Design hybrid attestation architecture | L5 | 24 | None |
| 3.2.2 | Implement Solidity smart contract (§41) | L4 | 40 | 3.2.1 |
| 3.2.3 | Deploy to L2 testnet (Polygon Mumbai) | L3 | 16 | 3.2.2 |
| 3.2.4 | Implement L2 attestation publisher | L3 | 24 | 3.2.3 |
| 3.2.5 | Implement local Merkle accumulator fallback | L4 | 32 | 3.2.1 |
| 3.2.6 | Implement gas price monitoring/fallback | L3 | 16 | 3.2.4 |
| 3.2.7 | Add attestation receipt verification | L3 | 16 | 3.2.4 |
| 3.2.8 | Implement emergency offline mode | L3 | 16 | 3.2.5 |
| 3.2.9 | Create attestation status dashboard | L2 | 16 | 3.2.4 |

**Deliverables:** Hybrid attestation with L2, fallbacks working

---

### Sprint 3.3: DHT/IPFS Integration (Weeks 33-36)

**Goal:** Implement off-chain artifact storage (§39.2)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 3.3.1 | Set up IPFS cluster configuration | L3 | 16 | None |
| 3.3.2 | Implement artifact upload to IPFS | L3 | 16 | 3.3.1 |
| 3.3.3 | Implement CID-based retrieval | L2 | 12 | 3.3.2 |
| 3.3.4 | Configure pinning service (3x replication) | L3 | 16 | 3.3.1 |
| 3.3.5 | Implement 7-year retention policy | L3 | 16 | 3.3.4 |
| 3.3.6 | Link on-chain attestation to off-chain CID | L3 | 16 | 3.2.4, 3.3.2 |
| 3.3.7 | Create artifact integrity verification | L3 | 16 | 3.3.3 |
| 3.3.8 | Monitor IPFS cluster health | L2 | 8 | 3.3.4 |

**Deliverables:** IPFS storage working, linked to blockchain

---

### Sprint 3.4: Zero-Trust Session Protocol (Weeks 35-38)

**Goal:** Implement per-request authentication (§40)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 3.4.1 | Design session protocol specification | L4 | 24 | 3.1.4 |
| 3.4.2 | Implement session certificate issuance | L3 | 16 | 3.1.4, 3.4.1 |
| 3.4.3 | Implement request signing (Ed25519) | L3 | 16 | 3.4.2 |
| 3.4.4 | Implement certificate validation chain | L3 | 16 | 3.4.2 |
| 3.4.5 | Implement nonce/replay prevention | L3 | 16 | 3.4.3 |
| 3.4.6 | Implement capability grant verification | L3 | 24 | 3.4.2 |
| 3.4.7 | Add session expiry handling | L2 | 8 | 3.4.2 |
| 3.4.8 | Create session protocol test suite | L2 | 24 | 3.4.1-3.4.7 |

**Deliverables:** Zero-trust sessions operational

---

## Phase 4: Capability & Corrigibility (Months 7-10)

### Sprint 4.1: Capability Bounds Enforcement (Weeks 37-42)

**Goal:** Implement hardware/OS capability enforcement (§22-26)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 4.1.1 | Define capability tier specifications | L4 | 16 | None |
| 4.1.2 | Implement CapabilityIndex computation | L4 | 24 | 4.1.1 |
| 4.1.3 | Implement resource quota enforcement (cgroups) | L3 | 24 | 2.4.5 |
| 4.1.4 | Implement tool whitelist enforcement | L3 | 24 | 4.1.1 |
| 4.1.5 | Implement rate limiting | L3 | 16 | 4.1.4 |
| 4.1.6 | Implement impact estimation (§26) | L4 | 32 | 4.1.1 |
| 4.1.7 | Implement approval gates for high-impact | L3 | 24 | 4.1.6 |
| 4.1.8 | Create capability verification tests | L3 | 24 | 4.1.2-4.1.7 |
| 4.1.9 | Implement adversarial capability index (§A-1) | L5 | 24 | 4.1.2 |

**Deliverables:** Capability bounds enforced, indexed

---

### Sprint 4.2: Corrigibility Tests (Weeks 41-46)

**Goal:** Implement corrigibility axiom testing (§28-30)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 4.2.1 | Design shutdown test protocol (C1) | L4 | 24 | None |
| 4.2.2 | Implement shutdown compliance tests | L3 | 24 | 4.2.1 |
| 4.2.3 | Design modification acceptance tests (C2) | L4 | 24 | None |
| 4.2.4 | Implement transparency tests (C3) | L3 | 24 | None |
| 4.2.5 | Implement deference tests (C4) | L3 | 24 | None |
| 4.2.6 | Implement non-manipulation tests (C5) | L4 | 32 | None |
| 4.2.7 | Create corrigibility test harness | L3 | 24 | 4.2.2-4.2.6 |
| 4.2.8 | Define passing thresholds | L5 | 16 | 4.2.7 |
| 4.2.9 | Document limitations honestly | L3 | 8 | 4.2.7 |

**Deliverables:** Corrigibility test suite, passing criteria defined

---

### Sprint 4.3: Emergency Override System (Weeks 45-50)

**Goal:** Implement tiered emergency overrides (§6, §E-1 to E-3)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 4.3.1 | Design tiered mutability architecture | L5 | 24 | None |
| 4.3.2 | Implement M-of-N approval system | L4 | 32 | 3.1.4 |
| 4.3.3 | Implement 24-hour auto-revert | L3 | 16 | 4.3.2 |
| 4.3.4 | Implement non-escalatory verification | L4 | 24 | 4.3.2 |
| 4.3.5 | Implement override fatigue protection | L3 | 16 | 4.3.2 |
| 4.3.6 | Create out-of-band approval channel | L4 | 32 | 4.3.2 |
| 4.3.7 | Implement incident commander protocol | L3 | 16 | 4.3.6 |
| 4.3.8 | Create override audit logging | L2 | 16 | 4.3.2, 1.5.6 |
| 4.3.9 | Test override workflows end-to-end | L3 | 24 | 4.3.1-4.3.8 |

**Deliverables:** Emergency override system operational

---

## Phase 5: Domain Modules (Months 8-12)

### Sprint 5.1: Medical Domain Module (Weeks 49-56)

**Goal:** Build G_medical transform suite and calibration

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 5.1.1 | Define medical domain ontology in ErisML | L4 | 40 | 1.2.1 |
| 5.1.2 | Create medical scenario corpus (200+) | L3 | 60 | 5.1.1 |
| 5.1.3 | Implement medical transforms (paraphrase, etc.) | L3 | 48 | 5.1.1 |
| 5.1.4 | Define field severity weights (§10.3) | L4 | 16 | 5.1.1 |
| 5.1.5 | Run calibration study (τ) with medical experts | L4 | 80 | 5.1.2, 5.1.3 |
| 5.1.6 | Compute Krippendorff's α (target >0.67) | L4 | 16 | 5.1.5 |
| 5.1.7 | Establish Bd baseline for G_medical | L3 | 24 | 5.1.3, 5.1.5 |
| 5.1.8 | Create boundary probes (≥15%) | L3 | 24 | 5.1.2 |
| 5.1.9 | Document medical module limitations | L3 | 16 | 5.1.7 |

**Deliverables:** G_medical_v1, τ calibrated, Bd < 0.15

---

### Sprint 5.2: Content Moderation Module (Weeks 53-60)

**Goal:** Build G_content transform suite

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 5.2.1 | Define content moderation ontology | L4 | 32 | 1.2.1 |
| 5.2.2 | Create content scenario corpus (300+) | L3 | 60 | 5.2.1 |
| 5.2.3 | Implement content transforms | L3 | 40 | 5.2.1 |
| 5.2.4 | Define field severity weights | L4 | 16 | 5.2.1 |
| 5.2.5 | Run calibration study with moderators | L4 | 80 | 5.2.2, 5.2.3 |
| 5.2.6 | Compute Krippendorff's α | L4 | 16 | 5.2.5 |
| 5.2.7 | Establish Bd baseline for G_content | L3 | 24 | 5.2.3, 5.2.5 |
| 5.2.8 | Create boundary probes | L3 | 24 | 5.2.2 |

**Deliverables:** G_content_v1, Bd < 0.15

---

### Sprint 5.3: Financial Domain Module (Weeks 57-64)

**Goal:** Build G_finance transform suite

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 5.3.1 | Define financial domain ontology | L4 | 32 | 1.2.1 |
| 5.3.2 | Create financial scenario corpus (200+) | L3 | 60 | 5.3.1 |
| 5.3.3 | Implement financial transforms | L3 | 40 | 5.3.1 |
| 5.3.4 | Define field severity weights | L4 | 16 | 5.3.1 |
| 5.3.5 | Run calibration study | L4 | 80 | 5.3.2, 5.3.3 |
| 5.3.6 | Compute Krippendorff's α | L4 | 16 | 5.3.5 |
| 5.3.7 | Establish Bd baseline | L3 | 24 | 5.3.3, 5.3.5 |

**Deliverables:** G_finance_v1, Bd < 0.1

---

### Sprint 5.4: General Assistant Module (Weeks 61-68)

**Goal:** Build G_general transform suite

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 5.4.1 | Define general assistant ontology | L4 | 40 | 1.2.1 |
| 5.4.2 | Create general scenario corpus (500+) | L3 | 80 | 5.4.1 |
| 5.4.3 | Implement general transforms | L3 | 48 | 5.4.1 |
| 5.4.4 | Define field severity weights | L4 | 16 | 5.4.1 |
| 5.4.5 | Run calibration study | L4 | 80 | 5.4.2, 5.4.3 |
| 5.4.6 | Compute Krippendorff's α | L4 | 16 | 5.4.5 |
| 5.4.7 | Establish Bd baseline | L3 | 24 | 5.4.3, 5.4.5 |

**Deliverables:** G_general_v1, Bd < 0.2

---

## Phase 6: Testing & Verification (Months 10-14)

### Sprint 6.1: Formal Verification - Parser (Weeks 65-76)

**Goal:** Coq verification of ErisML parser (§2.3 Tier 1)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 6.1.1 | Define grammar in Coq | L5 | 40 | 1.2.1 |
| 6.1.2 | Implement parser in Coq | L5 | 80 | 6.1.1 |
| 6.1.3 | Prove parser accepts exactly grammar L | L5 | 120 | 6.1.2 |
| 6.1.4 | Prove parser termination | L5 | 40 | 6.1.2 |
| 6.1.5 | Extract verified parser to OCaml/Haskell | L5 | 32 | 6.1.3 |
| 6.1.6 | Create verification documentation | L4 | 24 | 6.1.3 |
| 6.1.7 | Compare verified vs reference parser | L3 | 16 | 6.1.5, 1.2.3 |

**Deliverables:** Coq-verified parser, extraction

---

### Sprint 6.2: Formal Verification - Normalizer (Weeks 73-84)

**Goal:** Coq verification of normalizer (§2.3 Tier 2)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 6.2.1 | Specify N1-N7 in Coq | L5 | 48 | 1.3.1-1.3.7 |
| 6.2.2 | Implement normalizer in Coq | L5 | 80 | 6.2.1 |
| 6.2.3 | Prove determinism | L5 | 60 | 6.2.2 |
| 6.2.4 | Prove termination | L5 | 40 | 6.2.2 |
| 6.2.5 | Extract verified normalizer | L5 | 24 | 6.2.3 |
| 6.2.6 | Create verification documentation | L4 | 16 | 6.2.3 |

**Deliverables:** Coq-verified normalizer

---

### Sprint 6.3: Red Team Engagement (Weeks 77-88)

**Goal:** 1000+ hours adversarial testing (§52)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 6.3.1 | Create red team engagement plan | L5 | 24 | All Phase 1-5 |
| 6.3.2 | Recruit external red team members | L4 | 16 | 6.3.1 |
| 6.3.3 | Execute redescription attack testing | L4 | 200 | 6.3.1 |
| 6.3.4 | Execute boundary probing | L4 | 200 | 6.3.1 |
| 6.3.5 | Execute TCB bypass attempts | L5 | 200 | 6.3.1 |
| 6.3.6 | Execute side-channel analysis | L5 | 150 | 6.3.1 |
| 6.3.7 | Execute social engineering tests | L4 | 150 | 6.3.1 |
| 6.3.8 | Document all findings | L3 | 40 | 6.3.3-6.3.7 |
| 6.3.9 | Triage and prioritize remediation | L4 | 24 | 6.3.8 |

**Deliverables:** Red team report, remediation plan

---

### Sprint 6.4: Remediation (Weeks 85-92)

**Goal:** Address red team findings

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 6.4.1 | Fix critical vulnerabilities | L4-L5 | Variable | 6.3.9 |
| 6.4.2 | Fix high vulnerabilities | L4 | Variable | 6.3.9 |
| 6.4.3 | Document mitigations | L3 | Variable | 6.4.1-6.4.2 |
| 6.4.4 | Regression testing | L3 | Variable | 6.4.1-6.4.2 |
| 6.4.5 | Update threat model | L4 | 16 | 6.4.1-6.4.2 |

**Deliverables:** Vulnerabilities addressed, documentation updated

---

## Phase 7: Integration & Deployment (Months 14-18)

### Sprint 7.1: Full Pipeline Integration (Weeks 89-96)

**Goal:** Integrate all components end-to-end

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 7.1.1 | Create integration architecture diagram | L4 | 16 | All previous |
| 7.1.2 | Implement end-to-end pipeline | L4 | 48 | 7.1.1 |
| 7.1.3 | Create integration test suite | L3 | 48 | 7.1.2 |
| 7.1.4 | Performance benchmarking | L3 | 24 | 7.1.2 |
| 7.1.5 | Latency optimization (target <500ms) | L4 | 40 | 7.1.4 |
| 7.1.6 | Throughput optimization | L4 | 32 | 7.1.4 |
| 7.1.7 | Create deployment configuration | L3 | 24 | 7.1.5-7.1.6 |

**Deliverables:** Integrated system, performance validated

---

### Sprint 7.2: CI/CD with Bd Gating (Weeks 93-98)

**Goal:** Implement Bd-gated deployments (§51)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 7.2.1 | Design Bd gating workflow | L4 | 16 | 1.4.5 |
| 7.2.2 | Implement Bd computation in CI | L3 | 24 | 7.2.1 |
| 7.2.3 | Implement deployment blocking on Bd > threshold | L3 | 16 | 7.2.2 |
| 7.2.4 | Create Bd trend reporting | L2 | 16 | 7.2.2 |
| 7.2.5 | Implement canary deployment with Bd | L3 | 24 | 7.2.3 |
| 7.2.6 | Document deployment gates | L2 | 8 | 7.2.3 |

**Deliverables:** CI/CD with Bd gating operational

---

### Sprint 7.3: Production Monitoring (Weeks 97-104)

**Goal:** Production observability and alerting

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 7.3.1 | Implement production Bd monitoring | L3 | 24 | 7.1.2 |
| 7.3.2 | Create alerting for Bd drift | L3 | 16 | 7.3.1 |
| 7.3.3 | Implement veto rate monitoring | L3 | 16 | 7.1.2 |
| 7.3.4 | Create operational dashboards | L2 | 32 | 7.3.1-7.3.3 |
| 7.3.5 | Implement log aggregation | L3 | 24 | 7.1.2 |
| 7.3.6 | Create incident response playbooks | L3 | 24 | 7.3.1-7.3.5 |
| 7.3.7 | Set up on-call rotation | L2 | 8 | 7.3.6 |

**Deliverables:** Production monitoring operational

---

## Phase 8: Scaling & Governance (Months 16-24)

### Sprint 8.1: Recursive Safety (Weeks 105-116)

**Goal:** Implement provisioner safety (§32-36)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 8.1.1 | Design provisioner architecture | L5 | 40 | All previous |
| 8.1.2 | Implement capability inheritance rules (R1) | L5 | 48 | 8.1.1 |
| 8.1.3 | Implement monitoring inheritance (R2) | L4 | 32 | 8.1.1 |
| 8.1.4 | Implement resource constraints (R3) | L4 | 32 | 8.1.1 |
| 8.1.5 | Implement termination rights (R4) | L4 | 24 | 8.1.1 |
| 8.1.6 | Test recursive safety properties | L4 | 40 | 8.1.2-8.1.5 |

**Deliverables:** Provisioner with recursive safety

---

### Sprint 8.2: Transform Suite Governance (Weeks 109-120)

**Goal:** Implement G governance (§12)

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 8.2.1 | Create G versioning system (G-1) | L3 | 24 | None |
| 8.2.2 | Implement G public review process (G-2) | L3 | 32 | 8.2.1 |
| 8.2.3 | Implement coverage tracking (G-3) | L4 | 40 | 8.2.1 |
| 8.2.4 | Implement anti-Goodharting canaries (G-4) | L4 | 32 | 8.2.1 |
| 8.2.5 | Create quarterly expansion process (G-5) | L3 | 24 | 8.2.1 |
| 8.2.6 | Implement canary isolation (§C-1) | L4 | 32 | 8.2.4 |
| 8.2.7 | Document governance procedures | L2 | 24 | 8.2.1-8.2.6 |

**Deliverables:** G governance operational

---

### Sprint 8.3: Third-Party Audit (Weeks 113-124)

**Goal:** Prepare for and support external audit

| Task ID | Task | Skill | Est. Hours | Dependencies |
|---------|------|-------|------------|--------------|
| 8.3.1 | Prepare audit documentation package | L4 | 40 | All previous |
| 8.3.2 | Engage external auditors | L5 | 16 | 8.3.1 |
| 8.3.3 | Support audit process | L3-L5 | 160 | 8.3.2 |
| 8.3.4 | Address audit findings | L4 | Variable | 8.3.3 |
| 8.3.5 | Publish audit results | L3 | 16 | 8.3.4 |

**Deliverables:** External audit complete, published

---

## Appendix A: Task Assignment Guidelines

### Matching Tasks to Skill Levels

**L1 (Intern) Tasks:**
- Documentation writing
- Test case creation (following templates)
- Dashboard UI work
- Code review (learning)
- Issue triage

**L2 (Junior) Tasks:**
- Implementing well-specified functions
- Unit test writing
- Integration test execution
- Documentation
- Simple feature implementation

**L3 (Mid) Tasks:**
- Module implementation
- Test suite design
- Performance optimization
- Code review (active)
- Technical documentation

**L4 (Senior) Tasks:**
- System design
- Security implementation
- Protocol design
- Calibration studies
- Architecture review

**L5 (PhD/Expert) Tasks:**
- Formal verification
- Research design
- Threat modeling
- Algorithm development
- Architecture decisions

---

## Appendix B: Coordination Model

### Weekly Rhythms

**All Teams:**
- Monday: Weekly standup (async Slack post)
- Wednesday: Sync meeting (30 min, optional)
- Friday: Progress update + blockers

**Cross-Team:**
- Bi-weekly architecture review (leads)
- Monthly all-hands demo
- Quarterly planning

### Communication Channels

| Channel | Purpose | Frequency |
|---------|---------|-----------|
| #general | Announcements | As needed |
| #workstream-* | Team discussion | Daily |
| #help | Questions | As needed |
| #wins | Celebrations | Weekly |
| #blockers | Escalation | As needed |

---

## Appendix C: Success Metrics

### Phase Gate Criteria

| Phase | Gate Criteria |
|-------|---------------|
| 1 | Parser passes 100% test suite, Normalizer deterministic |
| 2 | Transpiler >95% accuracy, TCB isolation verified |
| 3 | CA operational, Attestation working on testnet |
| 4 | Capability bounds enforced, Corrigibility tests passing |
| 5 | At least 2 domain modules with Bd < threshold |
| 6 | Red team complete, Critical/High issues resolved |
| 7 | E2E latency <500ms, Bd gating in CI |
| 8 | External audit passed, Governance operational |

---

## Appendix D: Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Volunteer churn | High | Clear onboarding, modular tasks |
| Scope creep | High | Strict phase gates |
| Formal verification delays | Medium | Start early, parallel tracks |
| Blockchain cost spikes | Medium | Hybrid attestation architecture |
| Calibration study delays | Medium | Start recruiting early |
| Integration complexity | High | Continuous integration |

---

## Document Metadata

**Created:** December 2025  
**Author:** AI-Assisted Project Planning  
**Source:** GUASS_SAI.md v12.0  
**Total Estimated Effort:** ~8,000-12,000 person-hours  
**Recommended Team Size:** 60-80 active contributors
