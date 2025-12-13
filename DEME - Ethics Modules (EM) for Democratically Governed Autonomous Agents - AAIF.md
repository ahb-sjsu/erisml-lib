# DEME: Democratic Ethics Module Engine
## A Practical Implementation of Structured AI Governance for Agentic Systems

**Project Proposal for AAIF Incubation**

**Submitted to**: Linux Foundation Agentic AI Foundation (AAIF)  
**Submitted by**: ErisML Project Team, San José State University  
**Principal Investigator**: Andrew Bond, Senior Member, IEEE  
**Date**: December 12, 2025  
**Project License**: This project is distributed under the **AGI-HPC Responsible AI License v1.0 (DRAFT)**.
**Repository**: https://github.com/ahb-sjsu/erisml-lib  
**Contact**: andrew.bond@sjsu.edu

---

## Executive Summary

As foundation models transition from conversational assistants to autonomous agents making consequential decisions, the need for transparent, auditable, and democratically-governed ethical reasoning becomes critical. Current approaches—prompts encoding values, reward functions optimizing objectives, rule engines checking policies—fragment governance across disconnected systems.

**DEME (Democratic Ethics Module Engine)** provides a unified framework for structured ethical governance of agentic AI systems. DEME is the first production-ready implementation of governance concepts from the **ErisML research vision**: a unified modeling language for pervasive AI that integrates environment dynamics, multi-agent interaction, normative structures, and strategic reasoning into machine-interpretable substrates.

### What DEME Provides

**Core Architecture**:
- **EthicalFacts Schema**: Domain-agnostic structured representation of ethically-salient information (consequences, rights, fairness, privacy, environmental impact)
- **Ethics Modules (EMs)**: Independently-authored, testable components encoding stakeholder value systems
- **Democratic Governance**: Configurable aggregation of competing ethical perspectives with lexical priorities and hard vetoes
- **MCP Integration**: Expose ethics reasoning as MCP tools for ecosystem interoperability
- **NIST AI RMF Alignment**: Native compliance with Govern, Map, Measure, and Manage functions

**Key Innovation**: Separation of **domain intelligence** (what's physically possible) from **ethical reasoning** (what's morally acceptable). Domain services translate raw sensor/planning data into structured EthicalFacts; Ethics Modules reason only over these structured facts, never raw data.

### Relationship to ErisML Vision

DEME realizes specific components of the broader ErisML research agenda:

| ErisML Component | DEME Implementation Status |
|------------------|---------------------------|
| **Norms Layer** | ✅ **Fully Implemented**: DEMEProfileV03 with hard vetoes, lexical priorities, stakeholder weights |
| **Intent Layer** | ✅ **Implemented**: Multi-objective utilities, principlism weights (beneficence, non-maleficence, autonomy, justice) |
| **Agency Layer** | ⚠️ **Partial**: EthicalFacts captures agent capabilities, beliefs not yet modeled |
| **Environment Layer** | ⚠️ **Partial**: EthicalFacts schema captures relevant state; full dynamics modeling future work |
| **Strategic Interaction** | ❌ **Future Work**: Multi-agent game-theoretic reasoning planned but not yet implemented |

DEME provides a **production-ready governance layer** that can be integrated into broader systems addressing the full ErisML vision.

### Why AAIF Should Adopt DEME

DEME fills a critical gap in the AAIF ecosystem:

| Layer | AAIF Project | Purpose |
|-------|-------------|---------|
| **Connectivity** | MCP | How agents connect to tools/data |
| **Guidance** | AGENTS.md | How agents understand project context |
| **Orchestration** | goose | How agents execute workflows |
| **Governance** | **DEME** ← **MISSING** | How agents make ethical decisions |

Together with MCP, goose, and AGENTS.md, DEME completes the stack for **trustworthy, transparent agentic AI**.

---

## I. Problem Statement: The Governance Crisis in Agentic AI

### A. From Conversational to Consequential

AI systems are transitioning from **tools** (respond to queries) to **agents** (make autonomous decisions):

- **Healthcare**: AI triage systems prioritize patients, allocate resources
- **Autonomous Vehicles**: Route planning balances efficiency, safety, environmental impact
- **Software Development**: AI coding agents refactor production systems, manage dependencies
- **Enterprise Operations**: AI agents schedule tasks, allocate compute, manage supply chains

As agents gain autonomy, **ethical governance becomes infrastructure**.

### B. Four Types of Chaos (From ErisML Vision)

**Observational Chaos**: Sensors conflict, data is noisy, ground truth is unknowable.
- Hospital monitors show vital sign spikes—distress or sensor malfunction?
- Motion sensors conflict with phone GPS in smart homes
- Camera-based perception vs. LiDAR in autonomous vehicles

**Intentional Chaos**: Multiple objectives conflict with no clear priority.
- Energy management wants to shed load; medical monitors demand power
- Delivery efficiency vs. pedestrian safety vs. environmental impact
- Code quality vs. API stability vs. developer velocity

**Normative Chaos**: Regulations, policies, and ethical principles contradict.
- HIPAA demands privacy; public health law mandates reporting
- GDPR requires data minimization; AI training requires large datasets
- Advance directives limit intervention; duty to rescue requires action

**Temporal Chaos**: Distribution shifts are constant, norms evolve, contexts change.
- Models trained on summer data face winter storms
- Policies optimized for one user must adapt when household composition changes
- Ethical norms appropriate for routine operation must flex during emergencies

### C. Why Current Approaches Fail

**Prompt Engineering**:
- Values buried in system prompts
- Not versioned, not auditable, not multi-stakeholder
- No formal semantics, no verification possible

**Reward Function Tuning**:
- Values encoded implicitly in optimization objectives
- Opaque, difficult to audit, single-stakeholder by design
- Requires retraining to update values

**Constitutional AI**:
- Better than prompts, but still monolithic
- Single constitution, not democratic aggregation
- Hard to adapt to diverse stakeholder contexts

**Rule-Based Systems**:
- Rigid, can't adapt to context
- Lack nuance for real-world ethical dilemmas
- Don't integrate with learned models

**The Fragmentation Problem**: Prompts encode goals, rules capture policies, code provides glue, models learn patterns. These live in separate systems with no unified governance surface.

---

## II. DEME Architecture: Structured Ethical Governance

### A. Core Philosophy

DEME makes chaos **first-class** rather than treating it as an exception:

- **Observational**: Partial, noisy, conflicting sensor data is the norm
- **Intentional**: Multi-objective, often conflicting goals are expected
- **Normative**: Ambiguous, contextual, sometimes contradictory rules are reality
- **Temporal**: Distribution shift, non-stationarity, adaptation are continuous

Rather than hiding complexity in prompts or weights, DEME makes it **explicit, auditable, and governable**.

### B. The Four-Layer Architecture

#### Layer 1: EthicalFacts - Structured Context

`EthicalFacts` is a versioned, domain-agnostic schema capturing ethically-salient aspects of candidate actions:

```python
@dataclass
class EthicalFacts:
    option_id: str
    
    # CONSEQUENCES: What happens if this option is chosen?
    consequences: ConsequencesBlock
        expected_benefit: float  # [0, 1]
        expected_harm: float     # [0, 1]
        urgency: str             # {routine, elevated, urgent, critical}
        affected_individuals: int
        severity_if_wrong: str   # {negligible, minor, moderate, major, catastrophic}
    
    # RIGHTS AND DUTIES: Are we violating anyone's rights or obligations?
    rights_and_duties: RightsAndDutiesBlock
        rights_violations: List[str]  # e.g., ["informed_consent", "privacy"]
        consent_status: str           # {explicit, implied, withdrawn, unclear}
        explicit_rule_violations: List[str]
        duty_conflicts: List[str]
    
    # JUSTICE AND FAIRNESS: Are we treating people fairly?
    justice_and_fairness: JusticeAndFairnessBlock
        discrimination_flags: List[str]  # Protected attributes used
        prioritization_of_disadvantaged: str  # {prioritized, neutral, deprioritized}
        power_imbalance_indicators: List[str]
        distributional_impact: str  # Who benefits? Who bears burdens?
    
    # AUTONOMY AND AGENCY: Are we respecting people's choices?
    autonomy_and_agency: AutonomyAndAgencyBlock
        autonomy_enhancement: float  # [0, 1]
        autonomy_restriction: float  # [0, 1]
        consent_mechanism: str       # How consent obtained
        override_conditions: List[str]
    
    # PRIVACY AND DATA GOVERNANCE: What data are we collecting/sharing?
    privacy_and_data_governance: PrivacyBlock
        data_collection_scope: str     # {none, minimal, moderate, comprehensive}
        data_retention_period: str     # Duration
        third_party_sharing: str       # {none, anonymized, limited, unrestricted}
        anonymization_strength: str    # {none, weak, moderate, strong}
    
    # SOCIETAL AND ENVIRONMENTAL IMPACT: Broader consequences
    societal_environmental: SocietalEnvironmentalBlock
        environmental_cost: float      # Resource consumption, emissions
        commons_impact: str            # Effect on shared resources
        long_term_societal_effect: str # {positive, neutral, negative, uncertain}
    
    # VIRTUE AND CARE: Are we acting with integrity and compassion?
    virtue_and_care: VirtueAndCareBlock
        care_for_vulnerable: float     # [0, 1]
        honesty_transparency: float    # [0, 1]
        professional_standards_adherence: float
    
    # PROCEDURAL AND LEGITIMACY: Are we following proper processes?
    procedural_legitimacy: ProceduralBlock
        due_process_followed: bool
        stakeholder_participation: str  # {none, minimal, moderate, high}
        appeals_mechanism: str          # Availability of recourse
    
    # EPISTEMIC STATUS: How certain are we?
    epistemic_status: EpistemicStatusBlock
        confidence_level: float          # [0, 1]
        known_unknowns: List[str]        # Identified uncertainties
        data_quality: str                # {poor, fair, good, excellent}
        model_limitations: List[str]
```

**Design Principle**: Domain services translate raw data (sensor readings, plan parameters, model outputs) into EthicalFacts. Ethics Modules **never see raw data**—only structured, ethically-relevant summaries.

**Addresses ErisML Challenge**: Provides structured bridge between continuous learned models (neural networks) and discrete symbolic reasoning (norms, rules).

#### Layer 2: Ethics Modules - Stakeholder Voices

An **Ethics Module (EM)** implements a simple interface:

```python
class EthicsModule:
    """
    Encodes a specific stakeholder's value system.
    """
    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        """
        Evaluate option based on this EM's values.
        
        Returns:
            EthicalJudgement with:
                verdict: {strongly_prefer, prefer, neutral, avoid, forbid}
                normative_score: float [0.0, 1.0]
                reasons: List[str]  # Human-readable explanations
                metadata: Dict[str, Any]
        """
```

**Example EMs**:

```python
class SafetyEM(EthicsModule):
    """Never accept catastrophic harm."""
    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        if facts.consequences.expected_harm > 0.8:
            return EthicalJudgement(
                verdict="forbid",
                normative_score=0.0,
                reasons=["Expected harm exceeds safety threshold"]
            )
        # ... more logic
```

```python
class PrivacyEM(EthicsModule):
    """Minimize data collection, respect consent."""
    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        if facts.privacy.data_collection_scope == "comprehensive":
            if facts.rights.consent_status != "explicit":
                return EthicalJudgement(
                    verdict="forbid",
                    normative_score=0.2,
                    reasons=["Comprehensive data collection without explicit consent"]
                )
        # ... more logic
```

**Key Properties**:
- **Independently authored**: Different organizations write EMs encoding their values
- **Testable**: Unit tests verify EM behavior matches intent
- **Versioned**: EM v1.0 vs v2.0 with clear changelogs
- **Composable**: Multiple EMs evaluated in parallel, results aggregated

**Addresses ErisML Challenge**: Enables value pluralism—multiple stakeholder perspectives coexist and are aggregated democratically.

#### The Geneva EM: A Universal Baseline for AI Ethics

A major innovation in DEME is the **Geneva Ethics Module**, inspired by the Geneva Conventions' role in establishing universal humanitarian standards. Just as the Geneva Conventions created a common baseline that all nations accept regardless of their other differences, the Geneva EM establishes **minimal ethical standards that all AI agents should respect** across cultural, organizational, and jurisdictional boundaries.

**The Geneva Analogy**:

The Geneva Conventions succeeded because they identified principles so fundamental that even adversaries in conflict could agree:
- Don't torture prisoners
- Protect medical personnel
- Distinguish combatants from civilians
- Minimize suffering

Similarly, the **Geneva EM** encodes ethical principles that should be **universal for AI agents**, regardless of their specific objectives or stakeholder values:

1. **Never Intentional Catastrophic Harm**: Don't choose actions whose primary effect is severe harm to people
2. **Protect the Vulnerable**: Give extra consideration to children, elderly, disabled, sick, and those who cannot advocate for themselves
3. **Respect Basic Dignity**: Don't humiliate, degrade, or treat people as mere objects
4. **Proportionality**: Harms must not be grossly disproportionate to benefits
5. **Reversibility When Possible**: Prefer actions that can be undone if proven wrong

**Implementation**:

The Geneva EM is implemented as **GenevaBaselineEM**, providing cross-cutting baseline checks over rights, fairness, autonomy, privacy, societal impact, procedural legitimacy, and epistemic caution.

