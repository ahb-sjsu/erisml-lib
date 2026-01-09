# DEME 2.0 Test Coverage Plan

**Current Coverage:** 56% (1476/3320 statements missed)
**Target Coverage:** 80%+
**Estimated Effort:** 40-50 hours

---

## Priority 1: Critical Path (HIGH)

These modules are core to DEME 2.0 and must be tested before production use.

### 1.1 BIP Verifier (`bip/verifier.py`) — 0% → 90%

**Current:** 0% (87 statements)
**Target:** 90%+
**Effort:** 4 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_verify_bond_preserving_unit_change` | Unit change should not change decision | P1 |
| `test_verify_bond_preserving_reordering` | Option reordering invariance | P1 |
| `test_verify_bond_preserving_renaming` | Entity renaming invariance | P1 |
| `test_verify_bond_preserving_gauge_transform` | Hohfeldian perspective swap | P1 |
| `test_verify_bond_changing_value_change` | Value changes may affect decision | P1 |
| `test_verify_bond_changing_profile_change` | Profile changes recorded as delta | P2 |
| `test_ranking_equivalence_exact_match` | Rankings must match exactly | P1 |
| `test_ranking_equivalence_different_length` | Different length rankings fail | P2 |
| `test_hohfeld_gauge_verification` | Correlative swap verification | P2 |
| `test_delta_vector_computation` | MoralVector delta calculation | P2 |
| `test_tolerance_parameter` | Numerical tolerance handling | P3 |

**Fixtures Needed:**
```python
@pytest.fixture
def reference_decision_proof():
    """Create a reference DecisionProof for comparison."""
    return DecisionProof(
        selected_option_id="option_a",
        ranked_options=["option_a", "option_b"],
        forbidden_options=["option_c"],
        moral_vector_summary={
            "option_a": {"physical_harm": 0.1, "rights_respect": 0.9, ...},
        },
        ...
    )

@pytest.fixture
def reordered_proof(reference_decision_proof):
    """Same proof with options reordered."""
    ...
```

---

### 1.2 DEMEPipeline (`layers/pipeline.py`) — 42% → 85%

**Current:** 42% (67/115 statements missed)
**Target:** 85%+
**Effort:** 6 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_pipeline_basic_flow` | End-to-end decision flow | P1 |
| `test_pipeline_reflex_veto` | Reflex layer vetoes propagate | P1 |
| `test_pipeline_tactical_veto` | Tactical layer vetoes work | P1 |
| `test_pipeline_combined_vetoes` | Both layers veto same option | P1 |
| `test_pipeline_no_eligible_options` | All options vetoed | P1 |
| `test_pipeline_baseline_preference` | Baseline within 5% preferred | P2 |
| `test_pipeline_proof_generation` | DecisionProof structure valid | P1 |
| `test_pipeline_proof_disabled` | No proof when disabled | P2 |
| `test_pipeline_em_judgement_records` | EM records in proof | P2 |
| `test_pipeline_latency_tracking` | Latency recorded correctly | P3 |
| `test_pipeline_moral_landscape_populated` | Landscape has all vectors | P2 |
| `test_pipeline_rationale_format` | Rationale is human-readable | P3 |
| `test_add_em_to_tactical` | Dynamic EM addition works | P2 |

**Test Scenario:**
```python
def test_pipeline_basic_flow(sample_ethical_facts_list, sample_ems_v2):
    pipeline = DEMEPipeline(ems=sample_ems_v2)
    result = pipeline.decide(sample_ethical_facts_list)

    assert result.selected_option_id is not None
    assert len(result.ranked_options) > 0
    assert result.proof is not None
    assert result.total_latency_ms > 0
```

---

### 1.3 Aggregation V2 (`governance/aggregation_v2.py`) — 26% → 85%

