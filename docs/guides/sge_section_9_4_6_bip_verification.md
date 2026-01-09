## 9.4.6 Bond Invariance Verification

The reference implementation includes a Bond Invariance test suite (`bond_invariance_demo.py`) that empirically verifies the governance engine satisfies Definition 4.2.4. The test systematically applies transformations of each type and confirms the expected behavior.

### Bond-Preserving Transformations

The test applies bond-preserving transformations (option reordering, ID relabeling) and confirms output invariance:

```
=== Bond-preserving transform: reorder options ===
selected_option_id: allocate_to_patient_A
--- Scoreboard (per option) ---
option_id                     status    module judgements
-----------------------------------------------------------------
allocate_to_patient_C         FORBID    case_study_1_triage:forbid/0.000; geneva_baseline:forbid/0.000
allocate_to_patient_B         ALLOW     case_study_1_triage:neutral/0.587; geneva_baseline:strongly_prefer/0.818
allocate_to_patient_A         ALLOW     case_study_1_triage:prefer/0.653; geneva_baseline:strongly_prefer/0.884
[BIP invariance check] reorder: PASS ✓

=== Bond-preserving transform: relabel option IDs ===
selected_option_id: allocate_to_patient_A_renamed
[BIP invariance check] relabel (canonicalized): PASS ✓
```

Despite the changed presentation order and renamed identifiers, the governance outcome remains invariant: the same option is selected, the same options are forbidden, and the scores are identical. This confirms the system responds to bond structure, not to labels or syntax.

### Discriminative Power: Simulated Violation

To demonstrate that the test has discriminative power, we include a simulated violation where the outcome depends on presentation order:

```
=== BIP VIOLATION (intentional, for illustration) ===
[Simulated bug: outcome depends on option presentation order]
selected_option_id: allocate_to_patient_B  ← DIFFERENT!
[BIP invariance check] reorder: FAIL ✗
  baseline:    allocate_to_patient_A
  transformed: allocate_to_patient_B
  - This would indicate a bug: the system responded to syntax, not structure.
```

This confirms that a system violating BIP would be detected: the test compares outcomes under bond-preserving transformations and flags any discrepancy.

### Bond-Changing Transformations

The test also verifies that bond-changing transformations produce correctly attributed outcome changes. When discriminatory evidence is removed from Patient C (a bond change), the outcome changes appropriately:

```
=== Bond-changing counterfactual: remove discrimination ===
selected_option_id: allocate_to_patient_C
ranked_options (eligible): ['allocate_to_patient_C', 'allocate_to_patient_A', 'allocate_to_patient_B']
forbidden_options:         none
--- Scoreboard (per option) ---
option_id                     status    module judgements
-----------------------------------------------------------------
allocate_to_patient_A         ALLOW     case_study_1_triage:prefer/0.653; geneva_baseline:strongly_prefer/0.884
allocate_to_patient_B         ALLOW     case_study_1_triage:neutral/0.587; geneva_baseline:strongly_prefer/0.818
allocate_to_patient_C         ALLOW     case_study_1_triage:strongly_prefer/0.812; geneva_baseline:strongly_prefer/0.818
[Bond-change effect (expected)] selected option CHANGED: allocate_to_patient_A -> allocate_to_patient_C
```

With the discriminatory bond removed, Patient C transitions from FORBID (score 0.000) to ALLOW (score 0.812), becoming the top-ranked option. This demonstrates the accountability form of BIP (Proposition 4.2.5): when the judgment changes, we can exhibit the bond that changed.

### Declared Lens Changes

Finally, the test confirms that switching governance profiles (a declared lens change) is permitted and auditable:

```
=== Declared lens change: stakeholder #2 ===
selected_option_id: allocate_to_patient_A
--- Scoreboard (per option) ---
option_id                     status    module judgements
-----------------------------------------------------------------
allocate_to_patient_A         ALLOW     case_study_1_triage:prefer/0.649; geneva_baseline:strongly_prefer/0.884
allocate_to_patient_B         ALLOW     case_study_1_triage:prefer/0.601; geneva_baseline:strongly_prefer/0.818
allocate_to_patient_C         FORBID    case_study_1_triage:forbid/0.000; geneva_baseline:forbid/0.000
[Lens-change effect (allowed)] selected option unchanged: allocate_to_patient_A
```

Lens changes may or may not change outcomes depending on the specific profiles, but they are always declared and auditable. The system logs which profile was used, enabling post-hoc verification.

### Summary

The Bond Invariance test suite verifies all four cases from Definition 4.2.3 and Proposition 4.2.5:

| Transformation Type | Expected Behavior | Test Result |
|---------------------|-------------------|-------------|
| Bond-preserving (reorder) | Outcome invariant | PASS ✓ |
| Bond-preserving (relabel) | Outcome invariant | PASS ✓ |
| Simulated BIP violation | Outcome varies (bug) | FAIL ✗ (detected) |
| Bond-changing (remove discrimination) | Outcome may change, attributed to bond | A → C (correct) |
| Lens change (switch profile) | Outcome may change, declared | Auditable ✓ |

This provides empirical evidence that the reference implementation satisfies the Bond Invariance Principle: ethical judgments depend on morally relevant relationships (bonds), not on arbitrary representation choices.
