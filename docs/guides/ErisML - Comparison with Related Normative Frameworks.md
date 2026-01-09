# ErisML: Comparison with Related Normative Frameworks

## Executive Summary

This document provides a detailed comparison between ErisML and two prominent approaches to normative reasoning in AI systems: Governatori et al.'s Defeasible Deontic Logic (DDL) frameworks and Normative Supervisors for Reinforcement Learning agents. These comparisons highlight ErisML's unique contributions, identify areas of overlap, and clarify when each approach is most suitable.

---

## 1. Comparison with Defeasible Deontic Logic (DDL) Frameworks

### 1.1 Overview of Defeasible Deontic Logic

Defeasible Deontic Logic, developed primarily by Guido Governatori and collaborators, extends classical deontic logic (concerned with obligations, permissions, and prohibitions) with defeasible reasoning—the ability to weaken or overturn inferences based on new information. DDL has been extensively applied to legal reasoning, business process compliance, e-contracts, and normative multi-agent systems.

**Key characteristics:**
- **Non-monotonic reasoning**: Conclusions can be revised as new information emerges
- **Rule-based architecture**: Facts, constitutive rules, prescriptive rules, and superiority relations
- **Proof-theoretic foundation**: Constructive proof theory enabling transparent reasoning traces
- **Computational efficiency**: Linear-time complexity for standard inference
- **Tool support**: SPINdle theorem prover, Answer Set Programming implementations, Houdini framework

### 1.2 Architectural Comparison

| Dimension | Defeasible Deontic Logic | ErisML |
|-----------|-------------------------|---------|
| **Primary Focus** | Legal/normative reasoning with defeasible rules | Unified modeling of environment + agents + ethics + dynamics |
| **Scope** | Normative rules and obligations | Environment state, agent capabilities, norms, multi-agent interaction, ethics modules |
| **Reasoning Style** | Defeasible rule-based inference | Norm-as-constraint + democratic ethical governance |
| **Temporal Handling** | Temporal DDL extensions for deadlines, violations over time | Explicit environment dynamics, temporal evolution in state space |
| **Agent Modeling** | Implicit (norms apply to agent actions) | Explicit (agents with beliefs, capabilities, intents) |
| **Ethics Architecture** | Norms encoded directly in logic | Separate DEME layer with pluggable ethics modules |
| **Conflict Resolution** | Superiority relations between rules | Democratic governance with voting mechanisms |
| **Implementation** | Theorem prover (SPINdle), ASP meta-programs | Runtime engine with norm gate + metrics |

### 1.3 Logical Foundations

#### DDL Approach
DDL represents normative systems through:
- **Facts**: `f` (indisputable evidence)
- **Rules**: `r: a₁, ..., aₙ ⇒X c` where `X ∈ {C, P, O}` (constitutive, prescriptive, obligation)
- **Superiority relation**: `r₁ > r₂` (rule r₁ overrides r₂ in conflicts)
- **Deontic operators**: `O(p)` (obligation), `P(p)` (permission), `F(p)` (prohibition)

Inference proceeds via proof tags: `+∂O(p)` means "p is defeasibly obligatory."

**Example DDL theory:**
```
% Facts
patient_critical.
resources_limited.

% Prescriptive rules
r1: patient_critical ⇒O treat_immediately
r2: resources_limited ⇒O prioritize_based_on_severity
r3: young_patient ⇒P treat_first

% Superiority
r1 > r2  % Critical cases override resource constraints
```

#### ErisML Approach
ErisML provides:
- **Environment specification**: State variables, dynamics functions, observations
- **Agent specification**: Capabilities, beliefs, intents, utility functions
- **Normative layer**: Permissions, obligations, prohibitions as first-class constraints
- **Ethics layer (DEME)**: EthicalFacts abstraction + pluggable EthicsModules + governance
- **Execution semantics**: Runtime norm gate, NVR/ADV metrics

