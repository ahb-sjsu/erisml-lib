# ErisML/DEME Development Task List

## Objective: Production Readiness & Community Adoption (Target: 9/10)

**Current State:** 8/10 — Strong theoretical foundation, clean integration layer, but lacking packaging, documentation, and real-world validation.

**Target State:** 9/10 — Installable package, working demos, published schemas, one production integration.

---

## 🔴 Priority 1: Critical Path (Weeks 1-2)

### 1.1 PyPI Package Release

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Clean up `pyproject.toml` for PyPI compatibility | | 2 | ⬜ |
| Add `[project.scripts]` entry point for MCP server | | 1 | ⬜ |
| Create `__version__` and version management | | 1 | ⬜ |
| Write `MANIFEST.in` for including schemas/profiles | | 1 | ⬜ |
| Test local install: `pip install -e .` | | 1 | ⬜ |
| Register `erisml` on PyPI (test.pypi.org first) | | 2 | ⬜ |
| Publish v0.1.0 to PyPI | | 1 | ⬜ |
| Add PyPI badge to README | | 0.5 | ⬜ |

**Acceptance Criteria:**
```bash
pip install erisml
python -m erisml.ethics.interop.mcp_deme_server
# Server starts successfully
```

---

### 1.2 MCP Server Entry Point

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Add CLI entry point: `erisml-mcp-server` | | 2 | ⬜ |
| Add `--port` and `--profiles-dir` CLI args | | 2 | ⬜ |
| Add `--help` with usage examples | | 1 | ⬜ |
| Create default `deme_profiles/` with 2-3 example profiles | | 2 | ⬜ |
| Test with Claude Desktop MCP config | | 3 | ⬜ |
| Document MCP setup in README | | 2 | ⬜ |

**Acceptance Criteria:**
```bash
erisml-mcp-server --profiles-dir ./my_profiles --port 8080
# Server starts, Claude can connect and call tools
```

---

### 1.3 JSON Schema Publishing

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Create `schemas/` directory in repo | | 0.5 | ⬜ |
| Export `ethical_facts.json` schema to file | | 1 | ⬜ |
| Export `ethical_judgement.json` schema to file | | 1 | ⬜ |
| Export `deme_profile_v03.json` schema | | 2 | ⬜ |
| Set up GitHub Pages for `ahb-sjsu.github.io/erisml-lib/schemas/` | | 2 | ⬜ |
| Update `$id` URLs in schemas to point to hosted versions | | 1 | ⬜ |
| Add schema validation CI check | | 2 | ⬜ |

**Acceptance Criteria:**
- `https://ahb-sjsu.github.io/erisml-lib/schemas/ethical_facts.json` returns valid JSON Schema
- External services can validate payloads against published schemas

---

## 🟡 Priority 2: Documentation & Demos (Weeks 2-3)

### 2.1 Quick Start Tutorial

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Write "5-Minute Quick Start" for README | | 3 | ⬜ |
| Create `examples/hello_deme.py` — minimal ethics check | | 2 | ⬜ |
| Create `examples/mcp_client_demo.py` — call MCP server | | 3 | ⬜ |
| Create `examples/pettingzoo_ethics_demo.py` | | 4 | ⬜ |
| Add inline comments explaining each step | | 2 | ⬜ |
| Test all examples in CI | | 2 | ⬜ |

**Acceptance Criteria:**
- New user can run `hello_deme.py` in <5 minutes
- All examples pass in CI

---

### 2.2 MCP Integration Video/Tutorial

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Write step-by-step tutorial: "Claude + DEME" | | 4 | ⬜ |
| Record 3-5 min demo video (optional but high-value) | | 4 | ⬜ |
| Create `claude_desktop_config.json` example | | 1 | ⬜ |
| Document common MCP troubleshooting | | 2 | ⬜ |
| Add to `docs/tutorials/mcp_integration.md` | | 2 | ⬜ |

**Acceptance Criteria:**
- User can follow tutorial and have Claude making DEME calls in <15 minutes

---

### 2.3 API Reference Documentation

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Set up mkdocs or Sphinx | | 3 | ⬜ |
| Generate API docs from docstrings | | 2 | ⬜ |
| Write module overview pages | | 4 | ⬜ |
| Add architecture diagram | | 3 | ⬜ |
| Deploy to GitHub Pages | | 2 | ⬜ |
| Add "Documentation" badge to README | | 0.5 | ⬜ |

**Acceptance Criteria:**
- `https://ahb-sjsu.github.io/erisml-lib/docs/` has searchable API reference

---

## 🟢 Priority 3: Testing & Quality (Weeks 3-4)

### 3.1 Expand Test Coverage

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Add tests for `mcp_deme_server.py` | | 4 | ⬜ |
| Add tests for `serialization.py` edge cases | | 3 | ⬜ |
| Add tests for `profile_adapters.py` | | 3 | ⬜ |
| Add integration test: full DEME flow | | 4 | ⬜ |
| Set up coverage reporting (pytest-cov) | | 2 | ⬜ |
| Add coverage badge to README | | 1 | ⬜ |
| Target: 80%+ coverage on core modules | | — | ⬜ |

**Acceptance Criteria:**
- `pytest --cov=erisml` shows 80%+ on `ethics/` modules
- All MCP tools have unit tests

---

### 3.2 CI/CD Enhancements

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Add matrix testing (Python 3.10, 3.11, 3.12) | | 2 | ⬜ |
| Add Windows CI runner | | 2 | ⬜ |
| Add automatic PyPI publish on tag | | 3 | ⬜ |
| Add schema validation step | | 2 | ⬜ |
| Add example script smoke tests | | 2 | ⬜ |

