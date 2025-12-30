# 🍎 ErisML/DEME: Open Source Ethics Engine for AI Agents — Contributors Welcome

**TL;DR:** We're building an open-source ethics decision layer for AI agents. MCP server included — Claude (and other AI) can call it directly. 68K lines of code, working integration layer, needs contributors to reach production readiness.

**Repo:** https://github.com/ahb-sjsu/erisml-lib  
**Task List:** https://github.com/ahb-sjsu/erisml-lib/blob/main/DEVELOPMENT_TASKS.md  
**Discord:** https://discord.gg/W3Bkj4AZ

---

## What is this?

**ErisML** is a modeling language for governed AI agents. **DEME** (Democratically Governed Ethics Module Engine) is the ethics decision layer — it evaluates candidate actions against configurable ethical frameworks and returns structured judgments.

Think of it as: **guardrails, but with democratic governance and philosophical rigor.**

```python
# What DEME does
options = [allocate_to_patient_A, allocate_to_patient_B, wait_for_more_info]
judgements = deme.evaluate_options(profile="hospital_v1", options=options)
decision = deme.govern_decision(judgements)
# Returns: selected option, forbidden options, rationale, audit trail
```

---

## Why should you care?

1. **Regulation is coming.** EU AI Act, NIST AI RMF, state-level AI laws — all require auditable, transparent AI governance. This is infrastructure for compliance.

2. **MCP integration exists.** The repo includes a working Model Context Protocol server. Claude (or any MCP-compatible AI) can call DEME tools today:
   - `list_profiles` — available governance configurations
   - `evaluate_options` — run ethics modules on candidate actions
   - `govern_decision` — aggregate judgments, select action

3. **Multi-agent RL integration.** PettingZoo adapter lets you add ethics constraints to RL training environments.

4. **Novel theoretical foundations.** Bond Invariance Principle, Philosophy Engineering, Stratified Geometric Ethics — this isn't just "if harmful then don't." It's falsifiable ethics with mathematical structure.

---

## Current State: 8/10

| Strength | Status |
|----------|--------|
| Theoretical depth | ✅ Strong — 12+ papers/manuscripts |
| Integration layer | ✅ Strong — MCP, PettingZoo, PDDL |
| Documentation | ✅ Good — 59 docs, extensive README |
| Test suite | ⚠️ OK — 43 tests, needs expansion |
| PyPI package | ❌ Not yet |
| Community | ❌ Early — needs contributors |

---

## What we need help with

We've created a detailed task list with ~210 hours of work across 5 priority levels:

### 🔴 Critical Path (25 hrs) — Help us ship v0.1.0
- PyPI package release
- MCP server CLI entry point (`erisml-mcp-server`)
- JSON Schema hosting

### 🟡 Documentation (40 hrs) — Make it accessible
- Quick start tutorial
- MCP + Claude integration guide
- API reference docs

### 🟢 Testing (35 hrs) — Make it trustworthy
- Expand coverage to 80%+
- Add Windows CI
- Type checking with mypy

### 🔵 Ecosystem (60 hrs) — Make it useful
- Example DEME profiles for different domains
- PettingZoo demo with RL training
- Real-world pilot integration

### 🟣 Community (50 hrs) — Make it grow
- CONTRIBUTING.md, issue templates
- Blog posts, outreach
- Academic publication

**Full task list:** https://github.com/ahb-sjsu/erisml-lib/blob/main/DEVELOPMENT_TASKS.md

---

## Good First Issues

If you want to contribute but aren't sure where to start:

| Issue | Difficulty | Skills |
|-------|------------|--------|
| Add `--help` to MCP server CLI | Easy | Python, argparse |
| Create `hello_deme.py` example | Easy | Python |
| Add pytest-cov and coverage badge | Easy | CI/CD |
| Export JSON schemas to files | Medium | Python, JSON Schema |
| Write MCP integration tutorial | Medium | Technical writing |
| Add mypy type checking | Medium | Python typing |
| Create PettingZoo demo notebook | Hard | RL, Jupyter |

---

## Tech Stack

- **Python 3.12+**
- **Pydantic** — data validation
- **Lark** — grammar/parsing
- **PettingZoo/Gymnasium** — multi-agent RL
- **MCP (Model Context Protocol)** — AI agent integration
- **Tarski** — PDDL planning (optional)

---

## Who's behind this?

Andrew Bond, San José State University. Research focus: AI safety, ethics governance, pervasive computing. This started as academic research and is now becoming production infrastructure.

**Contact:** andrew.bond@sjsu.edu  
**License:** AGI-HPC Responsible AI License v1.0 (non-commercial research free, commercial requires agreement)

---

## How to get involved

1. ⭐ **Star the repo** — helps visibility
2. 📖 **Read the task list** — find something that fits your skills
3. 💬 **Join Discord** — https://discord.gg/W3Bkj4AZ
4. 🛠️ **Pick up an issue** — or propose your own
5. 🔀 **Submit a PR** — we review quickly

---

## Links

- **GitHub:** https://github.com/ahb-sjsu/erisml-lib
- **Task List:** https://github.com/ahb-sjsu/erisml-lib/blob/main/DEVELOPMENT_TASKS.md
- **Discord:** https://discord.gg/W3Bkj4AZ
- **DEME Whitepaper:** https://github.com/ahb-sjsu/erisml-lib/blob/main/deme_whitepaper_nist.md
- **QND Experiment Results:** https://github.com/ahb-sjsu/erisml-lib/blob/main/QND_EXPERIMENT_ANNOUNCEMENT.md

---

*"Ordo ex Chāōnā; Ethos ex Māchinā"*
*Order from Chaos; Ethics from the Machine*

---

## Cross-post locations

- [ ] r/MachineLearning
- [ ] r/artificial
- [ ] r/opensource
- [ ] Hacker News (Show HN)
- [ ] AI Safety community forums
- [ ] MCP Discord/community
- [ ] LinkedIn

