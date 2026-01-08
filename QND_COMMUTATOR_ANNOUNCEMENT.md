# Empirical Finding: Order Effects in LLM Moral Judgment

**TL;DR**: We ran ~33,000 API calls measuring whether the order in which you ask an LLM about moral frameworks affects its judgments. It does — significantly, and with interpretable structure.

---

## The Experiment

When evaluating a moral scenario, does it matter whether you first ask "was there harm?" then "was there intent?" — versus the reverse order?

Classical probability says no. Independent judgments shouldn't depend on measurement order.

We tested this systematically:
- 8 moral axes (harm, intent, duty, rights, fairness, virtue, consent, liberty)
- 6 scenarios (trolley, whistleblower, lying to murderer, broken promise, rescue, triage)
- 56 ordered pairs, 50 trials each
- Total: 16,800 measurements

## The Result

**55% of axis pairs (31/56) showed statistically significant order effects.**

Examples:
- Asking about "rights" first decreases subsequent "duty" judgments by 38.5 percentage points
- Asking about "virtue" first increases subsequent "duty" judgments by 33.5 percentage points
- Asking about "liberty" first decreases subsequent "rights" judgments by 36.4 percentage points

These are not small effects. They replicate across scenarios.

## The Structure

We found asymmetric patterns:

**High sensitivity** (judgment shifts based on prior questions):
- duty, harm, fairness, rights

**High context power** (asking this first shifts subsequent judgments):
- virtue, fairness, consent, liberty

**Low context power** (asking this first doesn't shift others much):
- harm, intent

The last finding is surprising: harm and intent are morally central, but asking about them first doesn't shift other judgments. Our interpretation: they're "pre-collapsed" — already determined by the scenario description before any explicit measurement.

## What This Is

An empirical observation about LLM behavior. The model does not treat moral frameworks as independent evaluations. The order of questioning matters.

## What This Isn't

- Proof of consciousness
- Proof of "quantum cognition"
- A claim about human moral psychology

We make no strong claims about mechanism. The structure is consistent with several interpretations:
1. Prompt sensitivity / attention effects
2. Learned patterns from human moral discourse
3. Something deeper about how moral concepts relate

The data doesn't distinguish between these. What it does establish is that the effect exists, it's large, and it has structure.

## Reproducibility

- Model: Claude Sonnet 4 (claude-sonnet-4-20250514)
- All runs via Anthropic Batch API
- Pre-registration hashes recorded before analysis
- Full data and code available on request

## Related Work

Order effects in human judgment are well-documented (Trueblood & Busemeyer, 2011; Pothos & Busemeyer, 2013). Some researchers model these using quantum probability theory. We're not committed to that interpretation, but our results are consistent with that literature.

## Next Steps

- Replication on other models (GPT-4, Gemini)
- Testing whether ambiguous scenarios show different patterns
- Formal analysis of the commutator algebra structure

---

*Research conducted December 2025. Total API cost: ~$58.*
