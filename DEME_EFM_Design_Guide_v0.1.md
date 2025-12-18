
# DEME / EFM Reflex Ethics Design Guide v0.1

_A starting specification for Ethics Modules (EMs), interfaces, and patterns_

---

## 0. Purpose and Scope

This document describes a **practical, governance-friendly design** for the DEME / EFM reflex ethics layer:

- A clean **interface** between domain logic and “moral” reasoning.
- A finite, reviewable **catalogue of Ethics Modules (EMs)**.
- A small set of **composition patterns** (DAGs) that wire EMs together.
- A realistic **complexity budget** for what belongs in the reflex layer.

The aim is to make EFM:

- **Reliable** (complexity is controlled).
- **Auditable** (humans can understand and review it).
- **Domain-agnostic** (minimal domain detail inside EMs).
- **Configurable but safe** (governance profiles can tune, but not break it).

This is **not** a final standard; it is a **v0.1 starting set**.

---

## 1. Architectural Overview

We assume three main layers:

1. **Domain Layer**
   - Perception, planning, control, world models.
   - Knows about geometry, sensors, vehicles, devices, etc.

2. **Moral Interface Layer**
   - Compresses raw world state into a **MoralInterfaceRecord (MIR)**:
     - Abstract actors & roles.
     - Hazard and context features.
     - Per-action projected moral effects.
   - _All domain-specific complexity stays here._

3. **Reflex EM Layer (DEME / EFM)**
   - A set of **Ethics Modules (EMs)**, each a small, deterministic function over MIR.
   - EMs are composed via a **DAG pattern** (no cycles).
   - EM outputs are combined to:
     - Veto unsafe / impermissible actions.
     - Rank remaining actions along moral dimensions.

Above this, slower **tactical / strategic layers** (DEME 3.x, tensorial ethics, game-theoretic analysis) may exist, but they feed only compressed summaries down into MIR and EM parameters.

---

## 2. MoralInterfaceRecord (MIR) v1.0

The MIR is the **only** thing EMs are allowed to read.

Conceptually, it has four sections:

1. Meta
2. Actors & roles
3. Hazard & context features
4. Per-action projections

### 2.1 Meta

For logging and routing; generally not used for core moral logic.

- `mi_version: string`  
  - Schema version (e.g. `"1.0"`).
- `domain_id: string`  
  - Domain identifier (e.g. `"hospital_delivery"`, `"urban_av"`, `"riot_control"`).
- `jurisdiction_id: string`  
  - Legal/political context (e.g. `"UN"`, `"EU"`, `"US_CA"`).
- `timestamp: int or ISO8601`  
  - Time of decision.

### 2.2 Actors & Roles

Abstract descriptions of who is present; no raw sensor detail.

Each `ActorSummary` contains:

- `actor_id: opaque`  
- `role: {civilian, child, combatant, medical, police, robot_self, unknown}`  
- `vulnerability_flags: set`  
  - e.g. `{disabled, restrained, unconscious}`.
- `proximity_band: {contact, near, mid, far}`  

EMs may see:

- The list of ActorSummaries.
- Aggregates (e.g. number of children near, etc.).

### 2.3 Moral Hazard Features

We define `MoralHazardFeatures = {F1, …, F17}`.

**F1. `hazard_immediacy`**  
- Type: categorical  
- Range: `{none, latent, emerging, imminent}`  
- Meaning: how soon severe harm is expected without intervention.

**F2. `hazard_severity`**  
- Type: categorical / ordinal  
- Range: `{none, minor, serious, mortal, catastrophic}`  
- Meaning: severity of expected harm per affected person.

**F3. `hazard_scope`**  
- Type: categorical  
- Range: `{single, few, crowd, mass_casualty}`  
- Meaning: how many people face serious harm.

**F4. `targets_profile`**  
- Type: categorical  
- Range: `{combatants_only, mixed, mostly_innocents, children_present}`  
- Meaning: coarse legal/moral status of those primarily at risk.