**Example ErisML specification:**
```python
# Environment
Environment(
    state_vars={'patient_status': ['critical', 'stable', 'deceased'],
                'resources': int},
    dynamics=TransitionFunction(...),
    observations=ObservationSpace(...)
)

# Norms
Prohibition(
    condition=lambda s: s['resources'] == 0,
    action='treat',
    priority=HIGH
)

# Ethics Module (DEME)
@dataclass
class UtilitarianEM(EthicsModule):
    def judge(self, facts: EthicalFacts) -> EthicalJudgement:
        score = facts.consequences.expected_benefit - facts.consequences.expected_harm
        return EthicalJudgement(verdict=..., normative_score=score, ...)

# Governance
governance = GovernanceConfig(
    modules=[UtilitarianEM(), RightsBasedEM(), FairnessEM()],
    selection_mechanism='weighted',
    weights={'utilitarian': 0.4, 'rights': 0.4, 'fairness': 0.2}
)
```

### 1.4 Handling Contrary-to-Duty (CTD) Obligations

**Challenge**: What should an agent do when a violation has already occurred?

**DDL Solution:**
DDL elegantly handles CTD scenarios through its constructive proof theory. When `O(p) ∧ ¬p` (obligation violated), DDL can derive compensatory obligations `O(q)` that depend on the violation state.

Example: "You must not speed (O¬speed). If you do speed (¬¬speed), you must pay a fine (O(pay_fine))."

**ErisML Solution:**
ErisML handles CTD through two mechanisms:

1. **Runtime norm violations tracking**: The norm gate records violations and updates metrics (NVR, ADV), maintaining violation history
2. **DEME compensatory reasoning**: Ethics modules can examine violation history in `EthicalFacts` and recommend compensatory actions

```python
facts = EthicalFacts(
    consequences=Consequences(expected_harm=0.3),
    violation_context={'prior_violations': ['speeding']},
    ...
)

# Ethics module recommends compensation
if 'speeding' in facts.violation_context['prior_violations']:
    judgement.reasons.append("Compensatory fine required due to prior violation")
    judgement.verdict = "strongly_prefer" if action == "pay_fine" else "forbid"
```

**Comparison:**
- DDL's approach is more formal and mathematically principled for legal reasoning
- ErisML's approach is more flexible for complex multi-dimensional ethical trade-offs
- DDL better suited for discrete, well-defined legal rules
- ErisML better suited for fuzzy ethical dilemmas requiring stakeholder input

### 1.5 Computational Complexity

**DDL:**
- Standard DDL inference: O(n) where n = number of rules
- Temporal DDL: O(n × t) where t = temporal depth
- Meta-rule extensions: polynomial but higher constants
- Practical performance: SPINdle processes thousands of rules/second

**ErisML:**
- Norm checking: O(m × k) where m = number of norms, k = state complexity
- DEME ethics evaluation: O(e × d) where e = number of ethics modules, d = decision complexity
- Full reasoning cycle: O((m × k) + (e × d))
- Multi-agent coordination: adds factor of O(a²) for a agents

**Trade-offs:**
- DDL is more efficient for pure normative reasoning (legal compliance, contracts)
- ErisML adds overhead for environment simulation and multi-stakeholder ethics
- ErisML's advantage: avoids retraining when norms change (unlike RL-embedded approaches)

### 1.6 Expressiveness Comparison

| Feature | DDL | ErisML |
|---------|-----|--------|
| **Deontic modalities** | O, P, F + CTD | O, P, F + priorities |
| **Defeasibility** | Native (core feature) | Via norm priorities + governance voting |
| **Temporal logic** | Extensions available (TDDL) | Built into dynamics + metrics (NVR, ADV) |
| **Agent beliefs** | Extensions (BIO logic) | Native (agent beliefs as state) |
| **Multi-agent interaction** | Via extended logics | Native (strategic interaction) |
| **Ethical reasoning** | Encoded as norms | Separate DEME layer |
| **Uncertainty** | Not native (extensions exist) | Via stochastic dynamics + expected values |
| **Environment dynamics** | Not modeled | Core feature (state transitions) |

### 1.7 Use Case Suitability

**When to use DDL:**
- Legal reasoning and regulatory compliance
- Business process verification
- E-contract monitoring and enforcement
- Well-defined normative systems with clear superiority relations
- Applications requiring explainable compliance proofs
- Single-agent systems with external norms

