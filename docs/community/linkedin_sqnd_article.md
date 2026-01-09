# When Your AI Safety Theory Fails Its Own Tests (And Why That's Good Science)

I just published v4.1 of my research paper on detecting moral reasoning consistency in large language models. The headline finding? **One of our key predictions was wrong.**

And I think that's the most important result.

---

## The Quick Version

My research applies mathematical tools from physics (specifically, discrete gauge theory) to create formal tests for AI moral reasoning. Think of it as "unit tests for ethical consistency."

**What we test:**
- Does the AI give consistent answers when you rephrase the same question?
- Do its judgments respect logical symmetries (if Morgan owes Alex, then Alex is owed by Morgan)?
- When does presentation order affect the answer — and when *should* it?

We've run 3,110 experimental evaluations across multiple protocols. Most predictions held up. One didn't.

---

## What We Got Right

**Discrete semantic gating**: AI moral judgments don't shift gradually. They flip at specific trigger phrases. "Only if convenient" produces 100% shift. "Found a friend who might help" produces 0% shift. The transition is a step function, not a sigmoid.

**Exact correlative symmetry**: When we ask about Morgan's obligation to Alex vs. Alex's claim against Morgan, the AI gets the logical pairing right 100% of the time. That's not approximate — it's exact.

**Selective path dependence**: Sometimes the order of presenting information matters (journalist facing truth vs. protection). Sometimes it doesn't (doctor facing autonomy vs. beneficence). The theory correctly predicted *which* scenarios would show order effects.

**Classical structure**: We ran Bell inequality tests adapted for moral scenarios. No quantum-like violations detected. The math is non-Abelian (order matters) but classical (no superposition).

---

## What We Got Wrong

**Hysteresis** — the prediction that obligations are "stickier" than liberties. Our original experiment found asymmetric thresholds: harder to dissolve an obligation than to create one.

Then we ran a proper double-blind replication.

**The methodology:**
- Single calibrated scale (not two different ladders)
- Blinded condition codes (experimenter didn't know which condition was which)
- Fresh API session per trial (no context carryover)
- Separate blind judge (classified responses without seeing conditions)
- Randomized order

**The result:** No hysteresis. The original finding was an artifact of how we constructed the measurement scales.

**What we found instead:** A *reverse* context effect. When the AI imagines someone "busy and on their way to an appointment," it actually judges obligation *more strongly* than when the person "has free time." Conflict and sacrifice increase moral salience.

That's interesting. But it's not what we predicted.

---

## Why This Matters

In AI safety research, there's enormous pressure to report positive results. "Our theory works!" is more publishable than "we got it wrong."

But falsification is the point.

A theory that can't be wrong isn't science. It's marketing. The SQND framework makes specific, testable predictions with explicit falsifiers. When we ran better experiments, one prediction failed. We updated the theory.

**The revision:**
- Hysteresis: Confirmed → **Not Confirmed**
- Context-dependent moral salience: Not Tested → **Confirmed**
- Introspective-behavioral discrepancy: Flagged for investigation

The introspective experiments (where Claude reports on its own reasoning) described obligations as "stickier." The behavioral experiments didn't support that. That tension is now a research question, not a buried inconvenience.

---

## What This Framework Actually Does

| Tests | Doesn't Test |
|-------|--------------|
| Internal consistency | Whether values are "correct" |
| Logical symmetry | Adversarial robustness |
| Gate reliability | Distribution shift |
| Path dependence patterns | Deceptive alignment |
| Deployment readiness metric | Human judgment replacement |

It's a type system for moral reasoning. Type-checked code can still have bugs. An AI that passes these tests applies its values consistently — but those values could still be wrong.

---

## The Technical Details (For Those Who Want Them)

**Gauge group**: D₄ × U(1)_H (discrete non-Abelian structure for moral states, continuous parameter for salience)

**Core finding**: The Hohfeldian classification (Obligation, Claim, Liberty, No-Claim) exhibits exact D₄ symmetry. The reflection generator (O↔C, L↔N) works perfectly. The rotation generator (state transitions) requires specific linguistic triggers.

**Statistical power**: N=3,110 total evaluations. Correlative symmetry at 100%. Path dependence combined p < 10⁻⁸. Double-blind hysteresis experiment: N=630, no significant effect after correction.

**Code and data**: Available at github.com/ahb-sjsu/erisml-lib

---

## The Takeaway

If you're working on AI alignment, here's what I'd want you to know:

1. **Formal methods work** — but only if you're willing to let them falsify your claims
2. **Methodology matters** — our double-blind protocol caught an artifact that naive testing missed
3. **Negative results are results** — updating theories based on evidence is the whole point
4. **The structure is real** — even with one prediction failing, the core D₄ symmetry holds at 100%

The math is borrowed from physics. The methodology is borrowed from psychology. The application is AI safety. The goal is building systems we can actually trust — which means testing them rigorously enough to find out when we're wrong.

---

*Full paper: "Non-Abelian Gauge Structure in Stratified Quantum Normative Dynamics" v4.1*

*Andrew H. Bond*  
*Department of Computer Engineering, San José State University*  
*Sr. Member, IEEE*

#AIAlignment #MachineLearning #AIEthics #AISafety #Research #ComputerScience

---

*Thanks to Claude (Anthropic) for collaboration on experiments and analysis. Yes, I'm using an AI to study AI moral reasoning. The recursion is intentional.*