**F5. `P_catastrophe_if_no_action`**  
- Type: real ∈ [0,1]  
- Meaning: probability of severe adverse outcome if system does nothing.

**F6. `P_catastrophe_if_best_action`**  
- Type: real ∈ [0,1]  
- Meaning: probability of severe adverse outcome under best available intervention.

**F7. `P_catastrophe_if_non_lethal`**  
- Type: real ∈ [0,1] or undefined  
- Meaning: probability of severe outcome under best non‑lethal intervention.

**F8. `time_to_catastrophe_estimate`**  
- Type: real (seconds)  
- Meaning: time until catastrophe under no action.

**F9. `num_persons_at_risk`**  
- Type: integer ≥ 0

**F10. `num_children_at_risk`**  
- Type: integer ≥ 0

**F11. `non_lethal_action_available`**  
- Type: boolean

**F12. `safe_evacuation_feasible`**  
- Type: boolean

**F13. `human_decision_eta`**  
- Type: real (seconds)  
- Meaning: earliest time a human decision-maker could realistically issue instructions.

**F14. `world_model_confidence`**  
- Type: real ∈ [0,1]  
- Meaning: aggregate confidence in hazard-related inferences.

**F15. `classification_stable`**  
- Type: boolean  
- Meaning: hazard classification stable over recent Δt.

**F16. `sensors_nominal`**  
- Type: boolean  
- Meaning: sensor health checks passed.

**F17. `unrest_intensity`**  
- Type: real ∈ [0,1]  
- Meaning: continuous measure of local civil unrest intensity; 0 = normal, 1 = extreme / conflict-like.

### 2.4 Moral Hazard Predicates

`MoralHazardPredicates = {P1, …, P5}`, derived from features and actor facts.

**P1. `protected_child_in_primary_zone`**  
- True if a child (under configured age threshold) is in the primary hazard zone and not a lawful combatant.

**P2. `protected_medical_in_primary_zone`**  
- True if protected medical/humanitarian personnel are in the primary hazard zone.

**P3. `protected_civilian_majority`**  
- True if a strict majority of those at risk are civilians.

**P4. `protected_hostages_present`**  
- True if persons at risk are being held against their will and threatened by the same hazard.

**P5. `presents_immediate_large_scale_mortal_danger_to_innocents`**  
- True iff:
  - `hazard_immediacy == imminent`  
  - `hazard_severity ∈ {mortal, catastrophic}`  
  - `hazard_scope ∈ {crowd, mass_casualty}`  
  - `targets_profile ∈ {mostly_innocents, children_present}`  
  - `P_catastrophe_if_no_action ≥ θ_prob`  
  - `num_persons_at_risk ≥ θ_count`  
- Where `θ_prob`, `θ_count` are governance parameters.

### 2.5 Per-Action Projections

For each candidate action `a` in `candidate_actions`, the domain layer provides an `ActionSummary`:

- `action_id: opaque`
- `is_baseline_safe: bool` (low-level collision/physics checks)
- `moral_effects`:
  - `delta_P_catastrophe` (vs. no action)
  - `risk_distribution` (expected harm per group)
  - `rights_flags` (e.g. `autonomy_ok`, `privacy_ok`, `dignity_ok`)
  - other pre-chewed moral deltas as needed

EMs never see geometry, raw sensor data, or domain-specific primitives.

---

## 3. EM Interface and Complexity Budget

### 3.1 EM Interface

Each EM `E` is a pure function:

```text
E(MIR, E_params) → {
  per_action: {
    veto        : {true|false}
    soft_block  : {true|false}
    score       : ℝ or [0,1] (optional)
    annotations : map
  },
  global: {
    health_ok : {true|false}
    summary   : map
  }
}
```

- **Binding EMs** primarily use `veto` / `soft_block`.
- **Advisory EMs** primarily use `score` / `annotations`.

### 3.2 Complexity Budget (Reflex Layer)

To keep the system reliable and auditable:

- MIR exposes on the order of **20–40 scalar/boolean features** to EMs.
- There are **6–12 core moral dimensions** (harm, autonomy, fairness, rights, privacy, dignity, etc.).
- Per system, we aim for:
  - **5–10 binding EMs** (that can veto),
  - Up to **~20 EMs total**, including advisory.
- Only **2–3 composition patterns** (DAG shapes) are allowed.

Anything more complex belongs in slower layers, not in the reflex EM loop.

---

## 4. EM Catalog – Functional Specs

Below is a v0.1 catalog grouped by tiers.

### 4.1 Tier 0 – Constitutional EMs

These are non-removable in high-risk systems. No pattern may override their vetoes.

#### 4.1.1 Geneva-EM

- **Tier:** 0  
- **Type:** Binding  
- **Context:** Armed conflict / warfighting / militarized peacekeeping.

**Purpose:**  
Enforce core International Humanitarian Law (IHL) principles: distinction, proportionality, protection of civilians and medical personnel.

**Inputs (from MIR):**

- `targets_profile`
- `protected_civilian_majority`
- `protected_medical_in_primary_zone`
- `protected_hostages_present`
- Per-action:
  - expected civilian vs combatant harm,
  - indication of direct targeting vs collateral effect.

**Behavior (informal):**

- `veto = true` when:
  - An action directly targets civilians or protected persons as such.
  - Expected civilian harm is grossly disproportionate to concrete military advantage (per configured proportionality criteria).
  - The action targets medical/humanitarian personnel or clearly protected objects.
- Actions not vetoed are passed onward to other EMs and pattern logic.

---

#### 4.1.2 BasicHumanRights-EM

- **Tier:** 0  
- **Type:** Binding  
- **Context:** All deployments.

**Purpose:**  
Enforce non-derogable human-rights constraints (no torture, cruel/inhuman/degrading treatment).

**Inputs:**

- Actor roles and vulnerability flags.
- Per-action rights impact flags: e.g. `torture_like`, `degrading_treatment`, `cruel_punishment`.

**Behavior:**

- `veto = true` for any action classified (by upstream projection) as:
  - torture or torture-like,
  - cruel or inhuman treatment beyond configured thresholds,
  - extreme degrading treatment.
- Annotations give `hr_violation_code`.

---

#### 4.1.3 NonDiscrimination-EM (Baseline)

- **Tier:** 0  
- **Type:** Binding

**Purpose:**  
Prevent explicit discrimination on protected grounds in core decision rules.

**Inputs:**

- Governance config: list of protected classes.
- Per-action:
  - indicator if decision logic uses protected attributes,
  - group-level expected harm/benefit distribution.

**Behavior:**

- `veto = true` if:
  - protected attributes are used directly as decision keys where forbidden, or
  - disparity exceeds configured maximum and cannot be justified by stronger Tier‑0/1 duties.

---

#### 4.1.4 ChildProtection-EM

- **Tier:** 0  
- **Type:** Binding

**Purpose:**  
Provide heightened protection for children.

**Inputs:**

- `protected_child_in_primary_zone`
- `num_children_at_risk`
- Per-action expected harms for children vs others.

**Behavior:**

- Tightens all harm thresholds when children are at risk.
- `veto = true` for actions that significantly harm children when a less harmful feasible alternative exists.
- Forbids treating young children as ordinary combatants, except under separate, tightly-defined LastResort EM conditions (which themselves must satisfy Geneva-EM).

---

### 4.2 Tier 1 – Core Safety & Law EMs

#### 4.2.1 CorePhysicalSafety-EM

- **Tier:** 1  
- **Type:** Binding

**Purpose:**  
Prevent immediate physical harms such as collisions, crush injuries, and falls.

**Inputs:**

- Per-action:
  - predicted collision probabilities and severities,
  - injury risk estimates by actor group.
- `sensors_nominal`, `world_model_confidence`.

**Behavior:**

- `veto = true` when predicted physical harm exceeds configured thresholds and a safer feasible alternative exists.
- Under low confidence or sensor faults, thresholds become stricter.

---

#### 4.2.2 ProxemicsSafety-EM

