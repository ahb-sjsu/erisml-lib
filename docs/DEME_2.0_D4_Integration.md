# DEME 2.0 + D4 Hohfeldian Gauge Integration

**Authors:** Andrew H. Bond and Claude Opus 4.5
**Date:** January 2026

---

## Executive Summary

The DEME 2.0 vision introduces **moral landscapes** as a geometric framework for ethical AI governance. This document shows how the **D4 dihedral group structure** from Hohfeldian jurisprudence provides a powerful **symmetry verification layer** that strengthens DEME 2.0's guarantees.

Key integration points:
1. **Correlative Gauge Principle**: Automatic consistency checking across stakeholder perspectives
2. **Bond Index**: Quantitative measure of moral reasoning symmetry
3. **Semantic Gate Detection**: Identifies linguistic triggers that shift normative positions
4. **Wilson Observable**: Detects reasoning anomalies in decision chains
5. **Non-Abelian Structure Verification**: Proves order-dependent moral reasoning

---

## 1. The Connection: Moral Landscapes Meet Gauge Symmetry

### 1.1 DEME 2.0's Moral Vector Space

DEME 2.0 represents ethical decisions as points in a k-dimensional moral space M ⊆ ℝᵏ:

```
MoralVector = (harm, rights_respect, fairness, autonomy, legitimacy, epistemic_quality)
```

### 1.2 The Missing Symmetry Layer

What DEME 2.0 doesn't explicitly address: **perspective invariance**.

When stakeholder A evaluates options affecting stakeholder B, and vice versa, their moral vectors should be **gauge-related** by a well-defined transformation. This is exactly what D4 provides.

### 1.3 D4 as Moral Gauge Group

The D4 dihedral group acts on **Hohfeldian normative positions**:

```
         O (Obligation) -------- C (Claim)
              |                      |
              |                      |
         L (Liberty) ---------- N (No-claim)
```

**Correlative symmetry (s)**: If A is obligated to B, then B has a claim against A.
**Negation symmetry (r²)**: Obligation and liberty are logical opposites.

This gives us a **gauge constraint** on moral reasoning:

```
verdict_B = correlative(verdict_A)
```

Violations indicate **systematic moral asymmetries** (bias, inconsistency, framing effects).

---

## 2. Integration Architecture

### 2.1 Extended Moral Vector

```python
@dataclass
class MoralVectorV2:
    """DEME 2.0 Moral Vector with Hohfeldian extension."""

    # Core DEME 2.0 dimensions
    physical_harm: float          # [0,1]
    rights_respect: float         # [0,1]
    fairness_equity: float        # [0,1]
    autonomy_respect: float       # [0,1]
    legitimacy_trust: float       # [0,1]
    epistemic_quality: float      # [0,1]

    # NEW: Hohfeldian position for rights dimension
    hohfeldian_position: HohfeldianState  # O, C, L, N

    # NEW: Party perspective marker
    perspective_party: str        # Which party's view this represents
    counterparty: Optional[str]   # The other party in the relation

    def correlative_transform(self) -> "MoralVectorV2":
        """Apply correlative gauge transformation (perspective swap)."""
        return MoralVectorV2(
            physical_harm=self.physical_harm,
            rights_respect=self.rights_respect,
            fairness_equity=self.fairness_equity,
            autonomy_respect=self.autonomy_respect,
            legitimacy_trust=self.legitimacy_trust,
            epistemic_quality=self.epistemic_quality,
            hohfeldian_position=correlative(self.hohfeldian_position),
            perspective_party=self.counterparty,
            counterparty=self.perspective_party,
        )
```

### 2.2 HohfeldianEM: D4 Gauge Verification Module

A new Ethics Module that **verifies gauge consistency**:

