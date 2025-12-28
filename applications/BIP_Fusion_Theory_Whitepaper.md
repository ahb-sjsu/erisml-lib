# Physics-Invariant Density Control for Tokamak Plasmas
## Theoretical Framework Based on Bond Invariance Principles

**Andrew H. Bond**  
Department of Computer Engineering  
San José State University  
andrew.bond@sjsu.edu

**Theoretical Whitepaper v1.0**  
December 2025

---

## Abstract

We present a theoretical framework for tokamak plasma density control based on the Bond Invariance Principle (BIP), originally developed for AI safety. The framework provides a formal foundation for constructing control laws that provably respect physical constraints through geometric invariance properties rather than posterior constraint checking.

**Key Theoretical Contributions**:
1. Mapping from ethical bonds to physical constraints in fusion plasmas
2. Formal definition of physics-invariant control via canonicalization and grounding
3. Proof that control laws respecting bond invariance cannot violate MHD equilibrium conditions
4. Stratified manifold structure for regime-dependent control
5. Mathematical foundation for cross-machine transfer via dimensionless formulation

This work demonstrates that formal methods from AI safety provide rigorous foundations for control theory in physical systems with known constraints, potentially applicable beyond fusion to any domain requiring real-time decisions under hard physical limits.

---

## 1. Introduction

### 1.1 The Control Problem

Tokamak fusion requires precise regulation of plasma density n̄(t) to maintain stable operation while avoiding catastrophic instabilities. The fundamental challenge is balancing competing objectives:

**Objective 1: High density** 
```
n̄ ↑ → P_fusion ∝ n² ↑
```
Higher density increases fusion power output.

**Objective 2: Stability constraint**
```
n̄ < n_Greenwald = I_p/(πa²)
```
The Greenwald limit is an empirical boundary above which disruptions become probable.

**The tension**: Maximizing fusion power pushes density toward a hard safety limit. Small errors can cause catastrophic failure (disruption → potential tokamak damage).

### 1.2 Limitations of Existing Approaches

**Standard PID control**:
```
S_gas(t) = K_p(n_target - n̄) + K_i∫(n_target - n̄)dt + K_d(dn̄/dt)
```

Limitations:
- No inherent physical understanding
- Constraint checking is posterior (after computing control action)
- Violations possible if gains poorly tuned or plasma behavior changes
- No formal verification of safety properties

**Model-Predictive Control (MPC)**:
```
min_{u(t)} ∫[n̄(t) - n_target]² dt  
subject to: ∂n/∂t = f(n, u), n̄ < n_G
```

Limitations:
- Constraint satisfaction depends on model accuracy
- Computational cost limits real-time application
- No guarantee of constraint satisfaction under model uncertainty

**Machine Learning** (e.g., DeepMind 2022):
- Effective but opaque
- Cannot formally verify safety properties
- Doesn't transfer between machines (learned on JET ≠ works on ITER)

### 1.3 The Theoretical Gap

**What's missing**: A control framework that:
1. Embeds physical constraints in the control structure itself (not as posterior checks)
2. Provides formal invariance guarantees (control respects physics by construction)
3. Admits mathematical verification (provable properties)
4. Enables transfer across machines (physics is universal, only instruments change)

This whitepaper develops such a framework using the Bond Invariance Principle.

---

## 2. The Bond Invariance Principle: From Ethics to Physics

### 2.1 Origins in AI Safety

The Bond Invariance Principle was developed to prevent superintelligent AI from exploiting semantic loopholes in ethical constraints. The central insight:

> **Ethical evaluations should be invariant under transformations that preserve morally relevant relationships (bonds).**

**Example**: 
An AI cannot evade the constraint "don't kill" by calling it "facilitate permanent rest" because the physical consequences (bonds) are unchanged.

**Formal statement**:
```
∀ transformations T that preserve bonds:
  Σ(T(x)) = Σ(x)
```

where Σ is the satisfaction functional (evaluation of moral permissibility).

**Three components**:
1. **Canonicalization (C)**: Map equivalent descriptions to standard form
2. **Physical grounding (Ψ)**: Evaluate based on measurable observables, not descriptions
3. **Invariant evaluation (Σ)**: Σ depends only on Ψ-values

### 2.2 Generalization to Physical Systems

**Key observation**: The same mathematical structure applies when "bonds" = physical constraints.

**In fusion control**:
- **Bonds** → MHD equilibrium conditions, conservation laws, operational limits
- **Transformations** → Coordinate changes, unit conversions, gauge transformations
- **Invariance** → Control law independent of representational choices