- **Tier:** 1  
- **Type:** Binding

**Purpose:**  
Maintain safe distances and speeds in proximity to humans.

**Inputs:**

- Actor proximities (`proximity_band`),
- Per-action planned speed and path.

**Behavior:**

- `veto = true` for actions that:
  - exceed maximum speed at given proximity,
  - intrude into forbidden distance bands around vulnerable persons.

---

#### 4.2.3 MedicalSafety-EM

- **Tier:** 1  
- **Type:** Binding  
- **Context:** Medical domains.

**Purpose:**  
Bound clinical risk and enforce medical device constraints.

**Inputs:**

- Per-action clinical risk projections,
- Flags for supervision, dosage limits, device safety constraints.

**Behavior:**

- `veto` when:
  - interventions violate dosage or device limits,
  - high-risk interventions are attempted without required human supervision.

---

#### 4.2.4 JurisdictionalLaw-EM

- **Tier:** 1  
- **Type:** Binding

**Purpose:**  
Enforce high-level legal constraints per jurisdiction.

**Inputs:**

- `jurisdiction_id`
- Per-action legal-compliance flags (computed upstream).

**Behavior:**

- `veto` legally prohibited actions.
- `soft_block` when human authorization is required by law but not present.

---

#### 4.2.5 DomainRegulation-EM

- **Tier:** 1  
- **Type:** Binding

**Purpose:**  
Enforce sector-specific regulatory rules (e.g., AV, aviation, medical device regulations).

**Inputs:**

- Per-action regulatory compliance indicators.

**Behavior:**

- `veto` actions that conflict with mandatory sector regulations (as encoded in configuration).

---

### 4.3 Tier 2 – Rights, Fairness, Privacy

#### 4.3.1 AutonomyConsent-EM

- **Tier:** 2  
- **Type:** Binding in many contexts

**Purpose:**  
Respect informed consent and refusals, with limited emergency overrides.

**Inputs:**

- For each affected actor:
  - consent status (`consented`, `refused`, `unknown`),
  - competency / capacity,
  - coercion indicators,
  - emergency flags.
- Hazard features: `hazard_immediacy`, `hazard_severity`.

**Behavior:**

- `veto` for actions that substantially affect competent actors who have refused or not consented, except when:
  - hazard is imminent and mortal,
  - action is necessary to prevent severe harm,
  - and override conditions are satisfied by governance rules.
- Overrides are annotated (`consent_override_reason`).

---

#### 4.3.2 Coercion-EM

- **Tier:** 2  
- **Type:** Binding or strong advisory

**Purpose:**  
Limit coercive actions, threats, and exploitative persuasion.

**Inputs:**

- Per-action coercion metrics from upstream models:
  - degree of threat,
  - level of manipulation,
  - exploitation of vulnerabilities.

**Behavior:**

- `veto` or `soft_block` actions whose coercion score exceeds configured thresholds.
- Provide `score` to help prefer less coercive among otherwise similar actions.

---

#### 4.3.3 AllocationFairness-EM

- **Tier:** 2  
- **Type:** Binding (constraints) + scoring

**Purpose:**  
Enforce fairness constraints and provide fairness-based ranking within safe sets.

**Inputs:**

- Group definitions (non-sensitive abstractions),
- Per-action expected harm/benefit per group,
- Governance parameters: fairness metrics and allowable disparity ranges.

**Behavior:**

- `veto` actions that violate hard fairness constraints (e.g., extreme, unjustified group disparities).
- `score` each action by fairness quality; the pattern uses this for ranking among safe/legal actions.

---

#### 4.3.4 QueueFairness-EM

- **Tier:** 2  
- **Type:** Binding

**Purpose:**  
Enforce fair queueing and scheduling.

**Inputs:**

- Queue positions, priorities, waiting times,
- Per-action effects on order and waiting times.

**Behavior:**

- `veto` actions that:
  - violate configured queue disciplines (FIFO, priority, triage based),
  - perform unjustified “queue jumping.”

---

#### 4.3.5 Privacy-EM

