*Layer 5 of the Grand Unified AI Safety Stack*

Modular Policy Translation with DAG-Based Composition

*Featuring Complete EU AI Ethics Guidelines Mapping*

**Technical Whitepaper v0.21 --- December 2025**

Andrew H. Bond

San José State University

andrew.bond@sjsu.edu

**DOCUMENT CLASSIFICATION:** For distribution to AI safety research
teams

# Abstract

The Translation Layer (Layer 5) of the Grand Unified AI Safety Stack
provides the universal adapter between human ethical frameworks and the
ErisML intermediate representation. This whitepaper specifies the
translation architecture with two key innovations:

- **Modular Policy Units**: Ethical requirements are decomposed into
  independent, reusable modules that can be composed, versioned, and
  governed separately.

- **DAG-Based Composition**: Policy modules are organized into Directed
  Acyclic Graphs (DAGs) that express hierarchical dependencies,
  inheritance relationships, and conflict resolution rules.

We demonstrate this architecture through a complete translation of the
EU Ethics Guidelines for Trustworthy AI (April 2019), mapping all seven
key requirements to ErisML policy modules with explicit dependency
structures.

This version also addresses the **Rawlsian Objection**---the claim that
ethics cannot be \'compiled\' because ethical principles emerge from
ongoing deliberation ***(the veil of ignorance)*** and are subject to
continuous revision ***(reflective equilibrium)***.

We show that Layer 5 translates provisional snapshots of ethical
consensus, with versioning to accommodate evolution, and that DEME
provides **computational reflective equilibrium**.

The result is a **composable, auditable, and governable translation**
that can be extended, specialized, or composed with other
frameworks---while remaining honest about the limits of formalization.

# 1. Introduction: From Monolithic to Modular Ethics

## 1.1 The Problem with Monolithic Translation

Version 0.1 of this whitepaper treated ethical frameworks as monolithic
units: \"**Kantian Deontology**\" mapped to a set of constraints,
\"**Utilitarianism**\" to another. This approach has serious
limitations:

- No Reuse: Common concepts (e.g., \"informed consent\") must be
  re-implemented for each framework.

- No Composition: Combining frameworks requires ad-hoc integration with
  no principled conflict resolution.

- No Granular Governance: Changes to one principle force re-review of
  the entire translation.

- No Hierarchy: Flat constraint sets cannot express that some
  requirements depend on others.

Real-world ethical frameworks are not monolithic. The EU AI Ethics
Guidelines, for instance, have seven requirements that depend on each
other in complex ways. \"Accountability\" presupposes \"Transparency.\"
\"Human Oversight\" presupposes \"Human Agency.\" These dependencies
matter.

## 1.2 The Modular Solution

This whitepaper introduces a modular architecture where:

1.  Policy Modules are the atomic unit of translation---self-contained,
    versioned, and independently governable.

2.  Dependencies between modules are explicit and form a Directed
    Acyclic Graph (DAG).

3.  Composition Rules specify how modules combine, including conflict
    resolution.

4.  Inheritance allows specialized modules to extend base modules.

5.  Hierarchical Organization supports both vertical (abstraction
    levels) and horizontal (domain specialization) structure.

## 1.3 Why DAGs?

A Directed Acyclic Graph (DAG) is the natural structure for policy
dependencies:

- **Directed**: Dependencies have direction---module A depends on module
  B, not vice versa.

- **Acyclic**: Circular dependencies are prohibited---no module can
  transitively depend on itself.

- **Graph**: Multiple inheritance is allowed---a module can depend on
  several others.

DAGs enable:

- **Topological Ordering**: Modules can be evaluated in dependency
  order.

- **Incremental Validation**: Changes propagate only to dependent
  modules.

- **Conflict Detection**: Diamond dependencies (A→B→D, A→C→D) are
  identified and resolved.

- **Visualization**: The dependency structure can be rendered as a
  comprehensible diagram.

# 2. Policy Module Architecture

## 2.1 Policy Module Definition

A Policy Module is the atomic unit of ethical translation. Each module:

> policy_module {
>
> // Identity
>
> id: \"eu.trustworthy_ai.transparency\"
>
> version: \"1.0.0\"
>
> // Metadata
>
> name: \"Transparency\"
>
> source_framework: \"EU Ethics Guidelines for Trustworthy AI\"
>
> source_reference: \"Section 1.4, Requirement 4\"
>
> // Dependencies (forms DAG edges)
>
> depends_on: \[
>
> \"eu.trustworthy_ai.technical_robustness\", // Hard dependency
>
> \"eu.trustworthy_ai.data_governance\" // Hard dependency
>
> \]
>
> // Optional/soft dependencies
>
> recommends: \[
>
> \"eu.trustworthy_ai.diversity\"
>
> \]
>
> // Conflicts (cannot be active simultaneously)
>
> conflicts_with: \[\]
>
> // The actual constraints
>
> constraints: \[ \... \]
>
> // Governance
>
> governance: { \... }
>
> }

## 2.2 Dependency Types

The DAG supports multiple edge types:

  ----------------------------------------------------------------------------
  **Edge Type**    **Semantics**   **Example**
  ---------------- --------------- -------------------------------------------
  depends_on       Hard            Accountability requires Transparency
                   requirement     

  extends          Inheritance     GDPR_Transparency extends base Transparency

  recommends       Soft dependency Transparency recommends Diversity

  conflicts_with   Mutual          Full_Automation conflicts_with
                   exclusion       Human_Oversight

  specializes      Domain          Medical_AI_Safety specializes
                   narrowing       Technical_Robustness
  ----------------------------------------------------------------------------

## 2.3 DAG Validation Rules

The policy DAG must satisfy:

1.  Acyclicity: No circular dependencies. Detected via topological sort
    failure.

2.  Completeness: All depends_on targets must exist in the registry.

3.  Conflict Freedom: No path activates conflicting modules
    simultaneously.

4.  Version Compatibility: Dependency version constraints must be
    satisfiable.

> function validate_dag(modules: Set\<PolicyModule\>) -\>
> ValidationResult {
>
> // Build adjacency list
>
> let graph = build_dependency_graph(modules);
>
> // Check acyclicity via topological sort
>
> let topo_result = topological_sort(graph);
>
> if (topo_result.has_cycle) {
>
> return ValidationResult.fail(
>
> \"Circular dependency detected\",
>
> topo_result.cycle_witness
>
> );
>
> }
>
> // Check completeness
>
> for each module in modules {
>
> for each dep in module.depends_on {
>
> if (!modules.contains(dep)) {
>
> return ValidationResult.fail(
>
> \"Missing dependency\",
>
> { module: module.id, missing: dep }
>
> );
>
> }
>
> }
>
> }
>
> // Check conflict freedom
>
> let conflict_check = check_conflict_paths(graph);
>
> if (conflict_check.has_conflict) {
>
> return ValidationResult.fail(
>
> \"Conflicting modules reachable\",
>
> conflict_check.conflict_witness
>
> );
>
> }
>
> return ValidationResult.pass(topo_result.ordering);
>
> }

# 3. Hierarchical Organization

## 3.1 Vertical Hierarchy: Abstraction Levels

Policy modules are organized into abstraction levels:

> Level 0: Meta-Principles
>
> └── human_dignity
>
> └── fundamental_rights
>
> └── rule_of_law
>
> Level 1: Core Requirements
>
> └── human_agency (depends_on: human_dignity)
>
> └── technical_robustness (depends_on: fundamental_rights)
>
> └── privacy (depends_on: fundamental_rights)
>
> └── transparency (depends_on: rule_of_law)
>
> └── fairness (depends_on: fundamental_rights)
>
> └── wellbeing (depends_on: human_dignity)
>
> └── accountability (depends_on: transparency, rule_of_law)
>
> Level 2: Implementation Requirements
>
> └── explainability (depends_on: transparency)
>
> └── traceability (depends_on: transparency, accountability)
>
> └── human_oversight (depends_on: human_agency)
>
> └── bias_detection (depends_on: fairness)
>
> └── \...
>
> Level 3: Domain Specializations
>
> └── medical_ai_transparency (extends: transparency)
>
> └── autonomous_vehicle_safety (extends: technical_robustness)
>
> └── \...

## 3.2 Horizontal Hierarchy: Domain Specialization

Within each level, modules can be specialized for domains:

> transparency (base)
>
> ├── transparency.healthcare
>
> │ └── transparency.healthcare.diagnosis
>
> │ └── transparency.healthcare.treatment
>
> ├── transparency.finance
>
> │ └── transparency.finance.credit_scoring
>
> │ └── transparency.finance.trading
>
> ├── transparency.law_enforcement
>
> │ └── transparency.law_enforcement.predictive_policing
>
> │ └── transparency.law_enforcement.facial_recognition
>
> └── transparency.employment
>
> └── transparency.employment.hiring
>
> └── transparency.employment.performance

## 3.3 The Full DAG Structure

Combining vertical and horizontal hierarchies produces a rich DAG:

> ┌─────────────────┐
>
> │ human_dignity │
>
> └────────┬────────┘
>
> │
>
> ┌────────────────┼────────────────┐
>
> ▼ ▼ ▼
>
> ┌──────────────┐ ┌─────────────┐ ┌───────────┐
>
> │ human_agency │ │ wellbeing │ │ fund_rts │
>
> └──────┬───────┘ └─────────────┘ └─────┬─────┘
>
> │ │
>
> ▼ ┌────────────┼────────────┐
>
> ┌──────────────┐ ▼ ▼ ▼
>
> │human_oversght│ ┌──────────┐ ┌─────────┐ ┌─────────┐
>
> └──────────────┘ │ privacy │ │fairness │ │robustns │
>
> └────┬─────┘ └────┬────┘ └────┬────┘
>
> │ │ │
>
> ▼ ▼ ▼
>
> ┌────────────┐ ┌──────────┐ ┌──────────┐
>
> │data_govern │ │bias_det │ │safety │
>
> └────────────┘ └──────────┘ └──────────┘

# 4. Complete Translation: EU AI Ethics Guidelines

## 4.1 Source Framework Overview

The EU Ethics Guidelines for Trustworthy AI (April 2019) define seven
key requirements for trustworthy AI systems. These are not
independent---they form a dependency structure rooted in the EU\'s
commitment to human dignity and fundamental rights.

Source document: \"Ethics Guidelines for Trustworthy AI\" --- High-Level
Expert Group on Artificial Intelligence, European Commission, April
2019.

## 4.2 Meta-Principles (Level 0)

The EU Guidelines are grounded in four foundational principles:

### 4.2.1 Module: Human Dignity

> policy_module {
>
> id: \"eu.trustworthy_ai.meta.human_dignity\"
>
> version: \"1.0.0\"
>
> level: 0
>
> source_text: \"The human-centric approach to AI strives to
>
> ensure that human values are central to the way in which
>
> AI systems are developed, deployed, used and monitored,
>
> by ensuring respect for fundamental rights\... all of which
>
> are united by reference to a common foundation rooted in
>
> respect for human dignity.\"
>
> depends_on: \[\] // Root node
>
> constraints: \[
>
> {
>
> id: \"human_dignity_core\",
>
> type: \"invariant\",
>
> erisml: \"
>
> constraint HumanDignityCore(action: Action) {
>
> for each person in affected_persons(action) {
>
> require person.dignity_respected == true;
>
> require person.treated_as_end == true;
>
> require person.mere_means == false;
>
> }
>
> }
>
> \"
>
> }
>
> \]
>
> }

### 4.2.2 Module: Fundamental Rights

> policy_module {
>
> id: \"eu.trustworthy_ai.meta.fundamental_rights\"
>
> version: \"1.0.0\"
>
> level: 0
>
> source_text: \"Fundamental rights\... including those set out
>
> in the Treaties of the European Union and Charter of
>
> Fundamental Rights of the European Union.\"
>
> depends_on: \[\"eu.trustworthy_ai.meta.human_dignity\"\]
>
> constraints: \[
>
> {
>
> id: \"fundamental_rights_impact\",
>
> type: \"precondition\",
>
> erisml: \"
>
> precondition FundamentalRightsCheck(system: AISystem) {
>
> require system.fundamental_rights_impact_assessment
>
> .completed == true;
>
> require system.fundamental_rights_impact_assessment
>
> .violations == \[\];
>
> }
>
> \"
>
> }
>
> \]
>
> }

## 4.3 Core Requirements (Level 1)

The seven key requirements map to Level 1 modules:

### 4.3.1 Module: Human Agency and Oversight

> policy_module {
>
> id: \"eu.trustworthy_ai.human_agency\"
>
> version: \"1.0.0\"
>
> level: 1
>
> requirement_number: 1
>
> source_text: \"AI systems should support human autonomy and
>
> decision-making\... Users should be able to make informed
>
> autonomous decisions\... Human oversight helps ensuring that
>
> an AI system does not undermine human autonomy.\"
>
> depends_on: \[
>
> \"eu.trustworthy_ai.meta.human_dignity\",
>
> \"eu.trustworthy_ai.meta.fundamental_rights\"
>
> \]
>
> sub_modules: \[
>
> \"eu.trustworthy_ai.human_agency.autonomy\",
>
> \"eu.trustworthy_ai.human_agency.oversight\"
>
> \]
>
> constraints: \[
>
> {
>
> id: \"human_autonomy\",
>
> erisml: \"
>
> constraint HumanAutonomy(system: AISystem) {
>
> // Users can make informed decisions
>
> require system.user_can_understand_interaction == true;
>
> require system.user_informed_of_ai_nature == true;
>
> // Right not to be subject to solely automated decisions
>
> if (system.decision.has_legal_effect \|\|
>
> system.decision.significantly_affects_user) {
>
> require system.human_review_available == true;
>
> }
>
> }
>
> \"
>
> },
>
> {
>
> id: \"human_oversight\",
>
> erisml: \"
>
> constraint HumanOversight(system: AISystem) {
>
> // Humans can intervene
>
> require system.stop_button_available == true;
>
> require system.human_override_possible == true;
>
> // Oversight mechanisms
>
> require system.oversight_mechanism in
>
> \[HumanInTheLoop, HumanOnTheLoop, HumanInCommand\];
>
> }
>
> \"
>
> }
>
> \]
>
> }

### 4.3.2 Module: Technical Robustness and Safety

> policy_module {
>
> id: \"eu.trustworthy_ai.technical_robustness\"
>
> version: \"1.0.0\"
>
> level: 1
>
> requirement_number: 2
>
> source_text: \"Trustworthy AI requires algorithms to be secure,
>
> reliable and robust enough to deal with errors or
>
> inconsistencies during all life cycle phases.\"
>
> depends_on: \[
>
> \"eu.trustworthy_ai.meta.fundamental_rights\"
>
> \]
>
> constraints: \[
>
> {
>
> id: \"resilience_to_attack\",
>
> erisml: \"
>
> constraint ResilienceToAttack(system: AISystem) {
>
> require system.vulnerability_assessment.completed == true;
>
> require system.attack_surface.minimized == true;
>
> require system.fallback_plan.exists == true;
>
> }
>
> \"
>
> },
>
> {
>
> id: \"safety\",
>
> erisml: \"
>
> constraint Safety(system: AISystem) {
>
> require system.safety_risks.assessed == true;
>
> require system.unintended_harm.minimized == true;
>
> if (system.safety_critical) {
>
> require system.human_control.takeover_possible == true;
>
> }
>
> }
>
> \"
>
> },
>
> {
>
> id: \"accuracy\",
>
> erisml: \"
>
> constraint Accuracy(system: AISystem) {
>
> require system.accuracy.measured == true;
>
> require system.accuracy.communicated_to_users == true;
>
> }
>
> \"
>
> },
>
> {
>
> id: \"reliability\",
>
> erisml: \"
>
> constraint Reliability(system: AISystem) {
>
> require system.reproducible_under_conditions == true;
>
> require system.error_handling.graceful == true;
>
> }
>
> \"
>
> }
>
> \]
>
> }

### 4.3.3 Module: Privacy and Data Governance

> policy_module {
>
> id: \"eu.trustworthy_ai.privacy_data_governance\"
>
> version: \"1.0.0\"
>
> level: 1
>
> requirement_number: 3
>
> source_text: \"AI systems must guarantee privacy and data
>
> protection throughout a system\'s entire lifecycle\...
>
> Data governance that covers the quality and integrity of
>
> the data used.\"
>
> depends_on: \[
>
> \"eu.trustworthy_ai.meta.fundamental_rights\"
>
> \]
>
> external_requirements: \[
>
> \"GDPR\" // Links to legal framework
>
> \]
>
> constraints: \[
>
> {
>
> id: \"privacy_by_design\",
>
> erisml: \"
>
> constraint PrivacyByDesign(system: AISystem) {
>
> require system.data_minimization == true;
>
> require system.purpose_limitation == true;
>
> require system.storage_limitation == true;
>
> }
>
> \"
>
> },
>
> {
>
> id: \"data_quality\",
>
> erisml: \"
>
> constraint DataQuality(system: AISystem) {
>
> require system.training_data.quality_assessed == true;
>
> require system.training_data.bias_checked == true;
>
> require system.training_data.provenance_documented == true;
>
> }
>
> \"
>
> },
>
> {
>
> id: \"user_control\",
>
> erisml: \"
>
> constraint UserDataControl(system: AISystem) {
>
> require system.user_data_access == true;
>
> require system.user_data_rectification == true;
>
> require system.user_data_erasure == true;
>
> }
>
> \"
>
> }
>
> \]
>
> }

### 4.3.4 Module: Transparency

> policy_module {
>
> id: \"eu.trustworthy_ai.transparency\"
>
> version: \"1.0.0\"
>
> level: 1
>
> requirement_number: 4
>
> source_text: \"The data sets and the processes that yield the
>
> AI system\'s decision, including those of data gathering and
>
> data labelling as well as the algorithms used, should be
>
> documented to the best possible standard.\"
>
> depends_on: \[
>
> \"eu.trustworthy_ai.technical_robustness\",
>
> \"eu.trustworthy_ai.privacy_data_governance\"
>
> \]
>
> sub_modules: \[
>
> \"eu.trustworthy_ai.transparency.traceability\",
>
> \"eu.trustworthy_ai.transparency.explainability\",
>
> \"eu.trustworthy_ai.transparency.communication\"
>
> \]
>
> constraints: \[
>
> {
>
> id: \"traceability\",
>
> erisml: \"
>
> constraint Traceability(system: AISystem) {
>
> require system.data_provenance.documented == true;
>
> require system.model_provenance.documented == true;
>
> require system.decision_logging.enabled == true;
>
> }
>
> \"
>
> },
>
> {
>
> id: \"explainability\",
>
> erisml: \"
>
> constraint Explainability(system: AISystem) {
>
> // Decisions should be explainable
>
> require system.decision_explanation.available == true;
>
> // Degree depends on context
>
> if (system.impacts_fundamental_rights) {
>
> require system.explanation_detail \>= HIGH;
>
> }
>
> }
>
> \"
>
> },
>
> {
>
> id: \"ai_identification\",
>
> erisml: \"
>
> constraint AIIdentification(system: AISystem) {
>
> // Users must know they\'re interacting with AI
>
> require system.ai_nature.disclosed == true;
>
> require system.capabilities.communicated == true;
>
> require system.limitations.communicated == true;
>
> }
>
> \"
>
> }
>
> \]
>
> }

### 4.3.5 Module: Diversity, Non-discrimination and Fairness

> policy_module {
>
> id: \"eu.trustworthy_ai.diversity_fairness\"
>
> version: \"1.0.0\"
>
> level: 1
>
> requirement_number: 5
>
> source_text: \"In order to achieve Trustworthy AI, we must enable
>
> inclusion and diversity throughout the entire AI system\'s
>
> life cycle\... Data sets used by AI systems may suffer from
>
> the inclusion of inadvertent historic bias.\"
>
> depends_on: \[
>
> \"eu.trustworthy_ai.meta.fundamental_rights\",
>
> \"eu.trustworthy_ai.privacy_data_governance\"
>
> \]
>
> constraints: \[
>
> {
>
> id: \"unfair_bias_avoidance\",
>
> erisml: \"
>
> constraint UnfairBiasAvoidance(system: AISystem) {
>
> require system.bias_assessment.completed == true;
>
> require system.protected_attributes.identified == true;
>
> for each attr in system.protected_attributes {
>
> require system.disparate_impact(attr) \<= THRESHOLD;
>
> }
>
> }
>
> \"
>
> },
>
> {
>
> id: \"accessibility\",
>
> erisml: \"
>
> constraint Accessibility(system: AISystem) {
>
> require system.accessibility_standards.met == true;
>
> require system.disability_accommodations.available == true;
>
> }
>
> \"
>
> },
>
> {
>
> id: \"stakeholder_participation\",
>
> erisml: \"
>
> constraint StakeholderParticipation(system: AISystem) {
>
> require system.stakeholder_consultation.completed == true;
>
> require system.affected_groups.represented == true;
>
> }
>
> \"
>
> }
>
> \]
>
> }

### 4.3.6 Module: Societal and Environmental Wellbeing

> policy_module {
>
> id: \"eu.trustworthy_ai.wellbeing\"
>
> version: \"1.0.0\"
>
> level: 1
>
> requirement_number: 6
>
> source_text: \"AI systems should benefit all human beings,
>
> including future generations\... Sustainability and ecological
>
> responsibility of AI systems should be encouraged.\"
>
> depends_on: \[
>
> \"eu.trustworthy_ai.meta.human_dignity\"
>
> \]
>
> constraints: \[
>
> {
>
> id: \"environmental_impact\",
>
> erisml: \"
>
> constraint EnvironmentalImpact(system: AISystem) {
>
> require system.energy_consumption.measured == true;
>
> require system.environmental_footprint.assessed == true;
>
> }
>
> \"
>
> },
>
> {
>
> id: \"social_impact\",
>
> erisml: \"
>
> constraint SocialImpact(system: AISystem) {
>
> require system.social_impact_assessment.completed == true;
>
> require system.impact_on_democracy.assessed == true;
>
> require system.mental_wellbeing_impact.considered == true;
>
> }
>
> \"
>
> }
>
> \]
>
> }

### 4.3.7 Module: Accountability

> policy_module {
>
> id: \"eu.trustworthy_ai.accountability\"
>
> version: \"1.0.0\"
>
> level: 1
>
> requirement_number: 7
>
> source_text: \"Mechanisms should be put in place to ensure
>
> responsibility and accountability for AI systems and their
>
> outcomes\... Auditability is crucial.\"
>
> depends_on: \[
>
> \"eu.trustworthy_ai.transparency\", // Can\'t be accountable without
> transparency
>
> \"eu.trustworthy_ai.meta.fundamental_rights\"
>
> \]
>
> constraints: \[
>
> {
>
> id: \"auditability\",
>
> erisml: \"
>
> constraint Auditability(system: AISystem) {
>
> require system.audit_trail.complete == true;
>
> require system.external_audit.possible == true;
>
> if (system.impacts_fundamental_rights) {
>
> require system.independent_audit.required == true;
>
> }
>
> }
>
> \"
>
> },
>
> {
>
> id: \"redress\",
>
> erisml: \"
>
> constraint Redress(system: AISystem) {
>
> require system.redress_mechanism.available == true;
>
> require system.complaint_process.accessible == true;
>
> }
>
> \"
>
> },
>
> {
>
> id: \"impact_assessment\",
>
> erisml: \"
>
> constraint ImpactAssessment(system: AISystem) {
>
> require system.risk_assessment.completed == true;
>
> require system.negative_impact_reporting.enabled == true;
>
> require system.trade_off_documentation.available == true;
>
> }
>
> \"
>
> }
>
> \]
>
> }

# 5. EU Guidelines: Complete DAG Structure

## 5.1 Visual Representation

The complete dependency structure of the EU AI Ethics Guidelines:

> ┌─────────────────────┐
>
> │ HUMAN_DIGNITY │
>
> │ (Level 0) │
>
> └──────────┬──────────┘
>
> │
>
> ┌───────────────┼───────────────┐
>
> │ │ │
>
> ▼ ▼ ▼
>
> ┌────────────────┐ ┌──────────┐ ┌────────────────┐
>
> │FUNDAMENTAL_RGTS│ │WELLBEING │ │ RULE_OF_LAW │
>
> │ (Level 0) │ │(Level 1) │ │ (Level 0) │
>
> └───────┬────────┘ └──────────┘ └───────┬────────┘
>
> │ │
>
> ┌─────────────┼─────────────┬─────────────────┤
>
> │ │ │ │
>
> ▼ ▼ ▼ │
>
> ┌──────────┐ ┌──────────┐ ┌────────────┐ │
>
> │HUMAN\_ │ │TECHNICAL\_│ │PRIVACY\_ │ │
>
> │AGENCY │ │ROBUSTNESS│ │DATA_GOV │ │
>
> │(Level 1) │ │(Level 1) │ │(Level 1) │ │
>
> └────┬─────┘ └────┬─────┘ └─────┬──────┘ │
>
> │ │ │ │
>
> │ │ ┌───────┴───────┐ │
>
> │ │ │ │ │
>
> │ ▼ ▼ ▼ │
>
> │ ┌────────────────┐ ┌──────────────┐ │
>
> │ │ TRANSPARENCY │ │ DIVERSITY\_ │ │
>
> │ │ (Level 1) │ │ FAIRNESS │ │
>
> │ │ Req #4 │ │ (Level 1) │ │
>
> │ └───────┬────────┘ └──────────────┘ │
>
> │ │ │
>
> │ └──────────────┬──────────────┘
>
> │ │
>
> │ ▼
>
> │ ┌────────────────┐
>
> │ │ ACCOUNTABILITY │
>
> │ │ (Level 1) │
>
> │ │ Req #7 │
>
> │ └────────────────┘
>
> │ ▲
>
> └──────────────────────────────┘
>
> (oversight enables accountability)

## 5.2 Topological Ordering

Modules must be evaluated in dependency order:

1.  eu.trustworthy_ai.meta.human_dignity

2.  eu.trustworthy_ai.meta.fundamental_rights (depends on 1)

3.  eu.trustworthy_ai.meta.rule_of_law (depends on 1)

4.  eu.trustworthy_ai.human_agency (depends on 1, 2)

5.  eu.trustworthy_ai.technical_robustness (depends on 2)

6.  eu.trustworthy_ai.privacy_data_governance (depends on 2)

7.  eu.trustworthy_ai.wellbeing (depends on 1)

8.  eu.trustworthy_ai.transparency (depends on 5, 6)

9.  eu.trustworthy_ai.diversity_fairness (depends on 2, 6)

10. eu.trustworthy_ai.accountability (depends on 3, 8)

## 5.3 Composition with Other Frameworks

The modular structure enables composition with other frameworks:

> composed_policy EUTrustworthyAI_Plus_GDPR {
>
> include: \"eu.trustworthy_ai.\*\" // All EU AI modules
>
> // GDPR modules extend privacy requirements
>
> include: \"gdpr.article_5\" // Processing principles
>
> include: \"gdpr.article_22\" // Automated decision-making
>
> // Specify that GDPR extends EU AI privacy
>
> link: \"gdpr.article_5\" extends
> \"eu.trustworthy_ai.privacy_data_governance\"
>
> link: \"gdpr.article_22\" extends \"eu.trustworthy_ai.human_agency\"
>
> // Conflict resolution
>
> conflict_resolution: {
>
> strategy: \"stricter_wins\",
>
> documentation_required: true
>
> }
>
> }

# 6. Validation and Testing

## 6.1 Module-Level Validation

Each policy module is validated independently:

> test_suite ModuleValidation(module: PolicyModule) {
>
> test \"Constraints are syntactically valid\" {
>
> for each constraint in module.constraints {
>
> assert ErisML.parse(constraint.erisml).success == true;
>
> }
>
> }
>
> test \"Source text is mapped\" {
>
> assert module.source_text != null;
>
> assert module.source_reference != null;
>
> }
>
> test \"Dependencies exist\" {
>
> for each dep in module.depends_on {
>
> assert Registry.contains(dep);
>
> }
>
> }
>
> test \"No circular dependencies\" {
>
> assert !transitive_closure(module).contains(module.id);
>
> }
>
> }