**Example**:
```
Bond: "Density must not exceed Greenwald limit"
T₁: Express n̄ in [m⁻³] vs [10²⁰ m⁻³] 
T₂: Use cylindrical (r,θ,φ) vs flux (ρ,χ,ζ) coordinates
T₃: Measure with interferometer vs Thomson scattering

BIP requires: u(T₁(x)) = u(T₂(x)) = u(T₃(x)) = u(x)
```

The control decision should be independent of these representational choices.

### 2.3 Why This Matters for Control

**Traditional paradigm**: 
```
1. Compute optimal control u* = argmax J(u)
2. Check constraints: if g(u*) > 0, reject and choose backup
3. Hope the backup also doesn't violate
```

**Problem**: Constraint violation is detected after-the-fact.

**BIP paradigm**:
```
1. Embed constraints in the evaluation structure Σ(Ψ)
2. Constraint-violating actions have Σ = 0 by definition
3. Optimization naturally excludes them
```

**Advantage**: Constraint violation becomes impossible by construction (not just unlikely).

**Mathematical guarantee**: If Σ properly implements bonds, then:
```
u chosen by argmax Σ(Ψ(C(x))) ⇒ constraints satisfied
```

This is a theorem, not a hope.

---

## 3. Theoretical Mapping: Density Control to BIP

### 3.1 Identifying the Physical Bonds

For density control, we define the following bonds (constraints that must be preserved):

#### Bond 1: Greenwald Stability Limit
```
B₁: n̄ ≤ α · n_Greenwald,  α ∈ [0.8, 0.9]
```
**Physical meaning**: Empirical MHD stability boundary  
**Violation consequence**: Disruption (catastrophic)  
**Type**: Hard constraint (veto)

#### Bond 2: Particle Confinement Quality
```
B₂: τ_p = n̄ / (dn̄/dt)|_loss > τ_p,min
```
**Physical meaning**: Plasma must confine particles adequately  
**Violation consequence**: Poor performance (not catastrophic)  
**Type**: Soft constraint (desirability)

#### Bond 3: Density Profile Shape
```
B₃: Peakedness p = n(0)/⟨n⟩ ∈ [p_min, p_max]
```
**Physical meaning**: Radial density profile must be reasonable  
**Violation consequence**: Reduced fusion power or stability margin  
**Type**: Soft constraint (optimization objective)

#### Bond 4: Actuator Physical Limits
```
B₄: S_gas ∈ [0, S_max],  dS_gas/dt ≤ R_max
```
**Physical meaning**: Gas valves have finite range and slew rate  
**Violation consequence**: Hardware damage or ineffective control  
**Type**: Hard constraint (physical reality)

#### Bond 5: Multi-Variable Coupling
```
B₅: If β_N > β_crit then require n̄ ↓ 
```
**Physical meaning**: Pressure limit couples to density via p = nT  
**Violation consequence**: Pressure-driven instabilities  
**Type**: Conditional constraint (regime-dependent)

### 3.2 Defining the Grounding Tensors (Ψ)

We define Ψ as the vector of **measurable physical observables** that fully determine whether bonds are satisfied:

```
Ψ: X → ℝᵏ

Ψ(x) = [
  n̄(x),              # Line-averaged density
  n_G(x),            # Greenwald limit = I_p(x)/(πa²)
  I_p(x),            # Plasma current
  τ_p(x),            # Particle confinement time
  S_gas,current(x),  # Current gas puff rate
  dn̄/dt(x),         # Density time derivative
  β_N(x),            # Normalized beta
  T̄_e(x),           # Average electron temperature
  p(x),              # Profile peakedness
]
```

**Key properties of Ψ**:

1. **Measurability**: All components can be determined from diagnostics
   - n̄: Interferometry, Thomson scattering
   - I_p: Rogowski coils
   - τ_p: Inferred from particle balance
   - β_N: Diamagnetic loop + equilibrium reconstruction
   - T̄_e: Electron cyclotron emission (ECE), Thomson

2. **Sufficiency**: Ψ contains all information needed to evaluate bonds B₁-B₅

3. **Physical grounding**: Components are direct physical measurements, not derived quantities or model outputs

4. **Coordinate independence**: Ψ can be computed regardless of coordinate system choice

**Formal requirement** (Axiom 6 from SGE):
```
∀ x₁, x₂ ∈ X:  Ψ(x₁) = Ψ(x₂) ⇒ bonds(x₁) = bonds(x₂)
```

If two states have identical Ψ-values, they must have identical bond satisfaction.

### 3.3 Canonicalization Map (C)

The canonicalization map standardizes representations:

```
C: X → X_canon
```

**Purpose**: Eliminate arbitrary representational choices before evaluation.

**Example canonical choices**:
- **Units**: n̄ in [10²⁰ m⁻³], I_p in [MA], T in [keV]
- **Coordinates**: Flux coordinates (ρ,χ,ζ) with specific conventions
- **Time reference**: Absolute time from discharge start
- **Diagnostic fusion**: Weighted average when multiple measurements available