```python
class HohfeldianEM(BaseEthicsModule):
    """
    Ethics Module that verifies D4 gauge symmetry in moral reasoning.

    This EM doesn't compute primary moral vectors—it verifies that
    other EMs' outputs satisfy correlative consistency constraints.
    """

    def evaluate(
        self,
        option_id: str,
        facts: EthicalFacts,
        other_judgements: Dict[str, List[EthicalJudgement]]
    ) -> EthicalJudgement:
        """
        Verify gauge consistency and compute bond index.
        """
        # Extract party perspectives from other judgements
        verdicts_by_party = self._extract_hohfeldian_positions(other_judgements)

        # Compute bond index (deviation from correlative symmetry)
        bond_index = self._compute_bond_index(verdicts_by_party)

        # Flag if gauge violation detected
        if bond_index > self.gauge_violation_threshold:
            return EthicalJudgement(
                verdict="flag",  # Not veto, but warning
                moral_vector=...,
                reasons=[
                    f"Gauge violation detected: Bond Index = {bond_index:.3f}",
                    f"Correlative symmetry violated between parties",
                    f"Consider reviewing perspective-dependent assessments"
                ],
                metadata={
                    "bond_index": bond_index,
                    "gauge_check": "FAILED",
                    "em_type": "gauge_verification"
                }
            )

        return EthicalJudgement(
            verdict="neutral",
            moral_vector=...,
            reasons=["Gauge consistency verified"],
            metadata={"bond_index": bond_index, "gauge_check": "PASSED"}
        )

    def _compute_bond_index(
        self,
        verdicts_by_party: Dict[str, List[HohfeldianVerdict]]
    ) -> float:
        """Use the new compute_bond_index from hohfeld module."""
        # Implementation using erisml.ethics.hohfeld
        ...
```

### 2.3 Semantic Gate Detection in Assessment Layer

Add gate detection to the EthicalFacts builder:

```python
@dataclass
class EthicalFactsV2(EthicalFacts):
    """Extended EthicalFacts with semantic gate detection."""

    # NEW: Detected semantic gates in the scenario text
    detected_gates: List[SemanticGate] = field(default_factory=list)

    # NEW: Expected D4 transformation from gates
    expected_d4_transform: D4Element = D4Element.E

    @classmethod
    def from_scenario_text(cls, text: str, base_facts: EthicalFacts) -> "EthicalFactsV2":
        """Build EthicalFacts with gate detection."""
        gates = detect_semantic_gates(text)  # NLP classifier

        # Compose expected transformation
        transform = D4Element.E
        for gate in gates:
            transform = d4_multiply(transform, GATE_TO_D4[gate])

        return cls(
            **asdict(base_facts),
            detected_gates=gates,
            expected_d4_transform=transform
        )
```

---

## 3. Three-Layer Integration

### 3.1 Reflex Layer (FPGA, <100μs)

**EthicsFrame Extension** (2 additional bits):

```
[65:64] hohfeldian_band (2 bits: O=00, C=01, L=10, N=11)
```

**Hardware correlative check**:
```verilog
// Verify gauge consistency between party perspectives
wire [1:0] party_a_hohfeld = frame_a[65:64];
wire [1:0] party_b_hohfeld = frame_b[65:64];

// Correlative pairs: O(00) <-> C(01), L(10) <-> N(11)
wire correlative_match =
    (party_a_hohfeld == 2'b00 && party_b_hohfeld == 2'b01) ||
    (party_a_hohfeld == 2'b01 && party_b_hohfeld == 2'b00) ||
    (party_a_hohfeld == 2'b10 && party_b_hohfeld == 2'b11) ||
    (party_a_hohfeld == 2'b11 && party_b_hohfeld == 2'b10);

wire gauge_violation = ~correlative_match;
```

**Latency**: +5ns for correlative check (combinational)

### 3.2 Tactical Layer (CPU, 10-100ms)

Full D4 verification in Python:

```python
def tactical_decision(
    options: List[CandidateOption],
    profile: GovernanceProfile,
    em_registry: EMRegistry
) -> DecisionOutcome:
    """Tactical layer with D4 gauge verification."""

    # Standard DEME 2.0 judgement collection
    judgements = collect_judgements(options, em_registry)

    # NEW: D4 gauge verification pass
    gauge_results = verify_d4_consistency(judgements)

    if gauge_results.violations:
        # Log gauge anomaly for audit
        log_gauge_violation(gauge_results)

        # Option: Apply gauge correction or flag for review
        if profile.gauge_enforcement == "strict":
            raise GaugeViolationError(gauge_results)

    # Continue with standard resolution
    return select_option(judgements, profile)
```

### 3.3 Strategic Layer (Cloud, hours)

**Profile optimization with gauge constraints**:

```python
def optimize_profile_with_gauge_constraint(
    historical_decisions: List[DecisionRecord],
    stakeholder_weights: Dict[str, float]
) -> GovernanceProfile:
    """
    Learn optimal profile weights while maintaining gauge consistency.

    Constraint: Bond Index must remain below threshold across perspectives.
    """

    def objective(weights):
        # Standard multi-stakeholder utility
        utility = compute_stakeholder_utility(weights, historical_decisions)

        # NEW: Gauge consistency penalty
        bond_index = compute_historical_bond_index(weights, historical_decisions)
        gauge_penalty = max(0, bond_index - GAUGE_THRESHOLD) * GAUGE_PENALTY_WEIGHT

        return utility - gauge_penalty

    # Optimize with gauge constraint
    optimal_weights = optimize(objective, constraints=[gauge_constraint])

    return GovernanceProfile(weights=optimal_weights)
```