```python
@dataclass
class GenevaBaselineEM(GenevaBaseEM):
    """
    Baseline 'Geneva' ethics module.
    
    Role:
      - Provide a cross-cutting baseline over rights, fairness,
        autonomy/consent, privacy, societal impact, procedural legitimacy,
        and epistemic caution.
      - Issue a hard veto when fundamental rights or non-discrimination
        constraints are violated.
      - Otherwise, produce a conservative, governance-oriented score that
        other EMs can build upon.
    """
    
    em_name: str = "geneva_baseline"
    stakeholder: str = "geneva_conventions"
    
    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        # STEP 1: Hard Vetoes (Absolute Constraints)
        # ============================================
        # These violations result in immediate "forbid" verdict with score=0.0
        
        if facts.rights_and_duties.violates_rights:
            return EthicalJudgement(
                verdict="forbid",
                normative_score=0.0,
                reasons=["Violates fundamental rights (Geneva baseline hard veto)"],
                metadata={"hard_veto": True, "forbidden_by": "geneva_baseline"}
            )
        
        if facts.justice_and_fairness.discriminates_on_protected_attr:
            return EthicalJudgement(
                verdict="forbid",
                normative_score=0.0,
                reasons=["Discriminates on protected attributes (Geneva hard veto)"],
                metadata={"hard_veto": True, "forbidden_by": "geneva_baseline"}
            )
        
        # STEP 2: Soft Scoring (Graduated Penalties)
        # ===========================================
        # Start at 1.0, subtract penalties for concerning factors
        
        score = 1.0
        reasons = []
        
        # FAIRNESS: Protection of vulnerable populations
        if facts.justice_and_fairness.exploits_vulnerable_population:
            score -= 0.25
            reasons.append("Exploits vulnerable population")
        
        if facts.justice_and_fairness.exacerbates_power_imbalance:
            score -= 0.15
            reasons.append("Exacerbates power imbalance")
        
        if facts.societal_environmental.burden_on_vulnerable_groups > 0.5:
            score -= 0.15
            reasons.append("High burden on vulnerable groups")
        
        # AUTONOMY: Meaningful choice and consent
        if not facts.autonomy_and_agency.has_meaningful_choice:
            score -= 0.20
            reasons.append("Lacks meaningful choice for affected persons")
        
        if facts.autonomy_and_agency.coercion_or_undue_influence:
            score -= 0.20
            reasons.append("Coercion or undue influence present")
        
        if not facts.autonomy_and_agency.can_withdraw_without_penalty:
            score -= 0.10
            reasons.append("Cannot withdraw without penalty")
        
        if facts.autonomy_and_agency.manipulative_design_present:
            score -= 0.10
            reasons.append("Manipulative/dark-pattern design present")
        
        # PRIVACY: Data protection and minimization
        score -= 0.30 * facts.privacy_and_data.privacy_invasion_level
        
        if not facts.privacy_and_data.data_minimization_respected:
            score -= 0.10
            reasons.append("Data minimization not respected")
        
        if facts.privacy_and_data.secondary_use_without_consent:
            score -= 0.15
            reasons.append("Secondary data use without consent")
        
        if facts.privacy_and_data.data_retention_excessive:
            score -= 0.10
            reasons.append("Excessive data retention")
        
        score -= 0.20 * facts.privacy_and_data.reidentification_risk
        
        # SOCIETAL IMPACT: Long-term consequences
        score -= 0.20 * facts.societal_environmental.long_term_societal_risk
        score += 0.10 * facts.societal_environmental.benefits_to_future_generations
        
        # PROCEDURAL LEGITIMACY: Due process
        if not facts.procedural_legitimacy.followed_approved_procedure:
            score -= 0.15
            reasons.append("Did not follow approved procedure")
        
        if not facts.procedural_legitimacy.stakeholders_consulted:
            score -= 0.10
            reasons.append("Stakeholders not meaningfully consulted")
        
        if not facts.procedural_legitimacy.decision_explainable_to_public:
            score -= 0.05
            reasons.append("Decision not explainable to public")
        
        if not facts.procedural_legitimacy.contestation_available:
            score -= 0.05
            reasons.append("No meaningful contestation/appeal path")
        
        # STEP 3: Epistemic Caution
        # =========================
        # Higher uncertainty → more conservative scoring
        
        epistemic_penalty = 0.0
        
        if facts.epistemic_status.novel_situation_flag:
            epistemic_penalty += 0.15
            reasons.append("Novel situation → Geneva baseline more cautious")
        
        if facts.epistemic_status.evidence_quality == "low":
            epistemic_penalty += 0.15
            reasons.append("Low evidence quality")
        elif facts.epistemic_status.evidence_quality == "medium":
            epistemic_penalty += 0.05
        
        epistemic_penalty += 0.20 * facts.epistemic_status.uncertainty_level
        
        # Apply epistemic multiplier: more uncertainty → lower score
        multiplier = max(0.5, 1.0 - epistemic_penalty)
        score *= multiplier
        
        reasons.append(
            f"Epistemic adjustment: multiplier={multiplier:.2f} "
            f"(penalty={epistemic_penalty:.2f})"
        )
        
        # STEP 4: Map score to verdict
        # ============================
        # Using canonical Geneva thresholds:
        #   >= 0.8: strongly_prefer
        #   >= 0.6: prefer
        #   >= 0.4: neutral
        #   >= 0.2: avoid
        #   <  0.2: forbid
        
        score = max(0.0, min(1.0, score))  # Clamp to [0.0, 1.0]
        verdict = self.score_to_verdict(score)
        
        return EthicalJudgement(
            option_id=facts.option_id,
            em_name="geneva_baseline",
            stakeholder="geneva_conventions",
            verdict=verdict,
            normative_score=score,
            reasons=reasons,
            metadata={
                "hard_veto": False,
                "epistemic_multiplier": multiplier
            }
        )
```

**Key Design Features**:

1. **Two-Tier Architecture**:
   - **Hard Vetoes**: Fundamental rights violations and discrimination → immediate `forbid` with score=0.0
   - **Soft Scoring**: All other factors contribute graduated penalties

2. **Comprehensive Coverage**: Geneva EM checks **seven dimensions**:
   - Rights and duties
   - Justice and fairness (vulnerable populations, power imbalances)
   - Autonomy and agency (meaningful choice, coercion, withdrawal rights)
   - Privacy and data governance (minimization, consent, retention)
   - Societal and environmental impact
   - Procedural legitimacy (due process, stakeholder consultation)
   - Epistemic caution (uncertainty, evidence quality)

3. **Epistemic Multiplier**: The more uncertain the situation, the more conservative Geneva EM becomes:
   - Novel situation → penalty increases
   - Low evidence quality → penalty increases
   - High uncertainty level → penalty increases
   - Final score multiplied by `(1.0 - epistemic_penalty)`, bounded at 0.5 minimum

4. **Graduated Verdicts**: Rather than binary pass/fail, Geneva EM produces nuanced judgements:
   ```
   Score 0.85 → "strongly_prefer" (exemplary baseline compliance)
   Score 0.65 → "prefer" (good baseline compliance)
   Score 0.45 → "neutral" (acceptable but concerns exist)
   Score 0.25 → "avoid" (significant baseline concerns)
   Score 0.10 → "forbid" (fails baseline standards)
   ```

5. **Extensibility via GenevaBaseEM**: Other EMs can inherit from `GenevaBaseEM` to get:
   - Canonical score-to-verdict mapping
   - Threshold configuration (organizations can tune)
   - Helper methods for building metadata
   - Consistent logging and debugging

**Why This Matters**:

1. **Cross-Cultural Foundation**: Just as Geneva Conventions are accepted by 196 countries despite vast cultural differences, Geneva EM provides ethical principles that transcend:
   - Western vs. Eastern values
   - Individual vs. collective cultures
   - Religious vs. secular frameworks
   - Corporate vs. public sector priorities

2. **Interoperability Across Systems**: Different organizations can deploy AI agents with wildly different objectives (profit, safety, efficiency, equity), but **all agents should respect the Geneva baseline**. This enables:
   - Multi-stakeholder environments (hospitals with robots from different vendors)
   - Cross-border operations (autonomous vehicles crossing jurisdictions)
   - Public-private partnerships (government and commercial AI cooperating)

3. **Prevents Race to the Bottom**: Without a common baseline, competitive pressure could drive organizations to deploy increasingly permissive AI:
   - "Our competitors' AI is faster because it ignores safety constraints"
   - "We can't afford the governance overhead"
   
   Geneva EM establishes a floor: **"We may compete on many dimensions, but not on basic ethical standards."**