**When to use ErisML:**
- Pervasive computing environments (smart homes, hospitals, factories)
- Foundation model-enabled agents requiring governance
- Multi-stakeholder ethical decision-making
- Systems where environment dynamics matter (resource depletion, temporal evolution)
- Applications requiring democratic ethical governance
- Scenarios with fuzzy ethical trade-offs beyond binary compliance

**Hybrid Opportunity:**
ErisML could integrate DDL as a norm checking backend, using SPINdle for efficient rule-based reasoning while adding DEME for ethical governance and environment modeling.

---

## 2. Comparison with Normative Supervisors for RL Agents

### 2.1 Overview of Normative Supervisors

The Normative Supervisor approach, developed by Neufeld, Bartocci, Ciabattoni, and Governatori, integrates defeasible deontic logic theorem provers into the control loop of reinforcement learning agents. This modular architecture enforces normative compliance without retraining the policy.

**Key characteristics:**
- **Architecture**: Supervisor sits between perception and policy, filtering actions
- **Reasoning engine**: SPINdle (DDL theorem prover)
- **Techniques**: 
  - Online Compliance Checking (OCC): Block non-compliant actions in real-time
  - Norm-Guided RL (NGRL): Train with normative constraints as additional objectives
  - Normative Filters: Pre-computed compliance masks
- **Applications**: Pac-Man with ethical constraints, autonomous vehicles, robot assistants

### 2.2 Architectural Comparison

#### Normative Supervisor Architecture
```
Environment → Perception → Normative Supervisor → Policy → Action
                              ↓
                         DDL Reasoning
                         (SPINdle)
                              ↓
                         Norm Base
```

The supervisor:
1. Receives current state and possible actions from perception
2. Encodes state and actions as DDL facts
3. Queries SPINdle for compliance judgments
4. Filters non-compliant actions
5. Passes compliant actions to policy
6. Logs violations for analysis

#### ErisML Architecture
```
Foundation Model Agent
    ↓
ErisML Specification → Runtime Engine
    ↓                      ↓
Norm Gate ← → DEME ← → Environment Simulator
    ↓                      ↓
Action Selection       Metrics (NVR, ADV)
```

ErisML:
1. Agent queries environment through ErisML API
2. Proposes action based on beliefs and utilities
3. Norm gate checks against norms (first-class constraints)
4. If ethical decision required, DEME aggregates ethics modules
5. Action executed if compliant
6. Metrics updated (NVR, ADV)
7. State transitions according to dynamics

### 2.3 Key Differences

| Dimension | Normative Supervisor | ErisML |
|-----------|---------------------|---------|
| **Integration Point** | Control loop (between perception and policy) | Entire agent-environment specification |
| **Primary Application** | Retrofitting ethics onto pre-trained RL agents | Designing governed agents from scratch |
| **Policy Impact** | External constraint (supervisor overrides policy) | Native constraint (norms shape policy) |
| **Learning Paradigm** | RL with or without norm-guided training | Any learning/planning approach |
| **Ethical Architecture** | DDL norm base (single normative system) | DEME (multiple ethics modules + governance) |
| **Environment Model** | Implicit (MDP state) | Explicit (dynamics, observations, resources) |
| **Performance Trade-off** | Can degrade RL performance (normative deadlock) | Designed for norm-aware planning |
| **Transparency** | DDL proof traces | Norm gate logs + DEME voting records |

### 2.4 Handling Normative Deadlock

**Challenge**: What happens when all available actions violate norms?

**Normative Supervisor Solution:**
Early work with OCC suffered from normative deadlock—agents could get stuck in states where no compliant action exists. Solutions include:
- **Violation Counting**: Allow violations but minimize frequency
- **Penalty-based RL**: Weight violations differently based on severity
- **NGRL**: Train with normative constraints so agent learns to avoid deadlock states
- **LTLf specifications**: Formalize norms as temporal logic to enable forward planning

Example: Self-driving car on one-way street approaching prohibited private road must choose between illegally reversing or trespassing.