## 6.2 DAG-Level Validation

The complete DAG is validated as a unit:

> test_suite DAGValidation(dag: PolicyDAG) {
>
> test \"DAG is acyclic\" {
>
> let result = topological_sort(dag);
>
> assert result.success == true;
>
> }
>
> test \"No unreachable modules\" {
>
> let roots = dag.modules.filter(m =\> m.depends_on.isEmpty);
>
> let reachable = transitive_closure(roots);
>
> assert reachable == dag.modules;
>
> }
>
> test \"Conflict paths are resolved\" {
>
> for each (m1, m2) in dag.conflict_pairs {
>
> assert !dag.paths_to_both(m1, m2).exists \|\|
>
> dag.conflict_resolution_specified(m1, m2);
>
> }
>
> }
>
> test \"Version constraints satisfiable\" {
>
> let solution = solve_version_constraints(dag);
>
> assert solution.satisfiable == true;
>
> }
>
> }

## 6.3 Preservation Testing

Test that the translation preserves source framework semantics:

> test_suite PreservationTests {
>
> test \"Transparency requires traceability\" {
>
> // In source: \"The data sets and the processes\... should be
> documented\"
>
> // In translation: traceability constraint
>
> let system_without_traceability = MockSystem(
>
> data_provenance_documented: false
>
> );
>
> assert transparency.evaluate(system_without_traceability) == FAIL;
>
> }
>
> test \"Accountability depends on transparency\" {
>
> // Cannot be accountable if not transparent
>
> let dag = load_eu_guidelines_dag();
>
> assert dag.depends_on(\"accountability\", \"transparency\");
>
> }
>
> test \"Human oversight enables override\" {
>
> // In source: \"Humans should always have the possibility ultimately
> to
>
> // over-ride a decision made by a system\"
>
> let system_without_override = MockSystem(
>
> human_override_possible: false
>
> );
>
> assert human_agency.evaluate(system_without_override) == FAIL;
>
> }
>
> }