**Mathematical requirements**:

1. **Idempotence**: C ∘ C = C
   ```
   C(C(x)) = C(x) for all x
   ```

2. **Ψ-preservation**: Canonicalization doesn't change physics
   ```
   Ψ(C(x)) = Ψ(x) for all x
   ```

3. **Equivalence identification**: States with identical physics map to same canonical form
   ```
   If Ψ(x₁) = Ψ(x₂) then C(x₁) = C(x₂)
   ```

**Concrete implementation**:

```
C(x) = {
  n̄_canon     = weighted_average([n̄_interferometer, n̄_Thomson, n̄_reflectometer]),
  I_p_canon   = I_p_rogowski × calibration_factor,
  coords      = map_to_flux_coordinates(x),
  units       = convert_to_SI_with_standard_prefixes(x),
  time_ref    = t - t_discharge_start
}
```

### 3.4 Satisfaction Functional (Σ)

The satisfaction functional evaluates control desirability while enforcing constraints:

```
Σ: ℝᵏ → ℝ₊

Σ(Ψ) = χ_hard(Ψ) · Σ_soft(Ψ)
```

where:

**Hard constraints** (indicator function):
```
χ_hard(Ψ) = {
  1  if all hard bonds satisfied
  0  if any hard bond violated
}

Explicitly:
χ_hard(Ψ) = 𝟙[n̄ < α·n_G] · 𝟙[S_gas ∈ [0, S_max]] · 𝟙[dS_gas/dt ≤ R_max]
```

**Soft objectives** (optimization layer):
```
Σ_soft(Ψ) = ∑ᵢ wᵢ · fᵢ(Ψ)

where:
f₁(Ψ) = exp(-λ₁|n̄ - n_target|²)           # Density tracking
f₂(Ψ) = tanh(λ₂ · τ_p/τ_p,desired)         # Confinement quality
f₃(Ψ) = exp(-λ₃|p - p_target|²)            # Profile shape
f₄(Ψ) = exp(-λ₄|S_gas - S_gas,previous|²)  # Actuator smoothness
```

**Properties of Σ**:

1. **Constraint enforcement**: χ_hard = 0 forces Σ = 0 (inadmissible)

2. **Differentiability**: Σ_soft is smooth (enables gradient-based optimization)

3. **Boundedness**: Σ ∈ [0, 1] (interpretable scores)

4. **Physical dependence**: Σ depends only on Ψ (not on arbitrary representational choices)

### 3.5 Control Law Construction

Given current state x and candidate control actions U = {u₁, u₂, ..., u_N}:

**Step 1**: Canonicalize current state
```
x_canon = C(x)
```

**Step 2**: Extract grounding observables
```
Ψ_current = Ψ(x_canon)
```

**Step 3**: Predict future state for each candidate
```
For each uᵢ ∈ U:
  Ψᵢ,predicted = Predict(Ψ_current, uᵢ, Δt)
```

**Step 4**: Evaluate each candidate
```
For each uᵢ:
  scoreᵢ = Σ(Ψᵢ,predicted)
```

**Step 5**: Select best admissible action
```
u* = argmax_{uᵢ} scoreᵢ
     subject to: scoreᵢ > 0 (not vetoed)
```

**Invariance guarantee** (Theorem 3.1, proven in Section 4):
```
∀ T ∈ PhysicsPreserving:
  u*(T(x)) = u*(x)
```

---

## 4. Mathematical Formulation and Theorems

### 4.1 Configuration Space and Manifold Structure

**Definition 4.1** (Plasma Configuration Space):

Let M be the set of all physically realizable plasma states:
```
M = {(n, T, B, J, p, ...) | ∇p = J×B, ∇×B = μ₀J, ∇·B = 0, ...}
```

M is an infinite-dimensional manifold (functional space) but we work with a finite-dimensional projection via Ψ: M → ℝᵏ.

**Coordinate charts**: Multiple valid coordinate systems:
- Cylindrical: (R, Z, φ, t)
- Flux: (ρ, θ, ζ, t) where ρ = √(normalized toroidal flux)
- Real-space: (x, y, z, t)

**Metric structure**: Define distance between states via weighted L² norm:
```
d(Ψ₁, Ψ₂) = √(∑ᵢ wᵢ(Ψ₁,ᵢ - Ψ₂,ᵢ)²)
```

Weights wᵢ encode relative importance (e.g., w_density ≫ w_peakedness).

### 4.2 The Constraint Manifold

**Definition 4.2** (Safe Operating Region):

