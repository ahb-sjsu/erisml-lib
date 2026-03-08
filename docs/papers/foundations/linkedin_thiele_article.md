# Independent Replication Confirms: Moral Reasoning Has Geometric Structure

**The most important thing that can happen to a scientific claim just happened to ours.**

For the past two years, I've been developing a framework called *Geometric Ethics* — the argument that moral evaluation isn't a scalar (a single number: safe/unsafe, reward 0.7) but a *tensor* on a nine-dimensional manifold with metric structure, gauge symmetry, and conservation laws. The mathematics borrows from physics — gauge invariance, Noether's theorem, Whitney stratification — but it's applied non-metaphorically to ethics. The tensors literally compute. The conservation laws literally constrain.

The obvious critique was always: "Interesting, but it's all from one lab."

That critique just died.

---

## What Happened

Lucas Thiele at UCLA independently set out to test the framework's core empirical prediction: that the nine dimensions of moral evaluation (consequences, rights, fairness, autonomy, privacy, societal impact, virtue, legitimacy, epistemic status) are *geometrically encoded* in the way language models represent moral scenarios — and that this encoding is *language-invariant*.

He used:
- The publicly available LaBSE multilingual embedding model
- His own corpus of moral scenarios (no access to our data)
- His own probe architecture (no access to our code)
- Six typologically diverse languages: English, Spanish, Mandarin, Arabic, Hindi, Swahili

His methodology was deliberately independent. He worked from the published framework description alone.

## The Results

**All nine dimensions are linearly decodable.** F1 scores ranged from 0.74 to 0.91, with a mean of 0.83. Physical harm was strongest (0.91); epistemic quality was weakest (0.74) — consistent with the latter's greater context-dependence, exactly as the framework predicts.

**Cross-lingual transfer works.** Probes trained on English and tested on the other five languages achieved F1 scores of 0.71–0.82. Deontic structure transfers across languages without per-language tuning. This is what the Bond Invariance Principle predicts: if moral structure is a genuine geometric invariant, it shouldn't depend on the coordinate system (language) in which you express it.

**The killer finding: orthogonality.** Principal-component analysis showed that the moral-judgement subspace and the language-identity subspace share less than 3% of their variance. They're nearly orthogonal. Moral structure and linguistic identity occupy *different subspaces* of the embedding manifold.

This is the difference between "we found a pattern" and "this is a structural property of the representation space."

---

## Why This Matters

In science, the moment a finding moves from "one group's result" to "independently replicated" is the moment it becomes real. Not because one replication settles everything — it doesn't — but because the most parsimonious explanation shifts from "artifact of their methodology" to "feature of the phenomenon."

For AI alignment specifically, three implications stand out:

**1. Scalar alignment really is the wrong structure.** If moral evaluation has nine decodable dimensions that are geometrically independent of language, then compressing that to a single reward signal (as RLHF, constitutional AI, and scalar optimization all do) destroys information that is *provably irrecoverable*. We proved this mathematically (the Information Monotonicity Theorem); Thiele's work shows the structure being destroyed is empirically real.

**2. The Bond Invariance Principle is falsifiable and confirmed.** The BIP says: if a transformation preserves the morally relevant structure (the "bonds" between agents), the moral evaluation must be unchanged. This is the ethical analogue of gauge invariance in physics. Thiele tested it with different data, different methods, a different lab — and the prediction held.

**3. Post-hoc safety is provably insufficient.** The Mandatory Canonicalization Theorem shows that for actions with irreversible consequences, checking compliance *after* execution violates harm conservation. Ethics has to be in the decision loop, not bolted on as a filter. The geometric framework provides the mathematical content for what "in the decision loop" actually means.

---

## Current State of the Research

The framework is now supported by:

- **Theoretical foundation:** Five principal theorems — Information Monotonicity, Structured Preservation, Moral Noether (harm conservation), D4 Gauge Group (deontic symmetry), and No Escape (containment) — published across multiple papers and a 700+ page monograph (*Geometric Ethics: The Mathematical Structure of Moral Reasoning*, now v1.15)

- **Empirical validation:** 20,030 Dear Abby letters, 109,294 cross-lingual passages spanning 11 languages and 3,000 years, plus Thiele's independent replication across 6 additional languages

- **Working implementation:** ErisML v3.0 is open-source on PyPI (`pip install erisml-lib`). It supports moral tensors from rank 1 through rank 6, the DEME governance architecture, hardware acceleration (sub-microsecond latency on embedded GPUs), and an MCP server for integration with any AI agent

- **Companion papers** on the Noether theorem for ethics, stratified gauge theory, the No Escape theorem, differential geometry of DEME, and a Philosophy Engineering foundation document

The Geometric Ethics Foundational Paper has just been submitted to *Minds and Machines* (Springer), after the editor at *Artificial Intelligence* (AIJ) noted it was "better suited to a philosophical venue" — fair feedback that led us to the right home for the work.

---

## What's Next

Three priorities:

1. **Expert human annotation.** The current ground-truth labels derive from LLM consensus. A human-annotated validation subset would close the most credible remaining methodological critique.

2. **More independent replications.** Thiele is n=2. We need n=5, n=10, from groups with no connection to us. The code and framework are public. The predictions are specific. Anyone can test them.

3. **The moral metric.** The principal open problem: calibrating the context-dependent trade-off structure (how much of one dimension is worth how much of another). The framework proves the metric must exist and constrains its symmetries, but doesn't derive it from first principles. This is an empirical measurement program, not a philosophical deadlock.

---

The claim has always been bold: ethics is not a number, it's a geometry. That claim is now independently confirmed. The scalar paradigm — the assumption that moral evaluation can be captured by a single reward signal — is mathematically untenable and empirically falsified.

The mathematics is ready. The implementation is ready. The independent verification is in.

What remains is the will to use it.

---

*Andrew H. Bond is a Senior Lecturer in Computer Engineering at San José State University and the developer of the ErisML/DEME framework for governed AI agents. The Geometric Ethics monograph (v1.15), companion papers, and ErisML source code are available at [github.com/ahb-sjsu/erisml-lib](https://github.com/ahb-sjsu/erisml-lib).*

*Lucas Thiele is a researcher at UCLA whose independent replication study was conducted without access to the Bond lab's code, data, or methodology.*

#AIAlignment #AIEthics #GeometricEthics #MachineLearning #AIResearch #GaugeInvariance #ComputationalEthics #ResponsibleAI