# 7. Governance Framework

## 7.1 Module Lifecycle

  ------------------------------------------------------------
  **Phase**    **Module Actions**       **DAG Actions**
  ------------ ------------------------ ----------------------
  Draft        Write constraints, map   Declare dependencies
               sources                  

  Review       Expert review,           Validate DAG structure
               preservation tests       

  Approved     Sign, hash, register     Lock dependencies

  Deployed     Production use           Monitor constraint
                                        satisfaction

  Deprecated   Migration guide          Update dependent
                                        modules
  ------------------------------------------------------------

## 7.2 Version Compatibility

Modules declare version constraints on dependencies:

> policy_module {
>
> id: \"eu.trustworthy_ai.accountability\"
>
> version: \"1.1.0\"
>
> depends_on: \[
>
> {
>
> module: \"eu.trustworthy_ai.transparency\",
>
> version_constraint: \"\>=1.0.0 \<2.0.0\" // SemVer range
>
> }
>
> \]
>
> }

The DAG solver ensures version constraints are satisfiable before
deployment.

## 7.3 Change Propagation

When a module changes, dependent modules are affected:

- Patch change (1.0.0 → 1.0.1): No action required in dependents

- Minor change (1.0.0 → 1.1.0): Dependents should review

- Major change (1.0.0 → 2.0.0): Dependents must update dependency
  declaration