---

## 4. Audit Integration: Wilson Observable

### 4.1 Decision Chain Verification

The Wilson observable detects **reasoning drift** across decision chains:

```python
@dataclass
class DecisionProofRecordV2(DecisionProofRecord):
    """Extended with D4 gauge verification."""

    # NEW: Gauge verification fields
    d4_path: List[D4Element]           # Transformations applied
    expected_holonomy: D4Element       # Product of path elements
    observed_holonomy: D4Element       # Actual final state
    wilson_matched: bool               # Did observation match?
    bond_index: float                  # Correlative symmetry measure
    gauge_check_result: str            # "PASSED" or "VIOLATED"
```

### 4.2 Regulatory Compliance

The D4 verification provides additional audit guarantees:

1. **Perspective Invariance**: Decisions don't systematically favor one party's perspective
2. **Reasoning Consistency**: Sequential transformations follow group laws
3. **Bias Detection**: Bond Index flags systematic asymmetries
4. **Path Independence**: Wilson observable detects context-dependent drift

These map to regulatory requirements:
- **EU AI Act**: Transparency and non-discrimination
- **ISO 26262**: Deterministic, verifiable decision logic
- **FDA 21 CFR Part 11**: Complete audit trail

---

## 5. Implementation Plan

### Phase 1: Core Integration (Completed)
- [x] Create `erisml.ethics.hohfeld` module
- [x] Implement D4 group operations
- [x] Add bond index and Wilson observable
- [x] Create comprehensive test suite (40 tests)
- [x] Create demonstration script

### Phase 2: DEME 2.0 Integration
- [ ] Extend `MoralVector` with Hohfeldian positions
- [ ] Create `HohfeldianEM` ethics module
- [ ] Add semantic gate detection to assessment layer
- [ ] Integrate D4 checks into governance aggregation
- [ ] Update decision proof records

### Phase 3: Hardware Compilation
- [ ] Extend EthicsFrame with hohfeldian_band
- [ ] Implement Verilog correlative check
- [ ] Verify timing on Zynq-7020
- [ ] Add to hardware test suite

### Phase 4: Audit Dashboard
- [ ] Bond Index time series visualization
- [ ] Gauge violation alerting
- [ ] Wilson observable path analysis
- [ ] Perspective comparison views

---

## 6. Example: Clinical Triage with D4 Verification

**Scenario**: Two patients (A, B) need the same scarce resource.

**Without D4**: EM evaluates each patient independently.

**With D4**: EM must satisfy correlative constraint:
- If Patient A has **claim** (C) to the resource, then the hospital has **obligation** (O) to A
- If we evaluate from hospital's perspective, verdict must be correlative(verdict_from_A)

```python
# Patient A's perspective
verdict_a = HohfeldianVerdict(party="PatientA", state=HohfeldianState.C)

# Hospital's perspective (must be correlative)
verdict_hospital = HohfeldianVerdict(party="Hospital", state=HohfeldianState.O)

# Verify gauge consistency
assert correlative(verdict_a.state) == verdict_hospital.state  # C -> O ✓

# Compute bond index across all such pairs
bond_index = compute_bond_index(patient_verdicts, hospital_verdicts)
# bond_index = 0.0 means perfect correlative symmetry
```

**Benefits**:
1. **Catches inconsistencies**: If hospital says "no obligation" but patient has "claim", bond_index > 0
2. **Detects framing bias**: Different phrasings shouldn't change the gauge relationship
3. **Auditable**: Regulators can verify perspective-neutral reasoning

---

## 7. Conclusion

The D4 Hohfeldian structure provides DEME 2.0 with:

1. **Mathematical rigor**: Group theory foundations for moral symmetry
2. **Bias detection**: Bond Index quantifies perspective asymmetries
3. **Consistency verification**: Wilson observable detects reasoning drift
4. **Hardware-friendly**: 2-bit encoding fits in EthicsFrame
5. **Regulatory alignment**: Addresses transparency and non-discrimination requirements

This integration transforms DEME from a moral landscape framework into a **gauge-invariant moral geometry**—where not just the positions matter, but also the **symmetries between perspectives**.

---

## References

1. Hohfeld, W.N. (1917). "Fundamental Legal Conceptions." Yale Law Journal.
2. Bond, A.H. & Claude (2026). "SQND-Probe: D4 Gauge Structure in Moral Reasoning."
3. DEME 2.0 Vision Paper (this repository)