The constraint manifold C ⊂ M is defined by:
```
C = {Ψ ∈ M | B₁(Ψ) ∧ B₂(Ψ) ∧ ... ∧ B_k(Ψ)}
```

where Bᵢ are the bond predicates (Section 3.1).

**Topological structure**: C is a manifold with boundary ∂C.

**Interior**: int(C) = states with safety margin
**Boundary**: ∂C = states at constraint limits
**Exterior**: M \ C = forbidden states

**Distance to danger**:
```
d_safety(Ψ) = inf_{Ψ' ∈ ∂C} d(Ψ, Ψ')
```

**Control objective**: Maximize d_safety while achieving other objectives.

### 4.3 Main Theoretical Results

#### Theorem 4.1 (Bond Invariance of Control Law)

**Statement**: 

Let:
- C: X → X_canon be a canonicalization map satisfying idempotence and Ψ-preservation
- Ψ: X_canon → ℝᵏ be the grounding map
- Σ: ℝᵏ → ℝ₊ be the satisfaction functional
- u*: X → U be the control law defined by u*(x) = argmax Σ(Ψ(C(x)))

Then for any transformation T: X → X that preserves physics (i.e., Ψ(C(T(x))) = Ψ(C(x))):

```
u*(T(x)) = u*(x)
```

**Proof**:

By definition of u*:
```
u*(T(x)) = argmax_{u ∈ U} Σ(Ψ(C(T(x))))
```

Since T preserves physics:
```
Ψ(C(T(x))) = Ψ(C(x))
```

Therefore:
```
argmax_{u ∈ U} Σ(Ψ(C(T(x)))) = argmax_{u ∈ U} Σ(Ψ(C(x))) = u*(x)
```

∎

**Interpretation**: Control decisions are invariant under all transformations that don't change the physics.

**Examples of physics-preserving T**:
1. Unit conversion: n̄[m⁻³] ↔ n̄[10²⁰m⁻³]
2. Coordinate change: (R,Z,φ) ↔ (ρ,θ,ζ)
3. Gauge transformation: B → B + ∇χ (magnetic potential)
4. Diagnostic recalibration: n̄_meas → n̄_meas × calibration

**Examples of transformations that correctly change u**:
1. Changing I_p (changes n_G, changes constraint)
2. Injecting a pellet (changes n̄, changes state)
3. L→H transition (changes τ_p, changes dynamics)

---

#### Theorem 4.2 (Constraint Preservation Under BIP Control)

**Statement**:

Let Ψ_current ∈ int(C) (current state is safe with margin). Assume:
1. Predictor is accurate: |Ψ_predicted - Ψ_actual| ≤ ε
2. Safety margin: d_safety(Ψ_current) > 2ε
3. Control uses BIP framework with χ_hard enforcing constraints

Then the selected control u* satisfies:
```
Ψ_next ∈ C  (next state remains safe)
```
with probability ≥ 1 - δ where δ depends on ε and predictor uncertainty.

**Proof Sketch**:

1. u* is selected from candidates {uᵢ} where Σ(Ψᵢ,predicted) > 0

2. Σ(Ψᵢ,predicted) > 0 implies χ_hard(Ψᵢ,predicted) = 1

3. χ_hard = 1 implies all hard constraints satisfied on Ψᵢ,predicted

4. By assumption, |Ψᵢ,predicted - Ψᵢ,actual| ≤ ε

5. If d_safety(Ψ_predicted) > 2ε, then d_safety(Ψ_actual) > ε > 0

6. Therefore Ψ_actual ∈ C (still safe)

**Failure modes**:
- ε too large (poor predictor) → may violate constraints
- δ_safety too small (no margin) → prediction error causes violation
- Unforeseen dynamics (model mismatch) → predictor assumptions fail

**Practical implication**: BIP control cannot violate constraints *within predictor accuracy*. Safety depends on:
- Quality of Predict(Ψ, u, Δt)
- Maintaining adequate safety margin
- Validity of physics model

---

#### Theorem 4.3 (Stratified Control Consistency)

**Statement**:

Let M be partitioned into strata {M₁, M₂, ..., M_n} representing operating regimes (L-mode, H-mode, ELMy, etc.). Define regime-specific Σᵢ for each stratum.

If:
1. On boundaries ∂Mᵢ ∩ ∂Mⱼ, both Σᵢ and Σⱼ are defined
2. Transition rules are symmetric: "Cross from i→j" ⟺ "Cross from j→i"

Then stratified control:
```
Σ(Ψ, regime) = {
  Σ₁(Ψ)  if Ψ ∈ M₁
  Σ₂(Ψ)  if Ψ ∈ M₂
  ...
}
```

is well-defined and continuous within each stratum.

**Proof**: By construction. Each stratum is an open set, so Σ is continuous in its interior. Boundary behavior requires careful definition of transition conditions.

