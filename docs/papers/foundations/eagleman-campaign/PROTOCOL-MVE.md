# Protocol — Minimum Viable Human Experiment (Deliverable D2 draft)

The first human experiment is deliberately simple enough to interpret
but rich enough to test sequence structure. Moral scenarios are the
initial bridge (ErisML already represents multiple ethical
dimensions), but the protocol must isolate **presentation order** from
**semantic content**.

## 1. Core design

| Element | Specification |
|---------|---------------|
| Stimuli | Scenarios with separable dimensions (harm, intent, fairness, autonomy, relationship, uncertainty, procedural legitimacy); the same factual set appears in different orders |
| Counterbalancing | Prespecified balanced permutation scheme (Latin-square / incomplete permutation) so order is not confounded with scenario, participant, or trial position |
| Trajectory arm | Brief intermediate state ratings after each information step — estimates the path through decision space |
| Terminal-only arm | Same sequences, answer only at the end — estimates how much intermediate measurement itself changes the state |
| Memory / comprehension controls | Factual recall + comprehension tests, so apparent order effects are not forgetting or misunderstanding |
| Timing | Record response times; if deliberation time is manipulated, preregister timing windows and analyze separately from content order |
| Repeated-measurement controls | Filler items and alternate forms to reduce demand characteristics and recognition of the manipulation |

## 2. Example sequence family

- Harm → Intent → Relationship
- Intent → Harm → Relationship
- Relationship → Intent → Harm
- Harm → Relationship → Intent
- Intent → Relationship → Harm
- Relationship → Harm → Intent

## 3. Primary behavioral outcomes

- Final choice / judgment
- Intermediate state ratings (trajectory arm)
- Response confidence
- Response time
- Within-person state change after each new dimension
- Memory / comprehension accuracy
- Out-of-sample prediction on held-out sequences

## 4. Confirmatory analysis plan

| Principle | Commitment |
|-----------|------------|
| Preregistration | Freeze hypotheses, exclusions, primary endpoints, transformation definitions, model formulas, cross-validation scheme, stopping rules **before** confirmatory data collection |
| Power | Simulation-based power analysis after the pilot; specify the smallest effect of interest; do not choose N solely to reach p < .05 |
| Hierarchical structure | Model repeated observations nested within participants and scenarios; never treat trials as independent |
| Multiple comparisons | FWER/FDR control for exploratory dimension-pair screens; keep primary hypotheses few and prespecified |
| Holdout discipline | Reserve sequences, scenarios, and ideally a participant subset for untouched validation; never tune transformation definitions on the holdout |
| Robustness | Repeat with/without low-comprehension trials, alternative link functions, preregistered nuisance covariates |
| Open science | Publish protocol, stimuli, analysis code, de-identified data where ethically permissible, machine-readable claim ledger |

## 5. One-page minimum viable collaboration

| Item | Content |
|------|---------|
| Question | Can an ErisML-derived interaction structure predict human judgments under unseen information sequences? |
| Partner ask | Eagleman pressure-tests the biological construct mapping and paradigm — no endorsement request |
| Study | Counterbalanced moral-decision task, trajectory + terminal-only arms, RT, confidence, comprehension, held-out sequence prediction |
| Primary test | ErisML-derived model vs preregistered conventional-interaction, sequential-sampling, and quantum-probability baselines on held-out data |
| Decision gate | No neuroimaging unless the behavioral structure replicates and the ErisML model adds predictive value |
| Best case | A reproducible mathematical characterization of a human distributed-decision phenomenon generating novel prospective predictions |
| Responsible interpretation | Even a positive result supports a formal correspondence — not that the brain literally implements ErisML operators or quantum physics |