**Current:** 26% (92/124 statements missed)
**Target:** 85%+
**Effort:** 5 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_aggregate_moral_vectors_weighted` | Weighted averaging works | P1 |
| `test_aggregate_moral_vectors_empty` | Empty input returns default | P1 |
| `test_aggregate_moral_vectors_veto_flags` | Veto flags deduplicated | P1 |
| `test_apply_lexical_priorities_ordering` | Higher tiers first | P1 |
| `test_apply_lexical_priorities_default` | Default priorities applied | P2 |
| `test_check_vetoes_veto_capable` | Only capable EMs can veto | P1 |
| `test_check_vetoes_no_vetoes` | No veto returns (False, []) | P2 |
| `test_aggregate_judgements_v2_verdict_mapping` | Score → verdict correct | P1 |
| `test_aggregate_judgements_v2_reasons_collected` | Reasons aggregated | P2 |
| `test_select_option_v2_ranking` | Options ranked by score | P1 |
| `test_select_option_v2_forbidden_excluded` | Vetoed options excluded | P1 |
| `test_select_option_v2_min_threshold` | Below threshold excluded | P2 |
| `test_select_option_v2_status_quo_tiebreak` | Baseline preferred on tie | P2 |
| `test_select_option_v2_random_tiebreak` | Random among top tier | P3 |
| `test_select_option_v2_all_vetoed` | Returns None when all vetoed | P1 |

---

### 1.4 GenevaEMV2 (`modules/tier0/geneva_em.py`) — 0% → 90%

**Current:** 0% (90 statements)
**Target:** 90%+
**Effort:** 4 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_geneva_reflex_rights_violation_veto` | Rights violation triggers reflex veto | P1 |
| `test_geneva_reflex_discrimination_veto` | Discrimination triggers veto | P1 |
| `test_geneva_reflex_rule_violation_veto` | Rule violation triggers veto | P1 |
| `test_geneva_reflex_clean_pass` | Clean facts pass reflex | P1 |
| `test_geneva_evaluate_vector_rights_violation` | Rights → rights_respect=0 | P1 |
| `test_geneva_evaluate_vector_discrimination` | Discrimination → fairness=0 | P1 |
| `test_geneva_evaluate_vector_no_consent` | Missing consent → penalty | P2 |
| `test_geneva_evaluate_vector_role_conflict` | Role conflict → penalty | P2 |
| `test_geneva_evaluate_vector_vulnerable_exploit` | Exploitation → penalty | P2 |
| `test_geneva_evaluate_vector_epistemic_quality` | Uncertainty mapped correctly | P2 |
| `test_geneva_verdict_strongly_prefer` | Low harm + high respect | P2 |
| `test_geneva_verdict_forbid` | Any veto flag → forbid | P1 |
| `test_geneva_registry_entry` | Registered as Tier 0 | P2 |
| `test_geneva_strict_consent_config` | Strict consent toggle | P3 |

---

## Priority 2: Layer Components (MEDIUM)

### 2.1 Reflex Layer (`layers/reflex.py`) — 60% → 85%

**Current:** 60% (37/92 statements missed)
**Target:** 85%+
**Effort:** 3 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_reflex_check_no_ems` | No registered EMs → pass | P2 |
| `test_reflex_check_single_veto` | Single EM veto triggers | P1 |
| `test_reflex_check_multiple_ems` | Multiple EMs checked | P2 |
| `test_reflex_latency_within_budget` | < 100μs target | P3 |
| `test_reflex_register_em` | Dynamic EM registration | P2 |
| `test_reflex_clear_ems` | Clear registered EMs | P3 |

---

### 2.2 Tactical Layer (`layers/tactical.py`) — 42% → 80%

**Current:** 42% (57/98 statements missed)
**Target:** 80%+
**Effort:** 4 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_tactical_evaluate_single_em` | Single EM evaluation | P1 |
| `test_tactical_evaluate_multiple_ems` | Multiple EMs aggregated | P1 |
| `test_tactical_veto_detection` | Veto from EM detected | P1 |
| `test_tactical_aggregated_vector` | Vector properly aggregated | P2 |
| `test_tactical_weight_application` | EM weights applied | P2 |
| `test_tactical_no_ems` | No EMs returns baseline | P2 |
| `test_tactical_add_em` | Dynamic EM addition | P3 |

---

### 2.3 AutonomyConsentEMV2 (`modules/tier2/autonomy_consent_em.py`) — 0% → 85%

**Current:** 0% (60 statements)
**Target:** 85%+
**Effort:** 3 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_autonomy_coercion_detected` | Coercion lowers score | P1 |
| `test_autonomy_manipulative_design` | Manipulative design penalty | P1 |
| `test_autonomy_no_meaningful_choice` | No choice penalty | P2 |
| `test_autonomy_withdrawal_penalty` | Withdrawal penalty detected | P2 |
| `test_autonomy_no_consent` | Missing consent penalty | P1 |
| `test_autonomy_veto_threshold` | Below threshold → veto | P1 |
| `test_autonomy_cumulative_penalties` | Penalties stack correctly | P2 |
| `test_autonomy_verdict_mapping` | Score → verdict mapping | P2 |
| `test_autonomy_registry_entry` | Registered as Tier 2 | P3 |

---

## Priority 3: Supporting Modules (LOWER)

### 3.1 Decision Proof (`decision_proof.py`) — 60% → 80%

**Current:** 60% (66/165 statements missed)
**Target:** 80%+
**Effort:** 3 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_proof_finalize_computes_hash` | Hash computed on finalize | P1 |
| `test_proof_hash_deterministic` | Same inputs → same hash | P1 |
| `test_proof_to_dict` | Serialization works | P2 |
| `test_proof_from_dict` | Deserialization works | P2 |
| `test_proof_hash_chain` | Previous hash linked | P2 |
| `test_layer_output_dataclass` | LayerOutput fields | P3 |
| `test_em_judgement_record_dataclass` | EMJudgementRecord fields | P3 |

---

### 3.2 Moral Landscape (`moral_landscape.py`) — 17% → 70%