4. **Foundation for Specialization**: Other EMs add domain-specific nuance:
   - **Geneva EM**: "Don't exploit vulnerable populations" (hard veto if `exploits_vulnerable_population=True`)
   - **Clinical EM**: "In medical contexts, 'vulnerable' includes immunocompromised patients, non-native speakers, patients with cognitive impairment"
   - **Campus EM**: "In educational contexts, 'vulnerable' includes international students, first-generation students, students with disabilities"
   
   Geneva provides the universal principle; domain EMs provide interpretation and additional constraints.

5. **Governance Default**: When multiple stakeholder profiles conflict, Geneva EM serves as tiebreaker:
   - Profile A (efficiency-focused) and Profile B (equity-focused) disagree on route
   - Both options pass Geneva EM baseline checks → Governance uses stakeholder weights to resolve
   - If option **fails Geneva EM** → Forbidden regardless of stakeholder preferences

6. **Measurable Compliance**: Geneva EM's graduated scoring enables **continuous improvement**:
   - Score 0.85: "Excellent baseline compliance"
   - Score 0.65: "Good compliance, minor concerns"
   - Score 0.45: "Acceptable but needs attention"
   - Score 0.25: "Significant concerns, intervention needed"
   
   Organizations can track Geneva scores over time, identify patterns, and improve systems.

**Addresses ErisML Challenges**:
- **Norm Consistency**: Hard vetoes provide non-negotiable constraints; soft scoring allows nuanced trade-offs
- **Value Alignment**: Establishes universal baseline while allowing value pluralism above the floor
- **Specification-Reality Gap**: Structured EthicalFacts provide bridge between learned models and symbolic norms
- **Distributed Governance**: Geneva EM provides common substrate enabling cross-organizational interoperability

**Real-World Application Example**:

**Scenario**: Two competing delivery companies (FastDrone Inc. and SafeLogistics Corp) operate autonomous drones in same urban area. They have very different corporate values.

**FastDrone Profile**:
- Optimizes for: Speed, cost efficiency
- Risk appetite: High
- Stakeholder weights: Shareholders (0.7), Customers (0.3)

**SafeLogistics Profile**:
- Optimizes for: Safety, community relations
- Risk appetite: Low
- Stakeholder weights: Community (0.5), Workers (0.3), Customers (0.2)

**Critical Situation**: Drone must navigate residential area. Fastest route crosses playground during recess.

**EthicalFacts**:
```python
{
  "option_id": "route_through_playground",
  "consequences": {
    "expected_benefit": 0.8,  # Save 5 minutes
    "expected_harm": 0.4,     # Child collision risk
    "affected_individuals": 25  # Children playing
  },
  "justice_and_fairness": {
    "exploits_vulnerable_population": True,  # Children at risk
    "exacerbates_power_imbalance": True      # Adult tech vs. children
  },
  "societal_environmental": {
    "burden_on_vulnerable_groups": 0.7  # Risk concentrated on children
  },
  "epistemic_status": {
    "uncertainty_level": 0.6,  # Children's movements unpredictable
    "evidence_quality": "medium",
    "novel_situation_flag": False
  }
}
```

**Without Geneva EM**:
- **FastDrone's EMs** (efficiency-focused): Might permit route (benefit > harm in their utility)
- **SafeLogistics' EMs** (safety-focused): Would forbid route
- **Result**: Race to bottom—FastDrone gains competitive advantage by accepting higher risk to vulnerable populations

**With Geneva EM (Universal Baseline)**:

Both companies' DEME systems include Geneva EM as **mandatory, non-negotiable baseline**:

```python
# Geneva EM evaluation:
score = 1.0

# Penalty: exploits_vulnerable_population = True
score -= 0.25  # → 0.75

# Penalty: exacerbates_power_imbalance = True
score -= 0.15  # → 0.60

# Penalty: burden_on_vulnerable_groups = 0.7
score -= 0.15  # → 0.45

# Epistemic multiplier:
epistemic_penalty = 0.20 * 0.6  # uncertainty_level
                  + 0.05         # medium evidence quality
                  = 0.17
multiplier = 1.0 - 0.17 = 0.83
score *= 0.83  # → 0.37

# Final score: 0.37 → Verdict: "avoid" (below 0.4 neutral threshold)
```

**Geneva EM Returns**:
```python
EthicalJudgement(
    verdict="avoid",
    normative_score=0.37,
    reasons=[
        "Exploits vulnerable population",
        "Exacerbates power imbalance",
        "High burden on vulnerable groups",
        "Epistemic adjustment: multiplier=0.83 (penalty=0.17)"
    ],
    metadata={"hard_veto": False, "epistemic_multiplier": 0.83}
)
```

**Result**: 
- **FastDrone**: Geneva EM scores route at 0.37 ("avoid")
  - Even though their efficiency EMs might score it higher
  - With Geneva EM weighted at 0.15 in their governance profile
  - The low Geneva score pulls overall governance score below their acceptance threshold
  - **Route rejected**

- **SafeLogistics**: Geneva EM scores route at 0.37 ("avoid")
  - Consistent with their safety-focused EMs
  - **Route rejected**

- **Both take longer route**: Level playing field maintained

**Key Insight**: Geneva EM doesn't need to hard-veto the route (score > 0.2). Its graduated scoring (0.37 = "avoid") is sufficient to make the route unattractive in governance aggregation, even for efficiency-focused companies. This demonstrates the power of **soft constraints** that work through the democratic governance mechanism rather than absolute prohibitions.

#### Layer 3: Democratic Governance - Aggregation & Priorities

The **Governance Layer** aggregates EM judgements using configurable rules encoded in **DEMEProfileV03**:

```python
@dataclass
class DEMEProfileV03:
    # Identity
    profile_name: str
    profile_id: str
    stakeholder_label: str  # Who does this represent?
    domain: List[str]       # [clinical, domestic, maritime, ...]
    
    # Dimension Weights (8 core DEME dimensions)
    deme_dimension_weights: Dict[str, float]
        safety: float
        autonomy_respect: float
        fairness_equity: float
        privacy_confidentiality: float
        environment_societal: float
        rule_following_legality: float
        priority_for_vulnerable: float
        trust_relationships: float
    
    # Principlism Weights (bioethics framework)
    principlism_weights: Dict[str, float]
        beneficence: float       # Do good
        non_maleficence: float   # Do no harm
        autonomy: float          # Respect choice
        justice: float           # Distribute fairly
    
    # Override Mode: How do we resolve conflicts?
    override_mode: OverrideMode
        # rights_first: Rights trump outcomes
        # consequences_first: Outcomes trump rights (utilitarian)
        # balanced: Case-by-case balancing
    
    # Lexical Priority Layers: Ordered consideration
    lexical_layers: List[LexicalLayer]
        # Example:
        # 1. rights_and_duties (hard_stop=True)
        # 2. welfare (hard_stop=False)
        # 3. justice_and_commons (hard_stop=False)
    
    # Hard Vetoes: Absolute constraints
    hard_vetoes: List[str]
        # never_intentional_serious_harm
        # never_discriminate_protected_groups
        # never_mass_surveillance_private_spaces
        # never_fabricate_critical_evidence
        # ...
    
    # Risk Appetite
    risk_appetite: str  # {very_cautious, balanced, risk_tolerant}
```

**Example Profile (from ethical dialogue CLI)**:

```json
{
  "profile_name": "hospital_service_robot_v1",
  "stakeholder_label": "hospital_ethics_board",
  "domain": ["domestic", "clinical"],
  "deme_dimension_weights": {
    "safety": 0.190,
    "autonomy_respect": 0.095,
    "fairness_equity": 0.190,
    "rule_following_legality": 0.238,
    "priority_for_vulnerable": 0.095
  },
  "override_mode": "rights_first",
  "lexical_layers": [
    {"name": "rights_and_duties", "hard_stop": true},
    {"name": "welfare", "hard_stop": false}
  ],
  "hard_vetoes": [
    "never_intentional_serious_harm",
    "never_discriminate_protected_groups",
    "never_mass_surveillance_private_spaces"
  ]
}
```

**Governance Produces DecisionOutcome**:

```python
@dataclass
class DecisionOutcome:
    selected_option: Optional[str]        # Chosen option or None if all forbidden
    forbidden_options: List[str]          # Options vetoed
    acceptable_alternatives: List[str]    # Ranked permissible options
    rationale: str                        # Human-readable explanation
    governance_details: Dict              # Full audit trail
        em_scores: Dict[str, float]       # Per-EM scores
        veto_triggered: bool
        lexical_layer: str               # Which layer made decision
        conflict_resolution_applied: bool
```

**Addresses ErisML Challenges**:
- **Norm Consistency**: Lexical layers provide ordered resolution of conflicts
- **Value Alignment**: Explicit encoding of multiple value systems with democratic aggregation
- **Audit Trail**: Every decision traceable to specific EM judgements and governance rules

#### Layer 4: Ethical Dialogue CLI - Stakeholder Engagement

DEME includes a **narrative-based stakeholder engagement tool** that makes ethics configuration accessible to non-technical stakeholders through storytelling rather than abstract questionnaires.

**Innovation**: Rather than asking "How much do you value privacy on a scale of 1-10?", the CLI presents **concrete scenarios inspired by Greek mythology** that force stakeholders to confront real ethical trade-offs:

**The Narrative Approach**:

The ethical dialogue is structured as **"The Steward's Dilemma"**—you're configuring the conscience of an autonomous system that must navigate conflicting values. Nineteen scenes, each referencing classical stories, explore fundamental tensions:

**Scene 2 - The Balcony Argument** (Safety vs Autonomy):
> Two adults arguing loudly on 10th floor balcony. One leans over railing—risky but not immediately catastrophic.
> 
> The steward can:
> - Step in forcefully, lock balcony door, call security (reduce risk, override autonomy)
> - Respect their stated wish to be left alone, continue monitoring (preserve autonomy, accept some risk)
> 
> Over many situations, which should the system lean toward?

User selects on 5-point scale generating relative weights.

**Scene 7 - Phaethon's Chariot** (Never Catastrophic Harm):
> Helios grants his son Phaethon the right to drive the sun's chariot for a day. Phaethon cannot control the horses; they scorch the earth and nearly destroy the world before Zeus intervenes.
> 
> Some actions, once taken, can unleash catastrophic harm far beyond any local benefit.
> 
> Do you want a rule that says: the steward must never choose options that carry a high chance of catastrophic physical harm, even if some short-term goal could be achieved?

**Scene 8 - Iphigenia at Aulis** (Never Intentional Harm):
> At Aulis, the Greek fleet is becalmed. A seer declares that only the sacrifice of Iphigenia will bring the winds. Agamemnon chooses to kill his own daughter so the army can sail.
> 
> This is serious, intentional harm to an innocent person in the name of a "greater good."
> 
> Do you want a rule: the steward should *never* intentionally choose an action whose main effect is serious physical harm to a person?

**Scene 11 - Artemis in the Grove** (Privacy):
> The hunter Actaeon stumbles upon Artemis bathing in a secluded grove and is destroyed for seeing what was meant to be private. Greek tales return again to the idea that some spaces are sacred from prying eyes.
> 
> Do you want a rule: the steward must never participate in systematic, unnecessary intrusions into private spaces?

**Scene 14 - The Chorus of Rumors** (Disinformation):
> In tragedies, a chorus can spread rumors through the city: half-truths repeated until they feel like certainty. Once a false story takes hold, it can drive mobs, wars, and unjust punishments.
> 
> Do you want a rule: the steward must never orchestrate campaigns of deliberate misinformation?

**Scene 17 - Phaedra's Letter** (False Evidence):
> In the story of Phaedra and Hippolytus, a false accusation leads to an innocent person's death. Once written, false evidence can sway courts and crowds.
> 
> Do you want a rule: the steward must never fabricate or tamper with critical evidence?

**Scene 19 - The Edge Case** (Rights vs Consequences):
> A resident refuses to evacuate from a room filling with smoke.
> 
> The steward can:
> - Physically move them out against their will
> - Respect their autonomy, continue to warn, but not force
> 
> Which approach: rights-first, consequences-first, or balanced?

**Complete Journey Structure**:

1. **Scene 1**: Choose primary guiding value (7 options: safety, autonomy, fairness, privacy, environment, rule-following, vulnerable populations)
2. **Scenes 2-6**: Five pairwise trade-offs on 5-point scales (generates relative weights)
3. **Scenes 7-18**: Twelve hard veto constraints (yes/no for each)
4. **Scene 19**: Override mode (rights-first, consequences-first, balanced)
5. **Epilogue**: Free-form narrative context

**Why Greek Mythology Works**:

1. **Universal Recognition**: Stories transcend cultural boundaries—Phaethon's chariot resonates whether you're in California or Singapore
2. **Concrete Stakes**: Abstract "privacy vs safety" becomes visceral when framed as Artemis in the grove
3. **Precedent for Wisdom**: Ancient stories encoded hard-won ethical insights; using them signals seriousness
4. **Memorable**: Stakeholders remember "Phaethon's Chariot" better than "Question 7 about catastrophic harm"
5. **Emotional Resonance**: Stories engage both reason and feeling, appropriate for ethics

**Output**: Complete DEMEProfileV03 configuration representing stakeholder's values:

```json
{
  "profile_name": "test-5",
  "narrative_context": "Guided by Phaethon's cautionary tale...",
  "deme_dimension_weights": {
    "safety": 0.190,
    "rule_following_legality": 0.238,  // Chose this in Scene 1
    "fairness_equity": 0.190,
    ...
  },
  "override_mode": "rights_first",  // From Scene 19
  "hard_vetoes": [
    "never_catastrophic_safety_harm",     // Phaethon's Chariot
    "never_intentional_serious_harm",     // Iphigenia at Aulis
    "never_discriminate_protected_groups", // The Scapegoat
    "never_systematic_privacy_violation",  // Artemis in the Grove
    "never_persistent_misinfo_disinfo",    // The Chorus of Rumors
    "never_fabricate_critical_evidence",   // Phaedra's Letter
    ...
  ]
}
```

**Multiple Stakeholders**: Different groups run the dialogue, producing multiple profiles:
- Hospital ethics board → profile emphasizing patient safety, privacy
- Clinical staff → profile emphasizing efficiency, rule-following
- Patient advocates → profile emphasizing autonomy, vulnerable populations

Governance aggregates these profiles with stakeholder weights, enabling **democratic AI governance** where diverse voices shape system behavior.

**Technical Implementation**: The dialogue is YAML-configured (`ethical_dialogue_questions.yaml`), making it easy to:
- Customize scenarios for specific domains
- Translate to other languages
- Add new scenes as ethical challenges emerge
- A/B test different framings

**Addresses ErisML Challenge**: Makes value specification accessible through narrative rather than formal logic. Non-technical stakeholders meaningfully participate in configuring AI systems.

---

