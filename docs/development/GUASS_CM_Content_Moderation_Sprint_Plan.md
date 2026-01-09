# GUASS-CM: Content Moderation Safety Stack

## Sprint & Task Breakdown for Distributed Volunteer Team

**Document Version:** 1.0  
**Date:** December 2025  
**Adapted From:** GUASS-SAI v12.0 Whitepaper  
**Target Domain:** Content Moderation for Mid-Size Platforms

---

## Executive Summary

This plan adapts the Grand Unified AI Safety Stack to build an open-source content moderation system that provides **consistent, auditable, explainable decisions**. The core value proposition: the same content described or formatted differently should receive the same moderation decision.

**Target Users:** 
- Mid-size platforms (10K-10M users) without dedicated Trust & Safety teams
- Discord servers, forums, community platforms
- Startups needing moderation but lacking resources for custom ML

**Key Differentiator:** Measurable consistency (Bond index) + audit trails + human escalation

**Timeline:** 12 months to production-ready MVP  
**Team Size:** 30-50 part-time volunteers

---

## Why Content Moderation?

| Factor | Advantage |
|--------|-----------|
| **Regulatory burden** | Light (no FDA, FINRA, etc.) |
| **Real problem** | Platforms genuinely struggle with inconsistency |
| **Measurable value** | Bd metric directly applies ("same content, same decision") |
| **Harm ceiling** | Mistakes are bad but not catastrophic |
| **Potential adopters** | Thousands of mid-size platforms |
| **Funding potential** | Grants (Mozilla, NSF), platform partnerships |
| **Demonstrates GUASS** | Full stack proof-of-concept |

---

## Simplified Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GUASS-CM STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Content   │───▶│ Transpiler  │───▶│  ContentML Parser   │ │
│  │   Input     │    │ (LLM-based) │    │  (Structured Form)  │ │
│  └─────────────┘    └─────────────┘    └──────────┬──────────┘ │
│                                                   │             │
│                                        ┌──────────▼──────────┐ │
│                                        │    Normalizer       │ │
│                                        │    (Canonical Form) │ │
│                                        └──────────┬──────────┘ │
│                                                   │             │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────▼──────────┐ │
│  │   Policy    │───▶│  Constraint │───▶│     Decision        │ │
│  │   Rules     │    │  Evaluator  │    │  (Allow/Flag/Remove)│ │
│  └─────────────┘    └─────────────┘    └──────────┬──────────┘ │
│                                                   │             │
│                     ┌─────────────────────────────▼───────────┐│
│                     │            Audit Trail                  ││
│                     │  (Why this decision? Reproducible?)     ││
│                     └─────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**What We're NOT Building:**
- Real-time video/image analysis (use existing APIs)
- The underlying content classifiers (use Claude, GPT, Perspective API)
- A full platform (just the moderation decision layer)

**What We ARE Building:**
- Consistency layer on top of existing classifiers
- Structured decision format with audit trails
- Loop testing to measure/improve consistency
- Human escalation workflows
- Policy configuration interface

---

## Team Structure (Streamlined)

| # | Workstream | Lead | Size | Focus |
|---|------------|------|------|-------|
| 1 | **Core Engine** | L4 | 6-8 | Parser, normalizer, decision engine |
| 2 | **Transpiler** | L4 | 4-6 | NL content → ContentML |
| 3 | **Loop Testing** | L3 | 4-6 | Bd measurement, transform suites |
| 4 | **Policy & Rules** | L3 | 4-6 | Constraint language, rule engine |
| 5 | **Integrations** | L3 | 4-6 | Discord, Slack, REST API |
| 6 | **UI/Dashboard** | L2 | 4-6 | Moderator interface, audit viewer |
| 7 | **Docs & Community** | L2 | 4-6 | Documentation, onboarding |

**Total:** ~35-45 contributors

---

## Phase 1: Foundation (Months 1-3)

### Sprint 1.1: Project Setup (Weeks 1-2)

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 1.1.1 | Monorepo setup (TypeScript + Python) | L3 | 16 | |
| 1.1.2 | CI/CD pipeline | L3 | 16 | GitHub Actions |
| 1.1.3 | Documentation site | L2 | 12 | Docusaurus |
| 1.1.4 | Contributing guide | L2 | 8 | |
| 1.1.5 | Discord server for contributors | L1 | 4 | |
| 1.1.6 | Project board setup | L1 | 4 | |

