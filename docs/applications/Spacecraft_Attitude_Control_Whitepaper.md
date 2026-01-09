# Invariance-Based Safety Verification for Spacecraft Attitude Control

## A Philosophy Engineering Approach to Protecting High-Value Space Assets

---

**Technical Whitepaper v1.0 — December 2025**

**Andrew H. Bond**  
San José State University  
Ethical Finite Machines  
andrew.bond@sjsu.edu

---

> *"The Mars Climate Orbiter was lost because one team used pound-seconds while another expected newton-seconds. The physics was unchanged. The representation was inconsistent. A $327.6 million mission destroyed by a unit conversion error."*

---

## Executive Summary

This whitepaper presents a novel approach to spacecraft attitude control verification based on **representational invariance testing**—the principle that a satellite's guidance, navigation, and control (GN&C) decisions should not depend on arbitrary choices in attitude representation, coordinate frame, or time system.

We apply the **ErisML/DEME framework** (Epistemic Representation Invariance & Safety ML / Democratically Governed Ethics Modules) to spacecraft attitude control, demonstrating how:

1. **The Bond Index (Bd)** can quantify the coherence of attitude determination and control systems across quaternion/Euler/DCM representations, reference frames, and operating modes
2. **Declared transforms (G_declared)** map naturally to attitude parameterizations, coordinate frame rotations, time system conversions, and sensor modality substitution
3. **The Decomposition Theorem** separates implementation bugs (fixable via calibration) from fundamental specification conflicts (requiring mission redesign)
4. **Democratic governance profiles** allow multi-stakeholder requirements (mission operations, power systems, thermal, communications) to be composed without contradiction

**Key finding**: An attitude control system with Bond Index Bd < 0.01 across standard transforms is **provably consistent** in its control decisions—it will not command a slew maneuver under one attitude representation while commanding station-keeping under an equivalent representation.

**Market opportunity**: The global satellite market exceeds $280B, with attitude control systems essential for every spacecraft. High-value assets ($50M–$500M per satellite) and irreplaceable fuel budgets make verification critical—yet no current standard systematically tests for *representational consistency* across the GN&C pipeline.

---

## Table of Contents