**ErisML Solution:**
ErisML addresses deadlock through:
1. **Norm priorities**: Higher-priority norms take precedence in conflicts
2. **Governance arbitration**: DEME can vote on "least bad" option when all violate
3. **Explicit utilities**: Agent can reason about utility loss vs. norm violation
4. **Environment modeling**: Planner can anticipate deadlock states and avoid them

```python
# ErisML handling of ethical dilemma
options = [
    ('reverse', violates=['one_way_rule']),
    ('trespass', violates=['private_property']),
]

# DEME evaluates both options
for action, violations in options:
    facts = create_ethical_facts(action, violations)
    judgements = [em.judge(facts) for em in ethics_modules]
    
# Governance selects "least bad" based on aggregated scores
outcome = governance.select_option(judgements)
```

**Comparison:**
- Normative Supervisor relies on RL to learn to avoid deadlock (forward-looking)
- ErisML uses explicit utilities and governance to choose minimal violation (reactive)
- Both require careful norm design to minimize deadlock scenarios
- ErisML's DEME provides more principled handling of genuine dilemmas

### 2.5 Transparency and Explainability

**Normative Supervisor:**
- DDL proof traces show which rules fired
- Violation logs identify where compliance failed
- Constructive proof theory enables "why" explanations
- Limited insight into policy's internal reasoning (black box)

**ErisML:**
- Norm gate logs show which norms were checked
- DEME voting records show stakeholder perspectives
- Each ethics module provides reasons for its judgment
- Environment dynamics make counterfactual reasoning possible
- Full audit trail from perception → norms → ethics → action

**Example Explanations:**

Normative Supervisor:
```
Action 'eat_ghost' blocked.
Reason: Violates obligation O(vegan_diet) derived from rules:
  r1: vegan ⇒O vegan_diet
  r2: vegan_diet ⇒F eat_animal_products
```

ErisML:
```
Action 'eat_ghost' rejected by DEME.
Norm check: PASS (no explicit prohibition)
Ethics evaluation:
  - UtilitarianEM: AVOID (score=0.3) - High harm to ghost, low benefit
  - RightsEM: FORBID (score=0.1) - Violates ghost's right to life
  - FairnessEM: NEUTRAL (score=0.5) - No fairness implications
Governance (majority): FORBID
Final decision: Action blocked
```

### 2.6 Scalability to Foundation Models

**Normative Supervisor:**
- Designed for RL agents (discrete state/action spaces)
- Limited exploration of LLM integration
- Would require mapping LLM outputs to DDL predicates
- Supervisor operates at action level (post-generation filtering)

**ErisML:**
- Explicitly designed for "foundation-model-enabled agents"
- Can specify norms over generated text, multi-step plans, tool use
- DEME can evaluate LLM reasoning chains, not just final actions
- Governance applies to complex, multi-dimensional LLM outputs

**Potential Integration:**
```python
# LLM generates plan
plan = llm.generate("How should we allocate ICU beds during a crisis?")

# ErisML evaluates plan
for step in plan.steps:
    norm_compliant = norm_gate.check(step)
    if requires_ethical_judgment(step):
        facts = extract_ethical_facts(step, context)
        judgements = [em.judge(facts) for em in ethics_modules]
        if not governance.approves(judgements):
            plan.revise(step, governance.recommendations)

# Return governed plan
return plan
```

### 2.7 Performance Implications

**Normative Supervisor:**
- OCC adds ~10-50ms per action (DDL inference)
- Can significantly reduce RL performance if not trained with norm awareness
- Neufeld et al. report score drops in Pac-Man when norms constrain optimal paths
- NGRL mitigates performance loss but requires retraining

**ErisML:**
- Norm gate: O(m × k) per action
- DEME: O(e × d) per ethical decision (not every action)
- Environment simulation overhead for planning
- Not yet benchmarked on large-scale scenarios

**Trade-off Analysis:**
- Normative Supervisor better for retrofitting existing RL agents
- ErisML better for designing norm-aware agents from scratch
- Both introduce computational overhead vs. unconstrained agents
- ErisML's modular ethics allows caching and optimization opportunities

### 2.8 Adaptability to Changing Norms