# 8. The Rawlsian Objection: Can Ethics Be Translated?

A sophisticated critic might object that Layer 5 is not merely difficult
but impossible in principle. The strongest version of this objection
draws on the work of John Rawls (1921--2002), the most influential
political philosopher of the 20th century. This section takes the
objection seriously and shows how the architecture addresses it.

## 8.1 The Veil of Ignorance

In A Theory of Justice (1971), Rawls proposed a thought experiment:
Imagine you are designing the rules for society, but you do not know
what position you will occupy in that society. You do not know if you
will be rich or poor, healthy or sick, talented or ordinary, part of the
majority or a minority. Behind this \'veil of ignorance,\' what rules
would you choose?

Rawls argued that rational people behind the veil would choose:

1.  Equal basic liberties for all (speech, conscience, voting, due
    process)

2.  The Difference Principle: Inequalities are only justified if they
    benefit the least advantaged members of society

The veil of ignorance is not just a thought experiment---it is a
procedure for generating fair principles. The key insight: principles
are not given in advance; they emerge from a process of reasoning under
constraints.

## 8.2 Reflective Equilibrium

Rawls also introduced the concept of reflective equilibrium---the method
by which we actually reason about ethics. The process works as follows:

> ┌────────────────────────────────────────────────────────────┐
>
> │ REFLECTIVE EQUILIBRIUM │
>
> ├────────────────────────────────────────────────────────────┤
>
> │ │
>
> │ ┌──────────────────┐ ┌──────────────────┐ │
>
> │ │ PRINCIPLES │ ←───→ │ JUDGMENTS │ │
>
> │ │ (abstract rules)│ │ (specific cases) │ │
>
> │ └────────┬─────────┘ └────────┬─────────┘ │
>
> │ │ │ │
>
> │ └──────────┬───────────────┘ │
>
> │ ▼ │
>
> │ ┌─────────────────┐ │
>
> │ │ ADJUSTMENT │ │
>
> │ │ (back and forth │ │
>
> │ │ until coherent)│ │
>
> │ └─────────────────┘ │
>
> │ │ │
>
> │ ▼ │
>
> │ ┌─────────────────┐ │
>
> │ │ EQUILIBRIUM │ │
>
> │ │ (provisional │ │
>
> │ │ coherence) │ │
>
> │ └─────────────────┘ │
>
> │ │
>
> └────────────────────────────────────────────────────────────┘

