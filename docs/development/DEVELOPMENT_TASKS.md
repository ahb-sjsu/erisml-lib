# ErisML/DEME Development Task List

## 🍎 Philosophy Engineering — Development Roadmap

**Objective:** Production Readiness & Community Adoption  
**Current State:** 8/10  
**Target State:** 9/10 → Production-ready, installable, documented, validated

---

## Project Overview

ErisML/DEME is the implementation of the **Grand Unified AI Safety Stack (GUASS)** — a seven-layer architecture for ethically governed AI systems:

| Layer | Name | Status |
|-------|------|--------|
| L7 | The Geometry of Good (Application) | 📄 Whitepaper |
| L6 | ErisML (Presentation) | ✅ Implemented |
| L5 | Translation Layer (Session) | ✅ Implemented |
| L4 | Philosophy Engineering (Transport) | ✅ Implemented |
| L3 | GUASS Core (Network) | ✅ Implemented |
| L2 | Noether Ethics (Data Link) | 📄 Whitepaper |
| L1 | Quantum Normative Dynamics (Physical) | 🧪 Experimental |
| L0 | Pragmatist Rebuttal (Foundation) | 📄 Published |

**Codebase:** 68,593 LOC across 133 files  
**Estimated Effort to 9/10:** ~210 hours

---

## 🔴 Priority 1: Critical Path (Weeks 1-2)
*Goal: `pip install erisml` works, MCP server callable*

### 1.1 PyPI Package Release

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Clean `pyproject.toml` for PyPI compatibility | 2h | Python packaging | ⬜ |
| Add `[project.scripts]` entry points | 1h | setuptools | ⬜ |
| Create `__version__.py` with version management | 1h | Python | ⬜ |
| Write `MANIFEST.in` (include schemas, profiles) | 1h | Packaging | ⬜ |
| Test local install: `pip install -e .` | 1h | Testing | ⬜ |
| Register on test.pypi.org, test install | 2h | PyPI | ⬜ |
| Publish v0.1.0 to PyPI | 1h | PyPI | ⬜ |
| Add PyPI badge to README | 0.5h | Markdown | ⬜ |

**Acceptance Criteria:**
```bash
pip install erisml
python -c "from erisml.ethics import DEME; print('OK')"
```

### 1.2 MCP Server CLI Entry Point

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Add `erisml-mcp-server` CLI command | 2h | argparse/click | ⬜ |
| Add `--port`, `--profiles-dir`, `--log-level` args | 2h | CLI design | ⬜ |
| Add `--help` with usage examples | 1h | Documentation | ⬜ |
| Create default `deme_profiles/` with 3 examples | 2h | DEME profiles | ⬜ |
| Test with Claude Desktop MCP configuration | 3h | MCP, testing | ⬜ |
| Document MCP setup in README | 2h | Technical writing | ⬜ |

**Acceptance Criteria:**
```bash
erisml-mcp-server --profiles-dir ./profiles
# Server starts, responds to MCP tool calls
```

### 1.3 JSON Schema Publishing

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Create `schemas/` directory in repo | 0.5h | Git | ⬜ |
| Export `ethical_facts.json` to file | 1h | Python | ⬜ |
| Export `ethical_judgement.json` to file | 1h | Python | ⬜ |
| Export `deme_profile_v03.json` schema | 2h | JSON Schema | ⬜ |
| Export `erisml_model.json` schema | 2h | JSON Schema | ⬜ |
| Set up GitHub Pages for schemas | 2h | GitHub | ⬜ |
| Update `$id` URLs in schemas | 1h | JSON Schema | ⬜ |

**Acceptance Criteria:**
- `https://ahb-sjsu.github.io/erisml-lib/schemas/ethical_facts.json` returns valid schema
- External services can validate against published schemas

---

## 🟡 Priority 2: Documentation (Weeks 2-3)
*Goal: New users can get started in 15 minutes*

### 2.1 Quick Start Guide

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Write "5-Minute Quick Start" section | 3h | Technical writing | ⬜ |
| Create `examples/hello_deme.py` | 2h | Python | ⬜ |
| Create `examples/mcp_client_demo.py` | 3h | MCP, Python | ⬜ |
| Create `examples/evaluate_scenario.py` | 2h | Python | ⬜ |
| Add inline comments to all examples | 2h | Documentation | ⬜ |
| Test examples in CI | 2h | CI/CD | ⬜ |