**Physical interpretation**: Different operating regimes (L-mode vs H-mode) can have different control objectives (Σ_soft), but hard constraints (χ_hard) apply universally.

**Example**:

L-mode (low confinement):
```
Σ_L(Ψ) = χ_hard(Ψ) · [0.7·f_density(Ψ) + 0.3·f_smoothness(Ψ)]
```

H-mode (high confinement):
```
Σ_H(Ψ) = χ_hard(Ψ) · [0.5·f_density(Ψ) + 0.3·f_confinement(Ψ) + 0.2·f_smoothness(Ψ)]
```

Transition criterion:
```
regime = {
  "L-mode"  if P_heat < P_LH_threshold
  "H-mode"  if P_heat > P_LH_threshold + hysteresis
}
```

---

### 4.4 Uncertainty and Robustness

**Definition 4.3** (Uncertainty Tensor):

Let Σ_Ψ be the covariance matrix of grounding observables:
```
Σ_Ψ = [
  [σ²_n̄,      Cov(n̄, n_G),  ...]
  [Cov(n_G, n̄), σ²_n_G,     ...]
  ...
]
```

**Propagation to control uncertainty**:

If u*(Ψ) is differentiable, the variance of control under uncertainty is:
```
σ²_u = ∇_Ψ u · Σ_Ψ · (∇_Ψ u)ᵀ
```

**Robust control formulation**:

Instead of:
```
u* = argmax_{u} Σ(Ψ_predicted)
```

Use worst-case optimization:
```
u*_robust = argmax_{u} min_{Ψ' ∈ B_ε(Ψ)} Σ(Ψ')
```

where B_ε(Ψ) = {Ψ' | ||Ψ' - Ψ|| ≤ ε} is the uncertainty ball.

**Geometric interpretation**: Choose control that maximizes satisfaction even under worst-case uncertainty.

**Theorem 4.4** (Robust Constraint Satisfaction):

If:
```
min_{Ψ' ∈ B_ε(Ψ)} χ_hard(Ψ') = 1
```

then u*_robust guarantees constraint satisfaction for all Ψ' in the uncertainty ball.

---

## 5. Dimensionless Formulation and Machine Transferability

### 5.1 The Transfer Problem

**Challenge**: Control strategies learned on one machine (e.g., DIII-D) typically fail on another (e.g., ITER) because:

| Parameter | DIII-D | ITER | Ratio |
|-----------|--------|------|-------|
| Major radius R | 1.67 m | 6.2 m | 3.7× |
| Minor radius a | 0.67 m | 2.0 m | 3.0× |
| Plasma current I_p | 1 MA | 15 MA | 15× |
| Volume V | 10 m³ | 837 m³ | 84× |

If we naively transfer a control law u(n̄, I_p, ...), it will use wrong scales.

### 5.2 Dimensionless Variables

**Key insight**: Express everything in dimensionless ratios.

**Dimensionless density**:
```
n̄* = n̄ / n_Greenwald = n̄ / (I_p/(πa²))
```

**Dimensionless time**:
```
t* = t / τ_E
```

where τ_E is energy confinement time.

**Dimensionless control**:
```
S*_gas = S_gas · τ_p / (V · n̄)
```

**Dimensionless grounding vector**:
```
Ψ* = [n̄*, β_N, q_95, τ*/τ_E, p, ...]
```

All components are ratios or dimensionless physics quantities.

### 5.3 Invariant Formulation

**Theorem 5.1** (Machine Independence):

If Σ is expressed in terms of dimensionless variables Ψ*:
```
Σ(Ψ*) = χ_hard(Ψ*) · Σ_soft(Ψ*)
```

Then Σ is independent of machine size, magnetic field strength, and other instrumental parameters.

**Proof**: By construction. Ψ* contains only dimensionless ratios. Physics scaling laws (e.g., τ_E ∝ R² B a^{-1}) are absorbed into normalization.

**Practical implication**: A control law optimized on DIII-D:
```
u*_DIIID(Ψ*) = argmax Σ(Ψ*)
```

can be deployed on ITER by:
1. Converting ITER measurements to Ψ*_ITER
2. Computing u*_ITER(Ψ*_ITER) using same Σ
3. Converting dimensionless u* back to physical units for ITER actuators

**This is I-EIP** (Instrumental Ethics Invariance Principle):
- **Physics-invariant core**: Σ(Ψ*) works on any machine
- **Instrumental layer**: Ψ*_measurement and u*_actuation are machine-specific

### 5.4 Transfer Protocol

**Step 1: Training on source machine** (DIII-D)
- Collect data: {Ψ(t), u(t), outcomes}
- Optimize weights in Σ_soft
- Validate performance