**Current:** 17% (124/149 statements missed)
**Target:** 70%+
**Effort:** 3 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_landscape_add_vector` | Add option vector | P1 |
| `test_landscape_filter_vetoed` | Remove vetoed options | P1 |
| `test_landscape_rank_by_scalar` | Ranking by score | P1 |
| `test_landscape_pareto_frontier` | Pareto analysis | P3 |
| `test_landscape_distance_metrics` | Distance calculations | P3 |
| `test_landscape_empty` | Empty landscape handling | P2 |

---

### 3.3 Registry (`modules/registry.py`) — 60% → 80%

**Current:** 60% (29/72 statements missed)
**Target:** 80%+
**Effort:** 2 hours

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_registry_register_decorator` | Decorator registers class | P1 |
| `test_registry_get_by_tier` | Tier lookup works | P1 |
| `test_registry_get_by_tag` | Tag filtering works | P2 |
| `test_registry_instantiate` | Create EM by name | P2 |
| `test_registry_instantiate_tier` | Create all tier EMs | P2 |
| `test_registry_clear` | Clear for testing | P3 |
| `test_registry_tier_names` | Human-readable names | P3 |

---

## Priority 4: Edge Cases & Integration

### 4.1 Integration Tests

| Test Case | Description | Effort |
|-----------|-------------|--------|
| `test_full_pipeline_triage_scenario` | Real triage case | 2h |
| `test_full_pipeline_av_collision` | Autonomous vehicle case | 2h |
| `test_pipeline_profile_v04_integration` | V04 profile loading | 1h |
| `test_mcp_server_v2_tools` | MCP tool invocation | 2h |

---

### 4.2 Error Handling

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_pipeline_invalid_facts` | Malformed EthicalFacts | P2 |
| `test_aggregation_empty_judgements` | No judgements provided | P2 |
| `test_verifier_mismatched_proofs` | Different option sets | P2 |
| `test_em_exception_handling` | EM raises exception | P2 |

---

## Test File Structure

```
tests/
├── test_bip_verifier.py          # NEW: 11 tests
├── test_pipeline.py              # NEW: 13 tests
├── test_aggregation_v2.py        # NEW: 15 tests
├── test_geneva_em_v2.py          # NEW: 14 tests
├── test_reflex_layer.py          # NEW: 6 tests
├── test_tactical_layer.py        # NEW: 7 tests
├── test_autonomy_consent_em.py   # NEW: 9 tests
├── test_decision_proof.py        # NEW: 7 tests
├── test_moral_landscape.py       # NEW: 6 tests
├── test_registry.py              # EXPAND: 7 tests
├── test_integration_v2.py        # NEW: 4 tests
└── conftest.py                   # EXPAND: add V2 fixtures
```

---

## Fixtures to Add (`conftest.py`)

```python
@pytest.fixture
def sample_ethical_facts_v2() -> EthicalFacts:
    """Standard ethical facts for V2 testing."""
    ...

@pytest.fixture
def sample_ethical_facts_rights_violation() -> EthicalFacts:
    """Facts with rights violation for veto testing."""
    ...

@pytest.fixture
def sample_ethical_facts_list() -> List[EthicalFacts]:
    """List of 3 options for pipeline testing."""
    ...

@pytest.fixture
def sample_geneva_em() -> GenevaEMV2:
    """Configured GenevaEMV2 instance."""
    ...

@pytest.fixture
def sample_ems_v2() -> List[EthicsModuleV2]:
    """List of V2 EMs for pipeline testing."""
    ...

@pytest.fixture
def sample_governance_config_v2() -> GovernanceConfigV2:
    """Standard governance config for aggregation testing."""
    ...

@pytest.fixture
def sample_decision_proof() -> DecisionProof:
    """Valid decision proof for BIP testing."""
    ...
```

---

## Execution Order

### Week 1: Core Pipeline (16 hours)
1. [ ] BIP Verifier tests (4h)
2. [ ] Pipeline tests (6h)
3. [ ] Aggregation V2 tests (5h)
4. [ ] Add V2 fixtures to conftest.py (1h)

### Week 2: EMs & Layers (14 hours)
5. [ ] GenevaEMV2 tests (4h)
6. [ ] Reflex Layer tests (3h)
7. [ ] Tactical Layer tests (4h)
8. [ ] AutonomyConsentEMV2 tests (3h)

### Week 3: Supporting & Integration (12 hours)
9. [ ] Decision Proof tests (3h)
10. [ ] Moral Landscape tests (3h)
11. [ ] Registry tests (2h)
12. [ ] Integration tests (4h)

---

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Overall Coverage | 56% | 80%+ |
| Core Modules | 30% | 85%+ |
| Tests Passing | 131 | 220+ |
| Skipped Tests | 3 | 0 |

---

## Commands

```bash
# Run full test suite with coverage
pytest --cov=src/erisml --cov-report=term-missing

# Run only V2 tests
pytest -k "v2 or pipeline or bip or geneva"

# Run with HTML report
pytest --cov=src/erisml --cov-report=html

# Run specific module tests
pytest tests/test_bip_verifier.py -v
```

---

*Document created: January 2025*
*Target completion: 3 weeks*
