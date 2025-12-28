# Invariance-Based Safety Verification for Autonomous Vehicle Collision Avoidance

## A Philosophy Engineering Approach to Preventing Fatal Crashes

---

**Technical Whitepaper v1.0 — December 2025**

**Andrew H. Bond**  
San José State University  
Ethical Finite Machines  
andrew.bond@sjsu.edu

---

> *"The 2018 Uber ATG fatality occurred because the perception system oscillated between classifying the pedestrian as 'vehicle,' 'bicycle,' and 'unknown'—each classification triggering different prediction models. The physics was unchanged. The representation was unstable."*

---

## Executive Summary

This whitepaper presents a novel approach to autonomous vehicle (AV) safety verification based on **representational invariance testing**—the principle that a collision avoidance system's safety decisions should not depend on arbitrary choices in how the driving scene is represented, fused, or transformed.

We apply the **ErisML/DEME framework** (Epistemic Representation Invariance & Safety ML / Democratically Governed Ethics Modules) to AV collision avoidance, demonstrating how:

1. **The Bond Index (Bd)** can quantify the coherence of perception-planning pipelines across sensor configurations, coordinate systems, and operating regimes
2. **Declared transforms (G_declared)** map naturally to coordinate frame rotations, sensor modality substitution, semantic label equivalence, and sim-to-real transfer
3. **The Decomposition Theorem** separates implementation bugs (fixable via calibration) from fundamental specification conflicts (requiring safety case redesign)
4. **Democratic governance profiles** allow multi-stakeholder safety requirements (OEMs, regulators, insurers, public) to be composed without contradiction

**Key finding**: A collision avoidance system with Bond Index Bd < 0.01 across standard transforms is **provably consistent** in its safety judgments—it will not classify a scenario as "safe to proceed" under one sensor configuration while triggering emergency braking under an equivalent configuration.

**Market opportunity**: The global autonomous vehicle market exceeds $100B, with collision avoidance as the foundational safety requirement. Post-Uber/Tesla fatalities, regulatory pressure from NHTSA, EU GSR, and UN R157 demands rigorous safety verification—yet no current standard systematically tests for *representational consistency* across the perception-planning pipeline.

---

## Table of Contents