**Normative Supervisor:**
- Norm base can be updated without retraining RL policy
- DDL's non-monotonic nature handles rule additions/deletions
- Agent may perform poorly on new norms if not anticipated during training
- Requires careful norm design to avoid surprise deadlocks

**ErisML:**
- Norms are first-class constraints, easily added/removed
- DEME modules can be swapped without changing environment model
- Governance weights can be adjusted to reflect changing societal values
- Longitudinal metrics (NVR, ADV) track adaptation over time

**Example Adaptation:**

Normative Supervisor:
```python
# Add new norm to existing agent
norm_base.add_rule("r_new: pandemic ⇒O social_distance")
# Agent continues with same policy, supervisor filters actions
# May cause performance degradation if policy wasn't trained for this
```

ErisML:
```python
# Add new norm
env.norms.append(Obligation(
    condition=lambda s: s['pandemic_active'],
    action='maintain_distance',
    priority=HIGH
))

# Add new ethics module
ethics_modules.append(PublicHealthEM())

# Update governance weights
governance.weights['public_health'] = 0.3
governance.renormalize()

# Metrics track adaptation
print(f"NVR before norm: {nvr_before}")
print(f"NVR after norm: {nvr_after}")
print(f"ADV: {(nvr_after - nvr_before) / time_elapsed}")
```

### 2.9 Use Case Suitability

**When to use Normative Supervisor:**
- You have a pre-trained RL agent that needs ethical constraints
- The agent operates in a discrete state-action MDP
- You need real-time compliance checking with minimal policy changes
- The normative system is well-defined and relatively stable
- You want DDL's formal guarantees and proof traces
- Single-agent scenarios or loosely-coupled multi-agent systems

**When to use ErisML:**
- You're designing a new agent from scratch
- The environment has complex dynamics (resource depletion, multi-step processes)
- You need multi-stakeholder ethical governance (not just compliance)
- The agent uses foundation models (LLMs) for reasoning/planning
- You want to track longitudinal safety metrics (NVR, ADV)
- You need to model pervasive computing environments explicitly

**Complementary Use:**
ErisML could integrate a Normative Supervisor as its norm gate implementation, using SPINdle for efficient DDL reasoning while adding DEME for multi-stakeholder governance and environment modeling.

---

## 3. Unique Contributions of ErisML

### 3.1 Unified Modeling Language
Unlike DDL (norms only) or Normative Supervisor (RL architecture), ErisML provides a single specification for:
- Environment dynamics
- Agent architectures
- Normative constraints
- Ethical reasoning
- Multi-agent coordination

This holistic view enables reasoning about agent-environment coupling that other approaches don't capture.

### 3.2 Democratic Ethical Governance (DEME)
Neither DDL nor Normative Supervisor addresses the fundamental challenge of ethical pluralism. ErisML's DEME:
- Allows multiple ethical frameworks to coexist
- Provides democratic aggregation mechanisms
- Enables transparent stakeholder participation
- Supports evolving societal values through weight adjustments

### 3.3 Longitudinal Safety Metrics
ErisML introduces novel metrics for tracking agent alignment over time:
- **NVR (Norm Violation Rate)**: Frequency of violations
- **ADV (Alignment Drift Velocity)**: Rate of alignment change

These metrics enable:
- Early warning of misalignment
- Comparison across agent versions
- Regulatory reporting
- Continuous monitoring

### 3.4 Foundation Model Integration by Design
While Normative Supervisor focuses on RL, ErisML explicitly targets foundation model-enabled agents:
- Norms can constrain generated text, plans, tool use
- DEME can evaluate reasoning chains, not just actions
- Supports multi-step, hierarchical decision-making
- Enables governance over LLM-generated content

### 3.5 Pervasive Computing Focus
ErisML is designed for environments where:
- Physical resources matter (beds, energy, materials)
- Temporal dynamics are critical (resource depletion, cascading failures)
- Multiple agents interact strategically
- Environment state is partially observable
- Norms emerge from physical/social constraints

---

## 4. Integration Opportunities

### 4.1 ErisML + DDL
**Proposal**: Use SPINdle as ErisML's norm gate backend

Benefits:
- Leverage DDL's efficient rule-based inference
- Gain formal proof traces for compliance
- Benefit from DDL's mature handling of CTD obligations
- Maintain ErisML's DEME layer for ethical governance