- **Tier:** 2  
- **Type:** Binding

**Purpose:**  
Control personal data collection, retention, and sharing.

**Inputs:**

- Per-action:
  - data categories to be collected/shared,
  - subject types,
  - retention policies,
  - purpose tags.
- Context features such as `unrest_intensity`.

**Behavior:**

- `veto` if an action:
  - collects more data than allowed for stated purpose,
  - shares data with unauthorized entities,
  - violates allowed retention periods.
- Tightens constraints with increasing `unrest_intensity` where appropriate (e.g., protests, riots).

---

#### 4.3.6 Confidentiality-EM

- **Tier:** 2  
- **Type:** Binding

**Purpose:**  
Protect medical, financial, and other confidential information.

**Inputs:**

- Per-action confidential domain tags,
- Intended recipients, purpose.

**Behavior:**

- `veto` actions that:
  - expose confidential information without a valid legal/ethical basis,
  - fail to meet minimal disclosure conditions (e.g., minimal necessary information).

---

#### 4.3.7 Dignity-EM

- **Tier:** 2  
- **Type:** Binding or advisory

**Purpose:**  
Avoid degrading, humiliating, or objectifying treatment.

**Inputs:**

- Per-action dignity risk scores from upstream models,
- Context (role, setting, cultural parameters).

**Behavior:**

- When configured as binding:
  - `veto` actions whose dignity risk exceeds thresholds.
- Otherwise:
  - Provide a `score` that penalizes dignity harms and annotate reasons.

---

### 4.4 Tier 3 – Soft Values & Institutional Duties

#### 4.4.1 Beneficence-EM

- **Tier:** 3  
- **Type:** Score/advisory or binding in health/care

**Purpose:**  
Promote welfare within constraints set by higher-tier EMs.

**Inputs:**

- Expected welfare (utility) changes per actor/group for each action.

**Behavior:**

- Assigns a `score` to each safe/legal action based on expected welfare,
- Can be used to choose between multiple equally safe/right-respecting actions.

---

#### 4.4.2 EnvironmentalImpact-EM

- **Tier:** 3  
- **Type:** Advisory or binding thresholds

**Purpose:**  
Account for environmental and resource impacts.

**Inputs:**

- Per-action: energy use, emissions, environmental disturbance.

**Behavior:**

- Provide `score` penalizing high-impact actions.
- Optionally, `veto` actions whose impact exceeds configured caps.

---

#### 4.4.3 OrganizationalPolicy-EM

- **Tier:** 3  
- **Type:** Binding or advisory

**Purpose:**  
Enforce institution-specific ethics and operational policies beyond law.

**Inputs:**

- Policy tags per action from domain layer,
- Policy configuration (e.g., “no operation in areas with `unrest_intensity > 0.6`”).

**Behavior:**

- `veto` or `soft_block` actions when they conflict with organizational policies.
- E.g., abort deliveries into active riots; disallow certain behaviors in schools/hospitals.

---

#### 4.4.4 CulturalNorms-EM

- **Tier:** 3  
- **Type:** Advisory

**Purpose:**  
Promote local etiquette and cultural respect where consistent with higher-tier duties.

**Inputs:**

- Cultural context identifier,
- Per-action norm-compatibility scores.

**Behavior:**

- Provide `score`/annotations that favor norm-respecting actions among those allowed.

---

### 4.5 Tier 4 – Meta-Governance & Integrity EMs

These oversee the entire EM stack and pattern selection.

#### 4.5.1 PatternGuard-EM

- **Tier:** 4  
- **Type:** Binding

**Purpose:**  
Ensure that only approved EM patterns (DAGs) are used and that constitutional EMs are present in required positions.

**Inputs:**

- Current EM graph/pattern ID,
- List of active EMs and their tiers.

**Behavior:**

- If pattern or EM set is invalid:
  - `health_ok = false`,
  - System required to enter safe-degraded mode (e.g., halt high-risk actions).

---

#### 4.5.2 ProfileIntegrity-EM

- **Tier:** 4  
- **Type:** Binding