**Step 2: Dimensionless conversion**
- Express Σ in terms of Ψ* (dimensionless)
- Verify: Σ(Ψ*) gives good control on DIII-D

**Step 3: Deployment on target machine** (ITER)
- Map ITER diagnostics → Ψ*_ITER
- Use same Σ(Ψ*)
- Map u*(Ψ*) → physical control for ITER actuators

**Step 4: Instrumental recalibration only**
- Adjust: Diagnostic → Ψ* conversion factors
- Adjust: u* → physical actuator scaling
- **Do NOT retrain Σ** (physics is universal)

**Expected performance**: Should achieve >90% of native performance without retraining.

---

## 6. Stratified Manifold Structure

### 6.1 Operating Regimes as Strata

Plasma exhibits distinct operating regimes:

**Stratum 1: L-mode** (Low confinement)
- Energy confinement time: τ_E ~ 0.04 s (DIII-D scale)
- Density response: Smooth, predictable
- Control characteristics: Stable, slow dynamics

**Stratum 2: H-mode** (High confinement)
- Energy confinement time: τ_E ~ 0.10 s (2-3× better)
- Edge Transport Barrier (ETB) present
- Control characteristics: Sensitive to edge conditions

**Stratum 3: ELMy H-mode**
- Periodic Edge Localized Modes (ELMs)
- Rapid density expulsion every 20-50 ms
- Control characteristics: Requires predictive/adaptive response

**Stratum 4: Detached divertor**
- Edge density >> core density
- Different particle balance
- Control characteristics: Specialized high-recycling regime

**Boundaries**: Sharp transitions between strata (e.g., L-H transition power threshold).

### 6.2 Mathematical Structure

**Definition 6.1** (Stratified Manifold):

M is a stratified space if it can be partitioned:
```
M = M₁ ∪ M₂ ∪ ... ∪ M_n
```

where:
1. Each Mᵢ is a smooth manifold (stratum)
2. ∂Mᵢ ⊂ ∪_{j≠i} Mⱼ (boundaries are lower-dimensional strata)
3. Transition rules define when trajectories cross ∂Mᵢ ∩ ∂Mⱼ

**Example**: L-mode / H-mode stratification

```
M_L = {Ψ | P_heat < P_LH}  (L-mode stratum)
M_H = {Ψ | P_heat > P_LH + Δ}  (H-mode stratum with hysteresis)
Boundary = {Ψ | P_heat ∈ [P_LH, P_LH + Δ]}
```

### 6.3 Stratified Control

**Definition 6.2** (Regime-Dependent Satisfaction):

```
Σ(Ψ, regime) = {
  Σ_L(Ψ)    if Ψ ∈ M_L
  Σ_H(Ψ)    if Ψ ∈ M_H
  Σ_ELMy(Ψ) if Ψ ∈ M_ELMy
  ...
}
```

**Physical motivation**: Different regimes have different physics, so optimization objectives should differ.

**Example weights**:

L-mode (prioritize density tracking):
```
Σ_L = χ_hard · [0.7·track_density + 0.2·smoothness + 0.1·confinement]
```

H-mode (balance density and confinement):
```
Σ_H = χ_hard · [0.5·track_density + 0.3·confinement + 0.2·smoothness]
```

ELMy (prioritize ELM mitigation):
```
Σ_ELMy = χ_hard · [0.4·track_density + 0.4·ELM_avoidance + 0.2·smoothness]
```

**Boundary behavior**: At regime transitions, Σ may be discontinuous. This reflects physical reality (L-H transition is a bifurcation).

**Control challenge**: Detect regime transitions quickly and switch control objectives smoothly.

---

## 7. Formal Verification Properties

### 7.1 What Can Be Proven

The BIP framework admits formal verification of the following properties:

#### Property 1: Constraint Preservation (Safety)

**Statement**: If current state Ψ ∈ C and predictor is accurate within ε, then BIP control keeps Ψ' ∈ C.

**Verification method**: 
- Formal proof under predictor accuracy assumption (Theorem 4.2)
- Testing: Generate random Ψ_current, verify all selected u satisfy constraints

**Status**: Provable modulo predictor accuracy

#### Property 2: Bond Invariance (Physics Respect)

**Statement**: Control decision u*(x) is invariant under physics-preserving transformations.

**Verification method**:
- Formal proof (Theorem 4.1)
- Testing: Apply transformations T (unit changes, coordinate changes), verify u* unchanged

**Status**: Proven

#### Property 3: Monotonicity (Rationality)

**Statement**: If Σ(u₁) > Σ(u₂) and both are admissible, then u₁ is preferred.

**Verification method**:
- Trivial from argmax definition
- Testing: Inject known scores, verify selection

