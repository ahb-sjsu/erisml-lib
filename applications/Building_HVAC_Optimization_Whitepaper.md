# Invariance-Based Verification for Building HVAC Optimization

## A Philosophy Engineering Approach to Multi-Stakeholder Energy Management and Grid-Interactive Buildings

---

**Technical Whitepaper v1.0 — December 2025**

**Andrew H. Bond**  
San José State University  
Ethical Finite Machines  
andrew.bond@sjsu.edu

---

> *"DeepMind achieved 40% energy reduction in Google's data centers. But Google owns the data centers, runs the sensors, and has one stakeholder. Real buildings have legacy BMS from 1995, three different sensor vendors, a landlord, tenants, a utility with demand response, and a city code inspector. The ML works. The governance is the problem."*

---

## Executive Summary

This whitepaper presents a complementary approach to ML-based HVAC optimization based on **representational invariance testing**—not to replace solutions like Google DeepMind's data center optimization, but to address the deployment challenges they face in real-world buildings with heterogeneous systems, multiple stakeholders, and emerging grid-interactive requirements.

We apply the **ErisML/DEME framework** (Epistemic Representation Invariance & Safety ML / Democratically Governed Ethics Modules) to building energy management, demonstrating how:

1. **The Bond Index (Bd)** can verify that ML-based HVAC controllers produce consistent decisions across legacy BMS representations, sensor configurations, and building types
2. **Declared transforms (G_declared)** map naturally to unit conversions, sensor substitution, zone aggregation, and building-to-building transfer
3. **The Decomposition Theorem** separates calibration issues (fixable) from fundamental model-building mismatches (requiring retraining)
4. **Democratic governance profiles (DEME)** allow conflicting stakeholder requirements (owners, tenants, utilities, regulators) to be composed and adjudicated transparently

**Key finding**: While individual HVAC optimization algorithms are well-developed, the challenge of **portfolio-scale deployment across heterogeneous buildings with multiple stakeholders** remains unsolved. Bond Index verification and DEME governance address this gap.

**Market opportunity**: The global building automation market exceeds $100B, but adoption of advanced ML-based optimization remains <5% of buildings. The barrier is not algorithm quality—it's deployment complexity, legacy system integration, and stakeholder conflict. ErisML/DEME addresses these barriers.

---

## Table of Contents