### 2.2 MCP + Claude Integration Tutorial

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Write "Claude + DEME" step-by-step guide | 4h | Technical writing | ⬜ |
| Create `claude_desktop_config.json` example | 1h | MCP | ⬜ |
| Document common troubleshooting issues | 2h | Support docs | ⬜ |
| Record demo video (optional, high-value) | 4h | Video production | ⬜ |
| Add to `docs/tutorials/` | 1h | Git | ⬜ |

### 2.3 API Reference Documentation

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Set up mkdocs or Sphinx | 3h | Documentation tools | ⬜ |
| Generate API docs from docstrings | 2h | Sphinx/mkdocs | ⬜ |
| Write module overview pages | 4h | Technical writing | ⬜ |
| Add GUASS architecture diagram | 3h | Diagramming | ⬜ |
| Deploy to GitHub Pages | 2h | GitHub Actions | ⬜ |

### 2.4 GUASS Layer Documentation

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Create `docs/guass/` directory structure | 1h | Documentation | ⬜ |
| Write L6 (ErisML) implementation guide | 3h | Technical writing | ⬜ |
| Write L5 (Translation Layer) guide | 3h | Technical writing | ⬜ |
| Write L4 (Philosophy Engineering) guide | 3h | Technical writing | ⬜ |
| Write L3 (GUASS Core) integration guide | 2h | Technical writing | ⬜ |
| Document Bond Index calculation | 2h | Technical writing | ⬜ |

---

## 🟢 Priority 3: Testing & Quality (Weeks 3-4)
*Goal: 80%+ coverage, type-safe, CI on all platforms*

### 3.1 Expand Test Coverage

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Add tests for `mcp_deme_server.py` | 4h | pytest | ⬜ |
| Add tests for `serialization.py` edge cases | 3h | pytest | ⬜ |
| Add tests for `profile_adapters.py` | 3h | pytest | ⬜ |
| Add tests for `pettingzoo_adapter.py` | 3h | pytest, PettingZoo | ⬜ |
| Add tests for `pddl_adapter.py` | 2h | pytest, Tarski | ⬜ |
| Add integration test: full DEME flow | 4h | pytest | ⬜ |
| Add Bond Index calculation tests | 3h | pytest | ⬜ |

### 3.2 Coverage & CI Enhancements

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Set up pytest-cov | 1h | pytest | ⬜ |
| Add coverage badge to README | 1h | CI/CD | ⬜ |
| Add matrix testing (Python 3.10-3.12) | 2h | GitHub Actions | ⬜ |
| Add Windows CI runner | 2h | GitHub Actions | ⬜ |
| Add macOS CI runner | 1h | GitHub Actions | ⬜ |
| Add automatic PyPI publish on tag | 3h | GitHub Actions | ⬜ |

### 3.3 Type Checking

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Run mypy on full codebase | 2h | mypy | ⬜ |
| Fix type errors (target: 0 errors) | 6h | Python typing | ⬜ |
| Add mypy to CI | 1h | CI/CD | ⬜ |
| Add py.typed marker for PEP 561 | 0.5h | Packaging | ⬜ |

---

## 🔵 Priority 4: Ecosystem (Weeks 4-6)
*Goal: Ready for real-world use cases*

### 4.1 DEME Profile Library

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Create `hospital_service_robot_v1.json` | 2h | DEME | ⬜ |
| Create `home_assistant_v1.json` | 2h | DEME | ⬜ |
| Create `content_moderation_v1.json` | 2h | DEME | ⬜ |
| Create `autonomous_vehicle_v1.json` | 2h | DEME | ⬜ |
| Create `financial_advisor_v1.json` | 2h | DEME | ⬜ |
| Create `jain_1.json` (values-based example) | 2h | DEME | ⬜ |
| Document profile customization guide | 3h | Technical writing | ⬜ |