**Purpose:**  
Verify that governance profiles and EM parameters are signed, valid, and within safety envelopes.

**Inputs:**

- Governance profile metadata (signatures, version, jurisdiction),
- EM parameter ranges.

**Behavior:**

- `health_ok = false` when:
  - signatures invalid or missing,
  - parameters out of allowed range.

---

#### 4.5.3 HumanOversight-EM

- **Tier:** 4  
- **Type:** Binding

**Purpose:**  
Enforce human-in-the-loop or human-on-the-loop requirements for certain actions.

**Inputs:**

- `time_to_catastrophe_estimate`,
- `human_decision_eta`,
- Action categories (e.g., lethal force, irreversible surgery).

**Behavior:**

- `veto` actions in categories that require human approval but lack it.
- Enforce that if `human_decision_eta` is acceptable relative to urgency, the system defers to humans.

---

#### 4.5.4 AuditLogging-EM

- **Tier:** 4  
- **Type:** Binding

**Purpose:**  
Ensure that each decision is logged for later audit.

**Inputs:**

- Intended log record (hash of MIR, EM outputs, chosen action),
- Log channel status.

**Behavior:**

- If log cannot be written (critical context), force degraded mode.
- Annotates chosen action with a log ID / hash chain marker.

---

#### 4.5.5 SelfTest-EM

- **Tier:** 4  
- **Type:** Binding

**Purpose:**  
Monitor EM health and sensor integrity; force safe degradation on failure.

**Inputs:**

- Self-test signals from EMs,
- `sensors_nominal`,
- `classification_stable`.

**Behavior:**

- `health_ok = false` when:
  - critical EMs fail self-test,
  - sensor status is persistently non-nominal.
- Trigger safe mode / restricted action set.

---

## 5. Composition Patterns (DAGs)

### 5.1 Hard-Shell Safety Pattern

**Idea:** Constitutional & Safety/Legal EMs form an outer shell that produce a combined veto mask. Inner EMs only act on actions that survive the shell.

**DAG Sketch:**

```text
                   +----------------------+
                   |  MoralInterfaceRecord|
                   +----------+-----------+
                              |
                              v
             +----------------+----------------+
             |                                 |
             v                                 v
+--------------------------+       +--------------------------+
|  Tier 0: Constitutional  |       |    Tier 1: Safety & Law  |
+--------------------------+       +--------------------------+
             \                             //
              \                           //
               v\                       //v
               +-------------------------+
               |  HardShell Veto Mixer   |
               +------------+------------+
                            |
                            v
                +------------------------+
                |  SafeActionSet         |
                +------------+-----------+
                             |
                             v
           +-----------------+------------------+
           |                                    |
           v                                    v
+------------------------+          +------------------------+
| Tier 2: Rights/Fairness|          | Tier 3: Soft Values   |
+------------------------+          +------------------------+
            \                          //
             \                        //
              v\                    //v
            +-----------+
            | Score &    |
            | Rank Mixer |
            +-----+-----+
                  |
                  v
          +-----------------+
          | ActionSelector  |
          +-----------------+
```

- Shell EMs: Geneva-EM, BasicHumanRights-EM, NonDiscrimination-EM, ChildProtection-EM, CorePhysicalSafety-EM, ProxemicsSafety-EM, JurisdictionalLaw-EM, DomainRegulation-EM.
- Inner EMs: Rights, fairness, privacy, dignity, beneficence, etc.

---

### 5.2 Hard-Shell + Fairness Wrapper

Same shell, but fairness EMs get a dedicated “wrapper” stage over already utility-filtered actions.

```text
MIR
 |
 v
[Hard-Shell Veto Mixer] -> SafeActionSet
                             |
                             v
                +------------------------+
                |  Utility / Welfare EMs |
                +------------+-----------+
                             |
                             v
               +---------------------------+
               | Utility-Filtered Actions |
               +-------------+------------+
                             |
                             v
                   +-------------------+
                   | Fairness Wrapper  |
                   | AllocationFairness|
                   | Dignity-EM (opt.) |
                   +--------+----------+
                            |
                            v
                    +---------------+
                    | ActionSelector|
                    +---------------+
```