We begin with considered judgments about particular cases (\'torture is
wrong,\' \'promises should be kept\'). We also have general principles
(\'maximize welfare,\' \'respect autonomy\'). When principles and
judgments conflict, we adjust one or both until they cohere. The result
is reflective equilibrium---a provisional, revisable coherence.

Crucially, this process never terminates. New cases arise. Principles
get refined. Judgments shift. The equilibrium is always provisional.

## 8.3 The Objection to Layer 5

The Rawlsian objection to Layer 5 is now clear:

> *\"You cannot \'translate\' ethics because there is no fixed source to
> translate from. Ethical principles are not inputs to be
> compiled---they are outputs of an ongoing deliberative process. The
> veil of ignorance generates principles; reflective equilibrium revises
> them. Layer 5 assumes ethics is static, but Rawls showed it is
> fundamentally dynamic.\"*

This is a serious objection. It does not say Layer 5 is technically
flawed---it says the entire project rests on a philosophical mistake.

## 8.4 Response: Translation of Snapshots

The objection is correct that ethics is dynamic. But it does not follow
that translation is impossible---only that translations must be
versioned.

Consider an analogy: A nation\'s constitution embodies its current
reflective equilibrium. The constitution can be amended as the
equilibrium shifts. But at any given moment, the constitution has
specific, enforceable content. Courts interpret it, legislatures work
within it, citizens are bound by it.

Layer 5 translates the constitutional moment---the current state of an
institution\'s ethical equilibrium---into machine-checkable constraints.
When the equilibrium shifts:

- Stakeholder deliberation occurs (see DEME, Section 8.6)

- The translation model is revised

- A new version is produced (v1.0.0 → v2.0.0)

- The DAG is updated accordingly

The translation is not eternal. It is timestamped, versioned, and
explicitly provisional.

> translation_model {
>
> id: \"eu.trustworthy_ai\"
>
> version: \"2.0.0\"
>
> valid_from: \"2024-01-01\"
>
> supersedes: \"1.0.0\"
>
> provenance: {
>
> deliberation_process: \"MORAL COMPASS v3\"
>
> stakeholder_sessions: 12
>
> consensus_threshold: 0.75
>
> equilibrium_date: \"2023-12-15\"
>
> }
>
> }

## 8.5 Response: The Veil as Constraint Generator

The veil of ignorance is itself formalizable. It specifies a procedure:

1.  Enumerate possible positions in society (rich/poor, healthy/sick,
    etc.)

2.  Assign equal probability to each position (you could be anyone)

3.  Choose principles that maximize the minimum outcome (maximin)

This is a decision procedure under uncertainty---exactly the kind of
thing that can be translated to ErisML:

> policy_module {
>
> id: \"rawlsian.veil_of_ignorance\"
>
> version: \"1.0.0\"
>
> source_framework: \"Rawls, A Theory of Justice (1971)\"
>
> constraints: \[
>
> {
>
> id: \"maximin_principle\",
>
> erisml: \"
>
> constraint MaximinJustice(policy: Policy) {
>
> let positions = enumerate_social_positions();
>
> let outcomes = positions.map(p =\> policy.outcome_for(p));
>
> let worst_outcome = min(outcomes);
>
> // Rawlsian requirement: maximize the minimum
>
> require policy.improves_or_maintains(worst_outcome);
>
> }
>
> \"
>
> },
>
> {
>
> id: \"equal_basic_liberties\",
>
> erisml: \"
>
> constraint EqualLiberties(policy: Policy) {
>
> let liberties = \[speech, conscience, voting, due_process\];
>
> for each liberty in liberties {
>
> for each person in affected_persons(policy) {
>
> require person.has(liberty) == true;
>
> }
>
> }
>
> }
>
> \"
>
> },
>
> {
>
> id: \"difference_principle\",
>
> erisml: \"
>
> constraint DifferencePrinciple(inequality: Inequality) {
>
> // Inequalities must benefit the least advantaged
>
> let least_advantaged = min_by(
>
> affected_persons(inequality),
>
> p =\> p.primary_goods
>
> );
>
> require inequality.benefits(least_advantaged);
>
> }
>
> \"
>
> }
>
> \]
>
> fidelity_class: \"Approximate\"
>
> loss_documentation: {
>
> what_is_lost: \[
>
> \"The deliberative process behind the veil (only outcomes
> formalized)\",
>
> \"The full theory of primary goods (simplified to basic liberties +
> welfare)\",
>
> \"Lexical priority (implemented as soft precedence, not strict
> ordering)\"
>
> \]
>
> }
>
> }