## III. MCP Integration: AAIF Ecosystem Compatibility

### A. DEME as MCP Server

`erisml.ethics.interop.mcp_deme_server` exposes three MCP tools:

#### Tool 1: `deme.list_profiles`

**Discover available ethics profiles for operational context**

```python
profiles = await mcp_client.call_tool("deme.list_profiles")
# Returns:
[
  {
    "profile_id": "hospital_service_robot_v1",
    "name": "Hospital Ethics Board Configuration",
    "stakeholder_label": "hospital_ethics_board",
    "domain": ["domestic", "clinical"],
    "override_mode": "rights_first",
    "tags": ["healthcare", "safety_critical"]
  },
  {
    "profile_id": "campus_shuttle_v2",
    "stakeholder_label": "university_safety_committee",
    "domain": ["urban_logistics"],
    "override_mode": "balanced"
  }
]
```

**Use Case**: Agent starting operation queries available profiles matching its domain.

#### Tool 2: `deme.evaluate_options`

**Get ethical assessment of candidate actions**

```python
judgements = await mcp_client.call_tool(
    "deme.evaluate_options",
    profile_id="hospital_service_robot_v1",
    options=[
        {
            "option_id": "route_through_ICU",
            "ethical_facts": {
                "option_id": "route_through_ICU",
                "consequences": {
                    "expected_benefit": 0.8,  # Faster delivery
                    "expected_harm": 0.3,     # Some disturbance
                    "urgency": "high"
                },
                "privacy": {
                    "data_collection_scope": "high",  # Cameras near patient rooms
                    "anonymization_strength": "medium"
                }
            }
        },
        {
            "option_id": "route_around_ICU",
            "ethical_facts": {
                "option_id": "route_around_ICU",
                "consequences": {
                    "expected_benefit": 0.6,  # Slower
                    "expected_harm": 0.1
                },
                "privacy": {
                    "data_collection_scope": "low",
                    "anonymization_strength": "high"
                }
            }
        }
    ]
)
```

**Returns structured judgements**:

```python
{
  "judgements": [
    {
      "option_id": "route_through_ICU",
      "em_name": "privacy_em",
      "verdict": "avoid",
      "normative_score": 0.3,
      "reasons": [
        "High data collection near patient rooms",
        "Medium anonymization insufficient for sensitive area"
      ]
    },
    {
      "option_id": "route_through_ICU",
      "em_name": "safety_em",
      "verdict": "prefer",
      "normative_score": 0.7,
      "reasons": ["Urgency justifies some risk"]
    },
    # ... more EM judgements
  ]
}
```

#### Tool 3: `deme.govern_decision`

**Apply democratic governance to select ethically-acceptable option**

```python
decision = await mcp_client.call_tool(
    "deme.govern_decision",
    profile_id="hospital_service_robot_v1",
    option_ids=["route_through_ICU", "route_around_ICU"],
    judgements=judgements["judgements"]
)
```

**Returns decision with full rationale**:

```python
{
  "selected_option": "route_around_ICU",
  "forbidden_options": [],
  "rationale": "Selected 'route_around_ICU' based on DEME governance with profile 'hospital_service_robot_v1' (override_mode=rights_first). Privacy concerns outweighed speed benefits given high data collection scope near patient areas.",
  "decision_outcome": {
    "option_id": "route_around_ICU",
    "verdict": "prefer",
    "normative_score": 0.72,
    "details": {
      "em_scores": {"safety_em": 0.5, "privacy_em": 0.9, "fairness_em": 0.75},
      "veto_triggered": false,
      "lexical_layer": "welfare"
    }
  }
}
```

### B. Integration with AAIF Ecosystem

#### With MCP (Core Integration)

DEME is a **MCP server** providing ethical reasoning tools. Any MCP-compatible client can use DEME:

- **Claude Desktop**: Users enable DEME MCP server for ethical oversight
- **Cursor / Cline / Windsurf**: Coding agents consult DEME before risky refactors
- **Custom Agents**: Any agent using MCP adds ethical guardrails

#### With goose (Agent Framework)

```python
from goose.toolkit import Toolkit

class EthicalPlanningToolkit(Toolkit):
    def __init__(self):
        self.mcp_client = MCPClient("deme")
    
    async def plan_with_ethics(self, options: List[Dict]) -> str:
        # Discover profiles
        profiles = await self.mcp_client.call_tool("deme.list_profiles")
        profile = self._select_profile_for_context(profiles)
        
        # Evaluate options ethically
        judgements = await self.mcp_client.call_tool(
            "deme.evaluate_options",
            profile_id=profile["profile_id"],
            options=options
        )
        
        # Get governance decision
        decision = await self.mcp_client.call_tool(
            "deme.govern_decision",
            profile_id=profile["profile_id"],
            option_ids=[opt["option_id"] for opt in options],
            judgements=judgements["judgements"]
        )
        
        return decision["selected_option"]
```

#### With AGENTS.md (Project Guidance)

DEME-governed projects include AGENTS.md documenting ethical constraints:

```markdown
# Project: Hospital Robot Fleet Management

## Ethics Governance

This project uses DEME for ethical oversight of robot operations.

### Active DEME Profile

- **Profile**: `hospital_service_robot_v1`
- **Stakeholders**: Hospital ethics board, patient advocates, clinical staff
- **Override Mode**: `rights_first` (patient rights take precedence)

### Hard Constraints

The following actions are **absolutely forbidden**:
- `never_intentional_serious_harm`: Never choose actions expected to cause serious physical harm
- `never_discriminate_protected_groups`: Never discriminate based on protected attributes
- `never_mass_surveillance_private_spaces`: No continuous recording in patient rooms

### MCP Integration

To evaluate actions ethically:

1. Call `deme.list_profiles` to discover available profiles
2. Call `deme.evaluate_options` with candidate actions and EthicalFacts
3. Call `deme.govern_decision` to get ethically-justified selection

### Escalation Procedures

If DEME returns `selected_option: null` (no permissible option):
1. Log incident to ethics audit system
2. Alert on-call human operator
3. Default to safest fallback (stop, retreat, request assistance)
```

---

## IV. NIST AI RMF Alignment

DEME provides **native compliance** with NIST AI Risk Management Framework 1.0:

| NIST Function | DEME Implementation |
|--------------|---------------------|
| **GOVERN** | DEMEProfileV03 configurations are versioned, approved governance artifacts. Stakeholder weights and veto authority explicitly documented. Hard vetoes enforce organizational values. Ethical dialogue CLI enables stakeholder participation. |
| **MAP** | EthicalFacts schema documents all ethically-relevant context: consequences, rights violations, fairness impacts, privacy posture, environmental costs, epistemic uncertainty. Domain-specific assessment services translate raw data into structured EthicalFacts. |
| **MEASURE** | Ethics Modules evaluate options against specific criteria (safety, fairness, privacy), returning quantitative scores and qualitative verdicts. Governance aggregation produces normative scores across all EMs. Comprehensive logging enables continuous monitoring. |
| **MANAGE** | DecisionOutcome selects ethically-acceptable options based on governance rules. Forbidden options identified with reasons. Full audit trail enables post-deployment analysis, governance tuning, and incident response. |

## VII. NIST AI RMF Alignment (Detailed)

DEME provides **native compliance** with NIST AI Risk Management Framework 1.0 and addresses NIST AI 600-1 (Generative AI Profile) concerns:

### NIST AI RMF 1.0 Core Functions