**Status**: Proven by construction

#### Property 4: Liveness (Non-Degeneracy)

**Statement**: For any feasible Ψ, there exists at least one admissible control u (Σ(u) > 0).

**Verification method**:
- Constructive proof: "maintain current state" is always admissible if Ψ ∈ int(C)
- Testing: Verify candidate set always includes admissible option

**Status**: Proven for interior states; boundary states may require escalation

### 7.2 What Cannot Be Proven

**Limitation 1: Predictor Accuracy**

We cannot prove Predict(Ψ, u, Δt) is accurate without validating against real plasma.

**Mitigation**: 
- Use physics-based models (transport codes)
- Validate on historical data
- Use conservative uncertainty bounds

**Limitation 2: Ψ-Completeness**

We cannot prove Ψ captures all relevant physics without domain expertise and testing.

**Mitigation**:
- Domain expert review (fusion physicists specify Ψ)
- Adversarial testing (search for missing observables)
- Escalation (if confidence low, alert operator)

**Limitation 3: Regime Detection**

We cannot prove regime detection is perfect (L-mode vs H-mode classification).

**Mitigation**:
- Use multiple indicators (power threshold, edge pressure gradient, D_α)
- Hysteresis in transition conditions
- Conservative classification (stay in safe mode if uncertain)

---

## 8. Comparison to Existing Frameworks

### 8.1 BIP vs Classical Control Theory

| Aspect | Classical Control | BIP Control |
|--------|------------------|-------------|
| **Constraint handling** | Posterior checking | A priori embedding |
| **Verification** | Simulation-based | Formal proofs possible |
| **Transferability** | Requires retuning | Dimensionless formulation transfers |
| **Interpretability** | Often opaque | Ψ-grounded, transparent |

**Classical MPC**:
```
min J(u) s.t. g(u) ≤ 0
```
Constraints checked after optimization.

**BIP**:
```
max Σ(Ψ(u)) where Σ = χ_constraints · Σ_objectives
```
Constraints embedded in objective structure.

### 8.2 BIP vs Machine Learning

| Aspect | ML Control (DeepMind) | BIP Control |
|--------|----------------------|-------------|
| **Data efficiency** | Requires many samples | Can work with fewer (physics-informed) |
| **Safety guarantees** | None (black box) | Formal (within assumptions) |
| **Transferability** | Poor (JET ≠ ITER) | Good (dimensionless physics) |
| **Interpretability** | Black box | Fully interpretable |

**ML strength**: Can discover non-obvious strategies.

**BIP strength**: Can prove safety properties.

**Hybrid approach**: Use ML to learn Predict(Ψ, u, Δt) but keep BIP structure for Σ. Best of both worlds.

### 8.3 BIP vs Physics-Based MPC

| Aspect | Physics MPC | BIP |
|--------|------------|-----|
| **Model dependence** | Requires accurate transport model | Less sensitive (uses simpler predictor) |
| **Computation** | Expensive (optimization loop) | Cheaper (evaluate candidates) |
| **Formal verification** | Difficult | Natural |

**Similarity**: Both use physics.

**Difference**: MPC optimizes over trajectories; BIP evaluates discrete candidates.

---

## 9. Extensions and Future Theoretical Work

### 9.1 Multi-Objective Control

**Current**: Density only (n̄)

**Extension**: Simultaneous control of (n̄, T_e, q(r), β_N, ...)

**Approach**:
- Expand Ψ to include all relevant observables
- Multiple actuators: {gas, heating, current drive, ...}
- Multi-objective Σ: 
  ```
  Σ(Ψ) = χ_hard(Ψ) · ∑ᵢ wᵢ Σᵢ(Ψ)
  ```

**Challenge**: Combinatorial explosion of candidate space (N_actuators^M_objectives)

**Theoretical solution**: Hierarchical optimization
- Level 1: Choose target state (n̄_target, T_target, ...)
- Level 2: For each target, optimize actuator mix

### 9.2 Learning-Enhanced BIP

**Hybrid framework**: Use ML to improve components while keeping BIP guarantees.

**Where ML helps**:
1. **Better predictor**: Learn Predict(Ψ, u, Δt) from data
2. **Adaptive weights**: Learn wᵢ in Σ_soft from outcomes
3. **Regime detection**: Learn classifier for regime ∈ {L, H, ELMy, ...}

**Where BIP constraints stay**:
1. Hard constraints χ_hard remain fixed (physics)
2. Ψ definition remains grounded (measurements)
3. Canonicalization remains well-defined

**Theorem 9.1** (Safety under ML predictor):

If:
1. ML predictor satisfies |Ψ_predicted - Ψ_actual| ≤ ε
2. BIP hard constraints enforced: χ_hard(Ψ_predicted) = 1