**Deliverable:** Repository ready, team can contribute

---

### Sprint 1.2: ContentML Grammar (Weeks 3-5)

**Goal:** Define the structured representation for moderation decisions

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 1.2.1 | Define ContentML schema | L4 | 32 | See schema below |
| 1.2.2 | Implement parser (TypeScript) | L3 | 24 | |
| 1.2.3 | Implement parser (Python) | L3 | 24 | |
| 1.2.4 | Parser test suite (200+ cases) | L2 | 32 | |
| 1.2.5 | Schema documentation | L2 | 12 | |

**ContentML Schema (Draft):**

```yaml
ContentML:
  content:
    id: string
    type: enum[text, image, video, link, file]
    text_content: string?          # if text
    media_hash: string?            # if media
    media_description: string?     # AI-generated description
    
  context:
    platform: string
    channel_type: enum[public, private, dm, broadcast]
    author_account_age_days: int
    author_prior_violations: int
    thread_context: string?        # surrounding messages
    
  signals:
    toxicity: float[0-1]           # from classifier
    spam_score: float[0-1]
    sexual_content: float[0-1]
    violence: float[0-1]
    self_harm: float[0-1]
    misinformation_risk: float[0-1]
    minor_involvement: bool
    pii_detected: bool
    
  classification:
    primary_category: enum[
      SPAM,
      HARASSMENT,
      HATE_SPEECH,
      SEXUAL_CONTENT,
      VIOLENCE,
      SELF_HARM,
      MISINFORMATION,
      ILLEGAL_ACTIVITY,
      PII_EXPOSURE,
      CLEAN
    ]
    confidence: float[0-1]
    secondary_categories: list[enum]
    
  decision:
    action: enum[ALLOW, FLAG_REVIEW, AUTO_REMOVE, ESCALATE]
    severity: enum[NONE, LOW, MEDIUM, HIGH, CRITICAL]
    reversibility: enum[REVERSIBLE, SEMI_REVERSIBLE, PERMANENT]
    explanation_code: string
```

**Deliverable:** ContentML parser, schema docs

---

### Sprint 1.3: Normalizer (Weeks 5-7)

**Goal:** Canonical form for consistent hashing/comparison

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 1.3.1 | Implement field sorting | L2 | 8 | |
| 1.3.2 | Implement float rounding (3 decimals) | L2 | 4 | |
| 1.3.3 | Implement enum canonicalization | L2 | 4 | |
| 1.3.4 | Implement canonical serialization | L3 | 12 | |
| 1.3.5 | Implement state_id (SHA-256) | L2 | 4 | |
| 1.3.6 | Determinism test suite | L2 | 16 | Same input → same output |
| 1.3.7 | Cross-language consistency tests | L3 | 16 | TS and Python must match |

**Deliverable:** Normalizer producing identical canonical forms in both languages

---

### Sprint 1.4: Transform Suite v0 (Weeks 6-9)

**Goal:** Initial set of transforms for loop testing

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 1.4.1 | Define Transform interface | L3 | 8 | |
| 1.4.2 | Implement paraphrase transforms | L3 | 24 | Using LLM to rephrase |
| 1.4.3 | Implement formatting transforms | L2 | 16 | Caps, spacing, punctuation |
| 1.4.4 | Implement context perturbations | L3 | 16 | Different channel types |
| 1.4.5 | Implement threshold perturbations | L2 | 12 | Classifier score ±ε |
| 1.4.6 | Document transform suite G_cm_v0 | L2 | 8 | |

**Initial Transform Suite (G_cm_v0):**

| Transform | Description | Example |
|-----------|-------------|---------|
| `paraphrase_mild` | Light rewording | "you're stupid" → "you are dumb" |
| `paraphrase_strong` | Heavy rewording | "kys" → "you should end your life" |
| `caps_normalize` | Case changes | "YOU SUCK" → "you suck" |
| `punctuation_strip` | Remove punctuation | "Die!!!" → "Die" |
| `leetspeak_decode` | Decode obfuscation | "h4t3" → "hate" |
| `emoji_to_text` | Describe emojis | "🔪🩸" → "[knife emoji][blood emoji]" |
| `context_public_to_dm` | Change channel type | Public → DM |
| `threshold_jitter` | Add noise to scores | toxicity ±0.05 |