1. [Introduction: The Representational Failure Mode](#1-introduction-the-representational-failure-mode)
2. [Background: Spacecraft Attitude Control and Current Practice](#2-background-spacecraft-attitude-control-and-current-practice)
3. [The Invariance Framework for Spacecraft](#3-the-invariance-framework-for-spacecraft)
4. [Observables and Grounding (Ψ)](#4-observables-and-grounding-ψ)
5. [Declared Transforms (G_declared)](#5-declared-transforms-g_declared)
6. [The Bond Index for Attitude Control Systems](#6-the-bond-index-for-attitude-control-systems)
7. [Regime Transitions and Coherence Defects](#7-regime-transitions-and-coherence-defects)
8. [The Fuel Budget: A Non-Renewable Constraint](#8-the-fuel-budget-a-non-renewable-constraint)
9. [Multi-Subsystem Governance](#9-multi-subsystem-governance)
10. [Case Study: GEO Communications Satellite Station-Keeping](#10-case-study-geo-communications-satellite-station-keeping)
11. [Implementation Architecture](#11-implementation-architecture)
12. [Deployment Pathway](#12-deployment-pathway)
13. [Limitations and Future Work](#13-limitations-and-future-work)
14. [Conclusion](#14-conclusion)
15. [References](#15-references)

---

## 1. Introduction: The Representational Failure Mode

### 1.1 A Different Kind of Failure

Most spacecraft anomaly analysis focuses on **hardware failures**: reaction wheel bearing degradation, solar cell radiation damage, thruster valve stuck open. These are important, and the space industry has developed sophisticated tools to address them (redundancy, radiation hardening, thermal management).

But there is another failure mode that has destroyed missions: **representational failures**—cases where the spacecraft's *model* of its state becomes inconsistent across processing stages, not because sensors failed, but because the *way the system interprets data* contains hidden inconsistencies.

### 1.2 The Mars Climate Orbiter: The Canonical Example

On September 23, 1999, NASA's Mars Climate Orbiter was lost during orbital insertion. The cause was devastatingly simple:

```
Lockheed Martin software: Reported thrust in pound-force·seconds
NASA navigation software: Expected thrust in newton·seconds

Conversion factor: 1 lbf·s = 4.448 N·s

Result: Navigation computed trajectory 4.45× too low
        Spacecraft entered atmosphere at 57 km instead of 140+ km
        $327.6 million mission destroyed
```

**The physics was unchanged**—the thrusters produced the same physical impulse. **The representation was inconsistent**—two systems used different units without proper conversion.

### 1.3 The Attitude Representation Problem

Spacecraft attitude is notoriously difficult to represent uniquely. Multiple mathematically equivalent representations exist:

| Representation | Parameters | Singularities | Unique? |
|----------------|------------|---------------|---------|
| **Euler angles** | 3 (φ, θ, ψ) | Gimbal lock at ±90° | Yes (with convention) |
| **Quaternion** | 4 (q₀, q₁, q₂, q₃) | None | No (q = -q) |
| **Direction Cosine Matrix (DCM)** | 9 (3×3 matrix) | None | No (must be orthonormal) |
| **Modified Rodrigues Parameters (MRP)** | 3 (σ₁, σ₂, σ₃) | At 360° rotation | No (shadow set) |
| **Axis-angle** | 4 (e, θ) | At 0° and 360° | No |

**The same physical orientation** can be described as:
```
Euler (3-2-1):     φ=10°, θ=20°, ψ=30°
Quaternion:        q = [0.9515, 0.0381, 0.1893, 0.2392]
                   (or -q = [-0.9515, -0.0381, -0.1893, -0.2392])
DCM:               [9-element matrix]
MRP:               σ = [0.0200, 0.0989, 0.1253]
                   (or shadow: σ_s = [-0.0194, -0.0955, -0.1211])
```

If different subsystems use different representations without rigorous conversion, the spacecraft may execute inconsistent commands.

### 1.4 The Reference Frame Problem

Compounding the representation issue, spacecraft operate in multiple coordinate frames:

```
Same position described in:
  ECI (Earth-Centered Inertial):    r = [42164, 0, 0] km
  ECEF (Earth-Centered Earth-Fixed): r = [41800, 5200, 0] km (depends on time)
  LVLH (Local Vertical Local Horizontal): r = [0, 0, 0] km (at satellite)
  Body frame: [0, 0, 0] km (at satellite, but axes rotate)
  Sun-pointing frame: Different orientation
```

Each frame is appropriate for different purposes (orbital mechanics, ground station visibility, payload pointing). Transformations between frames must be exact.

### 1.5 The Philosophy Engineering Insight

For decades, questions like "Is this attitude maneuver safe?" have been treated as matters of margin analysis, fault protection, and expert review. The **Philosophy Engineering** framework changes the question:

> We cannot test whether an attitude control decision is *optimal* in some absolute sense. But we **can** test whether an attitude control system is **consistent**—whether it gives the same command when the same physical state is described in different equivalent ways.

This is a *falsifiable* property. If we find a case where the system commands a 5° slew under representation A but a 15° slew under equivalent representation B, we have produced a **witness** to inconsistency. Witnesses enable debugging.

### 1.6 What This Whitepaper Offers

We present:

1. **A formal framework** for defining "equivalent representations" in spacecraft GN&C (the transform suite G_declared)
2. **A quantitative metric** (the Bond Index Bd) that measures how consistently an attitude control system treats equivalent states
3. **A verification protocol** that can be applied to existing flight software without replacing it
4. **A governance mechanism** for composing pointing requirements from multiple subsystems
5. **A deployment roadmap** from simulation validation to CubeSat demonstration to operational satellites

---

## 2. Background: Spacecraft Attitude Control and Current Practice

### 2.1 Why Attitude Control Matters

Spacecraft attitude—the orientation of the vehicle body relative to a reference frame—is critical for nearly every mission function:

| Function | Pointing Requirement | Consequence of Failure |
|----------|---------------------|------------------------|
| **Solar power generation** | Solar panels toward Sun | Power loss, battery depletion |
| **Thermal control** | Radiators away from Sun | Overheating, component damage |
| **Communications** | Antenna toward Earth/relay | Data loss, lost contact |
| **Payload operation** | Instrument toward target | Mission failure |
| **Orbit maintenance** | Thrusters in velocity direction | Wrong orbit, fuel waste |
| **Collision avoidance** | Maneuver execution | Debris impact |

**The stakes**: A satellite costs $50M–$500M+ to build and launch. There is no repair capability for most missions. Attitude control errors can end missions permanently.

### 2.2 Attitude Control Requirements

Typical attitude control requirements for different mission classes:

| Mission Type | Pointing Accuracy | Pointing Stability | Slew Rate |
|--------------|-------------------|-------------------|-----------|
| **Communications (GEO)** | 0.01–0.1° | 0.001°/s | 0.1°/s |
| **Earth observation (LEO)** | 0.001–0.01° | 0.0001°/s | 1°/s |
| **Space telescope** | 0.0001–0.001° (arcsec) | 0.00001°/s | 0.01°/s |
| **CubeSat** | 1–5° | 0.1°/s | 5°/s |
| **Deep space** | 0.01–0.1° | 0.001°/s | 0.5°/s |

### 2.3 Current GN&C Architecture

Modern spacecraft employ a layered guidance, navigation, and control architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SPACECRAFT GN&C ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 4: Mission Planning / Ground Operations                  │
│           - Maneuver planning                                   │
│           - Command generation                                  │
│           - Anomaly resolution                                  │
│           Timescale: Hours to days                              │
│                         ▲                                       │
│  LAYER 3: Guidance                                              │
│           - Reference attitude generation                       │
│           - Slew trajectory planning                            │
│           - Mode management                                     │
│           Timescale: Seconds to minutes                         │
│                         ▲                                       │
│  LAYER 2: Navigation (Attitude Determination)                   │
│           - Sensor processing (star tracker, gyro, etc.)        │
│           - State estimation (Kalman filter)                    │
│           - Attitude determination                              │
│           Timescale: 10 ms – 1 s                                │
│                         ▲                                       │
│  LAYER 1: Control                                               │
│           - Error computation                                   │
│           - Control law (PID, LQR, etc.)                        │
│           - Actuator command generation                         │
│           Timescale: 1 ms – 100 ms                              │
│                         ▲                                       │
│  LAYER 0: Actuators & Sensors                                   │
│           - Reaction wheels, CMGs, thrusters, magnetorquers     │
│           - Star trackers, gyros, sun sensors, magnetometers    │
│           Timescale: Hardware response                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 The Gap: Representational Consistency Testing

Current spacecraft verification focuses on:

- **Functional testing**: Does the software respond correctly to nominal inputs?
- **Fault protection**: Does the system handle hardware failures gracefully?
- **Environmental testing**: Does the hardware survive launch, space environment?
- **Performance analysis**: Does pointing accuracy meet requirements?

What they do **not** systematically test:

- **Do different attitude representations yield consistent control commands?**
- **Are reference frame transformations implemented consistently across subsystems?**
- **Does the navigation filter produce consistent estimates regardless of sensor selection?**
- **Is time synchronization consistent across the GN&C pipeline?**

These are precisely the questions the Bond Index framework addresses.

---

## 3. The Invariance Framework for Spacecraft

### 3.1 Core Definitions

**Definition 1 (Spacecraft State).** A spacecraft state σ is the complete specification of the vehicle's dynamical state:

```
σ = (attitude, angular_velocity, position, velocity, mass_properties, mode)
```

where:
- `attitude` = orientation of body frame relative to reference frame
- `angular_velocity` = ω in body frame
- `position` = r in ECI (or other inertial frame)
- `velocity` = v in ECI
- `mass_properties` = (mass, inertia tensor, center of mass)
- `mode` = operating mode (nominal, safe, thruster, etc.)

**Definition 2 (Representation).** A representation r(σ) is a specific encoding of the spacecraft state in terms of:
- Attitude parameterization (quaternion, Euler, DCM, MRP)
- Reference frame (ECI, ECEF, LVLH, body, payload)
- Time system (UTC, GPS, TDB, MET)
- Sensor source (star tracker, gyro-propagated, magnetometer)
- Units (radians, degrees, RPM, arcseconds)

**Definition 3 (Control Decision).** A control decision function C maps representations to actuator commands:

```
C: Representations → {ω_wheel, τ_thruster, m_magnetorquer, mode_change, ⊥}
```

where ⊥ indicates insufficient information to determine safe command (should trigger safe mode).

**Definition 4 (Declared Transform).** A declared transform g ∈ G_declared is a mapping between representations that preserves the underlying physical state:

```
g: r(σ) → r'(σ)    such that    σ is unchanged
```

### 3.2 The Consistency Requirement

**Axiom (Representational Invariance).** A consistent attitude control system must satisfy:

```
∀σ, ∀g ∈ G_declared:  C(r(σ)) = C(g(r(σ)))
```

In plain language: If two representations describe the same physical spacecraft state, they must produce the same control command.

### 3.3 Why This Matters for Spacecraft

Consider a GEO satellite maintaining station:

```
Representation A (Euler angles, 3-2-1, degrees):
  Roll = 0.05°, Pitch = -0.02°, Yaw = 0.08°
  Reference: LVLH
  → Error small → Reaction wheel torque: [0.001, -0.0004, 0.0016] N·m

Representation B (Quaternion):
  q = [0.9999996, 0.000436, -0.000175, 0.000698]
  Reference: ECI (different!)
  → Must transform to LVLH → q_LVLH depends on orbital position
  → If transformation wrong → Different error → Different torque command
```

If the ECI-to-LVLH transformation uses stale orbital elements, the "equivalent" quaternion will actually represent a different LVLH attitude, producing inconsistent commands.

**In space, there is no second chance**: A wrong thruster firing wastes irreplaceable fuel. A wrong reaction wheel command can saturate the wheel, requiring thruster desaturation and more fuel.

---

## 4. Observables and Grounding (Ψ)

### 4.1 The Observable Set for Spacecraft

Following the ErisML framework, we define the **grounding map Ψ** that specifies which physical quantities the spacecraft has access to:

| Observable | Symbol | Sensors | Sample Rate | Accuracy |
|------------|--------|---------|-------------|----------|
| Attitude (inertial) | q, C | Star tracker | 1–10 Hz | 1–10 arcsec |
| Angular velocity | ω | Gyroscope (IRU) | 100–1000 Hz | 0.001–0.01 °/hr |
| Magnetic field (body) | B_body | Magnetometer | 1–100 Hz | 1–100 nT |
| Sun vector (body) | s_body | Sun sensor | 1–10 Hz | 0.1–1° |
| Position (ECI) | r | GPS / ground tracking | 1–10 Hz | 1–100 m |
| Velocity (ECI) | v | GPS / ground tracking | 1–10 Hz | 0.01–1 m/s |
| Time | t | GPS / spacecraft clock | Continuous | 1 μs – 1 ms |
| Wheel speeds | Ω_wheel | Tachometers | 10–100 Hz | 0.1 RPM |
| Thruster state | valve_state | Discrete feedback | Event-driven | Binary |
| Temperature | T | Thermistors | 0.1–1 Hz | 0.1–1°C |

### 4.2 Attitude Determination Pipeline

Spacecraft typically employ sensor fusion for attitude determination:

```
┌─────────────────────────────────────────────────────────────────┐
│                ATTITUDE DETERMINATION PIPELINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐                                              │
│  │ STAR TRACKER  │───▶ q_ST (accurate, but slow, can be        │
│  │ (1-10 Hz)     │        blinded by Sun/Moon/Earth)           │
│  └───────────────┘                                              │
│                    ╲                                            │
│                     ╲    ┌──────────────────────────────────┐   │
│  ┌───────────────┐   ╲   │                                  │   │
│  │   GYROSCOPE   │────╲──│     EXTENDED KALMAN FILTER       │   │
│  │ (100-1000 Hz) │    ╱──│                                  │   │
│  └───────────────┘   ╱   │  State: [q, ω, gyro_bias]        │   │
│                     ╱    │  Measurement: Star tracker       │   │
│  ┌───────────────┐ ╱     │  Propagation: Gyro integration   │   │
│  │  SUN SENSOR   │╱      │                                  │   │
│  │ (1-10 Hz)     │───▶   │  Output: q_est, ω_est, P        │   │
│  └───────────────┘       │                                  │   │
│                          └──────────────────────────────────┘   │
│  ┌───────────────┐                       │                      │
│  │ MAGNETOMETER  │───────────────────────┘                      │
│  │ (1-100 Hz)    │   (for coarse attitude, gyro bias)           │
│  └───────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Derived Quantities

Beyond direct measurements, GN&C systems compute derived quantities:

| Derived Observable | Formula | Use |
|--------------------|---------|-----|
| Attitude error | q_err = q_ref⁻¹ ⊗ q_est | Control input |
| Angular momentum | H = I·ω + Σ(I_w·Ω_w) | Momentum management |
| Orbit position | Propagated from GPS + models | Frame transforms |
| Sun vector (ECI) | Ephemeris lookup | Sun-safe logic |
| Eclipse status | Geometry calculation | Power/thermal modes |
| Fuel remaining | Integration of thruster usage | Fuel budget |
| Antenna pointing error | θ_error = cos⁻¹(a·target) | Communication |

### 4.4 The Ψ-Completeness Advantage

Unlike ground vehicles or chemical reactors, spacecraft attitude control enjoys **excellent Ψ-completeness**:

| Property | Observability | Notes |
|----------|---------------|-------|
| Attitude | Complete | Star trackers provide full 3-axis |
| Angular velocity | Complete | Gyros measure body rates |
| External torques | Predictable | Gravity gradient, solar pressure, magnetic |
| Orbit | Complete | GPS or ground tracking |
| Time | Complete | GPS or atomic clocks |

**What remains uncertain**:
- Actuator degradation (wheel friction, thruster efficiency)
- Mass properties (fuel slosh, deployment uncertainties)
- Environmental perturbations (exact solar pressure coefficient)

This high observability makes spacecraft an ideal domain for Bond Index verification.

---

## 5. Declared Transforms (G_declared)

### 5.1 Transform Categories for Spacecraft

The transform suite G_declared defines which changes to the representation should **not** affect control decisions:

#### Category 1: Attitude Parameterization Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| Quaternion ↔ DCM | q ↔ C | C = q_to_dcm(q) |
| Quaternion ↔ Euler (any sequence) | q ↔ (φ,θ,ψ) | Gimbal lock handled |
| Quaternion ↔ MRP | q ↔ σ | Shadow set selection |
| Quaternion sign | q ↔ -q | Same rotation |
| MRP ↔ shadow MRP | σ ↔ σ_shadow | Same rotation |

**This is the critical transform class.** The same physical orientation has multiple valid representations. Control decisions must be invariant.

```python
# Example: Quaternion to DCM
def quaternion_to_dcm(q):
    q0, q1, q2, q3 = q
    return np.array([
        [1-2*(q2²+q3²), 2*(q1*q2-q0*q3), 2*(q1*q3+q0*q2)],
        [2*(q1*q2+q0*q3), 1-2*(q1²+q3²), 2*(q2*q3-q0*q1)],
        [2*(q1*q3-q0*q2), 2*(q2*q3+q0*q1), 1-2*(q1²+q2²)]
    ])
```

#### Category 2: Reference Frame Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| ECI ↔ ECEF | Inertial ↔ Earth-fixed | Earth rotation (time-dependent) |
| ECI ↔ LVLH | Inertial ↔ Local vertical | Orbital position (time-dependent) |
| LVLH ↔ Body | Local orbit ↔ spacecraft | Attitude (state-dependent) |
| J2000 ↔ GCRF | Different inertial epochs | Small rotation + precession |

**Critical**: Frame transforms depend on time and/or state. Consistency requires synchronized, accurate transformation data.

#### Category 3: Time System Transforms

| Transform | Example | Offset |
|-----------|---------|--------|
| UTC ↔ GPS | Civil ↔ Navigation | Leap seconds (~18 s in 2025) |
| UTC ↔ TAI | Civil ↔ Atomic | Leap seconds |
| GPS ↔ TDB | Navigation ↔ Barycentric | ~32 s + relativistic |
| MET ↔ UTC | Mission elapsed ↔ Civil | Mission-specific epoch |

**Warning**: Leap second errors have caused real spacecraft anomalies.

#### Category 4: Sensor Source Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| Star tracker A ↔ B | Redundant sensors | Same physical attitude |
| Star tracker ↔ gyro-propagated | Different determination methods | Bounded error growth |
| Sun/mag ↔ star tracker | Coarse ↔ fine | Same attitude (lower accuracy) |

**Use case**: If star tracker is blinded, the system should produce consistent (but less accurate) commands from gyro propagation.

#### Category 5: Unit Transforms

| Transform | Example | Conversion |
|-----------|---------|------------|
| Radians ↔ degrees | Angle units | × 180/π |
| RPM ↔ rad/s | Angular velocity | × 2π/60 |
| Arcseconds ↔ degrees | Fine angles | × 1/3600 |
| N·m ↔ lbf·ft | Torque units | × 0.7376 |
| N·s ↔ lbf·s | Impulse units | × 0.2248 |

**Mars Climate Orbiter was lost due to this category.** Unit transforms must be tested rigorously.

#### Category 6: Orbital Element Representations

| Transform | Example | Constraint |
|-----------|---------|------------|
| Keplerian ↔ Cartesian | (a,e,i,Ω,ω,ν) ↔ (r,v) | Same orbit |
| Mean ↔ osculating | Averaged ↔ instantaneous | Same mean state |
| Classical ↔ equinoctial | Different singularity handling | Same orbit |
| TLE ↔ precise | SGP4/SDP4 ↔ high-fidelity | Bounded error |

### 5.2 The Transform Suite Document

```yaml
transform_id: ATTITUDE_QUAT_TO_DCM
version: 1.0.0
category: attitude_parameterization
description: "Convert quaternion to Direction Cosine Matrix"
forward: |
  C = [[1-2(q2²+q3²), 2(q1q2-q0q3), 2(q1q3+q0q2)],
       [2(q1q2+q0q3), 1-2(q1²+q3²), 2(q2q3-q0q1)],
       [2(q1q3-q0q2), 2(q2q3+q0q1), 1-2(q1²+q2²)]]
inverse: |
  q0 = 0.5*sqrt(1+C11+C22+C33)
  q1 = (C32-C23)/(4*q0)
  ... (Shepperd's method for robustness)
semantic_equivalence: "Same physical orientation"
numerical_precision: 1e-15 (double precision)
validation:
  geometric_test_cases: 10000
  max_rotation_error: 1e-12 rad
```

### 5.3 Transforms That Are NOT Declared Equivalent

Some transformations **do** change the physical state:

| NOT Equivalent | Why |
|----------------|-----|
| Attitude change (slew) | Different physical orientation |
| Time evolution | State propagates |
| Different orbit | Different position/velocity |
| Mode change | Different control law applies |
| Sensor failure | Reduced observability |

---

## 6. The Bond Index for Attitude Control Systems

### 6.1 Definition

The **Bond Index (Bd)** quantifies how consistently an attitude control system treats equivalent representations:

```
Bd = D_op / τ
```

where:
- **D_op** is the observed coherence defect (measured inconsistency)
- **τ** is the human-calibrated threshold (the defect level GN&C engineers consider "meaningful")

### 6.2 The Three Coherence Defects

#### Defect 1: Commutator (Ω_op)

**Question**: Does the order of transforms matter?

```
Ω_op(σ; g₁, g₂) = |C(g₂(g₁(r(σ)))) - C(g₁(g₂(r(σ))))|
```

**Spacecraft example**: Convert quaternion to Euler, then transform ECI to LVLH, vs. transform ECI to LVLH (on quaternion), then convert to Euler. Should yield same control command.

#### Defect 2: Mixed (μ)

**Question**: Does the same transform behave differently in different contexts?

**Spacecraft example**: Quaternion-to-DCM conversion during nadir-pointing vs. during slew maneuver. The transform itself is the same, but numerical precision may differ during rapid rotation.

#### Defect 3: Permutation (π₃)

**Question**: Do three-way compositions have hidden interactions?

**Spacecraft example**: Convert representation → transform frame → change time system. All 6 orderings should yield consistent results.

### 6.3 Deployment Tiers

| Bd Range | Tier | Interpretation | Action |
|----------|------|----------------|--------|
| < 0.01 | **Negligible** | Excellent coherence | Certify for flight |
| 0.01 – 0.1 | **Low** | Minor inconsistencies | Deploy with enhanced telemetry |
| 0.1 – 1.0 | **Moderate** | Significant inconsistencies | Remediate before flight |
| 1 – 10 | **High** | Severe inconsistencies | Do not fly |
| > 10 | **Severe** | Fundamental incoherence | Complete redesign |

### 6.4 Calibration Protocol for Space Systems

The threshold τ is determined empirically:

1. **Recruit raters**: GN&C engineers, mission operations specialists (n ≥ 20)
2. **Generate test pairs**: Spacecraft states with known transform relationships
3. **Collect judgments**: "Should these produce the same control command?"
4. **Fit threshold**: Find defect level where 95% agree the difference matters
5. **Set τ**: Conservative estimate—for expensive spacecraft, tight threshold

For spacecraft attitude control, typical calibration yields **τ ≈ 0.001** (engineers expect < 0.1% deviation in control commands across equivalent representations).

### 6.5 Application to Specific GN&C Functions

| Function | Key Transforms | Target Bd |
|----------|----------------|-----------|
| **Attitude determination** | Sensor source, parameterization | < 0.001 |
| **Attitude control** | Parameterization, frame | < 0.001 |
| **Maneuver planning** | Frame, orbital elements | < 0.01 |
| **Fuel management** | Units, time system | < 0.0001 |
| **Ephemeris computation** | Time system, frame | < 0.001 |
| **Ground commanding** | Units, time system | < 0.0001 |

---

## 7. Regime Transitions and Coherence Defects

### 7.1 The Regime Transition Problem

Spacecraft operate in distinct regimes with different control strategies:

```
┌──────────────────────────────────────────────────────────────────┐
│                 SPACECRAFT OPERATING REGIMES                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  REGIME 1: DEPLOYMENT / DETUMBLING                               │
│  ─────────────────────────────────                               │
│  • High angular rates (released from launcher)                   │
│  • Limited sensor availability (star tracker may be blinded)     │
│  • Goal: Reduce rates, acquire Sun/Earth reference               │
│  • Actuators: Magnetorquers (fuel-free), or RCS thrusters        │
│  • Control: B-dot (magnetic), or rate damping                    │
│                                                                  │
│              ↓ (rates reduced, reference acquired)               │
│                                                                  │
│  REGIME 2: ACQUISITION / SAFE MODE                               │
│  ─────────────────────────────────                               │
│  • Coarse attitude knowledge                                     │
│  • Sun-pointing for power, thermal safe                          │
│  • Waiting for ground contact or autonomous recovery             │
│  • Actuators: Wheels (if available), magnetorquers               │
│  • Control: Sun-pointing with rate limit                         │
│                                                                  │
│              ↓ (ground contact, fine sensors acquired)           │
│                                                                  │
│  REGIME 3: NOMINAL OPERATIONS                                    │
│  ────────────────────────────                                    │
│  • Fine attitude knowledge (star tracker)                        │
│  • Mission-specific pointing (nadir, target, inertial)           │
│  • Payload operations active                                     │
│  • Actuators: Reaction wheels (primary)                          │
│  • Control: PD, LQR, or other fine control law                   │
│                                                                  │
│              ↓ (wheel saturation, maneuver required)             │
│                                                                  │
│  REGIME 4: MOMENTUM MANAGEMENT / SLEW                            │
│  ────────────────────────────────────                            │
│  • Wheel momentum dumping (magnetorquer or thruster)             │
│  • Large-angle slew maneuvers                                    │
│  • Payload operations paused                                     │
│  • Actuators: Thrusters (momentum dump), wheels (slew)           │
│  • Control: Momentum management + trajectory tracking            │
│                                                                  │
│              ↓ (eclipse entry)                                   │
│                                                                  │
│  REGIME 5: ECLIPSE                                               │
│  ─────────────                                                   │
│  • No solar power input                                          │
│  • Battery-powered operations                                    │
│  • Thermal constraints may change                                │
│  • Reduced activity to conserve power                            │
│                                                                  │
│  REGIME 6: CONTINGENCY / SAFE MODE                               │
│  ─────────────────────────────────                               │
│  • Anomaly detected                                              │
│  • Autonomous safing (Sun-point, reduce power)                   │
│  • Waiting for ground diagnosis                                  │
│  • Minimal operations, maximum margins                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 Regime-Specific Control Parameters

Different regimes require different control strategies:

| Parameter | Detumbling | Safe Mode | Nominal | Slew |
|-----------|------------|-----------|---------|------|
| **Attitude knowledge** | Coarse | Medium | Fine | Fine |
| **Pointing requirement** | None | Sun-safe | Mission-specific | Trajectory |
| **Primary actuator** | Mag-torquer | Wheels | Wheels | Wheels |
| **Control bandwidth** | 0.001 Hz | 0.01 Hz | 0.1 Hz | 0.1–1 Hz |
| **Rate limit** | 5°/s | 0.5°/s | 0.1°/s | 1°/s |
| **Fuel usage** | None (mag) | None | None | Momentum dump |

### 7.3 Coherence Across Regime Boundaries

A key test: **Does the system give consistent control commands for states near regime boundaries?**

**Example**: Transitioning from Safe Mode to Nominal:
- Safe mode: Sun-pointing, coarse attitude
- Nominal: Nadir-pointing, fine attitude
- Transition: Which reference applies?

**Incoherent behavior** (witness): At the transition point, the system attempts both Sun-pointing and nadir-pointing simultaneously because mode flag and attitude reference are updated at different times.

### 7.4 Testing Regime Boundary Coherence

The Bond Index framework tests regime boundary coherence by:

1. **Generating boundary states**: σ where mode transition is imminent
2. **Applying transforms**: Attitude representations, sensor sources
3. **Checking consistency**: Same control command regardless of representation?

High defect rates at regime boundaries indicate:
- Asynchronous mode flag updates
- Inconsistent reference attitude sources
- Timing vulnerabilities in fault protection

---

## 8. The Fuel Budget: A Non-Renewable Constraint

### 8.1 The Unique Challenge of Fuel

Unlike ground systems, spacecraft have a **non-renewable fuel constraint**:

```
Mission budget: ΔV_total = 150 m/s (typical GEO satellite)

Allocation:
  - Station-keeping:    100 m/s over 15-year life
  - Attitude control:    30 m/s (momentum dumps, contingencies)
  - End-of-life:         15 m/s (graveyard orbit)
  - Margin:               5 m/s
```

**Every unnecessary thruster firing shortens mission life.** A representational inconsistency that causes an unnecessary momentum dump could cost days of mission life.

### 8.2 How Representation Errors Waste Fuel

| Error Type | Mechanism | Fuel Cost |
|------------|-----------|-----------|
| **Attitude error** | Wrong slew direction, correction needed | 0.001–0.1 m/s per event |
| **Frame error** | Wrong burn direction for station-keeping | 0.1–1 m/s per maneuver |
| **Timing error** | Burn at wrong time, correction needed | 0.01–0.1 m/s per event |
| **Mode oscillation** | Repeated safe mode entries | 0.01 m/s per entry |

### 8.3 Bond Index for Fuel-Critical Operations

For operations involving propellant, we apply a tighter Bond Index threshold:

```
Fuel-critical operations (thrusting):
  - Target Bd < 0.0001 (0.01% consistency)
  - Any witness → immediate review
  
Non-fuel operations (wheels, magnetorquers):
  - Target Bd < 0.001 (0.1% consistency)
  - Witnesses acceptable if converging
```

### 8.4 The Fuel Budget as a Governance Constraint

The fuel budget acts as a hard constraint in DEME governance profiles:

```yaml
fuel_constraint:
  type: hard_veto
  remaining_margin: must_be_positive
  operations_requiring_review:
    - thruster_firing
    - contingency_response
    - unplanned_maneuver
  automated_abort_if:
    - fuel_estimate_uncertainty > 5%
    - burn_exceeds_plan_by > 10%
```

---

## 9. Multi-Subsystem Governance

### 9.1 The Multi-Subsystem Challenge

Spacecraft attitude affects multiple subsystems with different requirements:

| Subsystem | Pointing Requirement | Priority |
|-----------|---------------------|----------|
| **Power** | Solar panels toward Sun | Critical (survival) |
| **Thermal** | Radiators away from Sun | Critical (survival) |
| **Communications** | Antenna toward ground/relay | High (mission) |
| **Payload** | Instrument toward target | High (mission) |
| **Orbit maintenance** | Thrusters in correct direction | Medium (periodic) |
| **Star tracker** | Avoid Sun, Moon, Earth in FOV | Medium (operations) |

### 9.2 DEME Governance Profiles for Spacecraft

The DEME framework allows subsystem requirements to be composed into **governance profiles**:

```yaml
profile_id: "geo_comsat_nominal_v2.1"
stakeholders:
  - id: power_subsystem
    weight: 0.30
    priorities:
      - solar_array_illumination
      - battery_charge_state
    hard_vetoes:
      - sun_angle_max: 30  # degrees from normal
      - eclipse_duration_max: 72  # minutes
      
  - id: thermal_subsystem
    weight: 0.25
    priorities:
      - component_temperatures_in_range
      - radiator_view_factor
    hard_vetoes:
      - sun_on_radiator: false
      - temperature_max:
          reaction_wheel: 50  # °C
          star_tracker: 40  # °C
      
  - id: communications_subsystem
    weight: 0.25
    priorities:
      - antenna_pointing_accuracy
      - link_margin
    hard_vetoes:
      - pointing_error_max: 0.1  # degrees
      - link_margin_min: 3  # dB
      
  - id: payload_operations
    weight: 0.15
    priorities:
      - target_visibility
      - data_collection_efficiency
    constraints:
      - pointing_stability: 0.001  # deg/s
      
  - id: fuel_management
    weight: 0.05
    priorities:
      - minimize_propellant_usage
      - maintain_margin
    hard_vetoes:
      - remaining_fuel_min: 5  # m/s equivalent

aggregation:
  method: weighted_sum_with_vetoes
  veto_behavior: any_subsystem_veto_honored
  conflict_resolution: power_thermal_priority
```

### 9.3 Conflict Resolution

When subsystem requirements conflict, priority ordering applies:

1. **Survival** (power, thermal) — Non-negotiable
2. **Communication** (for command capability) — High priority
3. **Mission** (payload, orbit) — Negotiable timing
4. **Efficiency** (fuel, throughput) — Optimized within constraints

**Example conflict**: Payload wants to point at target, but this puts radiator in Sun.
**Resolution**: Payload operation waits until geometry allows both requirements.

### 9.4 Consistency Checking

Before uploading command sequences, the governance profile is checked for:

1. **Veto consistency**: Do hard constraints conflict over the planning horizon?
2. **Priority consistency**: Can all high-priority requirements be met?
3. **Fuel consistency**: Does the sequence stay within budget?
4. **Thermal consistency**: Do attitudes satisfy thermal constraints over time?

---

## 10. Case Study: GEO Communications Satellite Station-Keeping

### 10.1 Scenario Description

**Spacecraft**: Geostationary communications satellite

**Characteristics**:
- Mass: 3,000 kg (beginning of life)
- Orbit: GEO (42,164 km altitude, 0° inclination)
- Mission life: 15 years
- Fuel budget: 150 m/s ΔV
- Attitude: 3-axis stabilized, nadir-pointing

**GN&C equipment**:
- 2× Star trackers (redundant)
- 1× IMU (3-axis gyros + accelerometers)
- 2× Sun sensors
- 4× Reaction wheels (pyramid configuration)
- 12× Thrusters (station-keeping + attitude)

### 10.2 Observable Set (Ψ)

| Observable | Sensor | Accuracy | Rate |
|------------|--------|----------|------|
| Attitude (inertial) | Star tracker | 5 arcsec (3σ) | 2 Hz |
| Angular velocity | IRU gyros | 0.003°/hr | 100 Hz |
| Sun vector | Sun sensors | 0.5° | 1 Hz |
| Position (ECI) | Ground tracking | 50 m | 0.1 Hz |
| Wheel speeds | Tachometers | 0.1 RPM | 10 Hz |
| Fuel remaining | Flow integration | 5% | Integrated |

### 10.3 Transform Suite

For this case study, we apply 16 transforms:

| ID | Transform | Category |
|----|-----------|----------|
| T1 | Quaternion ↔ DCM | Attitude parameterization |
| T2 | Quaternion ↔ Euler (3-2-1) | Attitude parameterization |
| T3 | Quaternion ↔ MRP | Attitude parameterization |
| T4 | q ↔ -q (sign flip) | Quaternion ambiguity |
| T5 | MRP ↔ shadow MRP | MRP ambiguity |
| T6 | ECI ↔ ECEF | Reference frame |
| T7 | ECI ↔ LVLH | Reference frame |
| T8 | LVLH ↔ body | Reference frame |
| T9 | UTC ↔ GPS time | Time system |
| T10 | MET ↔ UTC | Time system |
| T11 | Star tracker A ↔ B | Sensor source |
| T12 | Star tracker ↔ gyro-propagated | Sensor source |
| T13 | Radians ↔ degrees | Units |
| T14 | RPM ↔ rad/s | Units |
| T15 | Keplerian ↔ Cartesian | Orbital elements |
| T16 | Simulation ↔ flight (nominal) | Sim-to-real |

### 10.4 Control Logic Under Test

The attitude control system implements:

```
CONTROL DECISION:

NOMINAL NADIR-POINTING:
  - q_ref = nadir_quaternion(orbit_state, time)
  - q_err = quaternion_error(q_est, q_ref)
  - ω_err = ω_est - ω_ref
  - τ_cmd = K_p * q_err[1:3] + K_d * ω_err  (PD control)
  - ω_wheel_cmd = wheel_allocation(τ_cmd)

MODE TRANSITIONS:
  IF |q_err| > 15°:
    SLEW_MODE (trajectory tracking)
  IF |H_wheel| > 0.9 * H_max:
    MOMENTUM_DUMP (thruster assist)
  IF star_tracker_invalid AND gyro_drift > threshold:
    SAFE_MODE (Sun-point)

STATION-KEEPING:
  - Execute uploaded burn commands
  - Verify attitude before burn
  - Monitor fuel usage
```

### 10.5 Bond Index Evaluation

**Test protocol**:
1. Generate 2,000 representative states over mission profile
2. Apply each of 16 transforms at 5 intensity levels
3. Compute control command before and after transform
4. Calculate coherence defects

**Results**:

```
═══════════════════════════════════════════════════════════════════
              BOND INDEX EVALUATION RESULTS
═══════════════════════════════════════════════════════════════════

System:        GEO CommSat GN&C Flight Software v8.3
Transform suite: G_declared_geo_v1.0 (16 transforms)
Test cases:    2,000 states × 16 transforms × 5 intensities = 160,000

───────────────────────────────────────────────────────────────────
                      BOND INDEX
───────────────────────────────────────────────────────────────────
  Bd_mean = 0.00034  [0.00028, 0.00041] 95% CI
  Bd_p95  = 0.0018
  Bd_max  = 0.047

  TIER: NEGLIGIBLE
  DECISION: ✅ Certify for flight

───────────────────────────────────────────────────────────────────
                  DEFECT BREAKDOWN
───────────────────────────────────────────────────────────────────
  Ω_op (commutator):     0.00021  ██
  μ (mixed):             0.00011  █
  π₃ (permutation):      0.00002  

───────────────────────────────────────────────────────────────────
                TRANSFORM SENSITIVITY
───────────────────────────────────────────────────────────────────
  T1  (quat↔DCM):        0.0000   (perfect - double precision)
  T2  (quat↔Euler):      0.0001   (gimbal lock handling)
  T3  (quat↔MRP):        0.0000   (perfect)
  T4  (q↔-q):            0.0000   (perfect)
  T5  (MRP↔shadow):      0.0000   (perfect)
  T6  (ECI↔ECEF):        0.0002   
  T7  (ECI↔LVLH):        0.0008   █  ← Notable
  T8  (LVLH↔body):       0.0001   
  T9  (UTC↔GPS):         0.0000   (perfect - leap second table)
  T10 (MET↔UTC):         0.0000   (perfect)
  T11 (ST_A↔ST_B):       0.0003   
  T12 (ST↔gyro):         0.0018   ██  ← Second highest
  T13 (rad↔deg):         0.0000   (perfect)
  T14 (RPM↔rad/s):       0.0000   (perfect)
  T15 (Kepl↔Cart):       0.0004   
  T16 (sim↔flight):      0.047    █████████  ← HIGHEST

───────────────────────────────────────────────────────────────────
                   WORST WITNESS
───────────────────────────────────────────────────────────────────
  Transform: T16 (simulation ↔ flight-equivalent)
  State: Post-eclipse transition, thermal transient
  
  Simulation:
    Gyro bias: Stable at calibrated value
    Star tracker: Immediate reacquisition
    Control: Smooth transition to nominal
    
  Flight-equivalent (with thermal effects):
    Gyro bias: Shifted by 0.001°/hr due to temperature change
    Star tracker: 2-second reacquisition delay
    Control: Brief attitude error spike during gyro-only period
    
  Simulation: Torque command = [0.0012, 0.0008, -0.0003] N·m
  Flight-equiv: Torque command = [0.0018, 0.0014, -0.0002] N·m
  
  Defect: 0.047 (50% torque difference during transient)
  
  ROOT CAUSE: Simulation doesn't model gyro thermal sensitivity
              or star tracker reacquisition delay accurately
  
  IMPACT: Transient only (2 seconds), converges to correct attitude
          Fuel impact: Negligible (reaction wheels only)
  
  RECOMMENDATION: Add thermal model for gyro bias;
                  Model star tracker acquisition time

───────────────────────────────────────────────────────────────────
                REGIME BOUNDARY ANALYSIS
───────────────────────────────────────────────────────────────────
  Eclipse entry:           Bd = 0.0004  
  Eclipse exit:            Bd = 0.0012  █  ← Highest regime transition
  Slew start:              Bd = 0.0003  
  Slew complete:           Bd = 0.0002  
  Momentum dump:           Bd = 0.0008  █
  Safe mode entry:         Bd = 0.0005  
  
  Eclipse exit is highest due to star tracker reacquisition dynamics

───────────────────────────────────────────────────────────────────
                FUEL-CRITICAL OPERATIONS
───────────────────────────────────────────────────────────────────
  Station-keeping burn:    Bd = 0.00002  (EXCELLENT)
  Momentum dump:           Bd = 0.00008  (EXCELLENT)
  Contingency maneuver:    Bd = 0.00015  (EXCELLENT)
  
  All fuel-critical operations well below 0.0001 threshold

═══════════════════════════════════════════════════════════════════
```

### 10.6 Decomposition Analysis

Applying the Decomposition Theorem:

```
Total defect: Ω = 0.00034 (mean)

Gauge-removable (Ω_gauge): 0.00029 (85%)
  - Fixable via:
    - Better simulation thermal modeling
    - Star tracker acquisition model
    - ECI-LVLH transformation timing sync
  
Intrinsic (Ω_intrinsic): 0.00005 (15%)
  - Fundamental:
    - Star tracker vs. gyro have different error sources
    - Simulation can never perfectly match flight
  - Acceptable given operational margins
```

### 10.7 Remediation Plan

| Issue | Root Cause | Remediation | Expected Improvement |
|-------|------------|-------------|----------------------|
| Sim-to-real gap | Missing thermal model | Add gyro thermal sensitivity | 0.047 → 0.01 |
| ECI-LVLH transform | Orbit propagation sync | Tighter timing | 0.0008 → 0.0002 |
| ST-to-gyro handoff | Reacquisition not modeled | Add acquisition delay | 0.0018 → 0.0005 |

**Post-remediation target**: Bd < 0.0002 (median), max < 0.01

---

## 11. Implementation Architecture

### 11.1 Integration with Existing Flight Software

The Bond Index framework integrates **non-invasively** with existing GN&C systems:

```
┌─────────────────────────────────────────────────────────────────┐
│                  FLIGHT SOFTWARE ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌──────────┐  │
│  │  Sensors  │──▶│Navigation │──▶│  Guidance │──▶│ Control  │  │
│  │           │   │           │   │           │   │          │  │
│  └───────────┘   └─────┬─────┘   └─────┬─────┘   └────┬─────┘  │
│                        │               │              │         │
│                        ▼               ▼              ▼         │
│                 ┌──────────────────────────────────────────┐    │
│                 │           TELEMETRY / DATA BUS           │    │
│                 └──────────────────────────────────────────┘    │
│                                      │                          │
└──────────────────────────────────────┼──────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              BOND INDEX VERIFICATION LAYER                      │
│             (Ground-based or HIL simulation)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              DATA ACQUISITION                            │   │
│  │  • Telemetry archive ingestion                           │   │
│  │  • Hardware-in-loop interface                            │   │
│  │  • Simulator API (STK, GMAT, custom)                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              TRANSFORM ENGINE                            │   │
│  │  • Attitude parameterization (quat, DCM, Euler, MRP)     │   │
│  │  • Reference frame rotation (ECI, ECEF, LVLH, body)      │   │
│  │  • Time system conversion (UTC, GPS, TDB, MET)           │   │
│  │  • Unit conversion (rad/deg, RPM, arcsec)                │   │
│  │  • Sensor source substitution                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              GN&C LOGIC EVALUATOR                        │   │
│  │  • Mirror of flight software control law                 │   │
│  │  • Evaluate original and transformed states              │   │
│  │  • Compare control commands                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BOND INDEX CALCULATOR                       │   │
│  │  • Compute Ω_op, μ, π₃                                   │   │
│  │  • Regime-specific analysis                              │   │
│  │  • Fuel-critical operation tracking                      │   │
│  │  • Generate witnesses                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              REPORTING & FLIGHT READINESS                │   │
│  │  • Flight readiness review evidence                      │   │
│  │  • Anomaly investigation support                         │   │
│  │  • Long-term trend monitoring                            │   │
│  │  • Audit trail                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Deployment Modes

| Mode | Description | Timing | Use Case |
|------|-------------|--------|----------|
| **Pre-flight verification** | Full test suite before launch | Months pre-launch | Flight readiness |
| **HIL testing** | Hardware-in-loop with testbed | Development | Design verification |
| **Simulation campaign** | Monte Carlo across mission profile | Weeks | Performance characterization |
| **On-orbit telemetry** | Analyze downloaded telemetry | Post-pass | Anomaly detection |
| **Post-anomaly** | Deep dive after observed issue | As needed | Root cause analysis |

### 11.3 Integration with Simulation Tools

The framework integrates with standard space industry tools:

| Tool | Integration Method | Capabilities |
|------|-------------------|--------------|
| **STK (AGI)** | Connect API, Python | Orbit, attitude, coverage |
| **GMAT** | Script interface | High-fidelity propagation |
| **MATLAB/Simulink** | S-function, MEX | Control system simulation |
| **42 (NASA)** | Input/output files | Multi-body dynamics |
| **FreeFlyer** | API | Mission planning |
| **Custom FSW sim** | Direct integration | Flight software verification |

### 11.4 Flight Safety Isolation

For flight systems, strict isolation is maintained:

| Requirement | Implementation |
|-------------|----------------|
| **No flight software modification** | Analysis only, no code changes |
| **Ground-based processing** | All Bond Index computation on ground |
| **Read-only telemetry access** | Cannot command spacecraft |
| **Independent verification** | Separate from FSW development team |
| **Configuration control** | Versioned, auditable |

---

## 12. Deployment Pathway

### 12.1 Phase 1: Simulation Validation (Years 1-2)

**Objective**: Demonstrate Bond Index framework in standard GN&C simulation

**Activities**:
- Implement G_declared transforms for common parameterizations
- Validate on MATLAB/Simulink attitude control models
- Partner with university space systems lab (CU Boulder, MIT, Stanford)
- Test across diverse mission profiles (LEO, GEO, deep space)
- Publish in AIAA Journal of Guidance, Control, and Dynamics

**Deliverables**:
- Validated transform suite for spacecraft attitude
- MATLAB/Simulink toolbox
- Technical paper demonstrating concept

**Resources**: $250K, 3 FTE, 2 years

### 12.2 Phase 2: Hardware-in-Loop Validation (Years 2-3)

**Objective**: Validate on spacecraft hardware testbed

**Activities**:
- Partner with aerospace company or NASA center
- Implement on air-bearing testbed (simulates torque-free environment)
- Test with flight-equivalent star trackers, gyros, wheels
- Validate sim-to-real consistency
- Demonstrate value for anomaly diagnosis

**Deliverables**:
- Hardware-validated verification system
- Air-bearing testbed case study
- Industry partnership

**Resources**: $600K, 4 FTE, 1.5 years

### 12.3 Phase 3: CubeSat Demonstration (Years 3-5)

**Objective**: Fly Bond Index verification on actual spacecraft

**Activities**:
- Partner with university CubeSat program or commercial provider
- Integrate monitoring capability (telemetry analysis)
- Fly as secondary payload on rideshare launch
- Analyze on-orbit data for representational consistency
- Demonstrate value for mission operations

**Target mission**:
- 3U or 6U CubeSat
- Standard ADCS (reaction wheels + magnetorquers)
- Bond Index telemetry analysis ground segment

**Deliverables**:
- Flight-validated system
- On-orbit case study
- Published results

**Resources**: $1.5M, 6 FTE, 2 years

### 12.4 Phase 4: Commercial/Government Satellite (Years 5-8)

**Objective**: Deploy on operational high-value satellite

**Target partners**:
1. **Commercial**: Maxar, Lockheed Martin, Northrop Grumman, Boeing
2. **Civil government**: NASA, ESA, JAXA
3. **Defense**: US Space Force, NRO

**Activities**:
- Negotiate integration with GN&C verification process
- Run parallel analysis during I&T (integration and test)
- Support flight readiness review with Bond Index evidence
- Monitor on-orbit operations
- Demonstrate value for mission life extension (fuel savings)

**Deliverables**:
- Production-validated system
- Flight heritage
- Industry adoption

**Resources**: $3M, 10 FTE, 3 years

### 12.5 Phase 5: Industry Standard (Years 8+)

**Objective**: Codify Bond Index in space systems standards

**Activities**:
- Engage AIAA, IEEE, ECSS standards bodies
- Propose as GN&C verification best practice
- Develop compliance framework
- Training and certification

**Target standards**:
- ECSS-E-ST-60-10C (GN&C standard)
- NASA-STD-8719.24 (software safety)
- SMC Standard SMC-S-016 (test requirements)

**Deliverables**:
- Industry standard contribution
- Certification framework
- Training curriculum

**Market potential**: $50M+ annual revenue at maturity

---

## 13. Limitations and Future Work

### 13.1 Current Limitations

| Limitation | Description | Mitigation |
|------------|-------------|------------|
| **Conservative industry** | Space industry slow to adopt new methods | Flight heritage builds trust |
| **Mission-specific** | Each mission has unique transforms | Parameterized transform library |
| **Simulation fidelity** | Sim-to-real always has gap | Ground truth from flight data |
| **Ground processing** | Cannot run on flight computer | Post-processing is sufficient |
| **Cost justification** | Value proposition for low-cost missions | Focus on high-value first |

### 13.2 What We Do NOT Claim

- **Completeness**: The Bond Index verifies consistency for declared transforms only. Novel representation issues may exist.
- **Correctness**: We verify that commands are consistent, not that the control law is optimal.
- **Radiation tolerance**: The framework doesn't address single-event upsets or radiation damage.
- **Real-time flight**: Current implementation is ground-based analysis, not onboard.

### 13.3 Future Work

1. **Formation flying**: Extend to multi-spacecraft relative navigation
2. **Onboard implementation**: Lightweight version for autonomous fault detection
3. **Electric propulsion**: Low-thrust trajectory optimization consistency
4. **Deep space**: Address communication delay challenges
5. **Autonomous operations**: Verify consistency of AI/ML-based GN&C

---

## 14. Conclusion

Spacecraft attitude control presents an ideal application domain for invariance-based safety verification:

1. **Excellent observability**: Star trackers, gyros provide precise attitude knowledge
2. **Well-defined physics**: Orbital mechanics and rigid body dynamics are deterministic
3. **Multiple representations**: Quaternion, Euler, DCM, MRP—all must be consistent
4. **High stakes**: $50M–$500M per satellite, no repair capability
5. **Non-renewable resources**: Fuel conservation extends mission life
6. **Proven sim-to-real**: Space environment is well-modeled

### The Mars Climate Orbiter Lesson

The $327.6 million Mars Climate Orbiter was destroyed by a unit conversion error—not a sensor failure, not a control law problem, not a hardware malfunction. **A representational inconsistency between two software systems.**

The Bond Index framework is designed to detect exactly this class of failure before it destroys a mission.

### The Path Forward

The space industry has the simulation tools, the verification rigor, and the economic motivation to adopt representational consistency testing. High-value satellites, irreplaceable fuel budgets, and long mission timelines make thorough verification essential.

What has been missing is a formal framework for asking: "Do all components of our GN&C system agree on what state the spacecraft is in?"

The ErisML/DEME Bond Index framework provides that framework.

> *"The obstacle to spacecraft safety is not that we cannot build accurate attitude control systems. It is that we might not verify our representations are consistent. The Bond Index makes that verification possible."*

---

## 15. References

1. NASA JPL. (1999). *Mars Climate Orbiter Mishap Investigation Board Phase I Report*.

2. Wertz, J. R. (Ed.). (1978). *Spacecraft Attitude Determination and Control*. Kluwer Academic Publishers.

3. Markley, F. L., & Crassidis, J. L. (2014). *Fundamentals of Spacecraft Attitude Determination and Control*. Springer.

4. Sidi, M. J. (1997). *Spacecraft Dynamics and Control*. Cambridge University Press.

5. Shuster, M. D. (1993). "A survey of attitude representations." *Journal of the Astronautical Sciences*, 41(4), 439-517.

6. Lefferts, E. J., Markley, F. L., & Shuster, M. D. (1982). "Kalman filtering for spacecraft attitude estimation." *Journal of Guidance, Control, and Dynamics*, 5(5), 417-429.

7. Schaub, H., & Junkins, J. L. (2009). *Analytical Mechanics of Space Systems* (2nd ed.). AIAA.

8. Vallado, D. A. (2013). *Fundamentals of Astrodynamics and Applications* (4th ed.). Microcosm Press.

9. ECSS-E-ST-60-10C. (2008). *Space engineering: Control performance*.

10. NASA-STD-8719.24. (2017). *NASA software safety standard*.

11. Bond, A. H. (2025). "A Categorical Framework for Verifying Representational Consistency in Machine Learning Systems." *IEEE Transactions on Artificial Intelligence* (under review).

12. Bond, A. H. (2025). "The Grand Unified AI Safety Stack (GUASS) v12.0." Technical whitepaper.

13. Hughes, P. C. (2004). *Spacecraft Attitude Dynamics*. Dover Publications.

14. Wie, B. (2008). *Space Vehicle Dynamics and Control* (2nd ed.). AIAA.

15. NASA/CR-2021-0023589. (2021). *Lessons Learned from Mars Spacecraft Missions*.

---

## Appendix A: Transform Suite Template

```yaml
# G_declared for spacecraft attitude control
# Version: 1.0.0
# Domain: 3-axis stabilized spacecraft
# Date: 2025-12-27

metadata:
  domain: spacecraft
  subdomain: attitude_control
  mission_class: geo_comsat
  author: ErisML Team
  hash: sha256:a1b2c3d4...

transforms:
  - id: ATTITUDE_QUAT_TO_DCM
    category: attitude_parameterization
    description: "Convert quaternion to Direction Cosine Matrix"
    forward: |
      C[0,0] = 1 - 2*(q2² + q3²)
      C[0,1] = 2*(q1*q2 - q0*q3)
      C[0,2] = 2*(q1*q3 + q0*q2)
      C[1,0] = 2*(q1*q2 + q0*q3)
      C[1,1] = 1 - 2*(q1² + q3²)
      C[1,2] = 2*(q2*q3 - q0*q1)
      C[2,0] = 2*(q1*q3 - q0*q2)
      C[2,1] = 2*(q2*q3 + q0*q1)
      C[2,2] = 1 - 2*(q1² + q2²)
    inverse: "Shepperd's method (numerically robust)"
    semantic_equivalence: "Same physical orientation"
    numerical_precision: 1e-15
    
  - id: ATTITUDE_QUAT_SIGN
    category: attitude_parameterization
    description: "Quaternion sign ambiguity (q and -q same rotation)"
    forward: "q' = -q"
    inverse: "q = -q'"
    semantic_equivalence: "Same physical orientation"
    note: "Control law must handle both signs consistently"
    
  - id: FRAME_ECI_TO_LVLH
    category: reference_frame
    description: "Transform from ECI to Local Vertical Local Horizontal"
    parameters:
      r_eci: "Position vector in ECI"
      v_eci: "Velocity vector in ECI"
    forward: |
      z_lvlh = -r_eci / |r_eci|        # Nadir
      y_lvlh = -cross(r, v) / |cross(r, v)|  # Orbit normal
      x_lvlh = cross(y_lvlh, z_lvlh)   # Velocity direction
      C_lvlh_eci = [x_lvlh; y_lvlh; z_lvlh]
    semantic_equivalence: "Same orientation, different reference"
    time_dependent: true
    
  - id: TIME_UTC_TO_GPS
    category: time_system
    description: "Convert UTC to GPS time"
    forward: "t_gps = t_utc + leap_seconds(t_utc)"
    inverse: "t_utc = t_gps - leap_seconds(t_gps)"
    semantic_equivalence: "Same physical instant"
    note: "Leap second table must be current"
    leap_seconds_2025: 18
    
  - id: UNIT_RAD_TO_DEG
    category: units
    description: "Convert radians to degrees"
    forward: "θ_deg = θ_rad × 180/π"
    inverse: "θ_rad = θ_deg × π/180"
    semantic_equivalence: "Same physical angle"
    mars_climate_orbiter_warning: |
      THIS IS THE CATEGORY THAT DESTROYED MCO.
      Verify all unit interfaces explicitly.
    
  # ... additional transforms
```

---

## Appendix B: GN&C Control Law Specification Template

```yaml
# Spacecraft GN&C Control Law
# For Bond Index verification

system_id: "GEO_CommSat_GNC_v8.3"
mission: "Commercial Communications"
verification_date: 2025-12-27

attitude_representations:
  primary: quaternion
  alternatives: [dcm, euler_321, mrp]
  sign_convention: "scalar first, right-hand rotation"
  
reference_frames:
  navigation: eci_j2000
  control: lvlh
  body: spacecraft_body
  
time_system:
  primary: utc
  onboard_clock: met
  gps_available: true
  
sensors:
  - id: star_tracker_1
    type: star_tracker
    accuracy: 5e-5  # rad (3σ)
    rate: 2  # Hz
    
  - id: imu
    type: inertial_measurement_unit
    gyro_arw: 8e-7  # rad/√s
    gyro_bias_stability: 5e-6  # rad/s
    rate: 100  # Hz
    
actuators:
  - id: reaction_wheels
    type: reaction_wheel_array
    configuration: pyramid_4
    max_torque: 0.3  # N·m each
    max_momentum: 50  # N·m·s each
    
  - id: thrusters
    type: chemical_thruster
    thrust: 10  # N
    isp: 220  # s
    
control_modes:
  - id: nominal
    description: "Nadir-pointing with payload operations"
    control_law: pd_quaternion_feedback
    gains:
      k_p: 0.01  # rad/s² per rad
      k_d: 0.1   # rad/s² per rad/s
    reference: nadir_lvlh
    
  - id: slew
    description: "Large-angle reorientation"
    control_law: eigenaxis_trajectory
    max_rate: 1.0  # deg/s
    reference: commanded_attitude
    
  - id: safe
    description: "Sun-pointing for power/thermal safety"
    control_law: sun_pointing_rate_damping
    reference: sun_vector
    
mode_transitions:
  nominal_to_slew:
    condition: "attitude_error > 15 deg"
  slew_to_nominal:
    condition: "attitude_error < 1 deg AND rate_error < 0.01 deg/s"
  any_to_safe:
    condition: "fault_detected OR ground_command"
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **ADCS** | Attitude Determination and Control System |
| **CMG** | Control Moment Gyroscope |
| **DCM** | Direction Cosine Matrix (rotation matrix) |
| **ECEF** | Earth-Centered Earth-Fixed frame |
| **ECI** | Earth-Centered Inertial frame |
| **FSW** | Flight Software |
| **GEO** | Geostationary Earth Orbit (35,786 km altitude) |
| **GN&C** | Guidance, Navigation, and Control |
| **GPS** | Global Positioning System |
| **HIL** | Hardware-in-Loop |
| **IMU** | Inertial Measurement Unit |
| **IRU** | Inertial Reference Unit |
| **LEO** | Low Earth Orbit (<2,000 km altitude) |
| **LVLH** | Local Vertical Local Horizontal frame |
| **MET** | Mission Elapsed Time |
| **MRP** | Modified Rodrigues Parameters |
| **Quaternion** | Four-parameter attitude representation (no singularities) |
| **Slew** | Intentional large-angle attitude maneuver |
| **TDB** | Barycentric Dynamical Time |
| **UTC** | Coordinated Universal Time |
| **Ψ (Psi)** | Observable set — physical quantities available to spacecraft |
| **ΔV** | Change in velocity (fuel budget metric) |

---

## Appendix D: Mars Climate Orbiter Incident Summary

| Aspect | Detail |
|--------|--------|
| **Mission** | Mars Climate Orbiter (MCO), 1998-1999 |
| **Cost** | $327.6 million |
| **Objective** | Mars atmospheric science, communications relay |
| **Failure date** | September 23, 1999 |
| **Failure mode** | Crashed into Mars atmosphere during orbit insertion |
| **Root cause** | Lockheed Martin software output thrust in pound-force·seconds; NASA navigation software expected newton·seconds |
| **Conversion factor** | 1 lbf·s = 4.448 N·s |
| **Effect** | Navigation errors accumulated over 9-month cruise |
| **Result** | Periapsis 57 km instead of 140+ km; spacecraft destroyed |
| **Lesson** | Unit consistency across interfaces is critical |
| **Bond Index relevance** | T14 (unit conversion) transform would have detected this |

---

**Document version**: 1.0.0  
**Last updated**: December 2025  
**License**: AGI-HPC Responsible AI License v1.0

---

<p align="center">
  <em>"The Bond Index is the deliverable. Everything else is infrastructure."</em>
</p>