**Acceptance Criteria:**
- CI passes on Linux + Windows, Python 3.10-3.12
- Tagged releases auto-publish to PyPI

---

### 3.3 Type Checking & Linting

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Run `mypy` on full codebase | | 2 | ⬜ |
| Fix type errors (target: 0 errors) | | 6 | ⬜ |
| Add `mypy` to CI | | 1 | ⬜ |
| Ensure `ruff` passes with strict config | | 2 | ⬜ |

**Acceptance Criteria:**
- `mypy src/` passes with no errors
- `ruff check .` passes

---

## 🔵 Priority 4: Ecosystem & Adoption (Weeks 4-6)

### 4.1 Example DEME Profiles Library

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Create `profiles/hospital_service_robot_v1.json` | | 2 | ⬜ |
| Create `profiles/home_assistant_v1.json` | | 2 | ⬜ |
| Create `profiles/content_moderation_v1.json` | | 2 | ⬜ |
| Create `profiles/autonomous_vehicle_v1.json` | | 2 | ⬜ |
| Create `profiles/jain_1.json` (values-based example) | | 2 | ⬜ |
| Document profile customization guide | | 3 | ⬜ |

**Acceptance Criteria:**
- 5+ ready-to-use profiles covering different domains
- Users can copy and customize for their use case

---

### 4.2 PettingZoo Integration Demo

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Create complete PettingZoo example environment | | 6 | ⬜ |
| Add norm violation tracking/logging | | 3 | ⬜ |
| Create Jupyter notebook walkthrough | | 4 | ⬜ |
| Benchmark: RL training with/without ethics constraints | | 6 | ⬜ |
| Write blog post / tutorial | | 4 | ⬜ |

**Acceptance Criteria:**
- Working RL training loop with DEME constraints
- Measurable difference in agent behavior with ethics enabled

---

### 4.3 Real-World Pilot Integration

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Identify pilot use case (robot, chatbot, etc.) | | 4 | ⬜ |
| Implement domain-specific EthicalFacts builder | | 8 | ⬜ |
| Create custom DEME profile for pilot | | 4 | ⬜ |
| Run pilot for 1 week, collect logs | | 20 | ⬜ |
| Analyze results, write case study | | 8 | ⬜ |
| Publish case study to repo/blog | | 4 | ⬜ |

**Acceptance Criteria:**
- One real system running DEME in production/staging
- Published case study with metrics

---

## 🟣 Priority 5: Community Building (Ongoing)

### 5.1 Community Infrastructure

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Create `CONTRIBUTING.md` | | 2 | ⬜ |
| Create issue templates (bug, feature, question) | | 1 | ⬜ |
| Create PR template | | 1 | ⬜ |
| Label existing issues (`good-first-issue`, etc.) | | 2 | ⬜ |
| Set up GitHub Discussions | | 1 | ⬜ |
| Create Discord roles/channels for contributors | | 2 | ⬜ |

---

### 5.2 Outreach

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Post to r/MachineLearning, r/artificial | | 2 | ⬜ |
| Post to Hacker News (Show HN) | | 1 | ⬜ |
| Submit to AI safety newsletters | | 2 | ⬜ |
| Reach out to MCP community / Anthropic devrel | | 2 | ⬜ |
| Present at local meetup / university seminar | | 4 | ⬜ |

---

### 5.3 Academic Publication

| Task | Owner | Est. Hours | Status |
|------|-------|------------|--------|
| Select target venue (NeurIPS, AAAI, FAccT, etc.) | | 2 | ⬜ |
| Prepare camera-ready paper | | 20 | ⬜ |
| Run experiments for empirical section | | 20 | ⬜ |
| Submit paper | | 4 | ⬜ |
| Prepare supplementary materials / code release | | 8 | ⬜ |

---

## Summary: Effort Estimates

| Priority | Tasks | Total Hours |
|----------|-------|-------------|
| 🔴 P1: Critical Path | 11 | ~25 |
| 🟡 P2: Docs & Demos | 12 | ~40 |
| 🟢 P3: Testing & Quality | 11 | ~35 |
| 🔵 P4: Ecosystem | 10 | ~60 |
| 🟣 P5: Community | 9 | ~50 |
| **Total** | **53** | **~210 hours** |

---

## Suggested Sprint Plan

### Sprint 1 (Weeks 1-2): "Installable & Callable"
- [ ] PyPI package release (v0.1.0)
- [ ] MCP server entry point
- [ ] JSON Schema publishing
- [ ] Basic quick start tutorial

### Sprint 2 (Weeks 3-4): "Documented & Tested"
- [ ] Expand test coverage to 80%
- [ ] API reference docs live
- [ ] MCP integration tutorial
- [ ] CI/CD enhancements

### Sprint 3 (Weeks 5-6): "Demonstrated & Validated"
- [ ] PettingZoo integration demo
- [ ] 5+ example profiles
- [ ] Real-world pilot kickoff
- [ ] Community outreach begins

### Sprint 4 (Weeks 7-8): "Published & Growing"
- [ ] Pilot case study published
- [ ] Paper submitted (if targeting deadline)
- [ ] First external contributor PR merged
- [ ] 100+ GitHub stars (stretch goal)

---

## Definition of Done: 9/10

- [ ] `pip install erisml` works
- [ ] `erisml-mcp-server` runs out of the box
- [ ] Published JSON Schemas at stable URLs
- [ ] 80%+ test coverage on core modules
- [ ] Working MCP + Claude tutorial
- [ ] Working PettingZoo demo
- [ ] One real-world pilot with case study
- [ ] 3+ contributors beyond original author
- [ ] 100+ GitHub stars
- [ ] One peer-reviewed or preprint publication

---

*Document created: December 2025*
*Review cadence: Weekly sprint planning*