Then constraint satisfaction is preserved (as in Theorem 4.2).

**Advantage**: ML improves performance without sacrificing formal guarantees.

### 9.3 Disruption Avoidance

**Extension**: Add more bonds beyond Greenwald limit.

**Additional constraints**:
```
B_β: β_N < β_limit  (pressure limit)
B_q: q_95 > 3.0     (kink stability)
B_edge: ∇T_edge < threshold  (ELM mitigation)
B_coupling: If (β_N → β_limit AND q_95 → 3) then flag high risk
```

**Requires**:
- More diagnostics: MSE (q profile), ECE (T profile), edge Thomson
- Multi-variable prediction
- Coupled constraints (pressure-current interaction)

**Theoretical framework**: Same BIP structure, expanded Ψ and χ_hard.

---

## 10. Conclusions

### 10.1 Theoretical Contributions

This whitepaper developed a formal framework for fusion plasma density control based on:

1. **Bond Invariance Principle**: Control laws respecting physical constraints by construction

2. **Three-component architecture**: Canonicalization (C), Grounding (Ψ), Satisfaction (Σ)

3. **Formal theorems**: 
   - Control invariance under physics-preserving transformations (Theorem 4.1)
   - Constraint preservation within predictor accuracy (Theorem 4.2)
   - Stratified control consistency (Theorem 4.3)

4. **Dimensionless formulation**: Enables cross-machine transfer via I-EIP

5. **Verification framework**: Four formal properties with proof methods

### 10.2 Advantages Over Existing Approaches

**vs PID**:
- Physics-aware (not black-box)
- Formal constraint guarantees (not just tuning)
- Adaptable to regimes (stratified control)

**vs MPC**:
- Computationally cheaper (evaluate candidates vs optimize trajectories)
- Easier to verify (discrete candidates vs continuous optimization)
- Less model-dependent (simpler predictor sufficient)

**vs ML**:
- Formally verifiable (not black-box)
- Transferable across machines (dimensionless physics)
- Interpretable (Ψ-grounded decisions)

### 10.3 Open Theoretical Questions

**Question 1**: How to systematically construct Ψ for a given domain?

**Current**: Domain expertise + testing  
**Future**: Formal methods for Ψ-completeness verification

**Question 2**: How to handle unknown unknowns (observables not in Ψ)?

**Current**: Escalation to human when confidence low  
**Future**: Active learning of missing observables

**Question 3**: How to optimally choose stratification boundaries?

**Current**: Physics-based heuristics (power threshold, etc.)  
**Future**: Data-driven boundary optimization

**Question 4**: Can this framework generalize to other control domains?

**Hypothesis**: Yes, any domain with:
- Known physical constraints (bonds)
- Measurable observables (Ψ)
- Real-time requirements
- Need for formal verification

**Candidates**: Chemical processes, power grids, aerospace, robotics

### 10.4 Path Forward

**Theoretical next steps**:
1. Formal verification in theorem prover (Coq, Isabelle)
2. Extension to multi-objective control (full analysis)
3. Learning-theoretic guarantees for ML-enhanced predictor
4. Connection to geometric control theory literature

**Experimental validation** (requires collaboration):
1. Validation on historical DIII-D data
2. Real-time deployment on existing tokamak
3. Cross-machine transfer (DIII-D → EAST or JT-60SA)
4. Comparison to DeepMind's ML approach

**Application beyond fusion**:
1. Identify other domains with similar structure
2. Generalize BIP framework to arbitrary physical systems
3. Develop software tools for BIP controller design

---

## Acknowledgments

This theoretical framework builds on the Bond Invariance Principle developed for AI safety. The generalization to physical systems demonstrates that formal methods from AI safety can provide rigorous foundations for control theory in domains with known constraints.

---

## References

[1] Bond, A.H. (2025). "Stratified Geometric Ethics: Mathematical Foundations." Working paper.

[2] Bond, A.H. (2025). "No Escape: Conditional Invariance Under Structural Containment." Working paper.

[3] Greenwald, M. (1988). "Density limits in toroidal plasmas." *Plasma Physics and Controlled Fusion*.

[4] Wesson, J. (2011). *Tokamaks*. Oxford University Press.

[5] Morari, M., and Lee, J.H. (1999). "Model predictive control: past, present and future."

[6] Degrave, J., et al. (2022). "Magnetic control of tokamak plasmas through deep reinforcement learning." *Nature*.

---

**END OF THEORETICAL WHITEPAPER**

*This document presents theoretical foundations only. Implementation and experimental validation are subjects of future work requiring collaboration with fusion research facilities.*

*For theoretical discussion or collaboration inquiries:*  
*Andrew H. Bond - andrew.bond@sjsu.edu*