Rawls himself was trained in analytic philosophy and sought rigor. The
veil is a quasi-formal construct. We are making it fully formal---while
documenting what is lost in translation.

## 8.6 Response: DEME as Computational Reflective Equilibrium

The strongest response to the Rawlsian objection is that the GUASS
architecture already includes a mechanism for reflective equilibrium:
the Democratic Ethical Meta-Environment (DEME).

DEME provides:

- Stakeholder deliberation: Representatives of affected parties propose
  and debate constraints

- Case-based reasoning: Concrete scenarios are evaluated against
  candidate principles

- Tension surfacing: Conflicts between principles and judgments are
  identified

- Iterative refinement: The governance profile is updated based on
  deliberation

> ┌──────────────────────────────────────────────────────────────┐
>
> │ DEME: COMPUTATIONAL REFLECTIVE EQUILIBRIUM │
>
> ├──────────────────────────────────────────────────────────────┤
>
> │ │
>
> │ ┌─────────────┐ MORAL COMPASS ┌─────────────────┐ │
>
> │ │ Governance │ ──── Episodes ────→ │ Case Judgments │ │
>
> │ │ Profile │ │ (n=1694 pairs) │ │
>
> │ │ (principles)│ ←─── Refinement ─── │ │ │
>
> │ └─────────────┘ └─────────────────┘ │
>
> │ │ │ │
>
> │ │ ┌───────────────┐ │ │
>
> │ └────────→│ Consensus │←──────────┘ │
>
> │ │ (α \> 0.67) │ │
>
> │ └───────┬───────┘ │
>
> │ │ │
>
> │ ▼ │
>
> │ ┌───────────────┐ │
>
> │ │ Translation │ │
>
> │ │ Model v(n+1) │ │
>
> │ └───────────────┘ │
>
> │ │
>
> └──────────────────────────────────────────────────────────────┘