### 4.2 Translation Layer (L5) Examples

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Complete EU AI Ethics Guidelines module | 4h | Policy translation | ⬜ |
| Create NIST AI RMF translation module | 4h | Policy translation | ⬜ |
| Create IEEE P7000 translation module | 3h | Policy translation | ⬜ |
| Document DAG composition patterns | 3h | Technical writing | ⬜ |
| Add contestation handling examples | 2h | Python | ⬜ |

### 4.3 PettingZoo Integration

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Complete PettingZoo adapter implementation | 4h | PettingZoo, Gymnasium | ⬜ |
| Create example environment with DEME | 4h | RL, Python | ⬜ |
| Add norm violation tracking/logging | 3h | Python | ⬜ |
| Create Jupyter notebook walkthrough | 4h | Jupyter | ⬜ |
| Benchmark: training with/without ethics | 6h | RL, benchmarking | ⬜ |

### 4.4 PDDL/Planning Integration

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Expand Tarski adapter beyond stub | 4h | Tarski, PDDL | ⬜ |
| Add norm constraints to PDDL export | 3h | PDDL | ⬜ |
| Create planning example with ethics | 3h | AI planning | ⬜ |
| Test with Fast Downward planner | 2h | Planning | ⬜ |

### 4.5 Real-World Pilot

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Identify pilot use case | 4h | Business dev | ⬜ |
| Implement domain-specific EthicalFacts builder | 8h | Python | ⬜ |
| Create custom DEME profile for pilot | 4h | DEME | ⬜ |
| Run pilot for 1 week, collect logs | 20h | Operations | ⬜ |
| Analyze results, write case study | 8h | Analysis, writing | ⬜ |

---

## 🟣 Priority 5: Community & Research (Ongoing)
*Goal: Sustainable open-source project*

### 5.1 Community Infrastructure

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Create `CONTRIBUTING.md` | 2h | Documentation | ⬜ |
| Create issue templates (bug, feature, question) | 1h | GitHub | ⬜ |
| Create PR template | 1h | GitHub | ⬜ |
| Label existing issues (`good-first-issue`, etc.) | 2h | GitHub | ⬜ |
| Set up GitHub Discussions categories | 1h | GitHub | ⬜ |
| Create Discord contributor channels | 2h | Discord | ⬜ |

### 5.2 Outreach

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Post to r/MachineLearning | 1h | Community | ⬜ |
| Post to r/artificial, r/opensource | 1h | Community | ⬜ |
| Submit to Hacker News (Show HN) | 1h | Community | ⬜ |
| Submit to AI safety newsletters | 2h | Outreach | ⬜ |
| Reach out to MCP community | 2h | Networking | ⬜ |
| Present at meetup / university seminar | 4h | Presentation | ⬜ |

### 5.3 Academic Publication

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Select target venue (NeurIPS, AAAI, FAccT) | 2h | Academic | ⬜ |
| Prepare camera-ready paper | 20h | Academic writing | ⬜ |
| Run experiments for empirical section | 20h | Research | ⬜ |
| Submit paper | 4h | Academic | ⬜ |
| Prepare supplementary materials | 8h | Documentation | ⬜ |

### 5.4 QND Experiment Expansion

| Task | Est. | Skills | Status |
|------|------|--------|--------|
| Run Phase 2: Total Probability Violation | 10h | Python, statistics | ⬜ |
| Run Phase 3: Interference Visibility | 10h | Python, statistics | ⬜ |
| Run Phase 4: Bell Inequality Test | 15h | Python, statistics | ⬜ |
| Multi-model replication (GPT-4, Gemini) | 10h | API integration | ⬜ |
| Human comparison study design | 8h | Research design | ⬜ |
| Write QND paper for publication | 20h | Academic writing | ⬜ |

---

## Good First Issues

New contributors start here:

| Issue | Difficulty | Skills | Est. |
|-------|------------|--------|------|
| Add `--help` to MCP server CLI | 🟢 Easy | Python, argparse | 2h |
| Create `hello_deme.py` example | 🟢 Easy | Python | 2h |
| Add pytest-cov and coverage badge | 🟢 Easy | CI/CD | 2h |
| Fix pytest marker warnings | 🟢 Easy | pytest | 1h |
| Export JSON schemas to files | 🟡 Medium | Python, JSON Schema | 3h |
| Write MCP integration tutorial | 🟡 Medium | Technical writing | 4h |
| Add mypy type checking | 🟡 Medium | Python typing | 4h |
| Add Windows CI runner | 🟡 Medium | GitHub Actions | 2h |
| Create PettingZoo demo notebook | 🔴 Hard | RL, Jupyter | 8h |
| Implement EU AI Ethics translation | 🔴 Hard | Policy, Python | 8h |