**Deliverable:** 8-10 working transforms

---

### Sprint 1.5: Loop Test Harness (Weeks 8-11)

**Goal:** Measure consistency (Bond index)

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 1.5.1 | Implement Ω_op calculation | L3 | 16 | |
| 1.5.2 | Implement Δ distance function | L3 | 12 | Field-weighted Hamming |
| 1.5.3 | Implement Bd = Ω_op / τ | L2 | 4 | |
| 1.5.4 | Implement batch loop test runner | L3 | 20 | |
| 1.5.5 | Implement result aggregation | L2 | 12 | Mean, p95, max, witnesses |
| 1.5.6 | Create Bd visualization | L2 | 16 | Charts, histograms |
| 1.5.7 | Define field severity weights | L4 | 8 | See table below |

**Field Severity Weights (Content Moderation):**

| Field | Weight | Rationale |
|-------|--------|-----------|
| `decision.action` | 1.0 | This is the whole point |
| `classification.primary_category` | 0.9 | Determines action |
| `signals.minor_involvement` | 1.0 | Safety-critical |
| `decision.severity` | 0.7 | Affects consequences |
| `signals.self_harm` | 0.9 | Safety-critical |
| `signals.toxicity` | 0.4 | Input signal |
| `context.channel_type` | 0.2 | Context factor |

**Deliverable:** Loop test harness, Bd metrics, visualizations

---

### Sprint 1.6: Basic Decision Engine (Weeks 10-12)

**Goal:** Rule-based decision engine (before ML)

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 1.6.1 | Design rule language | L4 | 24 | YAML-based policies |
| 1.6.2 | Implement rule parser | L3 | 16 | |
| 1.6.3 | Implement constraint evaluator | L3 | 20 | |
| 1.6.4 | Implement decision logic | L3 | 16 | |
| 1.6.5 | Create default policy set | L3 | 16 | Conservative defaults |
| 1.6.6 | Policy documentation | L2 | 8 | |

**Example Policy (YAML):**

```yaml
policy_name: "default_v1"
version: "1.0"

rules:
  - name: "auto_remove_csam"
    condition:
      AND:
        - signals.sexual_content > 0.8
        - signals.minor_involvement == true
    action: AUTO_REMOVE
    severity: CRITICAL
    escalate: true
    
  - name: "flag_high_toxicity"
    condition:
      AND:
        - signals.toxicity > 0.85
        - classification.primary_category == HARASSMENT
    action: FLAG_REVIEW
    severity: HIGH
    
  - name: "allow_low_risk"
    condition:
      AND:
        - signals.toxicity < 0.3
        - signals.spam_score < 0.3
        - signals.minor_involvement == false
    action: ALLOW
    severity: NONE

default_action: FLAG_REVIEW
```

**Deliverable:** Working rule engine with default policies

---

## Phase 2: Transpiler & Integrations (Months 4-6)

### Sprint 2.1: Transpiler MVP (Weeks 13-17)

**Goal:** Convert raw content + classifier output → ContentML

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 2.1.1 | Design prompt template | L4 | 24 | |
| 2.1.2 | Implement single-model transpiler | L3 | 20 | Claude API |
| 2.1.3 | Create training examples (300+) | L2 | 48 | Labeled content → ContentML |
| 2.1.4 | Implement output validation | L3 | 12 | Must parse as valid ContentML |
| 2.1.5 | Implement retry/fallback logic | L2 | 8 | |
| 2.1.6 | Transpiler accuracy eval | L3 | 24 | |
| 2.1.7 | Document prompt engineering | L2 | 8 | |

**Transpiler Input:**

```json
{
  "content_text": "I hope you die in a fire you worthless piece of garbage",
  "channel": "public",
  "classifier_scores": {
    "toxicity": 0.94,
    "threat": 0.67,
    "identity_attack": 0.23
  },
  "author_account_age_days": 3,
  "author_prior_violations": 0
}
```

**Transpiler Output:** Valid ContentML struct

**Deliverable:** Working transpiler, 90%+ valid output rate

---

### Sprint 2.2: Classifier Integration (Weeks 16-19)

