# ErisML Library

ErisML is a modeling layer for governed, foundation-model-enabled agents
operating in pervasive computing environments (homes, hospitals, campuses,
factories, vehicles, etc.).

ErisML provides a single, machine-interpretable and human-legible representation of
- **(i) environment state and dynamics**
- **(ii) agents and their capabilities and beliefs**
- **(iii) intents and utilities**
- **(iv) norms (permissions, obligations, prohibitions, sanctions)**
- **(v) multi-agent strategic interaction**

We define a concrete syntax, a formal grammar, denotational semantics, and
an execution model that treats norms as first-class constraints on action, 
introduces longitudinal safety metrics such as Norm Violation Rate (NVR) and
Alignment Drift Velocity (ADV), and supports compilation to planners, verifiers, and simulators.

![CI](https://github.com/ahb-sjsu/erisml-lib/actions/workflows/ci.yaml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

This repository contains a production-style Python library with:

- Modern `src/` layout and `pyproject.toml`
- GitHub Actions CI using:
  - **Black 24.4.2** for formatting checks
  - **Ruff** for linting
  - **Taplo** for TOML validation
  - **Pytest** for tests
- Core ErisML implementation:
  - Language grammar (Lark)
  - Typed AST (Pydantic)
  - Core IR (environment, agents, norms)
  - Runtime engine with a norm gate and metrics
  - PettingZoo adapter for multi-agent RL
  - PDDL/tarski adapter stub for planning
- An executable TinyHome example
- A basic test suite

## Quickstart (Windows / PowerShell)

```powershell
cd erisml-lib

python -m venv .venv
.\.venv\Scripts\activate

pip install -e ".[dev]"

pytest
```

## Project Layout

```text
erisml-lib/
  pyproject.toml
  README.md
  .gitignore
  .github/
    workflows/
      ci.yaml

  src/
    erisml/
      __init__.py
      language/
        grammar.lark
        ast.py
        parser.py
      core/
        types.py
        model.py
        norms.py
        engine.py
      interop/
        pettingzoo_adapter.py
        pddl_adapter.py
      metrics/
        telemetry.py
      examples/
        tiny_home.py

  tests/
    test_basic.py
```

## TinyHome Example

Run:

```bash
python -m erisml.examples.tiny_home
```

You should see:

- An initial TinyHome state (two rooms, one human, one robot, lights off)
- A legal action: toggle the light in the human's room
- An attempted norm-violating action (moving into a forbidden room) being blocked
- Final state and norm metrics (step count and NVR)

## CI Pipeline

The workflow in `.github/workflows/ci.yaml`:

1. Checks out the repository on Ubuntu.
2. Sets up Python 3.12.
3. Installs the library in editable mode with dev dependencies.
4. Installs Black 24.4.2, Ruff, and Taplo.
5. Runs:
   - `black --check src tests`
   - `ruff check src tests`
   - `taplo lint pyproject.toml`
   - `pytest`
6. Fails the build if the working tree is not clean at the end.

## Coding Style

- Black 24.4.2 is the single source of truth for formatting.
- Ruff enforces common lint rules (flake8-like).
- Type hints are included and can be checked with mypy (not wired into CI by default).

## License

MIT by default. Adjust `pyproject.toml` and add a LICENSE file if needed.
