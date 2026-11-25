# ErisML Documentation Index

This directory holds the documentation of the ErisML/DEME project and the source of the website
[erisml.org](https://erisml.org), which GitHub Pages serves from here on every push to `main`.

The library's own README is [`../README.md`](../README.md). It covers installation, the DEME pipeline, and
what version 3.2 adds.

## Related Repositories

| Repository | Description |
|------------|-------------|
| [ahb-sjsu/erisml-compiler](https://github.com/ahb-sjsu/erisml-compiler) | Compiler from moral text and structured scenes to a typed MoralGraph read by four ethical lenses. It extracts; erisml-lib judges |
| [ahb-sjsu/moral-spectrum-analyzer](https://github.com/ahb-sjsu/moral-spectrum-analyzer) | Formerly `gtc-prototype`. Content moderation on validated moral axes, and a simulated home-care robot whose proposed acts pass DEME as a veto gate |
| [ahb-sjsu/non-abelian-sqnd](https://github.com/ahb-sjsu/non-abelian-sqnd) | NA-SQND theoretical research: papers, experiments, and mathematical foundations |
| [ahb-sjsu/sqnd-probe](https://github.com/ahb-sjsu/sqnd-probe) | Dear Ethicist, an advice column game for measuring moral reasoning structure |

## Directory Structure

```
docs/
├── index.html               # erisml.org home page
├── assets/                  # shared CSS and JavaScript (sitebar.js draws the top bar of every section)
├── books.json               # the Geometric Series volumes; the site's menus are built from it
│
├── book/                    # Geometric Ethics (Book 2), built site        ┐ git submodules, each
├── geometric-*/             # the other volumes of the Geometric Series    ┘ a volume's built site
├── data-mining-as-observation/   # the OT textbook, online edition
├── encyclopedia/            # the Observation Theory Encyclopedia
│
├── papers/
│   ├── foundations/         # Core theory papers (TeX sources, some PDFs) and submission packages
│   └── experiments/         # Experiment reports
├── applications/            # Domain application whitepapers (markdown)
├── vision/                  # Vision and roadmap documents
├── guides/                  # Technical guides and whitepapers
├── qnd/                     # Quantum Normative Dynamics protocols and reports
├── notebooks/               # I-EIP Monitor tutorial notebook
├── EFM/                     # Ethical Facts Module material
├── community/               # Community and announcement docs
├── development/             # Sprint plans and development notes
├── brand/                   # Logo files
│
├── CONCEPT_REGISTRY.md      # one row per concept: its status and where it lives
├── moralvector_reference.md # the MoralVector dimensions and their evidence
├── moralvector_v2_architecture.md
├── I-EIP_Monitor_Whitepaper.md
└── CATEGORICAL_FRAMEWORK.md
```

## Quick Links

### Getting Started
- [`../README.md`](../README.md): install, quick start, the DEME decision flow
- Tutorials: the notebooks in [`../notebooks/tutorials/`](../notebooks/tutorials/), linked from the
  [Tutorials section](https://erisml.org/#tutorials) of the home page
- [CONCEPT_REGISTRY.md](CONCEPT_REGISTRY.md): what each concept is and whether it is proved, measured,
  posited or withdrawn

### Vision & Architecture
- [AI_SAFETY_STACK.md](vision/AI_SAFETY_STACK.md): AI Safety Stack overview
- [DEME_2.0_Vision_Paper.md](vision/DEME_2.0_Vision_Paper.md): DEME 2.0 architecture
- [DEME_3.0_Tensorial_Ethics_Vision.md](vision/DEME_3.0_Tensorial_Ethics_Vision.md): tensorial ethics vision
- [ErisML_Vision.md](vision/ErisML_Vision.md): ErisML vision document
- [erisml.md](vision/erisml.md): the language design

### Technical Guides
- [DEME_EFM_Design_Guide_v0.1.md](guides/DEME_EFM_Design_Guide_v0.1.md): Ethics Module design guide, the
  source of the composition patterns in 3.2
- [deme_whitepaper_nist.md](guides/deme_whitepaper_nist.md): NIST alignment whitepaper
- [moralvector_reference.md](moralvector_reference.md): MoralVector reference
- [I-EIP_Monitor_Whitepaper.md](I-EIP_Monitor_Whitepaper.md): the I-EIP Monitor
- [SQND_ROSETTA_STONE_PRIMER.md](guides/SQND_ROSETTA_STONE_PRIMER.md): SQND concepts primer

### QND Experiments
- [QUICKSTART.md](guides/QUICKSTART.md): quick start for the QND experiment scripts
- [QND_README.md](qnd/QND_README.md): QND overview
- [QND_BELL_TEST_README.md](qnd/QND_BELL_TEST_README.md): Bell test methodology
- [QND_EXPERIMENT_ANNOUNCEMENT.md](qnd/QND_EXPERIMENT_ANNOUNCEMENT.md): announcement of the first results

The outcome of this line as the book reports it in v1.25: order effects were observed in one language
model, not in people, and a Bell violation was not found and is withdrawn as a prediction.

### Research Papers
- [papers/foundations/](papers/foundations/): core theory papers
- [papers/experiments/](papers/experiments/): experiment reports
- [applications/](applications/): domain application whitepapers
- [Dear_Abby_Empirical_Ethics_Analysis.md](papers/foundations/Dear_Abby_Empirical_Ethics_Analysis.md):
  empirical ethics from the Dear Abby corpus

### Community
- [DISCUSSIONS_WELCOME.md](community/DISCUSSIONS_WELCOME.md): community guidelines
- [ANNOUNCEMENT.md](community/ANNOUNCEMENT.md): project announcements

### Development
- [DEVELOPMENT_TASKS.md](development/DEVELOPMENT_TASKS.md): development tasks
- [V2_TEST_PLAN.md](development/V2_TEST_PLAN.md): DEME 2.0 test coverage plan
- [`../BUILDING.md`](../BUILDING.md): how the website is put together and how to add a volume