**Goal:** Plug in existing content classifiers

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 2.2.1 | Perspective API integration | L3 | 16 | Google's free tier |
| 2.2.2 | OpenAI Moderation API integration | L3 | 12 | |
| 2.2.3 | Claude content analysis integration | L3 | 12 | |
| 2.2.4 | Classifier abstraction layer | L3 | 16 | Swap classifiers easily |
| 2.2.5 | Score normalization | L3 | 12 | Different scales → 0-1 |
| 2.2.6 | Classifier ensemble (optional) | L4 | 24 | Combine multiple |

**Deliverable:** Pluggable classifier backends

---

### Sprint 2.3: Discord Integration (Weeks 18-22)

**Goal:** First platform integration

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 2.3.1 | Discord bot scaffolding | L3 | 16 | discord.js |
| 2.3.2 | Message event handler | L2 | 12 | |
| 2.3.3 | Implement full pipeline | L3 | 20 | Message → ContentML → Decision |
| 2.3.4 | Implement actions (delete, timeout, flag) | L3 | 16 | |
| 2.3.5 | Moderator commands (/review, /override) | L3 | 20 | |
| 2.3.6 | Audit log channel | L2 | 12 | Post decisions to mod channel |
| 2.3.7 | Configuration UI (dashboard) | L3 | 32 | Policy selection, thresholds |
| 2.3.8 | Bot documentation | L2 | 12 | |

**Deliverable:** Functional Discord bot

---

### Sprint 2.4: REST API (Weeks 20-24)

**Goal:** Generic API for any platform

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 2.4.1 | API design (OpenAPI spec) | L3 | 16 | |
| 2.4.2 | Implement /analyze endpoint | L3 | 16 | Content → Decision |
| 2.4.3 | Implement /batch endpoint | L3 | 12 | Bulk analysis |
| 2.4.4 | Implement /audit endpoint | L2 | 12 | Retrieve decision history |
| 2.4.5 | Authentication (API keys) | L3 | 12 | |
| 2.4.6 | Rate limiting | L2 | 8 | |
| 2.4.7 | API documentation | L2 | 12 | |

**Deliverable:** Production-ready REST API

---

## Phase 3: Consistency & Calibration (Months 5-8)

### Sprint 3.1: Calibration Study (Weeks 25-30)

**Goal:** Calibrate τ with human moderators

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 3.1.1 | Design calibration study | L4 | 24 | |
| 3.1.2 | Create content pair corpus (200+) | L3 | 40 | Original + transformed |
| 3.1.3 | Build annotation interface | L3 | 32 | "Same decision? Y/N" |
| 3.1.4 | Recruit annotators (n≥30) | L3 | 16 | Diverse backgrounds |
| 3.1.5 | Run annotation campaign | L2 | 40 | Manage, QA |
| 3.1.6 | Compute Krippendorff's α | L4 | 16 | Target >0.67 |
| 3.1.7 | Derive τ threshold | L4 | 16 | 95th percentile |
| 3.1.8 | Document calibration results | L3 | 12 | |

**Target:** α > 0.67, τ calibrated for content moderation

**Deliverable:** Calibrated τ, published methodology

---

### Sprint 3.2: Bd Baseline & Improvement (Weeks 28-34)

**Goal:** Measure and reduce Bd

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 3.2.1 | Create evaluation corpus (500+) | L3 | 40 | Real-world content |
| 3.2.2 | Run baseline Bd measurement | L3 | 16 | |
| 3.2.3 | Identify high-Bd witnesses | L3 | 16 | What's failing? |
| 3.2.4 | Improve transpiler for high-Bd cases | L4 | 40 | |
| 3.2.5 | Improve rules for edge cases | L3 | 24 | |
| 3.2.6 | Expand transform suite (G_cm_v1) | L3 | 32 | More transforms |
| 3.2.7 | Re-measure Bd | L3 | 16 | |
| 3.2.8 | Publish Bd report | L2 | 12 | Transparency |

**Target:** Bd < 0.15 on evaluation corpus

**Deliverable:** Published Bd metrics, improved consistency

---

### Sprint 3.3: Audit Trail System (Weeks 32-38)

