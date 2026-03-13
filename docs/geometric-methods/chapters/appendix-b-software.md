# Appendix B: Software Dependencies and Installation

This appendix provides a guide to setting up the software environment
required to reproduce the examples in *Geometric Methods in Computational
Modeling*. The primary framework, `structural-fuzzing`, is available on
PyPI and serves as the backbone for the structural validation techniques
developed throughout the text.

## B.1 Python Version Requirements

All code in this book requires **Python 3.10 or later**. The
`structural-fuzzing` package is tested against Python 3.10, 3.11, 3.12,
and 3.13. We recommend the latest stable release in the 3.12 or 3.13
series for best performance and compatibility.

Python 3.10 is the minimum because the codebase uses modern type
annotation syntax (e.g., `X | Y` union types) introduced in that release.
Earlier versions will fail at import time.

```bash
python --version
```

If you need to manage multiple Python versions, we recommend
[pyenv](https://github.com/pyenv/pyenv) on Linux/macOS or the official
installers from [python.org](https://www.python.org/downloads/) on Windows.

## B.2 Virtual Environment Setup

We strongly recommend creating an isolated virtual environment before
installing any packages.

```bash
# Create
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows cmd)
.venv\Scripts\activate.bat
```

Alternatively, with conda:

```bash
conda create -n geometric-modeling python=3.12
conda activate geometric-modeling
```

**Best practices:**
- Create one virtual environment per project or per book chapter group.
- Pin dependencies with `pip freeze > requirements.txt` after installation.
- Never install packages into your system Python.
- On shared computing environments, use `--user` installs or virtual
  environments to avoid permission issues.

## B.3 The structural-fuzzing Package

The `structural-fuzzing` package (version 0.2.0 at the time of writing)
provides the core framework used throughout this book. It implements
structural validation through parameter-space exploration, Pareto analysis,
sensitivity profiling, robustness quantification, and adversarial threshold
detection.

### Installation

```bash
# Core package (installs NumPy as the sole dependency)
pip install structural-fuzzing

# With ML example dependencies (scikit-learn, pandas)
pip install structural-fuzzing[examples]

# With development tools (pytest, ruff, build, twine)
pip install structural-fuzzing[dev]

# With documentation tools (Sphinx, RTD theme)
pip install structural-fuzzing[docs]

# Everything at once
pip install structural-fuzzing[examples,dev,docs]
```

### Installing from source

```bash
git clone https://github.com/ahb-sjsu/structural-fuzzing.git
cd structural-fuzzing
pip install -e ".[dev,examples,docs]"
```

### Verifying the installation

```python
import structural_fuzzing
print(structural_fuzzing.__version__)  # Should print "0.2.0" or later
```

## B.4 Core and Optional Dependencies

### Core: NumPy (>= 1.24)

NumPy is the only hard dependency. It provides the n-dimensional array
operations underlying all geometric computations: parameter vectors,
perturbation sampling, log-space transformations, and statistical
aggregation. It is installed automatically with `structural-fuzzing`.

### Optional: scikit-learn (>= 1.3)

Required for the machine learning examples in Parts II and III, including
the defect prediction case study. Provides the classifiers and regressors
that serve as evaluation targets for structural fuzzing campaigns. Included
in the `[examples]` extras group.

### Optional: pandas (>= 2.0)

Used in several examples for data loading, preprocessing, and tabular
result formatting. Included in the `[examples]` extras group.

## B.5 Development and Documentation Dependencies

| Package | Version | Group | Purpose |
|---------|---------|-------|---------|
| pytest | >= 8.0 | `[dev]` | Test runner |
| pytest-cov | >= 4.0 | `[dev]` | Coverage reporting |
| ruff | >= 0.3 | `[dev]` | Linting and formatting |
| build | >= 1.0 | `[dev]` | Building distribution packages |
| twine | >= 5.0 | `[dev]` | Uploading to PyPI |
| sphinx | >= 7.0 | `[docs]` | Documentation generator |
| sphinx-rtd-theme | >= 2.0 | `[docs]` | Read the Docs theme |

## B.6 External Libraries for Specific Geometric Methods

Several chapters use specialized libraries beyond `structural-fuzzing`.
These are not dependencies of the package itself but appear in standalone
examples and exercises.

### SciPy -- Matrix Operations and Optimization

```bash
pip install scipy
```

SciPy extends NumPy with sparse matrices, eigenvalue decomposition, spatial
data structures, and optimization routines. Key submodules used in this book:
`scipy.spatial` (Delaunay triangulation, convex hulls, distance matrices),
`scipy.linalg` (matrix decompositions, matrix exponentials),
`scipy.optimize` (minimization, root finding), and
`scipy.sparse` (adjacency and Laplacian matrices).

### GUDHI or Ripser -- Persistent Homology

```bash
pip install gudhi    # Full TDA toolkit (requires C++ compiler)
pip install ripser   # Lightweight alternative for Vietoris-Rips persistence
```

GUDHI provides algorithms for simplicial complexes, persistent homology,
and topological data analysis. Chapters on topological feature extraction
use it for computing Vietoris-Rips complexes and Betti numbers. If GUDHI
installation fails due to compiler requirements, `ripser` offers a faster,
more focused alternative.

### Geoopt -- Riemannian Optimization and Hyperbolic Geometry

```bash
pip install geoopt
```

Geoopt provides Riemannian optimization primitives built on PyTorch,
including manifold-constrained gradient descent on the Poincare ball,
hyperboloid model, and Stiefel manifold. Used in chapters covering
hyperbolic embeddings and curvature-aware optimization. Note: install
PyTorch first (CPU-only is sufficient for this book's examples) via
[pytorch.org](https://pytorch.org/get-started/locally/).

## B.7 Related Packages from the Ecosystem

These packages apply structural fuzzing and geometric methods to specific
domains:

- **eris-econ** (`pip install eris-econ`) -- Geometric economics framework
  implementing multi-dimensional decision manifolds, A* pathfinding on
  economic surfaces, and Bond Geodesic Equilibrium. Validates a 9D
  ethical-economic parameter space against 16 behavioral economics targets.
  Repository: [github.com/ahb-sjsu/eris-econ](https://github.com/ahb-sjsu/eris-econ)

- **eris-ketos** (`pip install eris-ketos`) -- Marine ecosystem modeling
  with geometric structure, extending the decision framework to ecological
  and environmental domains.

- **arc-agi** -- ARC-AGI-2 solver using geometric embeddings, hyperbolic
  rule inference, and adversarial structure probing. Applies fuzzing and
  adversarial threshold techniques to test robustness of learned geometric
  rule representations.
  Repository: [github.com/ahb-sjsu/arc-prize](https://github.com/ahb-sjsu/arc-prize)

## B.8 Chapter Dependency Matrix

The table below shows which packages are required or recommended for each
chapter. "Core" means only `structural-fuzzing` and NumPy are needed.

| Chapter / Part | Core | scikit-learn | pandas | scipy | gudhi/ripser | geoopt |
|----------------|------|-------------|--------|-------|-------------|--------|
| **Part I: Foundations** | | | | | | |
| Ch 1. Introduction to Geometric Modeling | Required | -- | -- | -- | -- | -- |
| Ch 2. Parameter Spaces and Manifolds | Required | -- | -- | Recommended | -- | -- |
| Ch 3. Structural Validation Framework | Required | -- | -- | -- | -- | -- |
| **Part II: Algorithms** | | | | | | |
| Ch 4. Subset Enumeration and Pareto Analysis | Required | Recommended | -- | -- | -- | -- |
| Ch 5. Sensitivity and Ablation Methods | Required | Recommended | Recommended | -- | -- | -- |
| Ch 6. Robustness Quantification (MRI) | Required | -- | -- | Recommended | -- | -- |
| Ch 7. Adversarial Threshold Detection | Required | -- | -- | -- | -- | -- |
| **Part III: Patterns** | | | | | | |
| Ch 8. Compositional Model Building | Required | Recommended | Recommended | -- | -- | -- |
| Ch 9. Topological Feature Analysis | Required | -- | -- | Required | Required | -- |
| Ch 10. Hyperbolic Embeddings | Required | -- | -- | Recommended | -- | Required |
| **Part IV: Systems** | | | | | | |
| Ch 11. Geometric Economics (eris-econ) | Required | -- | Recommended | Recommended | -- | -- |
| Ch 12. Ecological Modeling (eris-ketos) | Required | -- | Recommended | Recommended | -- | -- |
| Ch 13. Abstract Reasoning (arc-agi) | Required | -- | -- | -- | -- | Required |

## B.9 Complete Installation for All Chapters

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install structural-fuzzing with all optional groups
pip install structural-fuzzing[examples,dev,docs]

# Install external geometric libraries
pip install scipy gudhi geoopt

# Install ecosystem packages
pip install eris-econ eris-ketos
```

For a minimal installation covering Parts I and II only:

```bash
pip install structural-fuzzing
```

This installs only `structural-fuzzing` and NumPy, sufficient for
Chapters 1 through 7.

## B.10 Verifying the Full Installation

```python
import sys

for module, name in [("structural_fuzzing", "structural-fuzzing"),
                     ("numpy", "NumPy"), ("sklearn", "scikit-learn"),
                     ("pandas", "pandas"), ("scipy", "SciPy"),
                     ("gudhi", "GUDHI"), ("geoopt", "Geoopt")]:
    try:
        mod = __import__(module)
        print(f"  {name:.<30s} {getattr(mod, '__version__', 'ok')}")
    except ImportError:
        print(f"  {name:.<30s} NOT FOUND")

print(f"\nPython version: {sys.version}")
```

## B.11 Troubleshooting

**pip resolver errors:** Upgrade pip first with `pip install --upgrade pip`.

**GUDHI compiler errors:** GUDHI requires a C++ compiler and CMake. On
Ubuntu: `sudo apt install build-essential cmake`. On macOS:
`xcode-select --install`. Alternatively, use `ripser`.

**Large PyTorch download from geoopt:** Install PyTorch separately first
with the CPU-only variant:
`pip install torch --index-url https://download.pytorch.org/whl/cpu`

**Import errors after installation:** Verify your virtual environment is
activated with `which python` (Linux/macOS) or `where python` (Windows).

**NumPy version conflicts:** If another package pins NumPy < 1.24, use a
separate virtual environment for the book's exercises.

**Platform notes:** On Windows, use PowerShell or WSL. On macOS Apple
Silicon, all packages have native ARM64 wheels. Linux has no special
considerations.

## B.12 Keeping Dependencies Updated

```bash
pip install --upgrade structural-fuzzing   # Update the package
pip freeze > requirements-book.txt         # Record versions for reproducibility
pip install -r requirements-book.txt       # Recreate the environment later
```