1. [Introduction: What DeepMind Got Right—and What Remains](#1-introduction-what-deepmind-got-right-and-what-remains)
2. [Background: Building HVAC and Current Practice](#2-background-building-hvac-and-current-practice)
3. [The Real Problem: Heterogeneity and Governance](#3-the-real-problem-heterogeneity-and-governance)
4. [The Invariance Framework for Building Systems](#4-the-invariance-framework-for-building-systems)
5. [Observables and Grounding (Ψ)](#5-observables-and-grounding-ψ)
6. [Declared Transforms (G_declared)](#6-declared-transforms-g_declared)
7. [The Bond Index for HVAC Controllers](#7-the-bond-index-for-hvac-controllers)
8. [Regime Transitions: Occupancy, Season, and Grid Events](#8-regime-transitions-occupancy-season-and-grid-events)
9. [Grid-Interactive Buildings: Where Stakes Get Higher](#9-grid-interactive-buildings-where-stakes-get-higher)
10. [Multi-Stakeholder Governance (DEME)](#10-multi-stakeholder-governance-deme)
11. [Case Study: University Campus Portfolio](#11-case-study-university-campus-portfolio)
12. [Implementation Architecture](#12-implementation-architecture)
13. [Deployment Pathway](#13-deployment-pathway)
14. [Limitations and Honest Assessment](#14-limitations-and-honest-assessment)
15. [Conclusion](#15-conclusion)
16. [References](#16-references)

---

## 1. Introduction: What DeepMind Got Right—and What Remains

### 1.1 The DeepMind Success Story

In 2016, Google DeepMind announced a remarkable achievement: using deep reinforcement learning to reduce energy consumption in Google's data centers by 40%. The approach was elegant:

1. **Rich observables**: Thousands of sensors measuring temperatures, pressures, power, cooling
2. **Clear objective**: Minimize PUE (Power Usage Effectiveness) while maintaining equipment safety
3. **Single stakeholder**: Google owns everything, makes all decisions
4. **Homogeneous infrastructure**: Data centers are purpose-built with modern, consistent systems
5. **Expert operators**: Trained staff available 24/7 to override if needed

This worked brilliantly. And it's been replicated in various forms by Verdigris, Turntide, BrainBox AI, and others.

### 1.2 Why the Same Approach Struggles in Commercial Buildings

But when companies try to apply similar ML-based optimization to typical commercial buildings, adoption remains surprisingly low (<5% of buildings use advanced ML optimization). Why?

| Factor | Google Data Center | Typical Commercial Building |
|--------|-------------------|----------------------------|
| **Sensor quality** | Purpose-built, calibrated | Legacy, often broken, inconsistent |
| **Data format** | Unified, modern | BACnet, Modbus, proprietary—mixed |
| **Stakeholders** | One (Google) | 3–10+ (owner, tenants, utility, regulator) |
| **Comfort tolerance** | Servers don't complain | Humans file complaints |
| **Objective** | Clear (minimize PUE) | Conflicting (cost vs. comfort vs. emissions) |
| **Upgrade authority** | Complete | Constrained by leases, budgets |
| **Age of systems** | <10 years | Often 20–30+ years |
| **Transfer** | Similar data centers | Every building is unique |

**The ML algorithm is not the bottleneck.** The bottleneck is:
1. **Representational heterogeneity**: Legacy BMS systems encode the same quantities differently
2. **Stakeholder conflict**: Owner wants savings; tenant wants comfort; utility wants demand response
3. **Transfer verification**: Does a model trained on Building A actually work on Building B?

### 1.3 Where ErisML/DEME Adds Value

This whitepaper argues that the Bond Index framework and DEME governance profiles address precisely these gaps:

| Problem | ErisML/DEME Solution |
|---------|---------------------|
| **Legacy BMS heterogeneity** | Bond Index verifies consistency across data representations |
| **Stakeholder conflict** | DEME profiles compose requirements with explicit priority and veto logic |
| **Transfer verification** | Bond Index tests whether model behavior is invariant to building-specific representation |
| **Regulatory compliance** | Declared transforms encode ASHRAE, building code requirements |
| **Grid integration** | DEME handles utility signals as stakeholder with specific constraints |

**We are not claiming to beat DeepMind's algorithm.** We are claiming to solve the deployment and governance problems that prevent DeepMind-class algorithms from scaling to millions of heterogeneous buildings.

### 1.4 Honest Assessment of Fit

Let's be direct about the limitations:

| Aspect | Fit for Bond Index | Notes |
|--------|-------------------|-------|
| **Hard constraints** | Moderate | Comfort is "soft"; equipment limits are harder |
| **Real-time criticality** | Low | Building thermal mass gives minutes–hours |
| **Life-safety stakes** | Low | Discomfort, not death (usually) |
| **Representational diversity** | High ✓ | Many sensor types, BMS systems, units |
| **Stakeholder complexity** | High ✓ | This is where DEME shines |
| **Portfolio scale** | High ✓ | Transfer learning verification is valuable |

**Conclusion**: HVAC is not the strongest fit for Bond Index safety verification (that's chemical reactors, power grids, AVs). But it's an excellent fit for **DEME multi-stakeholder governance** and for **verifying ML model transfer across heterogeneous buildings**.

---

## 2. Background: Building HVAC and Current Practice

### 2.1 The Building Energy Challenge

Buildings consume approximately 40% of global energy and produce 36% of energy-related CO₂ emissions. HVAC (Heating, Ventilation, and Air Conditioning) accounts for 40–60% of building energy use.

| Building Type | Energy Intensity (kBtu/ft²) | HVAC % | Annual Cost (100k ft²) |
|---------------|----------------------------|--------|------------------------|
| Office | 80–120 | 40% | $200–400K |
| Hospital | 200–400 | 50% | $500K–1M |
| Retail | 80–150 | 45% | $200–400K |
| Data center | 400–2000 | 60%+ | $1M–5M |
| University | 100–200 | 45% | $300–600K |

### 2.2 The HVAC Control Hierarchy

Modern buildings employ hierarchical control:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BUILDING HVAC HIERARCHY                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 4: Enterprise / Portfolio Management                    │
│           - Multi-building optimization                         │
│           - Utility coordination, demand response               │
│           - Capital planning                                    │
│           Timescale: Days to years                              │
│                         ▲                                       │
│  LAYER 3: Building Energy Management System (BEMS)              │
│           - Setpoint optimization                               │
│           - Schedule management                                 │
│           - Fault detection                                     │
│           Timescale: Minutes to hours                           │
│                         ▲                                       │
│  LAYER 2: Supervisory Control                                   │
│           - Zone coordination                                   │
│           - Equipment staging                                   │
│           - Economizer control                                  │
│           Timescale: Seconds to minutes                         │
│                         ▲                                       │
│  LAYER 1: Direct Digital Control (DDC)                          │
│           - PID loops (damper, valve, VFD)                      │
│           - Safety interlocks                                   │
│           - Equipment sequencing                                │
│           Timescale: Milliseconds to seconds                    │
│                         ▲                                       │
│  LAYER 0: Sensors & Actuators                                   │
│           - Temperature, humidity, CO2, pressure                │
│           - Dampers, valves, VFDs, compressors                  │
│           Timescale: Physical response                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Current State of ML-Based Optimization

| Solution | Approach | Claimed Savings | Deployment Scale |
|----------|----------|-----------------|------------------|
| **Google DeepMind** | Deep RL for data centers | 40% cooling | Google properties |
| **BrainBox AI** | Deep RL for commercial | 20–40% HVAC | 500+ buildings |
| **Turntide / GridPoint** | ML optimization | 10–30% | Thousands |
| **Verdigris** | AI load disaggregation | 15–25% | Hundreds |
| **Traditional MPC** | Model-predictive control | 15–25% | Thousands |

These solutions work. The question is why they haven't scaled to millions of buildings.

### 2.4 The Deployment Gap

```
Potential market:        ~100 million commercial buildings globally
Advanced ML penetration:   <5 million buildings
Addressable market:       ~95 million buildings

Barriers to adoption:
  - Legacy BMS incompatibility: 40%
  - Unclear ROI / measurement difficulty: 25%
  - Stakeholder conflict: 15%
  - Lack of skilled operators: 10%
  - Other: 10%
```

**The opportunity** is not in building a better algorithm—it's in building the verification, governance, and integration layer that enables existing algorithms to deploy at scale.

---

## 3. The Real Problem: Heterogeneity and Governance

### 3.1 The Legacy BMS Problem

A typical university campus might have:

```
Building A (built 1965): 
  - Pneumatic controls retrofitted with DDC in 2001
  - Johnson Controls Metasys N2 bus
  - Temperature in °F, setpoints as integers
  - Zone naming: "AHU-1-ZN-101"

Building B (built 1985):
  - Original DDC, upgraded in 2015
  - Honeywell Tridium/Niagara
  - Temperature in °C (European equipment)
  - Zone naming: "Floor1_Room_A"

Building C (built 2020):
  - Modern BACnet/IP
  - Mixed vendor (Siemens, Schneider)
  - Temperature in °F, high-resolution floats
  - Zone naming: per ASHRAE Guideline 36
```

An ML model trained on Building C's data representation will not work on Building A without careful translation. And **that translation introduces opportunities for representational inconsistency**.

### 3.2 The Multi-Stakeholder Problem

Consider a typical office building:

| Stakeholder | Priority | Requirement |
|-------------|----------|-------------|
| **Building Owner** | ROI | Minimize energy cost, maximize property value |
| **Property Manager** | Tenant satisfaction | No comfort complaints, fast response |
| **Tenant A (Law Firm)** | Comfort | 72°F ± 1°F, no exceptions, 24/7 |
| **Tenant B (Tech Startup)** | Cost | Keep it cheap, we'll wear sweaters |
| **Tenant C (Medical Office)** | Compliance | Strict temperature/humidity per regulation |
| **Utility (PG&E)** | Grid stability | Participate in demand response |
| **City (SF)** | Emissions | Comply with building performance standard |
| **HVAC Contractor** | Uptime | Don't burn out the equipment |

**Current approaches** either ignore this complexity (optimize for one objective) or hand-tune weights that no one understands or can audit.

**DEME governance profiles** make this explicit: each stakeholder's priorities, constraints, and veto powers are documented, versioned, and verifiable.

### 3.3 The Transfer Learning Problem

A common pitch: "We trained our model on 1,000 buildings—it will work on your building too!"

But does it? Transfer learning in ML is notoriously fragile. The Bond Index framework provides a way to **verify** that a model trained on Building A produces consistent behavior on Building B across the declared transform suite.

If Bd is low, transfer is working. If Bd is high, the model is producing inconsistent decisions based on building-specific representation artifacts, not physical differences.

---

## 4. The Invariance Framework for Building Systems

### 4.1 Core Definitions

**Definition 1 (Building State).** A building state σ is the complete specification of thermal and operational conditions:

```
σ = (zone_states, equipment_states, weather, grid_conditions, occupancy)
```

where:
- `zone_states = {(T_i, RH_i, CO2_i, occupancy_i)}`
- `equipment_states = {(status_j, power_j, efficiency_j)}`
- `weather = (T_outdoor, RH_outdoor, solar, wind)`
- `grid_conditions = (price, carbon_intensity, DR_event)`
- `occupancy = (schedule, actual_presence, forecast)`

**Definition 2 (Representation).** A representation r(σ) is a specific encoding of the building state:
- Unit system (°F vs. °C, CFM vs. L/s, kW vs. BTU/hr)
- BMS protocol (BACnet, Modbus, proprietary)
- Zone naming convention
- Sensor selection (which of redundant sensors)
- Aggregation level (zone, floor, building)
- Time resolution (1-min, 5-min, 15-min averages)

**Definition 3 (Control Decision).** A control decision function C maps representations to setpoints:

```
C: Representations → {setpoints, equipment_commands, mode_changes}
```

**Definition 4 (Declared Transform).** A declared transform g ∈ G_declared preserves the physical state while changing representation.

### 4.2 The Consistency Requirement

**Axiom (Representational Invariance).** A consistent HVAC controller must satisfy:

```
∀σ, ∀g ∈ G_declared:  C(r(σ)) = C(g(r(σ)))
```

In plain language: If two sensor readings describe the same thermal condition, they should produce the same setpoint decision.

### 4.3 Why This Matters for Building Portfolios

Consider an ML model evaluating whether to pre-cool a building:

```
Representation A (Building A's BMS):
  Zone temperatures: [71.2, 72.5, 70.8] °F
  Outdoor temp: 85°F
  Electricity price: $0.15/kWh
  → Decision: PRE_COOL (shift load to morning)

Representation B (Building B's BMS):
  Zone temperatures: [21.8, 22.5, 21.6] °C (same temps!)
  Outdoor temp: 29.4°C (same!)
  Electricity price: $0.15/kWh
  → Decision: ??? (if model wasn't trained on °C...)
```

A robust model should produce the same decision. Bond Index measures whether it does.

---

## 5. Observables and Grounding (Ψ)

### 5.1 The Observable Set for Buildings

| Observable | Symbol | Sensors | Sample Rate | Accuracy |
|------------|--------|---------|-------------|----------|
| Zone air temperature | T_zone | RTD, thermistor | 0.1–1 Hz | ±0.5°F |
| Supply air temperature | T_supply | RTD | 0.1–1 Hz | ±0.5°F |
| Outdoor air temperature | T_outdoor | Weather station | 0.01–0.1 Hz | ±1°F |
| Relative humidity | RH | Capacitive | 0.1–1 Hz | ±3% |
| CO₂ concentration | CO2 | NDIR | 0.01–0.1 Hz | ±50 ppm |
| Occupancy | Occ | PIR, camera, badge | Event-driven | Binary/count |
| Electrical power | P | CT meter | 1–10 Hz | ±2% |
| Airflow | Q | DP, hot-wire | 0.1 Hz | ±5% |
| Damper position | D | Feedback | 0.1 Hz | ±5% |
| Valve position | V | Feedback | 0.1 Hz | ±5% |
| VFD speed | ω | Drive feedback | 1 Hz | ±1% |

### 5.2 External Data Sources

Beyond building sensors, modern systems integrate external data:

| Source | Data | Update Rate | Use |
|--------|------|-------------|-----|
| Weather service | Forecast, current | 15 min – 1 hr | Predictive control |
| Utility | Price, DR signals | 5 min – 1 hr | Cost optimization |
| Grid operator | Carbon intensity | 5 min | Emissions optimization |
| Occupancy calendar | Schedule | Event-driven | Setback scheduling |
| Building model | Thermal response | Static | MPC prediction |

### 5.3 The Ψ-Completeness Situation

Buildings have **good but imperfect observability**:

| Observable | Status |
|------------|--------|
| Zone temperature | ✓ Generally observable |
| Humidity | ✓ Observable where sensors installed |
| CO₂ | ⚠️ Often limited sensors |
| Actual occupancy | ⚠️ Inferred, not measured |
| Equipment efficiency | ⚠️ Rarely measured directly |
| Thermal mass state | ✗ Not directly observable |
| Duct leakage | ✗ Not directly observable |
| Comfort (subjective) | ✗ Complaints are lagging indicator |

**Practical implication**: The framework must handle partial observability gracefully, with conservative defaults when data is missing.

---

## 6. Declared Transforms (G_declared)

### 6.1 Transform Categories for Building Systems

#### Category 1: Unit Transforms

| Transform | Example | Conversion |
|-----------|---------|------------|
| °F ↔ °C | Temperature | (°F - 32) × 5/9 |
| CFM ↔ L/s | Airflow | × 0.472 |
| BTU/hr ↔ kW | Power | × 0.000293 |
| kPa ↔ in.w.c. | Pressure | × 4.02 |
| psig ↔ kPa | Pressure | × 6.895 |

#### Category 2: Sensor Substitution

| Transform | Example | Constraint |
|-----------|---------|------------|
| Zone sensor ↔ return air sensor | Temperature measurement | Bounded offset |
| Supply air ↔ discharge air | Temperature at different location | Equipment-dependent |
| Main meter ↔ submeter sum | Power measurement | Should match |
| Weather station ↔ rooftop sensor | Outdoor temperature | Bounded difference |

#### Category 3: Aggregation Level

| Transform | Example | Constraint |
|-----------|---------|------------|
| Zone ↔ floor average | Temperature aggregation | Preserve physics |
| 1-min ↔ 15-min average | Temporal aggregation | Same mean behavior |
| Individual ↔ zone occupancy | Occupancy rollup | Preserve total |

#### Category 4: BMS Protocol

| Transform | Example | Notes |
|-----------|---------|-------|
| BACnet ↔ Modbus | Protocol conversion | Same physical values |
| Proprietary ↔ standard | Vendor-specific translation | Must preserve semantics |
| Legacy ↔ modern | Old system integration | Often lossy |

#### Category 5: Naming and Addressing

| Transform | Example | Constraint |
|-----------|---------|------------|
| AHU-1-ZN-101 ↔ Floor1.Zone.A | Zone naming convention | Same physical zone |
| Point ID ↔ semantic tag | Haystack tagging | Same physical point |

#### Category 6: Building-to-Building Transfer

| Transform | Example | Constraint |
|-----------|---------|------------|
| Building A ↔ Building B | Same climate zone | Similar thermal behavior |
| Old building ↔ new building | Different envelope | Scaled by UA-value |

### 6.2 Transform Suite Document

```yaml
transform_id: TEMP_F_TO_C
version: 1.0.0
category: unit_conversion
description: "Convert temperature from Fahrenheit to Celsius"
forward: "T_C = (T_F - 32) × 5/9"
inverse: "T_F = T_C × 9/5 + 32"
semantic_equivalence: "Same physical temperature"
precision: 0.1°C
validation:
  test_cases: 1000
  max_error: 0.01°C
```

---

## 7. The Bond Index for HVAC Controllers

### 7.1 Definition

The **Bond Index (Bd)** quantifies how consistently an HVAC controller treats equivalent representations:

```
Bd = D_op / τ
```

where:
- **D_op** is the observed coherence defect
- **τ** is the human-calibrated threshold

### 7.2 Deployment Tiers for HVAC

| Bd Range | Tier | Interpretation | Action |
|----------|------|----------------|--------|
| < 0.1 | **Negligible** | Excellent coherence | Deploy at scale |
| 0.1 – 0.5 | **Low** | Minor inconsistencies | Deploy with monitoring |
| 0.5 – 2.0 | **Moderate** | Significant inconsistencies | Investigate before deployment |
| 2 – 10 | **High** | Severe inconsistencies | Do not deploy to new buildings |
| > 10 | **Severe** | Fundamental incoherence | Retrain model |

**Note**: Thresholds are looser than safety-critical domains because consequences are less severe (comfort, not life).

### 7.3 Calibration for Building Systems

1. **Recruit raters**: Building operators, energy managers (n ≥ 15)
2. **Generate test pairs**: Control scenarios with known transform relationships
3. **Collect judgments**: "Should these produce the same setpoint?"
4. **Fit threshold**: Find defect level where 80% agree the difference matters
5. **Set τ**: Typically τ ≈ 0.1 for HVAC (10% deviation is noticeable to occupants)

### 7.4 Application to Specific Functions

| Function | Key Transforms | Target Bd |
|----------|----------------|-----------|
| **Setpoint optimization** | Units, aggregation | < 0.1 |
| **Occupancy response** | Sensor substitution, aggregation | < 0.2 |
| **Demand response** | Time resolution, grid signals | < 0.1 |
| **Fault detection** | Sensor substitution, protocol | < 0.05 |
| **Transfer to new building** | Building-to-building | < 0.5 |

---

## 8. Regime Transitions: Occupancy, Season, and Grid Events

### 8.1 Operating Regimes

Buildings cycle through distinct operating regimes:

```
┌──────────────────────────────────────────────────────────────────┐
│                    BUILDING OPERATING REGIMES                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  REGIME 1: OCCUPIED (Normal Operations)                          │
│  ────────────────────────────────────                            │
│  • Comfort is priority: T ∈ [68, 74]°F                           │
│  • Ventilation active: OA per ASHRAE 62.1                        │
│  • Full HVAC operation                                           │
│  • Respond to occupant requests                                  │
│                                                                  │
│              ↓ (end of occupied hours)                           │
│                                                                  │
│  REGIME 2: UNOCCUPIED (Setback)                                  │
│  ──────────────────────────────                                  │
│  • Energy is priority: T ∈ [55, 85]°F                            │
│  • Minimum ventilation                                           │
│  • Equipment off or cycling                                      │
│  • Prepare for next occupied period                              │
│                                                                  │
│              ↓ (demand response event)                           │
│                                                                  │
│  REGIME 3: DEMAND RESPONSE                                       │
│  ─────────────────────────                                       │
│  • Grid is priority: Reduce load by X%                           │
│  • Relax comfort bounds: T ∈ [65, 78]°F                          │
│  • Shed non-critical loads                                       │
│  • Pre-cool/pre-heat before event if possible                    │
│                                                                  │
│              ↓ (extreme weather)                                 │
│                                                                  │
│  REGIME 4: PEAK LOAD                                             │
│  ───────────────────                                             │
│  • Equipment limits: Stay below demand charge threshold          │
│  • Staged operation, load shedding                               │
│  • May sacrifice some comfort                                    │
│                                                                  │
│  REGIME 5: SEASONAL TRANSITION                                   │
│  ─────────────────────────────                                   │
│  • Changeover: Heating ↔ Cooling mode                            │
│  • Deadband widened                                              │
│  • Economizer optimization                                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.2 Regime-Specific Parameters

| Parameter | Occupied | Unoccupied | Demand Response | Peak Load |
|-----------|----------|------------|-----------------|-----------|
| **Cooling setpoint** | 72°F | 85°F | 76°F | 74°F |
| **Heating setpoint** | 70°F | 55°F | 66°F | 68°F |
| **Ventilation** | ASHRAE 62.1 | Minimum | Reduced | Normal |
| **Demand limit** | None | None | Grid signal | kW cap |
| **Equipment staging** | As needed | Minimal | Aggressive shed | Prioritized |

### 8.3 Coherence Across Regime Boundaries

Key test: Does the system produce consistent decisions at regime transitions?

**Example**: Transition from Occupied to Unoccupied:
- Occupied mode: Setpoint = 72°F
- Unoccupied mode: Setback to 85°F
- Transition: When exactly? What if occupancy sensor disagrees with schedule?

**Incoherent behavior** (witness): At 5:00 PM, schedule says unoccupied but motion sensor shows activity. System oscillates between regimes, repeatedly ramping setpoint up and down.

---

## 9. Grid-Interactive Buildings: Where Stakes Get Higher

### 9.1 The Emerging Requirement

As grids integrate more renewables and buildings become "grid-interactive," the stakes increase:

| Grid Service | Building Response | Timescale | Stakes |
|--------------|-------------------|-----------|--------|
| **Demand response** | Reduce load by X% | 15 min – 4 hr | Financial (penalties) |
| **Frequency regulation** | Modulate load ±Y% | Seconds | Grid stability |
| **Load following** | Track signal | Minutes | Grid stability |
| **Capacity market** | Committed reduction | Hours | Large financial |
| **Energy arbitrage** | Shift load | Hours | Financial |

### 9.2 Why This Changes the Calculus

Traditional HVAC optimization affects **comfort and cost**. Grid-interactive buildings affect:

1. **Grid reliability**: Aggregated building response can stabilize or destabilize grid
2. **Financial exposure**: Capacity market penalties can be $100K+ per event
3. **Carbon impact**: Load shifting affects marginal emissions
4. **Equity**: DR in some buildings may affect reliability in others

**This starts to look more like the power grid domain**—where representational consistency matters more because actions have external consequences.

### 9.3 Grid Signals as Stakeholder

In the DEME framework, the utility/grid operator becomes a stakeholder:

```yaml
stakeholder:
  id: grid_operator
  weight: 0.15  # Can be overridden by building owner
  priorities:
    - respond_to_DR_signal
    - provide_frequency_response
    - reduce_peak_demand
  hard_vetoes:
    - minimum_response: 80%_of_committed  # Must deliver promised
    - response_time: 15_min  # Must respond within window
  soft_constraints:
    - prefer_preconditioning: true
    - minimize_comfort_impact: true
```

### 9.4 Bond Index for Grid Interaction

For grid-interactive functions, we apply tighter thresholds:

| Function | Target Bd | Rationale |
|----------|-----------|-----------|
| Comfort optimization | < 0.2 | Low stakes |
| Energy cost optimization | < 0.1 | Financial impact |
| Demand response | < 0.05 | Committed obligation |
| Frequency regulation | < 0.01 | Grid stability |

---

## 10. Multi-Stakeholder Governance (DEME)

### 10.1 The Core Value Proposition

This is where ErisML/DEME provides clear value beyond existing solutions:

**Current state**: HVAC optimization systems are tuned by engineers with implicit assumptions about stakeholder priorities. When conflicts arise (e.g., tenant complaint during DR event), there's no principled way to resolve them.

**DEME solution**: Stakeholder priorities are made explicit, documented, and verifiable. Conflicts are resolved according to pre-agreed rules, not ad-hoc judgment.

### 10.2 Building Governance Profile

```yaml
profile_id: "office_building_sf_v2.1"
building_type: Class A Office
location: San Francisco, CA
climate_zone: 3C

stakeholders:
  - id: building_owner
    weight: 0.30
    priorities:
      - minimize_operating_cost
      - maximize_property_value
      - comply_with_local_law_97  # NYC BPS-style regulation
    hard_vetoes:
      - energy_cost_increase_max: 10%  # vs. baseline
      - emissions_exceed_cap: false
      
  - id: property_manager
    weight: 0.20
    priorities:
      - tenant_satisfaction
      - minimize_complaints
      - equipment_longevity
    constraints:
      - comfort_complaints_max: 5_per_month
      - equipment_runtime: balanced
      
  - id: tenant_law_firm
    zone: floors_10_15
    weight: 0.15
    priorities:
      - strict_comfort
      - 24_7_availability
    hard_vetoes:
      - temperature_range: [70, 74]  # °F, non-negotiable
      - hvac_availability: 24_7
      
  - id: tenant_startup
    zone: floors_5_9
    weight: 0.10
    priorities:
      - cost_savings
      - sustainability
    constraints:
      - temperature_range: [65, 78]  # °F, flexible
      - prefer_renewable_hours: true
      
  - id: utility_pge
    weight: 0.10
    priorities:
      - demand_response_participation
      - peak_reduction
    constraints:
      - dr_response_required: 80%_of_commitment
      - notification_time: 15_min
      
  - id: city_sf
    weight: 0.10
    priorities:
      - emissions_reduction
      - building_performance_standard
    hard_vetoes:
      - annual_emissions_max: 2.5  # kg CO2/ft²
      
  - id: hvac_contractor
    weight: 0.05
    priorities:
      - equipment_protection
      - maintenance_access
    hard_vetoes:
      - chiller_short_cycling: false
      - runtime_balance: true

conflict_resolution:
  priority_order:
    1: safety_interlocks  # Always first
    2: regulatory_compliance  # City, codes
    3: hard_vetoes  # Any stakeholder
    4: weighted_optimization  # Soft constraints
    
  escalation:
    - if_conflict: tenant_comfort_vs_dr
      resolution: notify_tenant_5min_advance
      compensation: rent_credit_if_exceeded
      
    - if_conflict: cost_vs_emissions
      resolution: emissions_priority_if_over_70%_cap
```

### 10.3 Conflict Resolution Examples

**Example 1: DR Event vs. Law Firm Comfort**

```
Situation:
  - Utility calls 20% DR event (1 PM - 4 PM)
  - Law firm (floors 10-15) has hard veto: T ∈ [70, 74]°F
  
DEME Resolution:
  1. Check if law firm constraint can be met with 20% reduction elsewhere
  2. If yes: Reduce other zones more, spare law firm
  3. If no: Notify utility of partial response (80% instead of 100%)
  4. Document: "DR response limited by tenant hard veto"
  
Result: System reduced load 17% instead of 20%
        Law firm comfort maintained
        Utility notified, reduced penalty applied
        Audit trail preserved
```

**Example 2: Emissions Cap vs. Cost Optimization**

```
Situation:
  - Owner wants to minimize cost
  - City requires annual emissions < 2.5 kg CO2/ft²
  - Currently tracking to 2.4 kg CO2/ft² with 3 months remaining
  
DEME Resolution:
  1. Project end-of-year emissions under current strategy
  2. If projection < 2.5: Continue cost optimization
  3. If projection ≥ 2.5: Switch to emissions priority mode
  4. Trade off: Accept higher cost to meet regulatory constraint
  
Result: System automatically shifts priorities as constraint approaches
        No human intervention needed
        Compliance documented
```

### 10.4 Governance Audit Trail

Every DEME decision is logged:

```json
{
  "timestamp": "2025-07-15T14:32:17Z",
  "decision": "setpoint_adjustment",
  "zone": "floor_12_east",
  "original_setpoint": 72,
  "new_setpoint": 74,
  "trigger": "demand_response_event",
  "stakeholder_impacts": {
    "utility_pge": "+15% load reduction contribution",
    "tenant_law_firm": "-2°F comfort (within hard veto range)",
    "building_owner": "+$47 avoided DR penalty"
  },
  "conflict_resolution": "weighted_priority",
  "override_available": true,
  "audit_hash": "sha256:a1b2c3..."
}
```

---

## 11. Case Study: University Campus Portfolio

### 11.1 Scenario Description

**Portfolio**: Major research university, 15 buildings

**Characteristics**:
- Buildings ranging from 1920s to 2023
- 5 different BMS vendors
- Mix of teaching, research, residence, athletics
- Central chilled water plant
- Strong sustainability goals (carbon neutrality by 2035)
- State mandate for demand response participation

### 11.2 The Heterogeneity Challenge

| Building | Vintage | BMS | Units | Naming Convention |
|----------|---------|-----|-------|-------------------|
| Chemistry | 1962 | Siemens Desigo | °F | CHEM_AHU1_ZN_101 |
| Engineering | 1985 | Johnson Metasys | °F | ENG.1.101 |
| Library | 1970 | Honeywell EBI | °C | LIB-FL1-RM101 |
| Business School | 2005 | Tridium Niagara | °F | Point ID only |
| New Dorm | 2023 | Modern BACnet | °F | Per ASHRAE 36 |

**Problem**: An ML model trained on the New Dorm data will not work directly on Chemistry building data without careful translation.

### 11.3 Transform Suite

For this portfolio, we define 18 transforms:

| ID | Transform | Category |
|----|-----------|----------|
| T1 | °F ↔ °C | Units |
| T2 | CFM ↔ L/s | Units |
| T3 | kW ↔ BTU/hr | Units |
| T4 | BACnet ↔ Modbus | Protocol |
| T5 | BACnet ↔ Siemens N1 | Protocol |
| T6 | BACnet ↔ Johnson N2 | Protocol |
| T7 | Zone ↔ floor average | Aggregation |
| T8 | 1-min ↔ 15-min | Temporal |
| T9 | Main meter ↔ submeters | Power measurement |
| T10 | Campus naming ↔ Haystack | Naming |
| T11 | Teaching ↔ research building | Transfer |
| T12 | 1960s ↔ 2020s building | Transfer (envelope) |
| T13 | Occupied ↔ unoccupied | Regime |
| T14 | Heating ↔ cooling | Regime |
| T15 | Normal ↔ DR event | Regime |
| T16 | Weather station ↔ building | Outdoor temp |
| T17 | PIR ↔ badge ↔ schedule | Occupancy |
| T18 | Simulation ↔ measured | Validation |

### 11.4 Multi-Stakeholder Profile

```yaml
profile_id: "university_campus_v1.0"

stakeholders:
  - id: facilities_management
    weight: 0.25
    priorities:
      - equipment_protection
      - operator_workload
      - maintenance_budget
    hard_vetoes:
      - equipment_short_cycling: false
      - operator_alarms_max: 20_per_day
      
  - id: sustainability_office
    weight: 0.20
    priorities:
      - carbon_reduction
      - renewable_energy_use
      - sustainability_reporting
    hard_vetoes:
      - annual_emissions_trajectory: on_track_to_2035
      
  - id: research_labs
    weight: 0.20
    priorities:
      - strict_environmental_control
      - 24_7_operation
      - no_interruptions
    hard_vetoes:
      - lab_temperature_range: [68, 72]  # °F
      - humidity_range: [40, 50]  # %
      - dr_participation: false  # Labs exempt
      
  - id: teaching_spaces
    weight: 0.15
    priorities:
      - comfort_during_classes
      - rapid_setback_between
    constraints:
      - temperature_range: [68, 76]  # °F
      - schedule_adherence: class_schedule_plus_30min
      
  - id: residence_halls
    weight: 0.10
    priorities:
      - student_comfort
      - energy_education
    constraints:
      - temperature_range: [66, 76]  # °F
      - student_setpoint_adjustment: ±2°F allowed
      
  - id: state_grid_operator
    weight: 0.10
    priorities:
      - demand_response
      - peak_shaving
    constraints:
      - minimum_dr_participation: non_lab_buildings
      - response_time: 15_min
```

### 11.5 Bond Index Evaluation

**Test protocol**:
1. Generate 2,000 building states across all 15 buildings
2. Apply each of 18 transforms at 3 intensity levels
3. Compute control decisions before and after transform
4. Calculate coherence defects

**Results**:

```
═══════════════════════════════════════════════════════════════════
              BOND INDEX EVALUATION RESULTS
═══════════════════════════════════════════════════════════════════

System:        University Campus HVAC Optimization (ML-based)
Transform suite: G_declared_campus_v1.0 (18 transforms)
Test cases:    2,000 states × 18 transforms × 3 intensities = 108,000

───────────────────────────────────────────────────────────────────
                      BOND INDEX
───────────────────────────────────────────────────────────────────
  Bd_mean = 0.087   [0.072, 0.103] 95% CI
  Bd_p95  = 0.31
  Bd_max  = 1.8

  TIER: LOW
  DECISION: ⚠️ Deploy with monitoring; investigate high-defect transforms

───────────────────────────────────────────────────────────────────
                TRANSFORM SENSITIVITY
───────────────────────────────────────────────────────────────────
  T1  (°F↔°C):           0.000   (perfect)
  T2  (CFM↔L/s):         0.000   (perfect)
  T3  (kW↔BTU/hr):       0.000   (perfect)
  T4  (BACnet↔Modbus):   0.021   ██
  T5  (BACnet↔Siemens):  0.089   ████
  T6  (BACnet↔Johnson):  0.145   ██████  ← High
  T7  (zone↔floor):      0.034   ███
  T8  (1-min↔15-min):    0.018   ██
  T9  (meter↔submeters): 0.042   ███
  T10 (naming):          0.000   (perfect - after mapping)
  T11 (teach↔research):  0.23    █████████  ← HIGHEST
  T12 (1960s↔2020s):     0.31    ████████████  ← HIGHEST
  T13 (occ↔unocc):       0.056   ████
  T14 (heat↔cool):       0.078   █████
  T15 (normal↔DR):       0.041   ███
  T16 (weather↔bldg):    0.015   █
  T17 (occupancy):       0.089   █████
  T18 (sim↔measured):    0.12    ██████

───────────────────────────────────────────────────────────────────
                   WORST WITNESS
───────────────────────────────────────────────────────────────────
  Transform: T12 (1960s building ↔ 2020s building)
  State: Moderate outdoor temperature, partial occupancy
  
  2020s building (New Dorm):
    Model predicts: Start cooling at outdoor = 68°F
    Decision: Pre-cool starting at 2 PM
    
  1960s building (Chemistry):
    Model predicts: Same control action
    But: Building has 10× thermal mass, no solar gain control
    Reality: Pre-cooling at 2 PM wastes energy
    Appropriate action: Delay cooling until 4 PM
    
  Defect: 1.8 (wrong timing by 2 hours)
  
  ROOT CAUSE: Model trained primarily on modern buildings
              Doesn't account for thermal mass differences
              Transfer learning failed
  
  RECOMMENDATION: 
    - Building-specific thermal models
    - Or: Cluster buildings by vintage, train separate models
    - Flag transfer to dissimilar buildings

───────────────────────────────────────────────────────────────────
                GOVERNANCE COMPLIANCE
───────────────────────────────────────────────────────────────────
  Research lab constraints:    PASSED (always honored)
  DR response capability:      PASSED (non-lab buildings)
  Emissions trajectory:        PASSED (on track)
  Operator alarm load:         WARNING (22 alarms/day, limit 20)
  
  Stakeholder satisfaction:
    Facilities: 78% (alarm fatigue issue)
    Sustainability: 95% (good progress)
    Research: 100% (no violations)
    Teaching: 85% (occasional complaints)

═══════════════════════════════════════════════════════────────────
```

### 11.6 Remediation Plan

| Issue | Root Cause | Remediation | Expected Improvement |
|-------|------------|-------------|----------------------|
| 1960s↔2020s transfer | Thermal mass difference | Building-specific models | 0.31 → 0.08 |
| Teaching↔research | Different occupancy patterns | Separate model paths | 0.23 → 0.06 |
| BACnet↔Johnson | Legacy protocol quirks | Improved translator | 0.145 → 0.03 |
| Simulation↔measured | Model-reality gap | Online model calibration | 0.12 → 0.05 |

**Post-remediation target**: Bd < 0.05 for intra-building, Bd < 0.2 for inter-building transfer

---

## 12. Implementation Architecture

### 12.1 Integration with Existing Infrastructure

The Bond Index framework integrates as a **verification layer**, not a replacement:

```
┌─────────────────────────────────────────────────────────────────┐
│                  EXISTING BUILDING INFRASTRUCTURE               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐                 │
│  │    BMS    │   │    BMS    │   │    BMS    │                 │
│  │  (Vendor  │   │  (Vendor  │   │  (Vendor  │                 │
│  │     A)    │   │     B)    │   │     C)    │                 │
│  └─────┬─────┘   └─────┬─────┘   └─────┬─────┘                 │
│        │               │               │                        │
│        └───────────────┼───────────────┘                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              INTEGRATION LAYER                           │   │
│  │  (Haystack, Brick, Project Haystack)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │       ML-BASED OPTIMIZATION ENGINE                       │   │
│  │  (DeepMind-style, BrainBox, Turntide, or custom)         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                        │
└────────────────────────┼────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              ErisML/DEME VERIFICATION LAYER                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              TRANSFORM ENGINE                            │   │
│  │  • Unit conversions                                      │   │
│  │  • Protocol translations                                 │   │
│  │  • Building-to-building mapping                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BOND INDEX CALCULATOR                       │   │
│  │  • Consistency verification                              │   │
│  │  • Transfer validation                                   │   │
│  │  • Witness generation                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              DEME GOVERNANCE ENGINE                      │   │
│  │  • Stakeholder profiles                                  │   │
│  │  • Conflict resolution                                   │   │
│  │  • Decision audit trail                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              REPORTING & COMPLIANCE                      │   │
│  │  • Energy benchmarking (ENERGY STAR)                     │   │
│  │  • Building performance standards                        │   │
│  │  • M&V for DR participation                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Deployment Modes

| Mode | Description | Timing | Use Case |
|------|-------------|--------|----------|
| **Pre-deployment** | Test model on new building before activation | Days | Transfer validation |
| **Shadow mode** | Run in parallel, compare to existing | Weeks | Confidence building |
| **Active verification** | Continuous Bd monitoring during operation | Continuous | Drift detection |
| **Governance audit** | Periodic stakeholder compliance review | Monthly | Compliance reporting |

### 12.3 Integration with Existing ML Systems

The framework is designed to work **with** existing ML optimization engines:

```python
# Example: Wrapping BrainBox/DeepMind-style optimizer
class VerifiedHVACOptimizer:
    def __init__(self, base_optimizer, transform_suite, governance_profile):
        self.optimizer = base_optimizer  # Existing ML engine
        self.transforms = transform_suite
        self.governance = governance_profile
        
    def get_setpoint(self, building_state):
        # Get base recommendation
        base_decision = self.optimizer.predict(building_state)
        
        # Verify consistency across transforms
        bd = self.compute_bond_index(building_state, base_decision)
        if bd > THRESHOLD:
            log_witness(building_state, bd)
            # Fall back to conservative default
            base_decision = self.conservative_fallback(building_state)
        
        # Apply governance constraints
        final_decision = self.governance.apply(base_decision, building_state)
        
        # Log for audit
        self.log_decision(building_state, base_decision, final_decision)
        
        return final_decision
```

---

## 13. Deployment Pathway

### 13.1 Phase 1: Simulation Validation (Year 1)

**Objective**: Demonstrate framework on building simulation

**Activities**:
- Implement transforms for EnergyPlus models
- Partner with DOE/NREL or university building research lab
- Test consistency across climate zones, building types
- Publish in Energy and Buildings or Building Simulation

**Deliverables**:
- Validated transform suite for buildings
- EnergyPlus integration
- Technical paper

**Resources**: $200K, 3 FTE, 1 year

### 13.2 Phase 2: Single Building Pilot (Year 2)

**Objective**: Deploy on real building with cooperative owner

**Activities**:
- Partner with university or corporate campus
- Integrate with existing BMS (read-only initially)
- Run shadow mode comparison
- Validate Bond Index in practice
- Test DEME governance with real stakeholders

**Deliverables**:
- Real-world validated system
- Case study with measured savings
- Stakeholder feedback

**Resources**: $400K, 4 FTE, 1 year

### 13.3 Phase 3: Portfolio Deployment (Years 3-4)

**Objective**: Scale to multi-building portfolio

**Activities**:
- Deploy across 10–50 buildings
- Test inter-building transfer
- Validate DEME governance at scale
- Build automation for onboarding

**Deliverables**:
- Portfolio-proven system
- Scalable deployment process
- ROI documentation

**Resources**: $1M, 6 FTE, 2 years

### 13.4 Phase 4: BMS Vendor Integration (Years 4-5)

**Objective**: Integrate with major BMS vendors

**Target partners**:
- Johnson Controls
- Honeywell
- Siemens
- Schneider Electric
- Tridium

**Activities**:
- Develop vendor-specific integrations
- Co-marketing agreements
- Training and certification
- API standardization

**Deliverables**:
- Vendor partnerships
- Integrated products
- Market presence

**Resources**: $2M, 10 FTE, 2 years

**Market potential**: $50M+ annual revenue at maturity

---

## 14. Limitations and Honest Assessment

### 14.1 What This Framework Does Well

| Capability | Value | Confidence |
|------------|-------|------------|
| **Multi-stakeholder governance** | High | Strong fit for DEME |
| **Transfer verification** | High | Bond Index adds real value |
| **Legacy system integration** | Medium-High | Transform suite helps |
| **Regulatory compliance** | Medium-High | Audit trail valuable |
| **Grid-interactive verification** | Medium-High | Higher stakes justify rigor |

### 14.2 What This Framework Does NOT Do Well

| Limitation | Explanation |
|------------|-------------|
| **ML algorithm improvement** | We verify, not improve, the core ML |
| **Safety-critical stakes** | HVAC is comfort, not life-safety (mostly) |
| **Real-time control** | Building thermal mass gives time; BIP advantage unclear |
| **Commoditization** | HVAC market is competitive; differentiation limited |

### 14.3 Honest Comparison to Existing Solutions

| Approach | Strengths | Weaknesses | Our Complement |
|----------|-----------|------------|----------------|
| **DeepMind-style RL** | Optimal control, proven savings | Single-building, homogeneous | Transfer verification |
| **BrainBox AI** | Commercial scale, proven | Black-box decisions | Governance transparency |
| **Traditional MPC** | Interpretable, robust | Limited adaptation | ML enhancement |
| **Rule-based BMS** | Simple, reliable | Suboptimal | All of the above |

**Our positioning**: We don't replace these—we add a verification and governance layer that enables them to scale to heterogeneous portfolios with multiple stakeholders.

### 14.4 When NOT to Use This Framework

- Single building with single owner (DeepMind/BrainBox is sufficient)
- New construction with modern BMS (less heterogeneity)
- No stakeholder conflicts (governance not needed)
- Pure cost optimization (simpler solutions exist)

### 14.5 When This Framework Adds Clear Value

- Multi-building portfolios with legacy systems
- Buildings with multiple tenants and conflicting requirements
- Grid-interactive buildings with financial exposure
- Regulatory compliance requirements (building performance standards)
- Transfer of ML models to dissimilar buildings

---

## 15. Conclusion

Building HVAC optimization is a different application domain than chemical reactors or autonomous vehicles. The constraints are softer, the stakes are lower, and excellent ML-based solutions already exist.

**Where ErisML/DEME adds value is not in the ML—it's in the deployment:**

1. **Transfer verification**: Bond Index quantifies whether an ML model will work on a new building before you deploy it
2. **Legacy integration**: Declared transforms handle the heterogeneity of real building portfolios
3. **Multi-stakeholder governance**: DEME makes conflicting priorities explicit, auditable, and resolvable
4. **Grid-interactive buildings**: As stakes increase with grid integration, verification rigor becomes more valuable

### The Scaling Problem

DeepMind achieved 40% energy reduction in Google's data centers. That's remarkable. But there are 100+ million commercial buildings globally, most with legacy BMS systems, multiple stakeholders, and no dedicated ML team.

**The question is not "Can we optimize a building?"—we know we can.**

**The question is "Can we deploy optimization across millions of heterogeneous buildings with conflicting stakeholders?"**

ErisML/DEME provides part of that answer: a verification and governance layer that enables existing ML solutions to scale beyond curated environments to the messy reality of the building stock.

### The Honest Pitch

If you have one modern building with one owner, use DeepMind/BrainBox/Turntide directly.

If you have 50 buildings from five decades with legacy BMS, three tenant types, a utility demanding DR, and a city requiring emissions compliance—**that's where we help**.

> *"The algorithm is solved. The governance isn't. That's the gap we fill."*

---

## 16. References

1. Google DeepMind. (2016). "DeepMind AI Reduces Google Data Centre Cooling Bill by 40%." Blog post.

2. ASHRAE. (2019). *ASHRAE Standard 90.1: Energy Standard for Buildings Except Low-Rise Residential Buildings*.

3. ASHRAE. (2019). *ASHRAE Standard 62.1: Ventilation for Acceptable Indoor Air Quality*.

4. ASHRAE. (2021). *ASHRAE Guideline 36: High-Performance Sequences of Operation for HVAC Systems*.

5. DOE. (2023). *EnergyPlus Documentation*. U.S. Department of Energy.

6. NREL. (2022). *Grid-Interactive Efficient Buildings Technical Report Series*.

7. NYC Local Law 97. (2019). *Climate Mobilization Act*.

8. Project Haystack. (2023). *Haystack 4 Standard*.

9. Brick Schema. (2023). *Brick Ontology for Buildings*.

10. Turntide Technologies. (2023). *Building Optimization Platform*.

11. BrainBox AI. (2023). *Autonomous Building Technology*.

12. Bond, A. H. (2025). "A Categorical Framework for Verifying Representational Consistency in Machine Learning Systems."

13. Bond, A. H. (2025). "The Grand Unified AI Safety Stack (GUASS) v12.0."

14. Wei, T., Wang, Y., & Zhu, Q. (2017). "Deep reinforcement learning for building HVAC control." *DAC*.

15. Drgoňa, J., et al. (2020). "All you need to know about model predictive control for buildings." *Annual Reviews in Control*, 50, 190-232.

---

## Appendix A: Comparison with Existing Solutions

| Feature | DeepMind | BrainBox AI | Turntide | Traditional MPC | ErisML/DEME |
|---------|----------|-------------|----------|-----------------|-------------|
| **ML optimization** | ✓ Excellent | ✓ Good | ✓ Good | △ Limited | ✗ Uses others |
| **Legacy BMS support** | ✗ Limited | △ Some | △ Some | ✓ Good | ✓ Designed for |
| **Multi-stakeholder** | ✗ Single owner | ✗ Implicit | ✗ Implicit | ✗ No | ✓ DEME core |
| **Transfer verification** | ✗ No | ✗ No | ✗ No | △ Manual | ✓ Bond Index |
| **Governance audit** | ✗ No | ✗ Limited | ✗ Limited | ✗ No | ✓ Full trail |
| **Grid interaction** | △ Internal | △ Some | △ Some | ✓ Good | ✓ Stakeholder |
| **Open standard** | ✗ Proprietary | ✗ Proprietary | ✗ Proprietary | ✓ Academic | ✓ Open |

---

## Appendix B: DEME Profile Template for Buildings

```yaml
# DEME Governance Profile Template for Buildings
# Version: 1.0.0

profile_id: "building_name_v1.0"
building_info:
  type: office | retail | hospital | university | residential
  location: city, state
  climate_zone: ASHRAE climate zone
  vintage: year
  area_ft2: number
  
stakeholders:
  - id: stakeholder_name
    weight: 0.0-1.0  # Must sum to 1.0
    priorities:  # Ordered list
      - priority_1
      - priority_2
    hard_vetoes:  # Non-negotiable constraints
      parameter: value
    soft_constraints:  # Preferences
      parameter: value
      
# Standard stakeholder templates available:
#   - building_owner
#   - property_manager
#   - tenant_standard
#   - tenant_premium
#   - utility_dr
#   - grid_iso
#   - city_regulator
#   - hvac_contractor

conflict_resolution:
  priority_order:
    1: safety
    2: regulatory
    3: hard_vetoes
    4: weighted
    
  escalation:
    - if_conflict: description
      resolution: action
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **ASHRAE** | American Society of Heating, Refrigerating and Air-Conditioning Engineers |
| **BACnet** | Building Automation and Control Networks (ANSI/ASHRAE 135) |
| **BMS** | Building Management System |
| **COP** | Coefficient of Performance (efficiency metric) |
| **DDC** | Direct Digital Control |
| **DR** | Demand Response |
| **EUI** | Energy Use Intensity (kBtu/ft²/year) |
| **GEB** | Grid-Interactive Efficient Building |
| **HVAC** | Heating, Ventilation, and Air Conditioning |
| **MPC** | Model Predictive Control |
| **PUE** | Power Usage Effectiveness (data center metric) |
| **VAV** | Variable Air Volume |
| **VFD** | Variable Frequency Drive |

---

**Document version**: 1.0.0  
**Last updated**: December 2025  
**License**: AGI-HPC Responsible AI License v1.0

---

<p align="center">
  <em>"The algorithm is solved. The governance isn't. That's the gap we fill."</em>
</p>