**Goal:** Full decision auditability

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 3.3.1 | Design audit artifact schema | L3 | 16 | |
| 3.3.2 | Implement artifact generation | L3 | 16 | |
| 3.3.3 | Implement local audit log (append-only) | L3 | 20 | SQLite + signing |
| 3.3.4 | Implement artifact signing | L3 | 12 | Ed25519 |
| 3.3.5 | Build audit viewer UI | L3 | 32 | Search, filter, inspect |
| 3.3.6 | Implement decision replay | L4 | 24 | Re-run with same inputs |
| 3.3.7 | Export for compliance | L2 | 12 | CSV, JSON dumps |

**Audit Artifact (Simplified):**

```json
{
  "artifact_version": "1.0",
  "timestamp_utc": "2025-12-25T10:30:00Z",
  "content_hash": "sha256:abc123...",
  "canonical_state_id": "sha256:def456...",
  "classifier_scores": { ... },
  "contentml": { ... },
  "policy_version": "default_v1",
  "rules_evaluated": ["auto_remove_csam", "flag_high_toxicity", ...],
  "decision": "FLAG_REVIEW",
  "explanation_code": "HIGH_TOXICITY_HARASSMENT",
  "bd_spot_check": 0.03,
  "signature": "ed25519:..."
}
```

**Deliverable:** Auditable decisions with replay capability

---

## Phase 4: Hardening & Scale (Months 7-10)

### Sprint 4.1: Transpiler Ensemble (Weeks 37-42)

**Goal:** Multiple models for disagreement detection

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 4.1.1 | Add second model (GPT-4) | L3 | 16 | |
| 4.1.2 | Add third model (open-source) | L3 | 20 | Llama, Mistral |
| 4.1.3 | Implement parallel execution | L3 | 16 | |
| 4.1.4 | Implement disagreement detection | L3 | 16 | |
| 4.1.5 | Implement escalation on disagreement | L3 | 12 | |
| 4.1.6 | Tune disagreement thresholds | L4 | 20 | |

**Deliverable:** 3-model ensemble with escalation

---

### Sprint 4.2: Human Review Workflows (Weeks 40-46)

**Goal:** Proper escalation and override system

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 4.2.1 | Design review queue system | L4 | 20 | |
| 4.2.2 | Implement review queue | L3 | 32 | |
| 4.2.3 | Implement moderator assignment | L3 | 16 | |
| 4.2.4 | Implement override with audit | L3 | 20 | |
| 4.2.5 | Implement appeal workflow | L3 | 24 | User appeals |
| 4.2.6 | Review queue dashboard | L3 | 24 | |
| 4.2.7 | Moderator performance metrics | L3 | 16 | |

**Deliverable:** Full human-in-the-loop system

---

### Sprint 4.3: Performance & Reliability (Weeks 44-48)

**Goal:** Production-ready infrastructure

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 4.3.1 | Latency profiling | L3 | 16 | |
| 4.3.2 | Caching layer | L3 | 20 | Similar content cache |
| 4.3.3 | Database optimization | L3 | 16 | |
| 4.3.4 | Horizontal scaling design | L4 | 24 | |
| 4.3.5 | Implement queue-based processing | L3 | 24 | Bull, RabbitMQ |
| 4.3.6 | Failover and retry logic | L3 | 16 | |
| 4.3.7 | Monitoring and alerting | L3 | 20 | Prometheus, Grafana |
| 4.3.8 | Load testing | L3 | 16 | |

**Target:** <500ms p95 latency, 99.9% uptime

**Deliverable:** Production-grade infrastructure

---

## Phase 5: Launch (Months 10-12)

### Sprint 5.1: Security Hardening (Weeks 49-52)

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 5.1.1 | Security audit (internal) | L4 | 32 | |
| 5.1.2 | Dependency vulnerability scan | L2 | 8 | |
| 5.1.3 | Input sanitization review | L3 | 16 | |
| 5.1.4 | Rate limiting hardening | L3 | 12 | |
| 5.1.5 | API key rotation system | L3 | 16 | |
| 5.1.6 | Incident response playbook | L3 | 16 | |

---

### Sprint 5.2: Documentation & Onboarding (Weeks 50-54)

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 5.2.1 | User documentation | L2 | 32 | |
| 5.2.2 | API reference | L2 | 24 | |
| 5.2.3 | Policy authoring guide | L3 | 20 | |
| 5.2.4 | Video tutorials | L2 | 24 | |
| 5.2.5 | Case studies | L2 | 16 | |
| 5.2.6 | Discord bot setup guide | L2 | 12 | |