Implementation sketch:
```python
class DDLNormGate(NormGate):
    def __init__(self, spindle_config):
        self.reasoner = SPINdleReasoner(spindle_config)
    
    def check(self, state, action) -> NormCheckResult:
        # Convert ErisML state to DDL facts
        ddl_facts = self._convert_state(state)
        ddl_action = self._convert_action(action)
        
        # Query SPINdle
        result = self.reasoner.query(
            facts=ddl_facts,
            action=ddl_action
        )
        
        return NormCheckResult(
            compliant=result.compliant,
            violated_norms=result.violated_rules,
            proof_trace=result.derivation
        )
```

### 4.2 ErisML + Normative Supervisor
**Proposal**: Use ErisML as specification layer for Normative Supervisor

Benefits:
- Specify environment dynamics explicitly
- Add DEME for ethical governance beyond compliance
- Leverage existing RL training infrastructure
- Gain longitudinal metrics (NVR, ADV)

Implementation sketch:
```python
class ErisMLSupervisor(NormativeSupervisor):
    def __init__(self, erisml_spec):
        self.env_model = erisml_spec.environment
        self.norm_gate = erisml_spec.norm_gate
        self.deme = erisml_spec.deme
        
    def filter_actions(self, state, actions):
        # Use ErisML norm gate
        compliant = [a for a in actions if self.norm_gate.check(state, a)]
        
        # If ethical decision needed, consult DEME
        if self._requires_ethical_judgment(state, compliant):
            ethical_actions = self.deme.evaluate_options(state, compliant)
            return ethical_actions
        
        return compliant
```

---

## 5. Limitations and Future Work

### 5.1 ErisML Limitations

**1. Computational Overhead**
- No empirical benchmarks for large-scale scenarios
- Norm checking + DEME evaluation adds latency
- Environment simulation overhead for planning

**Mitigation strategies:**
- Caching frequently checked norm conditions
- Parallel DEME module evaluation
- Lazy DEME invocation (only for ethically-charged decisions)

**2. Governance Mechanism Maturity**
- Limited exploration of voting mechanisms beyond plurality/majority
- No formal guarantees on governance properties (fairness, strategyproofness)
- Stakeholder weight assignment underspecified

**Future work:**
- Explore social choice theory mechanisms (Condorcet, ranked pairs)
- Prove properties of governance algorithms
- Develop stakeholder weight elicitation protocols

**3. Foundation Model Integration**
- Conceptual framework exists but lacks implementation examples
- Unclear how to map LLM outputs to ErisML constructs
- No benchmarks on LLM-powered agents

**Future work:**
- Implement case studies with GPT-4, Claude, etc.
- Develop LLM-ErisML interface protocols
- Benchmark governance overhead on LLM agents

### 5.2 DDL Limitations (from ErisML perspective)

**1. Environment Dynamics Not Modeled**
- DDL focuses on norms, not environment state transitions
- Resource depletion, temporal evolution require extensions
- Limited support for uncertainty and stochastic processes

**ErisML advantage**: Native environment modeling

**2. Single Normative Perspective**
- DDL encodes one coherent normative system
- Superiority relations resolve conflicts within that system
- No support for pluralistic ethical governance

**ErisML advantage**: DEME enables multiple ethical perspectives

**3. Agent Architecture Not Specified**
- Agents implicit in DDL (just subjects of norms)
- No explicit modeling of agent beliefs, capabilities, utilities

**ErisML advantage**: Agents as first-class entities

### 5.3 Normative Supervisor Limitations (from ErisML perspective)

**1. RL-Centric Design**
- Tailored to MDP-based RL agents
- Limited applicability to planning, symbolic reasoning, LLMs
- Assumes discrete state-action spaces

**ErisML advantage**: Agnostic to learning paradigm

**2. Post-Hoc Compliance**
- Supervisor retrofits ethics onto pre-trained agents
- Can cause performance degradation (deadlock, suboptimality)
- Requires NGRL to achieve norm-aware learning

**ErisML advantage**: Norms as first-class constraints from design