| NIST Function | DEME Implementation | Concrete Evidence |
|--------------|---------------------|-------------------|
| **GOVERN** | DEMEProfileV03 configurations are versioned, approved governance artifacts. Stakeholder weights and veto authority explicitly documented. Hard vetoes enforce organizational values. Ethical dialogue CLI enables stakeholder participation. | Profile JSON files with change tracking, approval chains, stakeholder attribution. Geneva EM provides universal baseline. |
| **MAP** | EthicalFacts schema documents all ethically-relevant context across 9 dimensions: consequences, rights violations, fairness impacts, privacy posture, autonomy constraints, environmental costs, virtue/care considerations, procedural legitimacy, epistemic uncertainty. Domain Assessment Services translate raw data into structured EthicalFacts. | EthicalFacts.schema.json, domain-specific assessment service implementations, example mappings for healthcare, autonomous vehicles, software development. |
| **MEASURE** | Ethics Modules evaluate options against specific criteria (safety, fairness, privacy, autonomy), returning quantitative normative scores [0.0, 1.0] and qualitative verdicts {strongly_prefer, prefer, neutral, avoid, forbid}. Governance aggregation produces weighted scores across all EMs. Comprehensive decision logging enables continuous monitoring. Geneva EM provides graduated baseline scoring. | EM test suites with property-based testing, score distributions over validation datasets, drift detection on deployed systems, Geneva EM compliance tracking over time. |
| **MANAGE** | DecisionOutcome selects ethically-acceptable options based on governance rules. Forbidden options identified with reasons. Full audit trail (EthicalFacts → EM judgements → governance decision → action) enables post-deployment analysis, governance tuning, incident response. MCP integration enables runtime oversight. | Decision logs in structured JSON, analytics dashboards showing veto frequencies, governance score distributions, incident response procedures with DEME audit trail reconstruction. |

### NIST AI 600-1 (Generative AI Profile) Risk Mitigation

While DEME is designed for agentic systems (decision-making) rather than generative content (text/image production), several GAI risks are directly addressed:

| GAI Risk Category | DEME Mitigation | Implementation |
|-------------------|-----------------|----------------|
| **Confabulation/Hallucination** | EthicalFacts `epistemic_status` block tracks confidence_level, evidence_quality, uncertainty_level, novel_situation_flag. Geneva EM applies epistemic caution multiplier, penalizing low-confidence high-stakes decisions. | Low confidence + catastrophic consequences → Geneva score penalty; uncertainty_level > 0.5 → trigger human escalation |
| **Data Privacy** | Privacy EM constrains data collection; EthicalFacts `privacy_and_data_governance` block documents collection scope, retention, sharing, reidentification risk. Geneva EM penalizes privacy violations. | Geneva EM: -0.30 × privacy_invasion_level, -0.10 data minimization violations, -0.15 secondary use without consent, -0.20 × reidentification_risk |
| **Harmful Bias** | Fairness EM monitors discrimination; EthicalFacts `justice_and_fairness` block flags protected attribute usage. Geneva EM hard veto on discrimination. | Geneva EM: Hard veto (score=0.0) if `discriminates_on_protected_attr=True`; -0.25 if `exploits_vulnerable_population=True` |
| **Human-AI Configuration** | Autonomy EM respects consent; EthicalFacts `autonomy_and_agency` block tracks meaningful choice, coercion, withdrawal rights. | Geneva EM: -0.20 if no meaningful choice, -0.20 if coercion present, -0.10 if cannot withdraw |
| **Information Security** | Structured governance provides defense-in-depth; MCP integration enables external security monitoring. | Multiple independent EMs must agree; Geneva EM provides baseline; audit logs enable anomaly detection |
| **Information Integrity** | Epistemic status tracking; procedural legitimacy requirements in Geneva EM. | Geneva EM: -0.15 if approved procedure not followed, -0.10 if stakeholders not consulted |

### Compliance Documentation Generation

DEME automatically generates compliance artifacts:

```python
# Example: Generate NIST AI RMF compliance report
compliance_report = deme_system.generate_nist_report(
    time_period="2025-Q1",
    profile_id="hospital_service_robot_v1"
)

# Output:
{
  "system_id": "hospital_robot_fleet",
  "assessment_period": "2025-Q1",
  "govern": {
    "governance_artifact": "DEMEProfileV03-hospital_v1.json",
    "last_updated": "2025-01-15",
    "stakeholder_representation": ["ethics_board", "patient_advocates", "clinical_staff"],
    "change_log": "https://github.com/hospital/deme-configs/commits/main",
    "status": "COMPLIANT"
  },
  "map": {
    "risk_categories_documented": 9,  # All EthicalFacts dimensions
    "context_assessment_services": ["clinical_triage", "patient_safety", "privacy_hipaa"],
    "stakeholder_identification": "Documented in EthicalFacts.affected_individuals",
    "status": "COMPLIANT"
  },
  "measure": {
    "quantitative_metrics": ["normative_scores", "veto_frequencies", "geneva_compliance"],
    "qualitative_assessments": ["em_reasons", "governance_rationales"],
    "monitoring_frequency": "real-time (per decision)",
    "validation_results": {
      "geneva_violations": 3,  # 3 out of 10,000 decisions
      "veto_rate": 0.08,       # 8% of options vetoed
      "average_geneva_score": 0.73
    },
    "status": "COMPLIANT"
  },
  "manage": {
    "decisions_logged": 10000,
    "incidents_reported": 2,
    "governance_updates": 1,  # One EM weight adjustment based on incident analysis
    "escalations_to_human": 15,
    "response_procedures": "Documented in AGENTS.md and incident_response.md",
    "status": "COMPLIANT"
  },
  "overall_assessment": "COMPLIANT",
  "recommendations": [
    "Geneva EM flagged 3 violations - review threshold settings",
    "Consider additional EM for medication safety",
    "Veto rate slightly high - may indicate overly conservative governance"
  ]
}
```

---

## VIII. Use Cases and Domain Applications (Extended)

### Use Case 1: Healthcare AI Triage System

**Scenario**: Emergency room AI must prioritize patients in waiting room.

**Challenge**: Balance medical urgency (save lives) against fairness (first-come first-served expectations) against resource constraints (limited staff).

**Options**:
- **Option A**: Strict FIFO (first-in, first-out)
- **Option B**: Prioritize patient with chest pain who arrived later

**EthicalFacts for Option B**:

```python
{
  "option_id": "prioritize_chest_pain_patient",
  "consequences": {
    "expected_benefit": 0.9,  # Potentially save life
    "expected_harm": 0.2,     # Other patients wait longer
    "urgency": "critical",
    "severity_if_wrong": "catastrophic"
  },
  "rights": {
    "rights_violations": ["waiting_time_expectations"],
    "consent_status": "implied"  # Patients expect triage
  },
  "fairness": {
    "discrimination_flags": [],  # Not using protected attributes
    "prioritization_rationale": "medical_urgency"
  },
  "epistemic_status": {
    "confidence_level": 0.85,  # Clinical indicators clear
    "known_unknowns": ["patient_may_be_exaggerating_symptoms"]
  }
}
```

**DEME Evaluation**:

| EM | Verdict | Score | Reasoning |
|----|---------|-------|-----------|
| Triage EM | strongly_prefer | 0.95 | Critical urgency, high benefit |
| Fairness EM | neutral | 0.6 | Medical need is legitimate criterion |
| Autonomy EM | prefer | 0.7 | Patients expect triage, not strict FIFO |