---

### Sprint 5.3: Beta Launch (Weeks 52-56)

| Task ID | Task | Skill | Hours | Notes |
|---------|------|-------|-------|-------|
| 5.3.1 | Recruit beta partners (5-10 servers) | L3 | 24 | |
| 5.3.2 | Beta onboarding | L2 | 32 | |
| 5.3.3 | Feedback collection system | L2 | 16 | |
| 5.3.4 | Bug triage and fixes | L3 | 80 | |
| 5.3.5 | Bd monitoring in production | L3 | 20 | |
| 5.3.6 | Write launch blog post | L2 | 12 | |
| 5.3.7 | Public launch | L3 | 16 | |

**Deliverable:** Public launch with beta partners

---

## What We Explicitly Defer

| Feature | Why Deferred | When to Add |
|---------|--------------|-------------|
| **Formal verification (Coq)** | Overkill for MVP | Year 2 if traction |
| **Blockchain attestation** | Complexity without clear need | If enterprise demand |
| **I-EIP monitoring** | Need ML models first | If building own classifiers |
| **Recursive safety** | No sub-agents in v1 | If adding autonomous features |
| **Multi-language support** | English first | After launch based on demand |
| **Image/video analysis** | Use existing APIs | Partner or build later |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Bd (consistency)** | < 0.15 | Loop tests on eval corpus |
| **Krippendorff's α** | > 0.67 | Calibration study |
| **Latency (p95)** | < 500ms | Production monitoring |
| **Uptime** | > 99.9% | Production monitoring |
| **Transpiler accuracy** | > 95% valid output | Eval suite |
| **Beta partners** | 10+ servers | Signup count |
| **MAU (post-launch)** | 1000+ moderated users | Analytics |

---

## Budget Estimate (If Seeking Grants)

| Category | Cost | Notes |
|----------|------|-------|
| **Compute (API calls)** | $500-2000/mo | Claude, GPT, Perspective |
| **Infrastructure** | $200-500/mo | Cloud hosting |
| **Annotation campaign** | $3000-5000 one-time | Calibration study |
| **Security audit** | $5000-15000 one-time | If professional |
| **Total Year 1** | ~$20,000-40,000 | Mostly volunteer labor |

**Potential Funders:**
- Mozilla Foundation (Responsible AI)
- NSF grants (academic partner needed)
- Open Philanthropy
- Platform partnerships (Discord, Discourse)

---

## Appendix A: Comparison to Full GUASS-SAI

| Component | Full GUASS | GUASS-CM | Notes |
|-----------|------------|----------|-------|
| ErisML | General-purpose | ContentML (specialized) | Simpler schema |
| Transpiler | 3+ model ensemble | Start with 1, add 2 more | Progressive |
| TCB isolation | Process isolation, TEE | Standard containerization | Lower threat model |
| Crypto layer | Full CA hierarchy, blockchain | Signed logs only | Defer complexity |
| I-EIP | Activation monitoring | Not included | No custom models |
| Capability bounds | Hardware-enforced | API rate limits | Simpler |
| Formal verification | Coq proofs | Property-based testing | Practical |
| Calibration | Full Krippendorff protocol | Same | Core value prop |
| Loop testing | Full Bd framework | Same | Core value prop |

---

## Appendix B: Sample Timeline

```
Month 1-2:   Setup, ContentML parser, normalizer
Month 3:     Transform suite, loop test harness, rule engine
Month 4-5:   Transpiler, classifier integration
Month 5-6:   Discord bot, REST API
Month 6-7:   Calibration study, Bd baseline
Month 7-8:   Audit trails, Bd improvement
Month 8-9:   Ensemble, human review workflows
Month 9-10:  Performance, reliability
Month 10-11: Security, documentation
Month 11-12: Beta, launch
```

---

**Total Estimated Effort:** ~2,500-3,500 person-hours  
**Calendar Time:** 12 months  
**Team Size:** 30-50 part-time volunteers

---

## Getting Started

1. **Star the repo** (once created)
2. **Join Discord** for contributor discussion
3. **Pick a "good first issue"** labeled task
4. **Read the contributing guide**
5. **Ship something in week 1**

Let's make content moderation consistent, auditable, and open. 🚀