The Rawlsian process of reflective equilibrium happens in DEME. Layer 5
translates the output of that process into machine-checkable form. We
are not replacing deliberation with computation---we are making the
results of deliberation auditable and enforceable.

## 8.7 The Real Disagreement

The Rawlsian critic and the GUASS architect may actually agree on
substance. Both accept:

- Ethical principles are not given a priori---they emerge from reasoning

- Reflective equilibrium is provisional and revisable

- Deliberation among stakeholders is essential to legitimacy

- No formalization captures everything

The disagreement is about what follows:

  -----------------------------------------------------------------------
  **The Critic Says**                **Layer 5 Says**
  ---------------------------------- ------------------------------------
  Because ethics is dynamic,         Because ethics is dynamic,
  formalization is inappropriate     formalizations must be versioned

  Translation destroys what matters  Translation documents what is lost

  Deliberation cannot be computed    Deliberation outputs can be compiled

  Better to leave ethics informal    Informal ethics is unauditable
                                     black-box
  -----------------------------------------------------------------------

The critic fears that formalization will freeze ethics, making it rigid
and unresponsive. Layer 5\'s response is that the
alternative---unformalized AI ethics---is worse. Without explicit
constraints, we get:

- Opaque models making life-affecting decisions

- No accountability when things go wrong

- No mechanism for democratic input

- No way to test whether stated principles are actually followed

Layer 5 does not claim to capture all of ethics. It claims to make the
enforceable part auditable. The rest remains in the domain of human
judgment---but now that domain has a boundary.

## 8.8 What Rawls Would Actually Want

We speculate that Rawls himself might have approved of Layer 5, for
these reasons:

1.  Rawls valued procedural justice---the fairness of the process, not
    just outcomes. Layer 5\'s governance framework ensures translation
    models are produced through legitimate deliberation.

2.  Rawls sought to make justice \'political, not
    metaphysical\'---independent of controversial comprehensive
    doctrines. Layer 5 is similarly neutral about which framework is
    correct.

3.  Rawls wanted principles that could be publicly justified to all
    citizens. Machine-checkable constraints are maximally
    public---anyone can read and test them.

4.  Rawls worried about stability. Versioned, DAG-structured policies
    enable evolution without rupture.

The veil of ignorance was Rawls\'s attempt to formalize fairness. Layer
5 is an attempt to formalize the implementation of whatever principles
emerge from behind the veil.

We honor Rawls not by refusing to formalize, but by formalizing
well---with humility, transparency, and explicit acknowledgment of what
lies beyond formalization.

# 9. Conclusion

## 9.1 What We Achieved

This whitepaper introduced a modular, DAG-based architecture for the
Translation Layer:

- Policy Modules: Self-contained, versioned, independently governable
  units

- DAG Structure: Explicit dependencies enabling topological ordering and
  conflict detection

- Hierarchical Organization: Vertical (abstraction levels) and
  horizontal (domain specialization)

- Complete EU Mapping: All seven requirements translated with
  dependencies

- Validation Framework: Module-level, DAG-level, and preservation
  testing

- Governance Model: Lifecycle management, versioning, change propagation

## 9.2 Why Modularity Matters

The modular architecture enables:

- Incremental Adoption: Organizations can adopt modules one at a time

- Composition: Combine EU Guidelines with GDPR, sector-specific rules,
  or organizational policies

- Auditability: Each module has clear provenance and governance

- Evolution: Update individual modules without disrupting the whole
  framework

- Reuse: Common concepts (e.g., informed consent) defined once, used
  everywhere

## 9.3 The DAG as Contract

The dependency DAG is not just implementation detail---it is a normative
statement about the structure of ethical requirements. When we say
\"Accountability depends on Transparency,\" we are making a claim about
the conceptual relationships within the EU\'s ethical framework.

This structure can be debated, refined, and governed---but it cannot be
ignored. The DAG makes implicit dependencies explicit and testable.

## 9.4 Future Work

- Formal verification of DAG properties (confluence, termination)

- Automated translation assistance using LLMs with human review

- Cross-framework conflict resolution strategies

- Dynamic policy composition for context-dependent requirements

- Integration with Layer 3 (GUASS) enforcement mechanisms

**--- END OF WHITEPAPER ---**