Fairness never resurrects vetoed actions; it only re-ranks within a safe, utility-filtered subset.

---

### 5.3 Lexicographic Stack

Use a strict priority ordering of “levels”:

```text
MIR
 |
 v
AllCandidateActions
 |
 v
[Level 0: Absolute Prohibitions]
  (Constitutional & hard safety)
 |
 v
Actions_L0
 |
 v
[Level 1: Rights & Strict Harm]
 |
 v
Actions_L1
 |
 v
[Level 2: Fairness & Distribution]
 |
 v
Actions_L2
 |
 v
[Level 3: Utility / Soft Values]
 |
 v
ActionSelector
```

At each level, EMs may:

- Veto actions outright.
- Identify the subset that best satisfies that level.
- Pass only the surviving / tied subset to the next level.

No lower level can reintroduce actions filtered out higher up.

---

## 6. Context Templates & Meta-Layer

### 6.1 Context Templates

A **ContextClassifier** uses MIR (and external signals) to pick a **template**:

- `ROUTINE_CIVIL`
- `CIVIL_UNREST`
- `CRISIS_TRIAGE`
- `CONFLICT_ZONE`, etc.

Each template binds:

- A specific pattern (e.g., Hard-Shell + Fairness Wrapper).
- Which EMs are active and how strongly (binding vs advisory).
- Parameter ranges (e.g., `unrest_intensity` thresholds).

### 6.2 Meta EMs Around Patterns

Meta EMs wrap pattern execution:

```text
MIR
 |
 v
ContextClassifier --> TemplateSelector
                        |
                        v
                 [Selected Pattern DAG]
                        |
                        v
            +--------------------------+
            | AuditLogging-EM,         |
            | SelfTest-EM,             |
            | HumanOversight-EM        |
            +-------------+------------+
                          |
                          v
                     Chosen Action
```

PatternGuard-EM and ProfileIntegrity-EM gate pattern activation before it runs.

---

## 7. Example: High-Risk Civilian Robot Profile v1.0

As an example, a **hospital delivery robot** might ship with:

- **Template:** `ROUTINE_CIVIL` using Hard-Shell + Fairness Wrapper.
- **Active EMs:**
  - Tier 0: BasicHumanRights, NonDiscrimination, ChildProtection
  - Tier 1: CorePhysicalSafety, ProxemicsSafety, JurisdictionalLaw, MedicalSafety, DomainRegulation
  - Tier 2: AutonomyConsent, Coercion, AllocationFairness (for shared resources), Privacy, Confidentiality, Dignity
  - Tier 3: Beneficence, EnvironmentalImpact, OrganizationalPolicy, CulturalNorms
  - Tier 4: PatternGuard, ProfileIntegrity, HumanOversight, AuditLogging, SelfTest
- **Key parameters:**
  - Strict thresholds for harm to patients and children.
  - Strong privacy rules around patient data.
  - Org policy: no operation in zones with `unrest_intensity > 0.6`.

This profile is:

- Small enough to audit (limited EM set, one pattern).
- Rich enough to encode non-trivial moral behavior.
- Configurable via governance profiles, not code changes.

---

## 8. Extensibility and Limits

This v0.1 design intentionally:

- **Limits reflex-layer complexity** to a manageable, auditable set.
- Keeps **domain semantics** outside EMs, in the moral interface.
- Uses **patterns** to constrain EM composition and avoid ad-hoc graphs.

Future versions (DEME 3.x) can:

- Add higher-order tensor / multi-agent analysis in slower layers.
- Use game-theoretic tools to compute `P_catastrophe` and distributional outcomes.
- Feed only summarized features and updated parameters back into this same reflex EM architecture.

The central discipline remains:

> _EMs are small, deterministic guardians over a bounded moral interface; they enforce hard constraints and provide transparent trade-offs, but they do not pretend to capture all of moral reality._