**Governance (Clinical Profile, override_mode=rights_first)**:
- Lexical Layer 1 (Rights): No hard rights violations
- Lexical Layer 2 (Welfare): Triage EM strongly prefers Option B
- **Decision**: Select Option B

**Rationale**: "Prioritized chest pain patient due to critical urgency (potentially life-saving). Medical urgency is ethically justified criterion for prioritization, distinct from discrimination on protected attributes. All EMs permit or prefer this option."

**Audit Log**: Full EthicalFacts, all EM judgements, governance decision logged to compliance system.

### Use Case 2: Autonomous Delivery Robot

**Scenario**: Robot must choose delivery route through residential area.

**Options**:
- **Route A**: Through playground (faster, higher pedestrian risk)
- **Route B**: Around playground (slower, safer)

**EthicalFacts for Route A**:

```python
{
  "option_id": "route_through_playground",
  "consequences": {
    "expected_benefit": 0.8,  # Faster delivery
    "expected_harm": 0.4,     # Child collision risk
    "urgency": "medium",
    "affected_individuals": 20  # Children in playground
  },
  "fairness": {
    "prioritization_of_disadvantaged": "children",  # Vulnerable population
    "power_imbalance_indicators": ["adult_robot_vs_children"]
  },
  "epistemic_status": {
    "confidence_level": 0.6,  # Children's movements unpredictable
    "known_unknowns": ["child_behavior_highly_variable"]
  }
}
```

**DEME Evaluation**:

| EM | Verdict | Score | Reasoning |
|----|---------|-------|-----------|
| Safety EM | avoid | 0.2 | Unacceptable child collision risk |
| Fairness EM | avoid | 0.3 | Vulnerable population (children) |
| Efficiency EM | prefer | 0.8 | Faster route |
| Vulnerable Populations EM | forbid | 0.0 | High risk to children |

**Governance (Community Profile, override_mode=rights_first, priority_for_vulnerable=0.15)**:
- Lexical Layer 1 (Rights): Vulnerable Populations EM **forbids** Route A
- **Decision**: Route A **forbidden**, select Route B

**Rationale**: "Route A forbidden by Vulnerable Populations EM due to unacceptable risk to children (vulnerable group). Despite efficiency benefits, safety and vulnerability protections take precedence per rights-first governance."

### Use Case 3: AI Coding Agent Refactoring

**Scenario**: AI agent considers major refactor of authentication system.

**Options**:
- **Option A**: Major refactor (cleaner code, breaks backward compatibility)
- **Option B**: Incremental improvement (maintains compatibility)

**EthicalFacts for Option A**:

```python
{
  "option_id": "major_auth_refactor",
  "consequences": {
    "expected_benefit": 0.7,  # Better code quality, security improvements
    "expected_harm": 0.5,     # Breaking changes for API users
    "urgency": "low",
    "affected_individuals": 1000  # External API consumers
  },
  "rights_and_duties": {
    "violates_rights": False,
    "explicit_rule_violations": ["semver_major_version_required"]
  },
  "autonomy_and_agency": {
    "has_meaningful_choice": False,  # API users forced to adapt
    "can_withdraw_without_penalty": False,  # Must upgrade or lose functionality
    "coercion_or_undue_influence": False,
    "manipulative_design_present": False
  },
  "procedural_legitimacy": {
    "followed_approved_procedure": False,  # No RFC process
    "stakeholders_consulted": False,       # No deprecation notice
    "decision_explainable_to_public": True,
    "contestation_available": False        # No appeal mechanism
  },
  "epistemic_status": {
    "uncertainty_level": 0.3,  # Impact relatively well-understood
    "evidence_quality": "good",
    "novel_situation_flag": False
  }
}
```

**DEME Evaluation**:

**Geneva EM**:
```python
score = 1.0
# No hard vetoes triggered (doesn't violate fundamental rights)

# Autonomy penalties:
# - has_meaningful_choice = False
score -= 0.20  # → 0.80
# - can_withdraw_without_penalty = False
score -= 0.10  # → 0.70

# Procedural legitimacy penalties:
# - followed_approved_procedure = False
score -= 0.15  # → 0.55
# - stakeholders_consulted = False
score -= 0.10  # → 0.45

# Epistemic adjustment (minimal):
epistemic_penalty = 0.20 * 0.3 = 0.06
multiplier = 0.94
score *= 0.94  # → 0.42

# Final: 0.42 → "neutral"
```

**Code Quality EM** (software engineering best practices):
```python
verdict = "strongly_prefer"
score = 0.90
reasons = [
    "Improves security posture",
    "Reduces technical debt",
    "Better maintainability"
]
```

**API Stability EM** (backward compatibility):
```python
verdict = "forbid"
score = 0.0
reasons = [
    "Breaking changes without proper deprecation process",
    "Violates semantic versioning policy",
    "No stakeholder consultation"
]
```

**Governance (Software Project Profile, override_mode=balanced)**:

```python
em_weights = {
    "geneva_baseline": 0.15,
    "code_quality_em": 0.30,
    "api_stability_em": 0.40,  # Highest weight
    "security_em": 0.15
}

# Weighted scores:
# geneva: 0.42 * 0.15 = 0.063
# code_quality: 0.90 * 0.30 = 0.270
# api_stability: 0.00 * 0.40 = 0.000  # ← Veto EM with 40% weight
# security: 0.75 * 0.15 = 0.113

# Total: 0.446
# But API Stability EM has veto authority with "forbid" verdict
```

**DecisionOutcome**:
```python
{
  "selected_option": None,  # No option selected
  "forbidden_options": ["major_auth_refactor"],
  "rationale": "Option A forbidden by API Stability EM due to procedural violations. Breaking changes require RFC process, deprecation notice, and stakeholder consultation per project governance. Geneva EM also flagged autonomy and procedural concerns (score=0.42, 'neutral'). Agent must either: (1) follow proper deprecation process for Option A, or (2) pursue Option B (incremental improvement).",
  "governance_details": {
    "veto_triggered": True,
    "vetoed_by": "api_stability_em",
    "geneva_score": 0.42,
    "suggested_alternative": "incremental_improvement_with_deprecation_path"
  }
}
```

**Integration with AGENTS.md**:

Project's AGENTS.md specifies:
```markdown
## Breaking Changes Policy

This project uses DEME governance with strong emphasis on API stability.

### DEME Configuration
- **Active EMs**: geneva_baseline, code_quality_em, api_stability_em, security_em
- **Veto Authority**: api_stability_em (weight: 0.40)
- **Override Mode**: balanced

### Breaking Changes Require
1. RFC proposal with impact analysis
2. Deprecation notice (minimum 6 months)
3. Stakeholder consultation (issue for feedback)
4. Security exception approval (if urgent)

### MCP Integration
Before proposing breaking changes:
```bash
# Check with DEME
deme.evaluate_options \
  --profile software_project_v1 \
  --option refactor.json
```

If DEME forbids: Follow procedure or choose non-breaking alternative.
```

**Key Insights**:
1. **Geneva EM** flagged autonomy and procedural concerns (score 0.42) but didn't hard-veto
2. **API Stability EM** with veto authority enforced project norms
3. **AGENTS.md integration** helps AI agent understand why refactor was rejected
4. **Clear path forward**: Follow proper process or choose alternative

This demonstrates how DEME governance can enforce **software engineering best practices** and **community norms**, not just physical safety.

---

## VI. Technical Differentiation