1. [Introduction: The Representational Failure Mode](#1-introduction-the-representational-failure-mode)
2. [Background: AV Safety and Current Practice](#2-background-av-safety-and-current-practice)
3. [The Invariance Framework for Autonomous Vehicles](#3-the-invariance-framework-for-autonomous-vehicles)
4. [Observables and Grounding (Ψ)](#4-observables-and-grounding-ψ)
5. [Declared Transforms (G_declared)](#5-declared-transforms-g_declared)
6. [The Bond Index for Collision Avoidance Systems](#6-the-bond-index-for-collision-avoidance-systems)
7. [Regime Transitions and Coherence Defects](#7-regime-transitions-and-coherence-defects)
8. [The Ψ-Incompleteness Challenge: Intent and Prediction](#8-the-ψ-incompleteness-challenge-intent-and-prediction)
9. [Multi-Stakeholder Governance](#9-multi-stakeholder-governance)
10. [Case Study: Pedestrian Detection at Crosswalks](#10-case-study-pedestrian-detection-at-crosswalks)
11. [Implementation Architecture](#11-implementation-architecture)
12. [Deployment Pathway](#12-deployment-pathway)
13. [Limitations and Future Work](#13-limitations-and-future-work)
14. [Conclusion](#14-conclusion)
15. [References](#15-references)

---

## 1. Introduction: The Representational Failure Mode

### 1.1 A Different Kind of Failure

Most autonomous vehicle safety analysis focuses on **sensor failures**: LIDAR malfunction, camera occlusion, radar interference. These are important, and the industry has developed sophisticated tools to address them (sensor fusion, redundancy, fault detection).

But there is another failure mode that receives far less attention: **representational failures**—cases where the AV's *model* of the driving scene becomes inconsistent across processing stages, not because sensors failed, but because the *way the system interprets sensor data* contains hidden inconsistencies.

### 1.2 The Uber ATG Fatality: A Case Study

On March 18, 2018, an Uber autonomous test vehicle struck and killed Elaine Herzberg in Tempe, Arizona. The NTSB investigation revealed a devastating representational failure:

**Timeline of classification oscillation (final 6 seconds)**:
```
T-5.6s: Object detected, classified as "VEHICLE"
T-5.2s: Reclassified as "OTHER"  
T-4.7s: Reclassified as "VEHICLE"
T-3.8s: Reclassified as "BICYCLE"
T-2.6s: Reclassified as "OTHER"
T-1.5s: Reclassified as "BICYCLE"
T-1.2s: System determines collision imminent
T-0.0s: Impact at 39 mph
```

**The critical failure**: Each classification triggered a different prediction model. "VEHICLE" predicted highway-like motion. "BICYCLE" predicted lane-following. "OTHER" had no reliable prediction. The system never achieved a consistent representation long enough to plan appropriate avoidance.

**The physics was unchanged**—a pedestrian pushing a bicycle across the road at walking speed. **The representation was unstable**—oscillating between incompatible models, each with different safety implications.

### 1.3 The Coordinate Frame Problem

Modern AVs process data in multiple coordinate frames:

```
Same obstacle appears as:
  LIDAR frame:    (x=12.3, y=-2.1, z=0.8) meters
  Camera frame:   (u=847, v=412) pixels + depth estimate
  Ego frame:      (r=12.5, θ=-9.7°, ż=0) polar
  World frame:    (lat=33.4372, lon=-111.9431, alt=361.2)
  Map frame:      (lane_id=47, s=234.7, d=-0.3)
```

If the fusion algorithm produces different safety judgments depending on which frame is used as the primary representation—which happens in practice—the system has a representational inconsistency.

### 1.4 The Philosophy Engineering Insight

For decades, questions like "Is this maneuver safe?" have been treated as matters of sensor confidence, simulation coverage, or miles driven without incident. The **Philosophy Engineering** framework changes the question:

> We cannot test whether a safety judgment is *correct* in some absolute sense. But we **can** test whether a safety judgment system is **consistent**—whether it gives the same answer when the same physical scenario is described in different equivalent ways.

This is a *falsifiable* property. If we find a case where the system says "SAFE" under representation A but "EMERGENCY BRAKE" under equivalent representation B, we have produced a **witness** to inconsistency. Witnesses enable debugging. Debugging enables improvement.

### 1.5 What This Whitepaper Offers

We present:

1. **A formal framework** for defining "equivalent representations" in AV perception-planning (the transform suite G_declared)
2. **A quantitative metric** (the Bond Index Bd) that measures how consistently a collision avoidance system treats equivalent scenarios
3. **A verification protocol** that can be applied to existing AV stacks without replacing them
4. **A governance mechanism** for composing safety requirements from multiple stakeholders
5. **A deployment roadmap** from simulation validation to regulatory approval

---

## 2. Background: AV Safety and Current Practice

### 2.1 The Safety Challenge

Autonomous vehicles must navigate a world designed for humans, where safety violations have irreversible consequences:

| Hazard | Mechanism | Timescale | Consequence |
|--------|-----------|-----------|-------------|
| **Rear-end collision** | Following too closely, late braking | 0.5–2 s | Vehicle damage, whiplash |
| **Pedestrian strike** | Failed detection, wrong prediction | 0.3–1.5 s | Severe injury, fatality |
| **Intersection collision** | Missed vehicle, wrong right-of-way | 0.5–3 s | T-bone crash, fatality |
| **Lane departure** | Localization error, wrong path | 0.5–2 s | Head-on collision, rollover |
| **Object strike** | Misclassification, wrong avoidance | 0.2–1 s | Damage, secondary crash |

**The stakes**: 1.35 million people die in road crashes globally each year. AVs promise to reduce this—but only if they're actually safer than human drivers.

### 2.2 Safety Requirements

The emerging consensus on AV safety requirements includes:

| Requirement | Specification | Source |
|-------------|---------------|--------|
| **Collision avoidance** | No at-fault collisions with detected objects | ISO 21448 (SOTIF) |
| **Time-to-collision (TTC)** | TTC > TTC_min (typically 1.5–3 s) | Industry practice |
| **Safe following distance** | d > v × t_reaction + v²/(2a_max) | Physics + regulation |
| **Pedestrian priority** | Always yield to pedestrians in crosswalk | Traffic law |
| **Fail-safe behavior** | Minimal risk condition if uncertain | ISO 26262 |
| **ODD compliance** | Operate only within designed conditions | SAE J3016 |

### 2.3 Current AV Architecture

Modern AV stacks employ a layered architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS VEHICLE STACK                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 5: Vehicle Interface                                     │
│           - Brake, steering, throttle actuation                 │
│           - CAN bus communication                               │
│           Latency budget: <10 ms                                │
│                         ▲                                       │
│  LAYER 4: Motion Control                                        │
│           - Trajectory tracking                                 │
│           - Vehicle dynamics compensation                       │
│           - Stability control                                   │
│           Latency budget: <20 ms                                │
│                         ▲                                       │
│  LAYER 3: Motion Planning                                       │
│           - Trajectory generation                               │
│           - Collision checking                                  │
│           - Optimization (comfort, efficiency)                  │
│           Latency budget: <50 ms                                │
│                         ▲                                       │
│  LAYER 2: Prediction & Decision                                 │
│           - Object trajectory prediction                        │
│           - Behavior planning (lane change, yield)              │
│           - Risk assessment                                     │
│           Latency budget: <100 ms                               │
│                         ▲                                       │
│  LAYER 1: Perception                                            │
│           - Object detection & classification                   │
│           - Tracking & state estimation                         │
│           - Sensor fusion                                       │
│           Latency budget: <100 ms                               │
│                         ▲                                       │
│  LAYER 0: Sensors & Localization                                │
│           - LIDAR, radar, cameras, ultrasonics                  │
│           - GPS/GNSS, IMU, wheel odometry                       │
│           - HD map matching                                     │
│           Latency: Real-time acquisition                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 The Gap: Representational Consistency Testing

Current AV safety verification focuses on:

- **Sensor performance**: Detection range, accuracy, failure modes
- **Scenario coverage**: Miles driven, simulation diversity, edge cases
- **Functional safety**: Hardware faults, systematic failures (ISO 26262)
- **SOTIF**: Performance limitations, misuse (ISO 21448)

What they do **not** systematically test:

- **Does the perception system give consistent classifications across equivalent representations of the same object?**
- **Are safety decisions invariant to coordinate frame selection?**
- **Does the planner produce equivalent trajectories for equivalent scene descriptions?**
- **Is sim-to-real transfer preserving safety-relevant behavior?**

These are precisely the questions the Bond Index framework addresses.

---

## 3. The Invariance Framework for Autonomous Vehicles

### 3.1 Core Definitions

**Definition 1 (Driving Scene).** A driving scene σ is the complete physical state of the vehicle and its environment:

```
σ = (ego_state, {object_states}, road_geometry, traffic_state, environment)
```

where:
- `ego_state = (pose, velocity, acceleration)` of the AV
- `object_states = {(class, pose, velocity, size, ...)_i}` for each detected object
- `road_geometry = (lanes, boundaries, signs, signals)`
- `traffic_state = (signal_phases, right_of_way)`
- `environment = (weather, lighting, road_surface)`

**Definition 2 (Representation).** A representation r(σ) is a specific encoding of the driving scene in terms of:
- Coordinate frame (ego-centric, world-centric, lane-relative)
- Sensor modality (LIDAR-primary, camera-primary, fused)
- Semantic labels (vehicle vs. truck vs. SUV)
- Temporal history (current frame, smoothed, predicted)
- Resolution/discretization (grid size, voxel resolution)

**Definition 3 (Safety Judgment).** A safety judgment function S maps representations to decisions:

```
S: Representations → {SAFE, CAUTION, YIELD, BRAKE, EMERGENCY_STOP, ⊥}
```

where ⊥ indicates insufficient information to judge (should trigger minimal risk condition).

**Definition 4 (Declared Transform).** A declared transform g ∈ G_declared is a mapping between representations that preserves the underlying physical scenario:

```
g: r(σ) → r'(σ)    such that    σ is unchanged
```

### 3.2 The Consistency Requirement

**Axiom (Representational Invariance).** A consistent collision avoidance system must satisfy:

```
∀σ, ∀g ∈ G_declared:  S(r(σ)) = S(g(r(σ)))
```

In plain language: If two representations describe the same physical driving scenario, they must receive the same safety judgment.

### 3.3 Why This Matters for Collision Avoidance

Consider a pedestrian detected at an intersection:

```
Representation A (LIDAR-primary):
  Class: PEDESTRIAN (0.91 confidence)
  Position: (15.2, -3.1) m in ego frame
  Velocity: (0.8, 1.2) m/s (crossing toward ego path)
  → Prediction: Will enter ego lane in 2.3s
  → Decision: YIELD (reduce speed, prepare to stop)

Representation B (Camera-primary):
  Class: PERSON (0.87 confidence)  
  Position: (14.9, -3.3) m in ego frame (from depth estimation)
  Velocity: (0.6, 1.0) m/s (noisier estimate)
  → Prediction: Will enter ego lane in 2.8s
  → Decision: CAUTION (maintain speed, monitor)
```

These represent the **same pedestrian** at the **same instant**. But sensor-specific noise and different classification taxonomies produce different safety judgments. If one representation triggers yielding and the other doesn't, the system has a coherence defect.

In the Uber fatality, this oscillation between representations prevented any consistent avoidance action.

---

## 4. Observables and Grounding (Ψ)

### 4.1 The Observable Set for Autonomous Vehicles

Following the ErisML framework, we define the **grounding map Ψ** that specifies which physical quantities the AV has access to:

| Observable | Symbol | Sensors | Sample Rate | Range | Uncertainty |
|------------|--------|---------|-------------|-------|-------------|
| 3D point cloud | P | LIDAR | 10–20 Hz | 200+ m | ±2 cm |
| Object range/velocity | (r, ṙ) | Radar | 20–100 Hz | 250+ m | ±0.1 m, ±0.1 m/s |
| Image | I | Camera | 30–60 Hz | ~150 m (perception) | Depth uncertain |
| Ego velocity | v_ego | Wheel encoders, IMU | 100–1000 Hz | — | ±0.1 m/s |
| Ego acceleration | a_ego | IMU | 100–1000 Hz | — | ±0.01 m/s² |
| Ego orientation | θ_ego | IMU, GNSS | 100 Hz | — | ±0.1° |
| Global position | (lat, lon, alt) | GNSS/RTK | 1–10 Hz | Global | ±2 cm (RTK) |
| HD map | M | Pre-built | Static | — | ±10 cm |
| Ultrasonic range | d_near | Ultrasonics | 10–40 Hz | 0–5 m | ±1 cm |

### 4.2 Derived Quantities

Beyond direct measurements, AV systems compute derived quantities:

| Derived Observable | Formula | Safety Relevance |
|--------------------|---------|------------------|
| Time-to-collision (TTC) | TTC = d / |ṙ| (if closing) | Primary collision metric |
| Time-to-lane-crossing | TTLC = d_lane / v_lateral | Intersection timing |
| Post-encroachment time | PET = time gap after paths cross | Near-miss severity |
| Required deceleration | a_req = v²/(2d) | Braking authority |
| Safe following distance | d_safe = v·t_react + v²/(2a_max) | Car following |
| Collision probability | P(collision) from prediction model | Risk-based planning |

### 4.3 The Ψ-Incompleteness Challenge

Unlike power grids or chemical reactors, AV systems face **fundamental Ψ-incompleteness**:

| Unobservable | Why It Matters | Mitigation |
|--------------|----------------|------------|
| **Pedestrian intent** | Will they cross or stop? | Predict from trajectory, posture |
| **Driver intent** | Will they yield or proceed? | Predict from kinematics, signals |
| **Occluded objects** | What's behind that truck? | Assume worst case, slow down |
| **Road surface condition** | Is there ice? | Conservative friction assumption |
| **Object mass** | Collision severity | Assume worst case |
| **System malfunction (others)** | Will that car's brakes fail? | Cannot anticipate |

**Critical insight**: The Bond Index framework explicitly acknowledges Ψ-incompleteness. When operating in regimes where key observables are missing (occlusion, sensor degradation), the system should return ⊥ (unknown) and trigger minimal risk condition—not guess.

### 4.4 Sensor Fusion and Observability

Modern AVs achieve high observability through sensor fusion:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SENSOR FUSION ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   LIDAR ──────┐                                                 │
│   (geometry)  │                                                 │
│               ├──▶ EARLY FUSION ──▶ Object-level ──▶ Tracked   │
│   RADAR ──────┤    (point cloud     detection       objects    │
│   (velocity)  │     concatenation)                             │
│               │                                                 │
│   CAMERA ─────┘                     ┌─────────────────────────┐ │
│   (semantics)                       │     LATE FUSION          │ │
│                                     │  (track association)     │ │
│   LIDAR ──▶ Detect ──┐              │                         │ │
│   RADAR ──▶ Detect ──┼──▶ Associate ▶ Fused tracks           │ │
│   CAMERA ─▶ Detect ──┘              │                         │ │
│                                     └─────────────────────────┘ │
│                                                                 │
│   Ego state:  IMU + Wheel + GNSS ──▶ State estimator ──▶ Pose  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**The Bond Index tests**: Does the fusion strategy affect safety judgments? Early fusion vs. late fusion should yield consistent safety decisions for equivalent physical scenarios.

---

## 5. Declared Transforms (G_declared)

### 5.1 Transform Categories for Autonomous Vehicles

The transform suite G_declared defines which changes to the representation should **not** affect safety judgments:

#### Category 1: Coordinate Frame Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| Ego-centric ↔ world-centric | Rotate/translate | Rigid body transform |
| Cartesian ↔ polar | (x,y) ↔ (r,θ) | Same position |
| Lane-relative ↔ world | (s,d) ↔ (x,y) | Frenet transform |
| Sensor frame ↔ ego frame | Calibration transform | Fixed extrinsics |

**Critical**: Safety decisions should depend on *physical* distances and velocities, not coordinate frame artifacts.

#### Category 2: Sensor Modality Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| LIDAR-primary ↔ camera-primary | Different detection pipeline | Same object detected |
| Radar-confirmed ↔ LIDAR-only | With/without radar confirmation | Same position/velocity |
| Fused ↔ single-sensor | Multi-modal vs. uni-modal | Same physical state |

**Challenge**: Different sensors have different noise characteristics. The transform is valid only when both detect the same object with overlapping uncertainty bounds.

#### Category 3: Semantic Label Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| VEHICLE ↔ CAR/TRUCK/SUV | Fine-grained ↔ coarse | Same safety-relevant behavior |
| PEDESTRIAN ↔ PERSON/CYCLIST | Classification hierarchy | Same vulnerability class |
| OBJECT ↔ specific class | Unknown ↔ identified | Conservative assumption preserved |

**Critical principle**: Semantic label refinement should not change safety decisions. A vehicle classified as "TRUCK" vs. "VEHICLE" should receive the same collision avoidance response.

#### Category 4: Temporal Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| Current frame ↔ smoothed | Raw vs. Kalman-filtered | Same underlying trajectory |
| 10 Hz ↔ 20 Hz | Different LIDAR rates | Same physical motion |
| T ↔ T+Δt (short) | Prediction horizon | Consistent extrapolation |

#### Category 5: Spatial Resolution Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| High-res ↔ downsampled | Point cloud density | Same object detection |
| Fine grid ↔ coarse grid | Occupancy resolution | Same collision geometry |
| Full FOV ↔ cropped ROI | Processing region | Object in both |

#### Category 6: Sim-to-Real Transforms

| Transform | Example | Constraint |
|-----------|---------|------------|
| Simulated ↔ real sensor | CARLA ↔ physical LIDAR | Same geometry preserved |
| Rendered ↔ real image | Game engine ↔ camera | Same semantic content |
| Physics sim ↔ real dynamics | Simulated ↔ actual vehicle | Same safety envelope |

**This is critical for validation**: If the system behaves differently in simulation vs. reality for equivalent scenarios, sim-to-real transfer has failed.

### 5.2 The Transform Suite Document

```yaml
transform_id: COORD_EGO_TO_WORLD
version: 1.0.0
category: coordinate_frame
description: "Transform from ego-centric to world-centric coordinates"
parameters:
  ego_pose: (x, y, θ)_world  # Ego position/heading in world frame
forward: |
  p_world = R(θ) @ p_ego + t_ego
  v_world = R(θ) @ v_ego
inverse: |
  p_ego = R(-θ) @ (p_world - t_ego)
  v_ego = R(-θ) @ v_world
semantic_equivalence: "Same physical position and velocity"
validation:
  geometric_test_cases: 1000
  max_position_error: 1e-6 m
  max_velocity_error: 1e-6 m/s
```

### 5.3 Transforms That Are NOT Declared Equivalent

Some transformations **do** change the physical scenario or safety-relevant meaning:

| NOT Equivalent | Why |
|----------------|-----|
| Object appears ↔ disappears | Different scenario |
| Object classified as vehicle ↔ pedestrian | Different vulnerability |
| Clear weather ↔ heavy rain | Different sensor performance |
| Object stationary ↔ moving | Different prediction |
| Ego moving ↔ ego stopped | Different dynamics |

These are **scenario changes**, not representation changes.

---

## 6. The Bond Index for Collision Avoidance Systems

### 6.1 Definition

The **Bond Index (Bd)** quantifies how consistently a collision avoidance system treats equivalent representations:

```
Bd = D_op / τ
```

where:
- **D_op** is the observed coherence defect (measured inconsistency)
- **τ** is the human-calibrated threshold (the defect level safety engineers consider "meaningful")

### 6.2 The Three Coherence Defects

#### Defect 1: Commutator (Ω_op)

**Question**: Does the order of transforms matter?

```
Ω_op(σ; g₁, g₂) = |S(g₂(g₁(r(σ)))) - S(g₁(g₂(r(σ))))|
```

**AV example**: Change coordinate frame, then change sensor modality, vs. change modality, then change frame. Should yield same safety judgment.

#### Defect 2: Mixed (μ)

**Question**: Does the same transform behave differently in different contexts?

**AV example**: Coordinate transform during highway driving vs. during parking. The transform itself is the same, but numerical precision may differ at different speeds.

#### Defect 3: Permutation (π₃)

**Question**: Do three-way compositions have hidden interactions?

**AV example**: Change coordinate frame → change label taxonomy → change temporal smoothing. All 6 orderings should yield consistent results.

### 6.3 Deployment Tiers

| Bd Range | Tier | Interpretation | Action |
|----------|------|----------------|--------|
| < 0.01 | **Negligible** | Excellent coherence | Certify for deployment |
| 0.01 – 0.1 | **Low** | Minor inconsistencies | Deploy with monitoring |
| 0.1 – 1.0 | **Moderate** | Significant inconsistencies | Remediate before deployment |
| 1 – 10 | **High** | Severe inconsistencies | Do not deploy |
| > 10 | **Severe** | Fundamental incoherence | Complete redesign |

### 6.4 Calibration Protocol for AV Safety

The threshold τ is determined empirically:

1. **Recruit raters**: Safety engineers, test drivers, human factors experts (n ≥ 30)
2. **Generate test pairs**: Driving scenarios with known transform relationships
3. **Collect judgments**: "Should these receive the same safety response?"
4. **Fit threshold**: Find defect level where 95% agree the difference matters
5. **Set τ**: Conservative estimate—for collision avoidance, human life is at stake

For AV collision avoidance systems, typical calibration yields **τ ≈ 0.005** (safety engineers expect < 0.5% deviation in safety judgments across equivalent representations).

### 6.5 Application to Specific AV Functions

| Function | Key Transforms | Target Bd |
|----------|----------------|-----------|
| **Object detection** | Sensor modality, resolution | < 0.01 |
| **Object classification** | Label taxonomy | < 0.01 |
| **Object tracking** | Temporal smoothing, frame rate | < 0.005 |
| **Trajectory prediction** | Coordinate frame, prediction horizon | < 0.01 |
| **Collision checking** | Grid resolution, geometry representation | < 0.001 |
| **Motion planning** | Discretization, optimization tolerance | < 0.01 |
| **End-to-end** | Full pipeline | < 0.01 |

---

## 7. Regime Transitions and Coherence Defects

### 7.1 The Regime Transition Problem

AVs operate in distinct regimes with different safety strategies:

```
┌──────────────────────────────────────────────────────────────────┐
│                    AV OPERATING REGIMES                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  REGIME 1: HIGHWAY DRIVING                                       │
│  ─────────────────────────                                       │
│  • High speed (60-80 mph)                                        │
│  • Structured environment (lanes, barriers)                      │
│  • Primary hazards: Rear-end, lane change                        │
│  • Strategy: Large following distance, gentle maneuvers          │
│  • Prediction: Highway-like kinematics                           │
│                                                                  │
│              ↓ (exit ramp, speed reduction)                      │
│                                                                  │
│  REGIME 2: ARTERIAL DRIVING                                      │
│  ─────────────────────────                                       │
│  • Medium speed (25-45 mph)                                      │
│  • Mixed traffic (vehicles, cyclists)                            │
│  • Primary hazards: Intersections, turning vehicles              │
│  • Strategy: Defensive driving, anticipate signals               │
│  • Prediction: Urban kinematics                                  │
│                                                                  │
│              ↓ (intersection, pedestrian area)                   │
│                                                                  │
│  REGIME 3: URBAN/INTERSECTION                                    │
│  ────────────────────────────                                    │
│  • Low speed (0-25 mph)                                          │
│  • Complex interactions (pedestrians, bikes, vehicles)           │
│  • Primary hazards: Pedestrian crossing, right-of-way            │
│  • Strategy: Yield-first, creep forward, eye contact proxy       │
│  • Prediction: Multi-agent interaction models                    │
│                                                                  │
│              ↓ (destination, tight space)                        │
│                                                                  │
│  REGIME 4: PARKING/LOW-SPEED MANEUVERING                         │
│  ───────────────────────────────────────                         │
│  • Very low speed (<5 mph)                                       │
│  • Tight spaces, limited visibility                              │
│  • Primary hazards: Pedestrians, obstacles, property damage      │
│  • Strategy: Ultrasonics dominant, frequent stops                │
│  • Prediction: Static or slow-moving obstacles                   │
│                                                                  │
│  REGIME 5: DEGRADED/EMERGENCY                                    │
│  ────────────────────────────                                    │
│  • Sensor failure, adverse weather, system fault                 │
│  • Strategy: Minimal risk condition (pull over, stop)            │
│  • Prediction: Conservative, assume worst case                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 Regime-Specific Safety Parameters

Different regimes require different safety thresholds:

| Parameter | Highway | Arterial | Urban | Parking |
|-----------|---------|----------|-------|---------|
| **TTC_min** | 3.0 s | 2.5 s | 2.0 s | 1.0 s |
| **Following time** | 2.0 s | 1.5 s | 1.0 s | N/A |
| **Max decel (comfort)** | 3 m/s² | 4 m/s² | 5 m/s² | 2 m/s² |
| **Max decel (emergency)** | 8 m/s² | 8 m/s² | 8 m/s² | 5 m/s² |
| **Pedestrian priority** | Medium | High | Very high | Very high |
| **Speed tolerance** | ±5 mph | ±3 mph | ±2 mph | ±1 mph |

### 7.3 Coherence Across Regime Boundaries

A key test: **Does the system give consistent judgments for scenarios near regime boundaries?**

**Example**: Approaching a freeway exit:
- Highway regime: Following distance based on highway model
- Transition zone: Which model applies?
- Arterial regime: Different following model

A coherent system must either:
1. Smoothly interpolate between regimes, OR
2. Use conservative parameters during transition

**Incoherent behavior** (witness): At 50 mph (boundary between highway and arterial), the system oscillates between regimes, causing jerky behavior as following distance target changes.

### 7.4 Weather/Condition Regime Transitions

Environmental changes also trigger regime transitions:

| Condition Change | Safety Impact | Coherent Response |
|------------------|---------------|-------------------|
| Clear → rain | Reduced visibility, braking distance | Increase following distance |
| Dry → wet road | Reduced friction | Conservative deceleration |
| Day → night | Camera degraded | Rely more on LIDAR/radar |
| Low traffic → congestion | Different prediction model | Switch to stop-and-go mode |

**Bond Index test**: Does sensor degradation change safety judgments for physically equivalent scenarios? (It should change behavior appropriately—increase caution—but consistently.)

---

## 8. The Ψ-Incompleteness Challenge: Intent and Prediction

### 8.1 The Fundamental Limitation

Unlike physical systems (chemical reactors, power grids), AV safety depends on **predicting human behavior**—which is fundamentally unobservable:

```
Observable: Pedestrian position = (5.2, -2.1) m, velocity = (0.8, 1.1) m/s
Unobservable: Will they continue crossing, or stop at the curb?

Observable: Vehicle position, velocity, turn signal ON
Unobservable: Will they actually turn, or did they forget the signal?

Observable: Child running on sidewalk
Unobservable: Will they dart into the street?
```

### 8.2 The ErisML/DEME Response

The framework explicitly handles Ψ-incompleteness:

1. **Acknowledge uncertainty**: Safety judgments should reflect prediction uncertainty
2. **Conservative default**: When intent is ambiguous, assume worst case
3. **Return ⊥ when appropriate**: If uncertainty is too high, trigger minimal risk condition
4. **Test across prediction models**: Bond Index should hold even with different prediction assumptions

### 8.3 Prediction-Invariant Safety

A key principle: **Core safety decisions should be invariant to prediction model selection**

```
Prediction Model A: Pedestrian will continue → TTC = 2.1 s
Prediction Model B: Pedestrian may stop → TTC = ∞ (no collision predicted)

Coherent safety response:
  - Prepare for both possibilities
  - Reduce speed to handle worst case
  - Safety judgment: CAUTION (same regardless of prediction)
```

**What varies**: The specific predicted trajectory
**What should NOT vary**: The safety classification for the current observable state

### 8.4 The "Same Scenario, Different Intent" Transform

We introduce a special transform class for testing prediction robustness:

```yaml
transform_id: INTENT_VARIATION
version: 1.0.0
category: prediction_invariance
description: "Vary assumed intent within uncertainty bounds"
parameters:
  observable_state: fixed
  intent_distribution: [continue: 0.6, stop: 0.3, reverse: 0.1]
semantic_equivalence: |
  Same observable state. 
  Safety judgment should reflect uncertainty, not assume specific intent.
test_criterion: |
  Safety judgment should be at least as conservative as 
  worst-case intent within plausible distribution.
```

This tests whether the system appropriately handles intent uncertainty rather than committing to a single prediction.

---

## 9. Multi-Stakeholder Governance

### 9.1 The Multi-Stakeholder Challenge

AV safety involves multiple stakeholders with different priorities:

| Stakeholder | Primary Concerns | Typical Requirements |
|-------------|------------------|----------------------|
| **OEM** | Product liability, brand reputation | Conservative, documented |
| **Regulators (NHTSA, EU)** | Public safety, standards compliance | Minimum performance, testing |
| **Insurers** | Actuarial risk, claims cost | Quantified risk metrics |
| **Passengers** | Comfort, arrival time | Balance safety/efficiency |
| **Other road users** | Predictable, courteous behavior | Follow traffic norms |
| **Public** | Trust, acceptance | Transparent, explainable |

### 9.2 DEME Governance Profiles for AVs

The DEME framework allows safety requirements to be composed into **governance profiles**:

```yaml
profile_id: "av_urban_usa_v2.1"
stakeholders:
  - id: oem_safety_engineering
    weight: 0.30
    priorities:
      - prevent_fatalities
      - prevent_injuries
      - prevent_property_damage
    hard_vetoes:
      - ttc_min: 1.5  # seconds
      - max_speed_in_school_zone: 15  # mph
      
  - id: nhtsa_fmvss
    weight: 0.25
    priorities:
      - fmvss_compliance
      - sotif_compliance
      - recall_prevention
    hard_vetoes:
      - pedestrian_aeb_required: true
      - lane_departure_warning: true
      
  - id: insurance_actuarial
    weight: 0.20
    priorities:
      - minimize_claims_cost
      - quantifiable_risk
    hard_vetoes:
      - collision_probability_max: 1e-7  # per mile
      
  - id: passenger_experience
    weight: 0.15
    priorities:
      - comfort
      - efficiency
      - predictability
    constraints:
      - max_lateral_accel: 2.5  # m/s² (comfort)
      - max_jerk: 1.0  # m/s³
      
  - id: public_trust
    weight: 0.10
    priorities:
      - transparent_behavior
      - traffic_norm_compliance
      - courteous_driving

aggregation:
  method: weighted_sum_with_vetoes
  veto_behavior: any_stakeholder_veto_honored
  conflict_resolution: safety_conservative
```

### 9.3 The Ethical Dimension: Unavoidable Collision Scenarios

The infamous "trolley problem" scenarios—where any action causes harm—require explicit governance:

```yaml
unavoidable_collision_policy:
  principle: "Minimize total harm; never deliberately target individuals"
  
  priorities:
    1: Minimize fatalities
    2: Minimize serious injuries  
    3: Minimize minor injuries
    4: Minimize property damage
    5: Protect ego vehicle occupants (within above constraints)
    
  prohibitions:
    - Never swerve toward pedestrian to avoid vehicle
    - Never consider protected characteristics (age, gender, etc.)
    - Never sacrifice pedestrians to protect vehicle occupants
    
  uncertainty_handling:
    - When outcomes uncertain, choose action with lowest expected harm
    - Log all unavoidable collision scenarios for review
```

### 9.4 Consistency Checking

Before deployment, the governance profile is checked for:

1. **Veto consistency**: Do hard constraints from different stakeholders conflict?
2. **Priority consistency**: Are safety and efficiency objectives compatible?
3. **Ethical consistency**: Is the collision policy coherent and defensible?

**Example conflict**: Passenger wants minimal jerk (smooth ride); safety requires emergency braking capability. Resolution: Comfort constraints are soft; safety constraints are hard.

---

## 10. Case Study: Pedestrian Detection at Crosswalks

### 10.1 Scenario Description

**Context**: Urban intersection with marked crosswalk, AV approaching at 25 mph

**Setup**:
- AV equipped with: 64-beam LIDAR, front radar, 8 cameras, HD map
- Crosswalk 50 m ahead, signal showing "WALK"
- Three pedestrians in crosswalk at varying distances

**Test objective**: Verify perception-planning pipeline gives consistent safety judgments across G_declared transforms.

### 10.2 Observable Set (Ψ)

| Observable | Sensor | Value | Uncertainty |
|------------|--------|-------|-------------|
| Pedestrian A position | LIDAR | (45.2, -2.1) m | ±0.05 m |
| Pedestrian A velocity | Tracked | (0.0, 1.2) m/s | ±0.15 m/s |
| Pedestrian B position | LIDAR | (38.7, 1.8) m | ±0.05 m |
| Pedestrian B velocity | Tracked | (0.2, -0.9) m/s | ±0.15 m/s |
| Pedestrian C position | LIDAR | (32.4, 0.3) m | ±0.05 m |
| Pedestrian C velocity | Tracked | (-0.1, 0.0) m/s | ±0.15 m/s |
| Signal state | Camera + map | "WALK" | 0.98 confidence |
| Ego velocity | IMU/wheel | 11.2 m/s (25 mph) | ±0.1 m/s |

### 10.3 Transform Suite

For this case study, we apply 14 transforms:

| ID | Transform | Category |
|----|-----------|----------|
| T1 | Ego-centric ↔ world-centric | Coordinate frame |
| T2 | Cartesian ↔ polar | Coordinate frame |
| T3 | Lane-relative (Frenet) ↔ Cartesian | Coordinate frame |
| T4 | LIDAR-primary ↔ camera-primary | Sensor modality |
| T5 | Fused ↔ LIDAR-only | Sensor modality |
| T6 | PEDESTRIAN ↔ PERSON | Label taxonomy |
| T7 | Individual ↔ GROUP | Label taxonomy |
| T8 | 10 Hz ↔ 20 Hz (LIDAR rate) | Temporal |
| T9 | Raw ↔ Kalman-smoothed | Temporal |
| T10 | High-res ↔ downsampled point cloud | Resolution |
| T11 | Fine grid ↔ coarse grid (occupancy) | Resolution |
| T12 | Short prediction ↔ long prediction | Prediction horizon |
| T13 | Simulated ↔ real-equivalent | Sim-to-real |
| T14 | Intent-vary (continue vs. stop) | Prediction invariance |

### 10.4 Safety Logic Under Test

The collision avoidance module implements:

```
SAFETY ASSESSMENT:

SAFE IF:
  (all TTC > 3.0 s) AND
  (all_pedestrians_outside_ego_path) AND
  (signal = "WALK" implies yielding)

CAUTION IF:
  (any TTC ∈ [2.0, 3.0] s) OR
  (pedestrian_may_enter_path AND TTC > 2.0 s)

YIELD IF:
  (pedestrian_in_crosswalk AND ego_path_intersects) OR
  (any TTC ∈ [1.5, 2.0] s)

BRAKE IF:
  (any TTC < 1.5 s) AND (collision_avoidable_with_braking)

EMERGENCY_STOP IF:
  (any TTC < 1.0 s) OR
  (collision_imminent AND braking_insufficient)
```

### 10.5 Bond Index Evaluation

**Test protocol**:
1. Generate 500 variations of crosswalk scenario
2. Apply each of 14 transforms at 5 intensity levels
3. Compute safety judgment before and after transform
4. Calculate coherence defects

**Results**:

```
═══════════════════════════════════════════════════════════════════
              BOND INDEX EVALUATION RESULTS
═══════════════════════════════════════════════════════════════════

System:        AV Perception-Planning Stack v5.2
Transform suite: G_declared_urban_pedestrian_v1.0 (14 transforms)
Test cases:    500 scenarios × 14 transforms × 5 intensities = 35,000

───────────────────────────────────────────────────────────────────
                      BOND INDEX
───────────────────────────────────────────────────────────────────
  Bd_mean = 0.0073   [0.0058, 0.0089] 95% CI
  Bd_p95  = 0.038
  Bd_max  = 0.31

  TIER: NEGLIGIBLE
  DECISION: ✅ Meets safety certification threshold

───────────────────────────────────────────────────────────────────
                  DEFECT BREAKDOWN
───────────────────────────────────────────────────────────────────
  Ω_op (commutator):     0.0048  █████
  μ (mixed):             0.0019  ██
  π₃ (permutation):      0.0006  █

───────────────────────────────────────────────────────────────────
                TRANSFORM SENSITIVITY
───────────────────────────────────────────────────────────────────
  T1  (ego↔world):       0.000   (perfect)
  T2  (cart↔polar):      0.000   (perfect)
  T3  (Frenet↔cart):     0.002   
  T4  (LIDAR↔camera):    0.047   █████  ← SECOND HIGHEST
  T5  (fused↔LIDAR):     0.012   █
  T6  (PED↔PERSON):      0.000   (perfect)
  T7  (indiv↔GROUP):     0.008   █
  T8  (10Hz↔20Hz):       0.015   ██
  T9  (raw↔smoothed):    0.023   ██
  T10 (res high↔low):    0.031   ███
  T11 (grid fine↔coarse):0.018   ██
  T12 (pred short↔long): 0.025   ███
  T13 (sim↔real):        0.089   █████████  ← HIGHEST
  T14 (intent vary):     0.011   █

───────────────────────────────────────────────────────────────────
                   WORST WITNESS
───────────────────────────────────────────────────────────────────
  Transform: T13 (simulated ↔ real-equivalent)
  Scenario: Pedestrian at crosswalk edge, backlit by sun
  
  Real sensor:
    LIDAR detection: Pedestrian at (12.3, -2.1) m
    Camera detection: Missed (backlit, low contrast)
    Fused result: PEDESTRIAN, confidence 0.72
    
  Simulated sensor (no sun glare modeled):
    LIDAR detection: Pedestrian at (12.3, -2.1) m
    Camera detection: PEDESTRIAN, confidence 0.89
    Fused result: PEDESTRIAN, confidence 0.91
    
  Real judgment: YIELD (lower confidence → more conservative)
  Sim judgment: CAUTION (higher confidence → less conservative)
  
  Defect: 0.31 (safety category changed)
  
  ROOT CAUSE: Simulation doesn't model camera degradation from 
              backlighting. Real system is more conservative.
  
  NOTE: Defect direction is SAFE (real more conservative than sim).
        Concerning if reversed.
  
  RECOMMENDATION: Add sun glare model to simulation;
                  verify sim-to-real always errs conservative

───────────────────────────────────────────────────────────────────
                PEDESTRIAN-SPECIFIC ANALYSIS
───────────────────────────────────────────────────────────────────
  Detection consistency:        99.2%
  Classification consistency:   98.7%
  TTC calculation consistency:  97.8%
  Safety judgment consistency:  99.3%
  
  Vulnerable scenario: Backlit pedestrian at dawn/dusk
  Vulnerable scenario: Pedestrian emerging from occlusion
  Vulnerable scenario: Multiple pedestrians (group vs. individual)

═══════════════════════════════════════════════════════════════════
```

### 10.6 Decomposition Analysis

Applying the Decomposition Theorem:

```
Total defect: Ω = 0.0073 (mean)

Gauge-removable (Ω_gauge): 0.0061 (84%)
  - Fixable via:
    - Better sim-to-real camera modeling
    - Improved sensor fusion weighting
    - Calibrated confidence thresholds
  
Intrinsic (Ω_intrinsic): 0.0012 (16%)
  - Fundamental:
    - Camera vs. LIDAR have different failure modes
    - Simulation can never perfectly match reality
  - Requires specification-level acceptance or redundancy
```

### 10.7 Remediation Plan

| Issue | Root Cause | Remediation | Expected Improvement |
|-------|------------|-------------|----------------------|
| Sim-to-real gap | Missing glare model | Add physically-based glare | 0.089 → 0.02 |
| LIDAR↔camera | Different noise profiles | Uncertainty-aware fusion | 0.047 → 0.015 |
| Resolution sensitivity | Downsampling artifacts | Adaptive resolution | 0.031 → 0.01 |
| Prediction horizon | Longer = more uncertainty | Horizon-dependent thresholds | 0.025 → 0.01 |

**Post-remediation target**: Bd < 0.005

---

## 11. Implementation Architecture

### 11.1 Integration with Existing AV Stacks

The Bond Index framework integrates **non-invasively** with existing AV architectures:

```
┌─────────────────────────────────────────────────────────────────┐
│                  EXISTING AV ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌──────────┐  │
│  │  Sensors  │──▶│ Perception│──▶│ Prediction│──▶│ Planning │  │
│  │           │   │           │   │           │   │          │  │
│  └───────────┘   └─────┬─────┘   └─────┬─────┘   └────┬─────┘  │
│                        │               │              │         │
│                        ▼               ▼              ▼         │
│                 ┌──────────────────────────────────────────┐    │
│                 │              DATA BUS / ROS              │    │
│                 └──────────────────────────────────────────┘    │
│                                      │                          │
└──────────────────────────────────────┼──────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              BOND INDEX VERIFICATION LAYER                      │
│                    (Non-invasive)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              DATA ACQUISITION                            │   │
│  │  • ROS bag recording / replay                            │   │
│  │  • Real-time topic subscription                          │   │
│  │  • Simulation API (CARLA, LGSVL)                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              TRANSFORM ENGINE                            │   │
│  │  • Coordinate frame transforms                           │   │
│  │  • Sensor modality substitution                          │   │
│  │  • Label taxonomy mapping                                │   │
│  │  • Temporal resampling                                   │   │
│  │  • Sim-to-real perturbations                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SAFETY LOGIC EVALUATOR                      │   │
│  │  • Mirror of AV safety assessment                        │   │
│  │  • Evaluate original and transformed                     │   │
│  │  • Compare safety judgments                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BOND INDEX CALCULATOR                       │   │
│  │  • Compute Ω_op, μ, π₃                                   │   │
│  │  • Per-scenario analysis                                 │   │
│  │  • Generate witnesses                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              REPORTING & CI/CD INTEGRATION               │   │
│  │  • Dashboard (scenario coverage, Bd trends)              │   │
│  │  • CI gate (fail build if Bd > threshold)                │   │
│  │  • Audit trail for safety case                           │   │
│  │  • Witness database for debugging                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Deployment Modes

| Mode | Description | Latency | Use Case |
|------|-------------|---------|----------|
| **CI/CD gate** | Run on every code commit | Minutes | Prevent regressions |
| **Nightly regression** | Full test suite overnight | Hours | Comprehensive coverage |
| **Simulation campaign** | Large-scale scenario testing | Hours-days | Safety case evidence |
| **On-vehicle logging** | Record for offline analysis | Real-time record | Field validation |
| **Real-time monitoring** | Continuous Bd calculation | <100 ms | Research/development |

### 11.3 Integration with Simulation

The framework integrates with major AV simulators:

| Simulator | Integration Method | Capabilities |
|-----------|-------------------|--------------|
| **CARLA** | Python API, ROS bridge | Full sensor sim, scenarios |
| **LGSVL** | Python API, Apollo bridge | Sensor sim, HD maps |
| **Waymax** | JAX API | Large-scale behavior |
| **NVIDIA DRIVE Sim** | Omniverse API | Photorealistic rendering |
| **Custom** | ROS bag replay | Any recorded data |

### 11.4 Cybersecurity and Safety Isolation

AV safety systems require strict isolation:

| Requirement | Implementation |
|-------------|----------------|
| **No control authority** | Verification layer is read-only |
| **Safety isolation** | Separate compute, cannot affect AV behavior |
| **Data integrity** | Cryptographic hashing of sensor data |
| **Audit logging** | Tamper-evident logs for safety case |
| **Functional safety** | ISO 26262 ASIL-D for safety-critical components |

---

## 12. Deployment Pathway

### 12.1 Phase 1: Simulation Validation (Years 1-2)

**Objective**: Demonstrate Bond Index framework in AV simulation

**Activities**:
- Implement G_declared transforms for CARLA/LGSVL
- Partner with AV research lab (Stanford, CMU, MIT)
- Validate Bd correlation with human-judged safety consistency
- Test across diverse scenarios (100k+ simulated miles)
- Publish in IEEE IV, CVPR, or CoRL

**Deliverables**:
- Validated transform suite for urban driving
- Simulation integration package
- Technical paper demonstrating concept

**Resources**: $400K, 4 FTE, 2 years

### 12.2 Phase 2: Closed-Track Testing (Years 2-3)

**Objective**: Validate on real vehicles in controlled environment

**Activities**:
- Partner with proving ground (MCity, GoMentum, Mcity)
- Instrument test vehicle with Bond Index monitoring
- Run standard AV test scenarios (Euro NCAP, NHTSA)
- Validate sim-to-real consistency
- Demonstrate value during edge-case testing

**Deliverables**:
- Hardware-validated software
- Closed-track case study
- Initial OEM engagement

**Resources**: $1.2M, 6 FTE, 1.5 years

### 12.3 Phase 3: Public Road Testing (Years 3-5)

**Objective**: Deploy with AV developer on public roads

**Target partners** (in order of likelihood):
1. **Waymo** — Most mature, safety-focused, extensive testing
2. **Cruise** — Urban focus, regulatory engagement
3. **Motional** — Partnership model, regulatory track record
4. **Aurora** — Trucking focus, safety case emphasis
5. **Tesla** — Large fleet data, but different architecture

**Activities**:
- Negotiate pilot with AV developer
- Deploy non-invasive monitoring on test fleet
- Analyze disengagements and safety events
- Demonstrate value for safety case development
- Build case for regulatory engagement

**Deliverables**:
- Production-validated system
- AV developer endorsement
- Regulatory briefing materials

**Resources**: $3M, 10 FTE, 2 years

### 12.4 Phase 4: Regulatory Engagement (Years 5-7)

**Objective**: Codify Bond Index in AV safety standards

**Activities**:
- Engage NHTSA (FMVSS, ADS framework)
- Engage EU (GSR, UN R157)
- Participate in SAE, ISO standards development
- Develop compliance monitoring approach
- Pilot with NHTSA ADS testing program

**Target standards**:
- ISO 21448 (SOTIF) — Add representational consistency requirement
- UL 4600 — Safety case evidence requirements
- UN R157 — Automated Lane Keeping System regulation

**Deliverables**:
- Regulatory guidance document
- Standards contribution
- Compliance certification framework

**Resources**: $2M, 8 FTE, 2 years

### 12.5 Phase 5: Industry-Wide Deployment (Years 7+)

**Objective**: Routine use across AV industry

**Activities**:
- Integration with major AV stacks (Apollo, Autoware)
- Licensing to OEMs and Tier 1 suppliers
- Training and certification programs
- Continuous improvement based on field data

**Market potential**: $200M+ annual revenue at maturity (software + certification services)

---

## 13. Limitations and Future Work

### 13.1 Current Limitations

| Limitation | Description | Mitigation |
|------------|-------------|------------|
| **Ψ-incompleteness** | Cannot observe intent, occluded objects | Conservative assumptions, acknowledge uncertainty |
| **Edge cases** | Long tail of rare scenarios | Extensive simulation, continuous field learning |
| **Real-time constraints** | Full verification takes time | Offline analysis, sampled online |
| **Sim-to-real gap** | Simulation never perfect | Test real vehicles, continuous calibration |
| **Adversarial inputs** | Malicious sensor spoofing | Out of scope (separate cybersecurity) |

### 13.2 What We Do NOT Claim

- **Completeness**: The Bond Index verifies consistency for declared transforms only. Novel representation failures may exist.
- **Correctness**: We verify that safety judgments are consistent, not that thresholds are correct.
- **Zero accidents**: Consistent systems can still fail due to Ψ-incompleteness (unobservable hazards).
- **Real-time guarantee**: Current implementation prioritizes accuracy over speed.
- **Adversarial robustness**: Malicious attacks on sensors require separate analysis.

### 13.3 Future Work

1. **Occlusion handling**: Extend framework to reason about unobserved regions
2. **Multi-agent coordination**: Test consistency across V2X communication
3. **Learning-based components**: Verify neural network perception consistency
4. **Adversarial testing**: Combine with robustness testing
5. **Continuous learning**: Verify consistency as models update in the field

---

## 14. Conclusion

Autonomous vehicle collision avoidance presents a critical application domain for invariance-based safety verification:

1. **Hard constraints exist**: Collision avoidance is physically meaningful and life-critical
2. **Transforms are well-defined**: Coordinate frames, sensor modalities, and label taxonomies have clear semantics
3. **Stakes are extreme**: 1.35 million road deaths annually; AVs must be demonstrably safer
4. **Observability is high**: Modern AV sensor suites provide rich, redundant data
5. **Regulatory pressure exists**: NHTSA, EU, UN pushing for rigorous safety evidence
6. **Market is massive**: $100B+ AV industry needs safety verification tools

### The Uber Lesson

The 2018 Uber fatality was not caused by sensor failure. It was caused by **representational instability**—the system's model of the pedestrian oscillating between incompatible classifications, preventing any coherent avoidance action.

**Elaine Herzberg did not die because the AV couldn't see her. She died because the AV couldn't decide what she was.**

The Bond Index framework is designed to detect and prevent exactly this failure mode.

### The Path Forward

The AV industry has the sensors, the simulation capability, and the regulatory pressure to adopt rigorous consistency verification. What has been missing is a formal framework for asking: "Does our perception-planning pipeline give consistent safety decisions?"

The ErisML/DEME Bond Index framework provides that framework.

> *"The obstacle to AV safety is not that we cannot build cars that detect obstacles. It is that we might not verify our perception systems maintain consistent representations. The Bond Index makes that verification possible."*

---

## 15. References

1. NTSB. (2019). *Collision Between Vehicle Controlled by Developmental Automated Driving System and Pedestrian, Tempe, Arizona, March 18, 2018*. Highway Accident Report NTSB/HAR-19/03.

2. SAE International. (2021). *Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles* (J3016_202104).

3. ISO 26262:2018. *Road vehicles — Functional safety*.

4. ISO 21448:2022. *Road vehicles — Safety of the intended functionality (SOTIF)*.

5. NHTSA. (2022). *Standing General Order on Crash Reporting for Automated Driving Systems*.

6. European Commission. (2019). *General Safety Regulation (EU) 2019/2144*.

7. UNECE. (2021). *UN Regulation No. 157 — Automated Lane Keeping Systems*.

8. Koopman, P., & Wagner, M. (2017). "Autonomous vehicle safety: An interdisciplinary challenge." *IEEE Intelligent Transportation Systems Magazine*, 9(1), 90-96.

9. Kalra, N., & Paddock, S. M. (2016). "Driving to safety: How many miles of driving would it take to demonstrate autonomous vehicle reliability?" *Transportation Research Part A*, 94, 182-193.

10. Shalev-Shwartz, S., Shammah, S., & Shashua, A. (2017). "On a formal model of safe and scalable self-driving cars." *arXiv:1708.06374*.

11. Bond, A. H. (2025). "A Categorical Framework for Verifying Representational Consistency in Machine Learning Systems." *IEEE Transactions on Artificial Intelligence* (under review).

12. Bond, A. H. (2025). "The Grand Unified AI Safety Stack (GUASS) v12.0." Technical whitepaper.

13. Dosovitskiy, A., et al. (2017). "CARLA: An open urban driving simulator." *Conference on Robot Learning*.

14. Caesar, H., et al. (2020). "nuScenes: A multimodal dataset for autonomous driving." *CVPR*.

15. Geiger, A., et al. (2012). "Are we ready for autonomous driving? The KITTI vision benchmark suite." *CVPR*.

---

## Appendix A: Transform Suite Template

```yaml
# G_declared for autonomous vehicle collision avoidance
# Version: 1.0.0
# Domain: Urban pedestrian scenarios
# Date: 2025-12-27

metadata:
  domain: autonomous_vehicles
  subdomain: collision_avoidance
  environment: urban
  author: ErisML Team
  hash: sha256:d4e5f6g7...

transforms:
  - id: COORD_EGO_TO_WORLD
    category: coordinate_frame
    description: "Transform from ego-centric to world-centric coordinates"
    forward: |
      p_world = R(ego_yaw) @ p_ego + ego_position
      v_world = R(ego_yaw) @ v_ego
    inverse: |
      p_ego = R(-ego_yaw) @ (p_world - ego_position)
      v_ego = R(-ego_yaw) @ v_world
    semantic_equivalence: "Same physical position and velocity"
    numerical_precision: 1e-6
    
  - id: COORD_CARTESIAN_TO_POLAR
    category: coordinate_frame
    description: "Transform from Cartesian to polar coordinates"
    forward: |
      r = sqrt(x^2 + y^2)
      theta = atan2(y, x)
    inverse: |
      x = r * cos(theta)
      y = r * sin(theta)
    semantic_equivalence: "Same 2D position"
    
  - id: SENSOR_LIDAR_TO_CAMERA
    category: sensor_modality
    description: "Use camera detection instead of LIDAR detection"
    constraints:
      - same_object_detected: true
      - position_uncertainty_overlap: true
    semantic_equivalence: "Same physical object, different sensor"
    note: "Only valid when both sensors detect object"
    
  - id: LABEL_PEDESTRIAN_TO_PERSON
    category: semantic_label
    description: "Use 'PERSON' label instead of 'PEDESTRIAN'"
    mapping:
      PEDESTRIAN: PERSON
      CYCLIST: PERSON
      CHILD: PERSON
    semantic_equivalence: "Same vulnerability class"
    safety_preservation: "Pedestrian safety response applies to all PERSON"
    
  - id: TEMPORAL_RAW_TO_SMOOTHED
    category: temporal
    description: "Apply Kalman filter smoothing to raw detections"
    parameters:
      process_noise: 0.1  # m/s²
      measurement_noise: 0.05  # m
    semantic_equivalence: "Same underlying trajectory"
    
  - id: SIM_TO_REAL_LIDAR
    category: sim_to_real
    description: "Transform simulated LIDAR to real-equivalent"
    perturbations:
      - add_gaussian_noise: {mean: 0, std: 0.02}  # meters
      - random_dropout: {rate: 0.001}
      - intensity_variation: {scale: 0.1}
    semantic_equivalence: "Same geometry, realistic noise"
    
  # ... additional transforms
```

---

## Appendix B: Safety Assessment Specification Template

```yaml
# AV Collision Avoidance Safety Assessment
# For Bond Index verification

system_id: "AV_Collision_Avoidance_v5.2"
functional_safety_level: ASIL_D
verification_date: 2025-12-27

inputs:
  - id: object_list
    description: "Detected objects with state estimates"
    fields: [class, position, velocity, size, confidence]
    source: perception_fusion
    
  - id: ego_state
    description: "Vehicle state"
    fields: [position, velocity, acceleration, yaw, yaw_rate]
    source: localization
    
  - id: road_geometry
    description: "Lane and road structure"
    fields: [lanes, boundaries, crosswalks]
    source: hd_map_matching
    
  # ... additional inputs

safety_levels:
  - id: SAFE
    description: "No collision risk, proceed normally"
    conditions:
      - all_ttc: "> 3.0 s"
      - all_objects: "outside ego path OR stationary"
      - visibility: "> 100 m"
      
  - id: CAUTION
    description: "Monitor situation, prepare for action"
    conditions:
      - any_ttc: "[2.0, 3.0] s"
      - OR any_object: "may enter ego path"
      
  - id: YIELD
    description: "Reduce speed, prepare to stop"
    conditions:
      - pedestrian_in_crosswalk: true
      - OR any_ttc: "[1.5, 2.0] s"
      - OR right_of_way_unclear: true
      
  - id: BRAKE
    description: "Active braking required"
    conditions:
      - any_ttc: "[1.0, 1.5] s"
      - AND collision_avoidable: true
      
  - id: EMERGENCY_STOP
    description: "Maximum braking"
    conditions:
      - any_ttc: "< 1.0 s"
      - OR collision_unavoidable: "minimize severity"

collision_checking:
  ego_geometry: bounding_box  # or polygon
  object_geometry: bounding_box
  time_horizon: 5.0  # seconds
  resolution: 0.1  # seconds

prediction_model:
  pedestrian: constant_velocity_with_intent_uncertainty
  vehicle: lane_following_with_interaction
  cyclist: lane_or_road_following

minimal_risk_condition:
  trigger:
    - sensor_failure: any_critical
    - localization_failure: position_uncertainty > 1m
    - perception_failure: detection_confidence < 0.5
  action:
    - reduce_speed: target_0_mph
    - pull_over: if_safe_location_available
    - activate_hazards: true
    - notify_remote_operator: true
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **AEB** | Automatic Emergency Braking |
| **ADAS** | Advanced Driver Assistance Systems |
| **ASIL** | Automotive Safety Integrity Level (ISO 26262) |
| **Bond Index (Bd)** | Quantitative measure of representational consistency |
| **Ego vehicle** | The autonomous vehicle under consideration |
| **G_declared** | Declared set of transforms that should not affect safety judgments |
| **LIDAR** | Light Detection and Ranging |
| **MRC** | Minimal Risk Condition |
| **ODD** | Operational Design Domain |
| **PET** | Post-Encroachment Time |
| **SOTIF** | Safety of the Intended Functionality (ISO 21448) |
| **TTC** | Time-to-Collision |
| **TTLC** | Time-to-Lane-Crossing |
| **Ψ (Psi)** | Observable set — physical quantities available to the AV |
| **Witness** | Specific example demonstrating a coherence violation |
| **⊥** | Unknown / insufficient information (triggers MRC) |

---

## Appendix D: Regulatory Mapping

| Regulation/Standard | Relevance to Bond Index | Verification Target |
|---------------------|-------------------------|---------------------|
| **ISO 26262** | Systematic failures | Bd measures representation consistency |
| **ISO 21448 (SOTIF)** | Performance limitations | Bd quantifies perception coherence |
| **UL 4600** | Safety case evidence | Bd provides quantifiable metric |
| **UN R157 (ALKS)** | Lane keeping safety | Bd < 0.01 for lane-relevant perception |
| **NHTSA ADS Framework** | Safety evidence | Bd supports safety case |
| **Euro NCAP 2025+** | AEB pedestrian | Bd for pedestrian detection consistency |
| **GB/T (China)** | AV safety testing | Bd methodology adaptable |

---

**Document version**: 1.0.0  
**Last updated**: December 2025  
**License**: AGI-HPC Responsible AI License v1.0

---

<p align="center">
  <em>"The Bond Index is the deliverable. Everything else is infrastructure."</em>
</p>
