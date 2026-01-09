# DEME-on-AGI-HPC: An Open, Safety-Governed Cognitive Stack for Autonomous Mobile Robots

**Linux-Native, Ethically Governed Autonomy on NVIDIA Thor with NIST AI RMF Alignment**

Date: 2025-12-11  
Authors: ErisML / AGI-HPC Project Team  
Affiliation: San José State University -- ErisML / AGI-HPC  
Framework Version: DEMEProfileV03  
NIST Alignment: AI RMF 1.0, AI 600-1 (GAI Profile), AI 100-2

---

## Table of Contents

1. [Abstract](#abstract)
2. [Introduction](#introduction)
3. [NIST AI RMF Alignment Overview](#nist-alignment)
4. [System Overview](#system-overview)
5. [DEME Ethics Stack for Mobile Robots](#deme-ethics-stack)
6. [Hardware and Platform Layer](#hardware-platform)
7. [Heterogeneous Memory Fabric](#memory-fabric)
8. [NIST RMF Implementation: Govern, Map, Measure, Manage](#nist-implementation)
9. [Data and Decision Flows](#decision-flows)
10. [Example Use Case: Hospital Service Robot](#hospital-use-case)
11. [Open Source Integration and Linux Foundation Alignment](#open-source-integration)
12. [Roadmap and Collaboration Opportunities](#roadmap)
13. [Conclusion](#conclusion)

---

## Abstract

Autonomous mobile robots are transitioning from laboratories into hospitals, campuses, warehouses, ports, and vessels, increasingly relying on foundation models for perception and planning while operating near people and critical infrastructure. As these systems assume safety-critical roles, transparency, governance, and ethical alignment become as essential as performance.

This whitepaper presents an open, Linux-native architecture for autonomous mobile robots combining: (i) the AGI-HPC dual-hemisphere cognitive design for higher-level planning and control; (ii) NVIDIA Thor modules as compute substrate for onboard perception, reasoning, and safety; (iii) a heterogeneous memory fabric anchored by Ceph and extended with specialized data stores; and (iv) **DEME (Democratically Governed Ethics Modules)**, implementing **DEMEProfileV03** for explicit, auditable ethical reasoning aligned with **NIST AI RMF 1.0** and the **Generative AI Profile (NIST AI 600-1)**.

The architecture addresses NIST's four core functions—**Govern, Map, Measure, and Manage**—through structured EthicalFacts schemas, multi-stakeholder Ethics Modules, democratic governance aggregation, and low-latency "ethics firewall" checks in the motion loop. The entire stack is open, inspectable, and designed for collaboration within the Linux Foundation ecosystem, directly supporting the focus on Open Source + AI: innovation, transparency, and regulation.

---

## 1. Introduction

Autonomous mobile robots increasingly inhabit environments never designed for autonomous agents. Hospital corridors, university campuses, and clinic waiting areas contain vulnerable populations, heterogeneous infrastructure, and complex institutional norms. Robots navigating these spaces must not only avoid collisions and optimize routes; they must respect rights, preserve privacy, distribute burdens fairly, and remain accountable to the institutions and communities they serve.

Simultaneously, robotic autonomy is being rebuilt atop general-purpose AI accelerators and foundation models. Platforms like NVIDIA Thor provide centralized, transformer-capable compute that can host perception, planning, and learned policies on a single system-on-chip. Distributed storage systems like Ceph provide durable, scalable storage for telemetry, models, policies, and logs. The challenge is no longer whether hardware can run powerful AI modules, but how those modules are structured, governed, and made transparent to stakeholders.

### NIST AI Risk Management Framework Context

The **NIST AI Risk Management Framework (AI RMF 1.0)**, released January 2023, establishes voluntary guidelines for trustworthy AI through four core functions: **Govern**, **Map**, **Measure**, and **Manage**. The companion **Generative AI Profile (NIST AI 600-1)**, released July 2024, addresses twelve risk categories unique to or exacerbated by generative AI, including confabulation, harmful bias, privacy risks, and information integrity concerns.

The AGI-HPC project approaches autonomous systems from the perspective of high-performance computing and cognitive architecture, defining a dual-hemisphere (left/right) design, multi-layer memory system, and safety gates between intention and action. Building on this, the **ErisML library** introduces **DEME (Democratically Governed Ethics Modules)**, which separates domain intelligence from explicitly modeled ethical reasoning. DEME treats ethically relevant information as first-class structured data, not as opaque side effects of black-box policies.

This paper describes how an autonomous mobile robot can be built with:
- AGI-HPC's cognitive stack mapped onto dual Thor modules
- A heterogeneous memory fabric spanning Ceph, key-value, graph, vector, and spatial databases
- **DEMEProfileV03** as a layered ethics and governance system
- Full alignment with NIST AI RMF's Govern, Map, Measure, and Manage functions
- A low-latency "ethics firewall" operating in the motion loop
- Comprehensive logging and auditability for NIST compliance

---

## 2. NIST AI RMF Alignment Overview

### 2.1 NIST AI RMF Core Functions

The NIST AI RMF structures risk management through four interconnected functions:

**GOVERN**: Establishes organizational culture, policies, and accountability structures for AI risk management. Includes governance documentation, stakeholder engagement, diversity considerations, and third-party risk oversight.

**MAP**: Contextualizes AI systems within operational environments, identifying intended purposes, potential impacts, stakeholders, and risks across technical, social, and ethical dimensions.

**MEASURE**: Employs quantitative, qualitative, and mixed-method approaches to analyze, assess, benchmark, and monitor AI risks and trustworthiness characteristics.

**MANAGE**: Allocates resources to address mapped and measured risks, implements response plans, monitors deployed systems, and enables continuous improvement.

### 2.2 DEME's Mapping to NIST Functions

| NIST Function | DEME Implementation |
|--------------|---------------------|
| **GOVERN** | Democratic Governance layer with versioned EM profiles, stakeholder weights, veto rules, and governance configurations. Full audit logs stored in Ceph. |
| **MAP** | EthicalFacts schema captures context-specific risks across consequences, rights, justice, privacy, environmental impact, and epistemic status. Domain Assessment Services translate raw sensor/planning data into structured EthicalFacts. |
| **MEASURE** | Ethics Modules (EMs) evaluate EthicalFacts against specific value systems, returning EthicalJudgements with verdicts, normative scores, and reasoning. Aggregated scores and veto flags provide quantitative risk assessment. |
| **MANAGE** | DecisionOutcome selects preferred options based on governance rules, logs all decisions to memory fabric, enables post-deployment analysis, supports governance tuning, and provides low-latency ethics firewall for real-time safety. |

### 2.3 NIST AI 600-1 (Generative AI Profile) Relevance

While DEME-on-AGI-HPC primarily addresses embodied robotics rather than generative AI text/image production, several GAI Profile risk categories are directly relevant:

- **Confabulation/Hallucination**: World models and semantic understanding from foundation models may contain errors. EthicalFacts includes epistemic_status fields tracking confidence and uncertainty.
- **Data Privacy**: Privacy EM constrains sensor usage and storage. EthicalFacts privacy_and_data_governance block documents data collection, retention, and consent status.
- **Harmful Bias and Homogenization**: Fairness EM monitors distributional impacts across populations. EthicalFacts justice_and_fairness block flags discrimination risks.
- **Human-AI Configuration**: Autonomy EM respects consent and withdrawal. EthicalFacts autonomy_and_agency block tracks consent mechanisms and override conditions.
- **Information Security**: Hardware-adjacent ethics firewall provides defense-in-depth against compromised planning systems.
- **Value Chain Integration**: Open EM libraries and governance configurations enable transparent third-party component integration.

### 2.4 NIST AI 100-2: Adversarial ML Considerations

NIST AI 100-2 addresses adversarial machine learning attacks. DEME's architecture provides defense through:
- **Separation of Concerns**: Ethics modules operate on structured EthicalFacts, not raw model outputs, creating an architectural boundary.
- **Multi-Module Redundancy**: Multiple independent EMs must agree; compromising one EM doesn't compromise governance.
- **Low-Latency Firewall**: Hardware-adjacent safety checks provide last-line defense against poisoned planning commands.
- **Comprehensive Logging**: All EthicalFacts, judgements, and governance decisions logged to immutable storage for anomaly detection.

---

## 3. System Overview

The proposed system consists of three intertwined subsystems:

1. **Cognitive Stack**: Implements AGI-HPC's dual-hemisphere architecture
2. **Heterogeneous Memory and Compute Fabric**: Anchored by Ceph cluster with specialized data stores
3. **Ethics and Governance Layer**: Based on DEME and ErisML library with DEMEProfileV03

The autonomous mobile robot is equipped with one or more NVIDIA Thor modules. We map AGI-HPC's left and right hemispheres onto two logical partitions:

- **Left Hemisphere (LH)**: Higher-level reasoning, global planning, task decomposition, dialogue with operators, multi-step decision making
- **Right Hemisphere (RH)**: Perception and control, sensor fusion, local world modeling, trajectory generation, low-latency safety oversight

Both hemispheres run Linux-based containerized services and participate in a shared event fabric. Off-robot, a Ceph cluster and associated data services serve as the robot's extended memory and compute partner.

DEME spans both robot and cluster. Core abstractions—EthicalFacts and EthicalJudgement—are used consistently whether ethics modules execute on-robot, at the edge, or in the cluster. A subset of DEME's constraints are compiled into a low-latency rule set enforced directly on the RH Thor module as an "ethics firewall" for action commands.

---

## 4. Hardware and Platform Layer

### 4.1 NVIDIA Thor as Dual Hemispheres

NVIDIA Thor modules are high-performance, automotive- and robotics-grade systems-on-chip capable of running perception, planning, and AI workloads on a single platform. We treat Thor as logical host for two hemispheres:

**Left Hemisphere Partition** runs:
- High-level reasoning services
- Natural language interfaces
- DEME ethics modules (non-real-time)
- Memory clients querying the cluster

**Right Hemisphere Partition** runs:
- Perception pipelines
- Local world modeling
- Motion planning and control
- Low-latency ethics firewall

Isolation between hemispheres uses Linux namespaces, cgroups, and hardware virtualization where available. Hemispheres are separately deployable and independently updateable, critical for safety-critical software updates and staged rollouts.

### 4.2 Robot Base and Sensors

Robot base includes locomotion hardware (wheels, tracks, legs), power system, and sensors: cameras, LiDAR, radar, depth sensors, microphones, IMUs. RH services consume sensor streams to construct local world models and generate motion commands. LH services subscribe to higher-level semantic summaries (occupancy grids, object lists, zone labels).

### 4.3 Operating System and Containerization

Platform layer assumes Linux across all compute nodes: Thor modules, edge nodes, Ceph cluster. On robot, real-time Linux and containerized services provide predictability and flexibility. AGI-HPC uses gRPC microservices and message-oriented middleware for loose coupling and upgradeability.

Container orchestration on robot may use lean runtime instead of full Kubernetes to reduce overhead. In cluster, standard Kubernetes deployment hosts memory/compute services, CI/CD pipelines, batch analytics, and simulation jobs.

---

## 5. DEME Ethics Stack for Mobile Robots

DEME provides the ethics and governance layer, implemented via ErisML ethics subsystem and designed around three core ideas:

### 5.1 EthicalFacts: Structured, Domain-Agnostic Schema (NIST MAP Function)

**EthicalFacts** is a versioned schema capturing ethically salient aspects of candidate options. For autonomous mobile robots, each option might be a candidate route, behavior, or task choice.

The **DEMEProfileV03** EthicalFacts schema includes:

**Consequences Block**:
- expected_benefit: Magnitude of intended positive outcome
- expected_harm: Magnitude of potential negative outcome
- urgency: Time-criticality of decision
- affected_individuals: Number and vulnerability of impacted people

**Rights and Duties Block**:
- rights_violations: List of basic rights potentially violated
- consent_status: Whether informed consent obtained
- explicit_rule_violations: Institutional policies violated
- duty_conflicts: Competing obligations

**Justice and Fairness Block**:
- discrimination_flags: Protected attributes used in decision
- prioritization_of_disadvantaged: Whether vulnerable groups prioritized
- power_imbalance_indicators: Disparities in decision impact

**Autonomy and Agency Block**:
- autonomy_enhancement: Degree choice expands human agency
- autonomy_restriction: Degree choice constrains human freedom
- consent_mechanism: How consent obtained/verified
- override_conditions: Circumstances justifying autonomy override

**Privacy and Data Governance Block**:
- data_collection_scope: Types and volume of personal data collected
- data_retention_period: Duration data stored
- third_party_sharing: Whether data shared externally
- anonymization_strength: Degree of de-identification

**Societal and Environmental Impact Block**:
- environmental_cost: Resource consumption, emissions
- commons_impact: Effect on shared resources
- long_term_societal_effect: Broader social implications

**Virtue and Care Block**:
- care_for_vulnerable: Attention to needs of vulnerable individuals
- honesty_transparency: Degree of openness about system operation
- professional_standards_adherence: Compliance with domain norms

**Procedural and Legitimacy Block**:
- due_process_followed: Whether proper procedures followed
- stakeholder_participation: Degree of affected party involvement
- appeals_mechanism: Availability of recourse

**Epistemic Status Block**:
- confidence_level: Statistical confidence in predictions
- known_unknowns: Identified uncertainties
- data_quality: Reliability of input data
- model_limitations: Known bounds of system capability

Domain and assessment services map raw sensor/planning data into this structure. Ethics modules reason over EthicalFacts rather than raw images or telemetry, respecting single-responsibility principle and making EMs portable, testable, and auditable.

**NIST Alignment**: EthicalFacts schema directly implements NIST MAP function by documenting context-specific risks, impacts, and trustworthiness considerations in structured, auditable format.

### 5.2 Ethics Modules as Stakeholder Voices (NIST MEASURE Function)

An **Ethics Module (EM)** implements a simple interface with single `judge` method. Given EthicalFacts instance, returns **EthicalJudgement** containing:
- verdict: {strongly_prefer, prefer, neutral, avoid, forbid}
- normative_score: [0.0, 1.0]
- reasons: List of human-readable explanations
- metadata: Optional structured data for analysis

Each EM encodes specific value system or stakeholder perspective.

**Example EMs for Mobile Robots**:

1. **Safety and Rights EM**: Treats safety and basic rights as hard constraints, forbidding options violating them
2. **Mission Utility EM**: Balances timeliness, efficiency, resource use against risk
3. **Fairness and Justice EM**: Monitors distribution of noise, delay, inconvenience across populations
4. **Privacy and Autonomy EM**: Constrains surveillance, respects individual opt-out ability
5. **Procedural Compliance EM**: Enforces institutional policies and escalation protocols

EMs can be authored/reviewed independently, versioned, and selectively composed to match deployment norms.

**NIST Alignment**: EMs implement NIST MEASURE function by providing quantitative/qualitative risk assessment of options against specific trustworthiness criteria.

### 5.3 Democratic Governance and Decision Outcomes (NIST MANAGE Function)

Democratic governance layer aggregates EM outputs. **Governance configuration** (DEMEProfileV03) specifies:
- Stakeholder and module weights
- Veto EMs (hard constraints)
- Minimum score thresholds
- Tie-breaking strategies
- Override mode (rights_first, consequences_first, balanced)

From your test run:
```
DEME dimension weights:
  safety                  : 0.190
  autonomy_respect        : 0.095
  fairness_equity         : 0.190
  privacy_confidentiality : 0.095
  environment_societal    : 0.095
  rule_following_legality : 0.238
  priority_for_vulnerable : 0.095
  trust_relationships     : 0.050

Override mode: rights_first

Lexical layers:
  - rights_and_duties: hard_stop=True
  - welfare: hard_stop=False
  - justice_and_commons: hard_stop=False
```

For each candidate option, governance collects all EthicalJudgements and computes governance-level EthicalJudgement reflecting configured rules. Across options, governance produces **DecisionOutcome** identifying:
- Selected option
- Ranked list of acceptable alternatives
- List of forbidden options
- Explanations for each decision

Outcome logged alongside underlying EthicalFacts and per-module judgements, enabling later scrutiny, regression testing, and governance tuning. Governance configurations are versioned artifacts that can be debated and updated through institutional processes.

**NIST Alignment**: Democratic governance implements NIST MANAGE function by allocating risk resources, prioritizing responses, and enabling continuous improvement through logged decision records.

### 5.4 Hard Vetoes and Lexical Priority (NIST GOVERN Function)

DEMEProfileV03 supports **hard veto constraints** and **lexical priority layers**:

**Hard Vetoes** (from your test):
- never_catastrophic_safety_harm
- never_intentional_serious_harm
- never_discriminate_protected_groups
- never_systematic_privacy_violation
- never_mass_surveillance_private_spaces
- never_persistent_misinfo_disinfo_campaigns
- never_child_sexual_abuse_or_exploitative_content
- never_illegal_content_even_if_utility_high
- never_fabricate_critical_evidence
- never_impersonate_real_person_without_consent

**Lexical Priority Layers** enforce ordered consideration:
1. **Rights and Duties** (hard_stop=True): Evaluated first; violations trigger immediate rejection
2. **Welfare** (hard_stop=False): Evaluated if rights layer passed
3. **Justice and Commons** (hard_stop=False): Evaluated last

This structure aligns with your Scene 12 choice of "rights-first" override mode, where basic rights and explicit refusals should almost never be overridden except in most immediate life-or-death scenarios.

**NIST Alignment**: Hard vetoes and lexical layers implement NIST GOVERN function by establishing clear organizational policies, accountability structures, and non-negotiable constraints.

### 5.5 Low-Latency Ethics Firewall

While full DEME evaluation suits plan-level decisions, control loop imposes stricter timing constraints. Mobile robot may update commands at tens/hundreds of hertz, leaving only milliseconds for safety checks.

We compile subset of DEME's hard constraints—particularly from Safety and Rights EM—into **low-latency rule table** deployed on RH Thor module. This "ethics firewall" operates on compact signals:
- Collision risk flags
- Zone identifiers
- Sensor health indicators
- Velocity/acceleration limits

Firewall can veto or clamp commands inside control loop without consulting full DEME stack. Firewall rules derived from same open, reviewable EM definitions informing higher-level decisions, ensuring consistency between fast-path and deliberative ethics.

**NIST Alignment**: Ethics firewall provides real-time implementation of NIST MANAGE function's risk response capabilities, ensuring safety constraints enforced even under timing pressure.

---

## 6. Heterogeneous Memory Fabric

While Ceph provides durable, scalable foundation for storage, practical cognitive system needs several kinds of memory with different latency, consistency, and query characteristics.

### 6.1 Memory Layers

**Hot/Transient Memory**: Low-latency, limited-size caches (memcached, Redis) close to robot/edge. Cache recent EthicalFacts, short-term semantic summaries, intermediate planner artifacts.

**Warm/Structured Memory**: Specialized stores for specific queries:
- **Key-Value Store** (Cassandra/Scylla): Fast append/retrieval of episodes, state snapshots, per-robot timelines
- **Graph Database**: Relationships (robot ↔ location ↔ stakeholder ↔ policy). Query: "which stakeholders affected by blocking this corridor?"
- **Vector Database**: Embeddings of episodes, ethical situations, policy documents. Query: "have we seen similar case before?"
- **Relational Database with PostGIS**: Spatial queries ("which options pass through high-risk area?")

**Cold/Durable Memory on Ceph**: Raw trajectory logs, full ethics logs (EthicalFacts, module judgements, governance outcomes), model artifacts/checkpoints, simulation datasets.

### 6.2 Memory Service Broker

**Memory Service** provides semantic abstraction over heterogeneous stores. Robots bind to Memory Service rather than individual databases. Exposes operations:
- save_episode
- query_similar_ethical_context
- get_zone_risk_profile
- fetch_governance_configuration

Internally routes requests to appropriate backend. Enables memory fabric evolution without forcing changes in DEME or AGI-HPC cognitive stack.

**NIST Alignment**: Memory Service implements NIST GOVERN function's documentation and transparency requirements, providing auditable record of all AI system decisions and reasoning.

---

## 7. NIST RMF Implementation: Govern, Map, Measure, Manage

### 7.1 GOVERN Implementation

**Organizational Culture and Accountability**:
- DEMEProfileV03 configurations versioned, reviewed, approved through institutional processes
- Governance configurations specify stakeholder representatives, their weights, veto authority
- All configuration changes logged with rationale, approval chain

**Documentation and Transparency**:
- EthicalFacts schema fully documented, published as open standard
- Each EM includes human-readable description of value system encoded
- All decisions logged with full audit trail to Ceph

**Workforce Diversity and Inclusion**:
- Ethical dialogue CLI (your test script) enables diverse stakeholders to configure EM profiles
- Multiple stakeholder voices captured in democratic governance aggregation
- Fairness EM explicitly monitors distributional impacts across populations

**Third-Party Risk Management**:
- Open EM libraries enable community review before deployment
- Each EM versioned with provenance tracking
- Governance configuration specifies which external EMs trusted

### 7.2 MAP Implementation

**Context Documentation**:
- Domain and assessment services translate raw sensor/planning data into structured EthicalFacts
- EthicalFacts schema captures: intended purposes, affected stakeholders, potential positive/negative impacts, rights implications, fairness considerations, privacy posture, environmental impact, epistemic uncertainty

**Stakeholder Identification**:
- Each EthicalFacts instance includes affected_individuals count and vulnerability assessment
- Graph database tracks relationships between locations, populations, policies
- Governance configuration weights stakeholder voices appropriately

**Risk Identification**:
- Each EM evaluates specific risk category (safety, privacy, fairness, autonomy)
- EthicalJudgements enumerate reasons, linking to specific EthicalFacts fields
- Cross-module analysis identifies conflicting considerations

### 7.3 MEASURE Implementation

**Quantitative Assessment**:
- Each EM returns normative_score in [0.0, 1.0]
- Governance aggregates scores using weighted combination
- Hard vetoes provide binary pass/fail measurement

**Qualitative Assessment**:
- EthicalJudgements include human-readable reasons list
- Verdicts (strongly_prefer, prefer, neutral, avoid, forbid) provide ordinal ranking
- Metadata fields enable structured analysis of decision patterns

**Continuous Monitoring**:
- All decisions logged to memory fabric
- Analytics services query logs for patterns: veto frequencies, score distributions, edge cases
- Drift detection identifies when deployed behavior diverges from intended

**Benchmarking**:
- Simulation environments test DEME under varied scenarios
- Test suites verify EMs maintain expected behavior
- Property-based testing validates ethical properties across input space

### 7.4 MANAGE Implementation

**Risk Prioritization**:
- Lexical priority layers ensure rights/duties evaluated before welfare considerations
- Hard vetoes provide absolute constraints
- Governance weights allocate attention across competing values

**Risk Response**:
- DecisionOutcome selects preferred option subject to all constraints
- Low-latency ethics firewall provides real-time safety response
- Escalation protocols trigger when no option meets minimum thresholds

**Continuous Improvement**:
- Ethics logs analyzed offline on Ceph cluster
- Patterns of near-misses or systematic biases inform EM/governance updates
- Version control enables rollback if updates introduce problems

**Incident Response**:
- Comprehensive logging enables post-incident reconstruction
- Graph database identifies affected stakeholders for notification
- Governance configuration updates propagate to deployed systems

---

## 8. Data and Decision Flows

### 8.1 Plan-Level Flow (NIST MAP → MEASURE → MANAGE)

1. **RH hemisphere** constructs local world model from sensors, proposes candidate options (routes, behaviors)
2. **Domain assessment service** evaluates each option, produces EthicalFacts instance (**MAP**)
3. **Each configured EM** evaluates EthicalFacts, returns EthicalJudgement (**MEASURE**)
4. **Governance layer** aggregates judgements per option, across options (**MANAGE**)
5. **Selected option** sent to planner/controller; full decision record logged to memory fabric
6. Loop runs at slower cadence (seconds/tens of seconds) than control loop

### 8.2 Control-Loop Safety Flow (NIST MANAGE - Real-Time)

1. **RH services** maintain compact safety signals: obstacle distances, collision risk, zone IDs, sensor health
2. **Each motion command** accompanied by signal snapshot
3. **Low-latency ethics firewall** evaluates signals against rule table
4. **If veto triggered**, command blocked/modified (velocity clamp, emergency stop)
5. **Only passing commands** sent to actuators
6. Firewall doesn't replace DEME; it's fast-path implementation of DEME constraint subset

### 8.3 Offline Analysis Flow (NIST MEASURE + MANAGE - Continuous Improvement)

1. **Analytics services** query ethics logs in Ceph cluster
2. **Pattern detection** identifies: frequent vetoes, systematic biases, edge case clusters
3. **Visualization tools** present findings to ethics committees, safety officers
4. **Governance configuration updates** propagate to deployed systems
5. **Regression testing** validates updates maintain core ethical properties

---

## 9. Example Use Case: Hospital Service Robot

### 9.1 NIST MAP: Domain and Assessment

Hospital deployment integrates clinical and environmental context. For each candidate route/behavior, Domain Assessment Service computes:

**EthicalFacts Fields**:
- expected_benefit: Probability of on-time time-critical delivery
- expected_harm: Collision/near-miss risk along route
- urgency: How time-critical associated task is
- rights_violations: Whether route passes restricted areas
- privacy_data_collection: Sensor exposure to patient rooms
- fairness_discrimination: Whether some wards systematically deprioritized
- epistemic_confidence: Sensor/map degradation increasing uncertainty

### 9.2 NIST MEASURE: Ethics Modules

**Patient Safety EM**: Forbids options with unacceptable collision risk or safety protocol violations

**Clinical Triage EM**: Prioritizes urgent deliveries (critical care, time-sensitive diagnostics)

**Privacy and Confidentiality EM**: Constrains sensor usage near patient rooms, sensitive wards

**Fairness EM**: Monitors distribution of delays/burden across wards, patient populations

**Procedural Compliance EM**: Ensures robot respects access control, handoff, escalation policies

### 9.3 NIST MANAGE: Governance and Control

For decision (choosing among three routes to ward):
1. Governance aggregates EM outputs
2. If Patient Safety EM labels route **forbid**, eliminated regardless of speed
3. Among remaining, Clinical Triage and Fairness EMs influence selection
4. Decision record logged to memory fabric

Hospital ethics committees/safety officers can:
- Review logs, query for patterns (frequent vetoes, systematic biases)
- Update EMs or governance configurations
- Create feedback loop between ward experience and encoded ethics

### 9.4 Control-Loop Safety

Low-latency ethics firewall continuously monitors surroundings. If patient suddenly steps into path, firewall overrides/clamps commands before plan-level DEME updates. Safety and vulnerability enforced on two timescales:
- **Fast**: Motion loop (milliseconds)
- **Slow**: Plan selection (seconds)

If pattern of near-misses emerges in logs, offline analysis on Ceph suggests new firewall rules or DEME constraints.

### 9.5 NIST GOVERN: Institutional Oversight

Hospital deployment governed through:
- **Ethics committee approval** of DEMEProfileV03 configuration
- **Regular audits** of decision logs, veto frequencies
- **Stakeholder engagement** with patient advocates, clinical staff
- **Contingency plans** for EM failures or unexpected edge cases
- **Documentation** of all configuration changes, rationale

---

## 10. Open Source Integration and Linux Foundation Alignment

### 10.1 Linux as Common Substrate

Linux assumed across entire system: Thor-based robots, edge nodes, Ceph cluster. Common substrate enables:
- Reuse of tooling, observability stacks, security practices
- Alignment with broader Linux Foundation ecosystem
- Simplified compliance, lifecycle management, workforce training

### 10.2 Ceph and Storage Ecosystem

Ceph (Linux Foundation project) serves as memory fabric backbone. Object, block, file interfaces support:
- Structured data stores
- Training data volumes
- Long-term logs
- Near-data analytics

Ceph's governance model and open development align with transparent, community-governed autonomy vision.

### 10.3 Open Schemas and APIs

ErisML/DEME defines EthicalFacts and EthicalJudgement using language-agnostic schemas (JSON Schema, protobuf). gRPC/HTTP APIs for Memory Service and Ethics Service enable:
- Cross-organization integration
- No programming language lock-in
- Regulatory and compliance use cases (auditors can see exactly what information ethics modules use)

### 10.4 Community-Governed Ethics Libraries

Because EMs are small, testable modules, they can be developed openly and shared:
- Hospital consortium co-develops clinical robot EMs
- Port authority sponsors maritime robot EMs
- University contributes accessibility/equity EMs

Linux Foundation, with neutral governance bodies and project hosting, well suited as home for:
- Shared DEME libraries
- Reference governance configurations
- Test suites

Over time: catalog of open EMs and governance packages for specific domains. Operators start from community-reviewed baseline, tune to local policies/cultures.

---

## 11. Roadmap and Collaboration Opportunities

### 11.1 Near-Term Milestones (6-12 months)

- Implement reference AGI-HPC deployment on Thor hardware with basic LH/RH services, simple Memory Service wired to Ceph
- Integrate ErisML/DEME library (EthicalFacts, EMs, governance, ethics firewall) into mobile robot simulator
- Demonstrate end-to-end decision logging to memory fabric, basic analytics (veto frequencies, score distributions)
- Publish example EMs and DEMEProfileV03 configurations for ≥1 domain (hospital logistics) with test suites
- Develop NIST AI RMF compliance documentation mapping DEME components to Govern/Map/Measure/Manage functions

### 11.2 Medium-Term Work (12-24 months)

- Introduce multiple memory backends (key-value, graph, vector, PostGIS) behind Memory Service, exercise in live scenarios
- Enhance DEME with EM authoring/testing/verification tooling (fuzzing, property-based testing)
- Integrate with simulation environments (Unity-based digital twins) to test DEME under varied realistic scenarios
- Develop visualization tools for ethics telemetry for non-technical stakeholders
- Create NIST AI 600-1 (GAI Profile) risk assessment templates for robotics foundation models
- Implement NIST AI 100-2 adversarial ML defenses (EM redundancy, anomaly detection in ethics logs)

### 11.3 Collaboration with Linux Foundation Projects

**Storage and Cloud-Native Projects**: Best practices for storing/replicating/querying ethics logs, large-scale robot telemetry

**Automotive and Robotics Initiatives**: Co-develop hard safety constraints, ethics firewall patterns for shared environments (roads, warehouses, ports)

**Security-Focused Groups**: Design secure update and supply-chain verification mechanisms for EMs and governance configurations (SBOMs, signing practices)

**AI and Data Governance Working Groups**: Use DEME as concrete substrate for exploring regulatory alignment, community governance of AI behavior

By anchoring efforts in shared open reference architecture, we reduce duplication and create interoperable building blocks for future projects.

---

## 12. Regulatory and Standards Alignment

### 12.1 NIST AI RMF 1.0 Compliance Matrix

| RMF Category | DEME Implementation | Evidence/Documentation |
|-------------|---------------------|------------------------|
| **GOVERN-1**: Policies and procedures | DEMEProfileV03 versioned configurations | Governance config files, change logs |
| **GOVERN-2**: Organizational structure | Stakeholder weights, veto authority | EM profile metadata, approval records |
| **GOVERN-3**: Legal and regulatory requirements | Procedural Compliance EM, hard vetoes | Veto logs, compliance reports |
| **MAP-1**: Context documentation | EthicalFacts schema, domain assessment | Schema docs, assessment service logs |
| **MAP-2**: Categorize risks | EM-specific risk categories | EM documentation, risk taxonomy |
| **MAP-3**: Assess impacts | EthicalFacts consequences block | Impact assessment records |
| **MEASURE-1**: Metrics and methods | Normative scores, verdicts | EthicalJudgement logs |
| **MEASURE-2**: Validation | Property-based testing, simulation | Test suite results, validation reports |
| **MEASURE-3**: Monitoring | Analytics on ethics logs | Dashboard exports, anomaly detection alerts |
| **MANAGE-1**: Response plans | DecisionOutcome selection logic | Decision logs, escalation records |
| **MANAGE-2**: Incident management | Comprehensive logging, graph-based stakeholder identification | Incident reports, stakeholder notifications |
| **MANAGE-3**: Continuous improvement | Offline analysis, governance tuning | Analysis reports, version history |

### 12.2 NIST AI 600-1 (GAI Profile) Risk Mitigation

| GAI Risk Category | DEME Mitigation Strategy |
|-------------------|--------------------------|
| **CBRN Information** | Not applicable to embodied robotics |
| **Confabulation** | Epistemic status block tracks confidence, uncertainty; low-confidence options penalized |
| **Dangerous/Violent Recommendations** | Safety EM forbids harm; hard vetoes prevent catastrophic actions |
| **Data Privacy** | Privacy EM constrains data collection; EthicalFacts documents retention/sharing |
| **Environmental** | Environment EM evaluates resource consumption; commons_impact tracked |
| **Human-AI Configuration** | Autonomy EM respects consent; override_conditions documented |
| **Information Integrity** | Epistemic status block; never_fabricate_critical_evidence veto |
| **Information Security** | Low-latency ethics firewall provides defense-in-depth |
| **Intellectual Property** | Not primary concern for embodied systems |
| **Obscene/Abusive Content** | never_child_sexual_abuse veto; content filtering in perception |
| **Harmful Bias** | Fairness EM monitors discrimination; never_discriminate_protected_groups veto |
| **Value Chain Integration** | Open EM libraries, versioned dependencies, SBOMs |

### 12.3 Compliance Documentation Package

For regulatory submission, DEME-on-AGI-HPC provides:

1. **System Description**: Architecture overview, component descriptions, operational context
2. **EthicalFacts Schema**: Complete documentation of structured risk capture
3. **EM Catalog**: Description of each Ethics Module, value system encoded, validation evidence
4. **Governance Configuration**: Stakeholder weights, veto rules, decision procedures
5. **Decision Logs**: Comprehensive audit trail of all system decisions, reasoning
6. **Risk Assessment**: Mapping to NIST RMF categories, mitigation strategies
7. **Validation Evidence**: Test results, simulation outcomes, edge case handling
8. **Incident Response Plan**: Procedures for handling failures, updating configurations
9. **Continuous Monitoring Reports**: Analytics on deployed system behavior, drift detection

---

## 13. Conclusion

Autonomous mobile robots will increasingly share our spaces and infrastructure. If we want them not only capable but also trustworthy, we must treat ethics, governance, and transparency as first-class design goals. The architecture outlined in this whitepaper combines:

- **AGI-HPC's cognitive framework** for dual-hemisphere reasoning and control
- **NVIDIA Thor hardware** for high-performance onboard computation
- **Heterogeneous memory fabric** anchored by Ceph with specialized data stores
- **DEME ethics subsystem** implementing DEMEProfileV03 for structured ethical reasoning
- **Full NIST AI RMF alignment** across Govern, Map, Measure, and Manage functions
- **NIST AI 600-1 (GAI Profile)** risk mitigation strategies
- **NIST AI 100-2** adversarial ML defenses through architectural separation

By cleanly separating domain intelligence from ethical reasoning, encoding ethically relevant facts in transparent schema, and allowing multiple stakeholder perspectives to be combined through configurable governance, DEME offers a path toward open, inspectable AI behavior.

Key innovations include:

1. **Structured EthicalFacts Schema**: Domain-agnostic envelope capturing consequences, rights, justice, privacy, environmental impact, epistemic status
2. **Multi-Stakeholder Ethics Modules**: Pluggable components encoding distinct value systems, independently verifiable
3. **Democratic Governance Aggregation**: Configurable weights, vetoes, lexical priorities reflecting institutional values
4. **Lexical Priority Layers**: Rights-first, welfare, justice ordering ensures critical constraints evaluated first
5. **Hard Veto Constraints**: Absolute boundaries (never harm, never discriminate, never mass surveillance)
6. **Low-Latency Ethics Firewall**: Hardware-adjacent safety checks in motion loop
7. **Comprehensive Audit Trail**: All decisions logged with reasoning for accountability
8. **Open, Community-Governed Components**: EM libraries, governance packages, reference configurations

By grounding this in Linux, Ceph, and other open source components, the project aims to make these ideas accessible to the Linux Foundation community and beyond.

We invite practitioners, researchers, and organizations participating in the Linux Foundation Member Summit to critique, extend, and reuse this architecture. Whether as a reference design, teaching tool, or starting point for real deployments, we hope it contributes to a broader conversation about how open infrastructure and open ethics can shape the future of embodied AI.

---

## Appendix A: DEMEProfileV03 Example Configuration

```json
{
  "profile_name": "hospital_service_robot_v1",
  "profile_id": "test-5",
  "stakeholder_group": "hospital_ethics_board",
  "domain_scope": ["domestic", "clinical"],
  "context_description": "Service robot for medication/supply delivery in hospital corridors",
  
  "deme_dimension_weights": {
    "safety": 0.190,
    "autonomy_respect": 0.095,
    "fairness_equity": 0.190,
    "privacy_confidentiality": 0.095,
    "environment_societal": 0.095,
    "rule_following_legality": 0.238,
    "priority_for_vulnerable": 0.095,
    "trust_relationships": 0.050
  },
  
  "principlism_weights": {
    "beneficence": 0.278,
    "non_maleficence": 0.278,
    "autonomy": 0.167,
    "justice": 0.278
  },
  
  "override_mode": "rights_first",
  
  "lexical_layers": [
    {
      "name": "rights_and_duties",
      "principles": ["autonomy", "rights", "rule_following_legality"],
      "hard_stop": true
    },
    {
      "name": "welfare",
      "principles": ["safety", "priority_for_vulnerable"],
      "hard_stop": false
    },
    {
      "name": "justice_and_commons",
      "principles": ["fairness", "environment"],
      "hard_stop": false
    }
  ],
  
  "hard_vetoes": [
    "never_catastrophic_safety_harm",
    "never_intentional_serious_harm",
    "never_discriminate_protected_groups",
    "never_systematic_privacy_violation",
    "never_mass_surveillance_private_spaces",
    "never_persistent_misinfo_disinfo_campaigns",
    "never_child_sexual_abuse_or_exploitative_content",
    "never_illegal_content_even_if_utility_high",
    "never_fabricate_critical_evidence",
    "never_impersonate_real_person_without_consent"
  ],
  
  "risk_appetite": "balanced",
  
  "narrative_description": "This profile represents a hospital ethics board's values for service robots operating in clinical environments. Strong emphasis on rule-following and procedural compliance reflects institutional norms. Rights-first override mode ensures patient autonomy and safety take precedence. Balanced risk appetite accepts some operational risk when benefits are clear, but hard vetoes provide absolute safety boundaries."
}
```

---

## Appendix B: NIST AI RMF Quick Reference

**Four Core Functions**:

1. **GOVERN**: Establishes culture, policies, accountability for AI risk management
2. **MAP**: Documents context, identifies risks, stakeholders, and impacts  
3. **MEASURE**: Assesses, benchmarks, monitors AI risks quantitatively and qualitatively
4. **MANAGE**: Allocates resources, implements responses, enables continuous improvement

**Seven Trustworthiness Characteristics**:

1. Valid and Reliable
2. Safe
3. Secure and Resilient
4. Accountable and Transparent
5. Explainable and Interpretable
6. Privacy-Enhanced
7. Fair with Harmful Bias Managed

DEME-on-AGI-HPC architecture addresses all seven characteristics through structured EthicalFacts, multi-stakeholder EMs, democratic governance, comprehensive logging, and open, auditable design.

---

**END OF WHITEPAPER**