**3. Single Ethical Framework**
- Norms encoded as DDL rules (one normative system)
- No mechanism for multi-stakeholder ethical governance
- No support for ethical pluralism

**ErisML advantage**: DEME with democratic governance

---

## 6. Recommendations

### For Practitioners

**Use Defeasible Deontic Logic when:**
- Your domain has well-established legal/regulatory rules
- You need formal proofs of compliance
- The normative system is relatively stable
- You want mature tooling (SPINdle, Answer Set Programming)
- Computational efficiency is critical (thousands of rules/second)

**Use Normative Supervisor when:**
- You have an existing RL agent to retrofit with ethics
- You work in MDP environments with discrete actions
- You need to enforce norms without retraining
- You want to leverage existing RL infrastructure
- You can tolerate some performance degradation

**Use ErisML when:**
- You're designing a new agent from scratch for pervasive computing
- You need to model complex environment dynamics (resources, time)
- You require multi-stakeholder ethical governance
- You're building foundation model-enabled agents
- You need longitudinal safety metrics (NVR, ADV)

### For Researchers

**Hybrid Approaches:**
1. ErisML + DDL: Use SPINdle as norm gate, add DEME for ethics
2. ErisML + Normative Supervisor: Use ErisML spec, leverage RL training
3. DDL + DEME: Extend DDL with democratic ethical governance

**Open Research Questions:**
1. Can DEME governance be proven to satisfy social choice criteria?
2. How does ErisML scale to hundreds of agents and thousands of norms?
3. What are the formal semantics of ErisML + foundation model interaction?
4. Can DDL's CTD handling be unified with ErisML's DEME?
5. How do we elicit stakeholder weights democratically?

### For ErisML Development

**Priority Enhancements:**
1. **Integrate DDL backend**: Use SPINdle for efficient norm checking
2. **Benchmark performance**: Compare against DDL and Normative Supervisor
3. **Implement LLM case studies**: Show foundation model governance
4. **Formalize governance**: Prove properties of voting mechanisms
5. **Develop tooling**: IDE support, visualization, simulation

**Documentation Needs:**
1. Detailed comparison like this document
2. Migration guide from DDL/Normative Supervisor
3. Tutorials for ethicists, not just developers
4. Performance optimization best practices

---

## 7. Conclusion

ErisML, Defeasible Deontic Logic, and Normative Supervisors each offer valuable approaches to governed AI agents, with distinct strengths:

- **DDL**: Best for formal legal/regulatory compliance with mature tooling
- **Normative Supervisor**: Best for retrofitting ethics onto existing RL agents
- **ErisML**: Best for designing governed foundation model agents in pervasive computing

Rather than competing, these approaches can be integrated:
- ErisML provides the specification layer (environment, agents, norms, ethics)
- DDL provides efficient norm checking and proof traces
- Normative Supervisor provides the RL integration pattern

The future of ethical AI likely requires all three perspectives: formal compliance (DDL), efficient enforcement (Normative Supervisor), and democratic governance (ErisML's DEME). By combining these approaches, we can build agents that are formally compliant, computationally efficient, and ethically pluralistic.

---

## References

### Defeasible Deontic Logic
- Governatori, G., et al. (2024). An ASP Implementation of Defeasible Deontic Logic. *Künstliche Intelligenz*, 38, 79–88.
- Governatori, G., & Rotolo, A. (2010). Changing legal systems: Legal abrogations and annulments in defeasible logic. *Logic Journal of IGPL*, 18(1), 157–194.
- Lam, H.-P., & Governatori, G. (2009). The Making of SPINdle. *Proc. RuleML 2009*.

### Normative Supervisors
- Neufeld, E., et al. (2021). A Normative Supervisor for Reinforcement Learning Agents. *CADE 2021*, 565–576.
- Neufeld, E., et al. (2022). Enforcing ethical goals over reinforcement-learning policies. *Ethics and Information Technology*, 24.
- Neufeld, E. (2024). Learning Normative Behaviour Through Automated Theorem Proving. *Künstliche Intelligenz*, 38.

### ErisML
- ErisML Library: https://github.com/ahb-sjsu/erisml-lib