---

## Sprint Plan

### Sprint 1 (Weeks 1-2): "Installable & Callable"
- [ ] PyPI package release (v0.1.0)
- [ ] MCP server CLI entry point
- [ ] JSON Schema publishing
- [ ] Basic quick start tutorial
- [ ] Fix pytest warnings

**Exit Criteria:** `pip install erisml && erisml-mcp-server --help` works

### Sprint 2 (Weeks 3-4): "Documented & Tested"
- [ ] Expand test coverage to 80%
- [ ] API reference docs live
- [ ] MCP + Claude tutorial complete
- [ ] CI/CD enhancements (multi-platform)
- [ ] Type checking passing

**Exit Criteria:** New contributor can understand and extend the codebase

### Sprint 3 (Weeks 5-6): "Demonstrated & Validated"
- [ ] 5+ example DEME profiles
- [ ] PettingZoo integration demo
- [ ] Translation Layer examples (EU, NIST)
- [ ] Real-world pilot kickoff
- [ ] Community outreach begins

**Exit Criteria:** External users running DEME in their projects

### Sprint 4 (Weeks 7-8): "Published & Growing"
- [ ] Pilot case study published
- [ ] Paper submitted
- [ ] First external contributor PR merged
- [ ] 100+ GitHub stars

**Exit Criteria:** Sustainable open-source project with external contributors

---

## Definition of Done: 9/10

- [ ] `pip install erisml` works
- [ ] `erisml-mcp-server` runs out of the box
- [ ] Published JSON Schemas at stable URLs
- [ ] 80%+ test coverage on core modules
- [ ] Working MCP + Claude tutorial
- [ ] Working PettingZoo demo
- [ ] 5+ DEME profiles for different domains
- [ ] One real-world pilot with case study
- [ ] 3+ contributors beyond original author
- [ ] 100+ GitHub stars
- [ ] One peer-reviewed or preprint publication

---

## Effort Summary

| Priority | Category | Tasks | Hours |
|----------|----------|-------|-------|
| 🔴 P1 | Critical Path | 22 | ~25h |
| 🟡 P2 | Documentation | 18 | ~45h |
| 🟢 P3 | Testing & Quality | 15 | ~35h |
| 🔵 P4 | Ecosystem | 22 | ~75h |
| 🟣 P5 | Community & Research | 18 | ~100h |
| **Total** | | **95** | **~280h** |

---

## How to Contribute

1. ⭐ **Star the repo** — helps visibility
2. 📖 **Read this task list** — find something that fits your skills
3. 💬 **Join Discord** — https://discord.gg/W3Bkj4AZ
4. 🛠️ **Pick up a task** — comment on issue or create one
5. 🔀 **Submit a PR** — we review quickly

**Questions?** Ask in Discord `#dev-help` or open a Discussion.

---

## Links

- **GitHub:** https://github.com/ahb-sjsu/erisml-lib
- **Discord:** https://discord.gg/W3Bkj4AZ
- **Discussions:** https://github.com/ahb-sjsu/erisml-lib/discussions/2
- **DEME Whitepaper:** [deme_whitepaper_nist.md](../guides/deme_whitepaper_nist.md)
- **GUASS Technical Spec:** [GUASS_SAI.md](../guides/GUASS_SAI.md)
- **Translation Layer:** [Translation_Layer_Whitepaper_v0.21.md](../guides/Translation_Layer_Whitepaper_v0.21.md)
- **QND Experiment Results:** [QND_EXPERIMENT_ANNOUNCEMENT.md](../qnd/QND_EXPERIMENT_ANNOUNCEMENT.md)

---

*"Ordo ex Chāōnā; Ethos ex Māchinā"*  
*Order from Chaos; Ethics from the Machine*

---

*Document created: December 2025*  
*Review cadence: Weekly sprint planning*  
*Contact: andrew.bond@sjsu.edu*
