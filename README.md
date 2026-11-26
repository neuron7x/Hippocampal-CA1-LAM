# Hippocampal-CA1-LAM v2.0

**CA1 Hippocampal Laminar Architecture Research Model**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/neuron7x/Hippocampal-CA1-LAM/actions/workflows/python-tests.yml/badge.svg)](https://github.com/neuron7x/Hippocampal-CA1-LAM/actions/workflows/python-tests.yml)

## 📋 Development Roadmap

We're following a comprehensive **8-phase evolution plan** to build v3.0:

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | Foundation Audit | 🔄 In Progress |
| 1 | Atomic Primitives | 📋 Planned |
| 2 | Fractal Regions | 📋 Planned |
| 3 | AI Memory Engine | 📋 Planned |
| 4 | Performance & Scale | 📋 Planned |
| 5 | Biological Fidelity | 📋 Planned |
| 6 | Framework Layer | 📋 Planned |
| 7 | Quality & Release | 📋 Planned |
| 8 | Community & Impact | 📋 Planned |

**📖 [Full Evolution Plan](docs/EVOLUTION_PLAN.md)** | **🎯 [Current Issues](https://github.com/neuron7x/Hippocampal-CA1-LAM/issues?q=is%3Aissue+is%3Aopen+label%3Aroadmap)**

### Contributing to the Roadmap
1. Check the [Evolution Plan](docs/EVOLUTION_PLAN.md) for available tasks
2. Create an issue using the **Phase Task** template
3. Submit a PR referencing the issue
4. Ensure all exit criteria are met

---

## Overview

The research model includes:
- Four laminar sublayers parameterized from the 58,065-cell atlas. The simulation size is configurable.
- Unified W+STP+Ca²⁺ plasticity (Graupner-Brunel PNAS 2012)
- Theta-SWR state switching with replay detection
- AI integration (HippoRAG-inspired LLM memory)
- 100% reproducible (seed=42, golden tests)

## Quick Start

### ⚡ SUPER QUICK START (Recommended)

**One-command installation and verification**:
```bash
bash quick_start.sh
```

This will:
1. ✓ Check Python installation
2. ✓ Create virtual environment
3. ✓ Install all dependencies
4. ✓ Run golden tests
5. ✓ Verify everything works

**Expected output**: `6/6 PASSED ✓` (golden suite)

---

### 🎁 BONUS: Automation Scripts (Time Savers!)

We've included professional automation tools to save your time:

#### 1. Quick Start Script
```bash
bash quick_start.sh
# One-click install + test
```

#### 2. Deploy to GitHub
```bash
bash deploy_to_github.sh
# Automatic GitHub setup and push
```

#### 3. Run All Tests
```bash
bash scripts/run_all_tests.sh
# Golden + unit + integration tests
```

#### 4. Development Setup
```bash
bash setup_dev_environment.sh
# Complete dev environment with pre-commit hooks
```

#### 5. Makefile Commands
```bash
make help          # Show all commands
make install       # Install dependencies
make test          # Run all tests
make format        # Auto-format code
make lint          # Check code quality
make deploy        # Deploy to GitHub
make benchmark     # Performance tests
```

#### 6. Release Creator
```bash
python utils/create_release.py
# Auto-generate release archives + notes
```

---

### 📦 Manual Installation

```bash
# Install
pip install -r requirements.txt

# Verify
python test_golden_standalone.py
# Expected: 6/6 PASSED

# Run demo
python examples/demo_unified_weights.py
```

### 🔒 Security & QA Checklist

Run these before opening a PR to satisfy the merge gates:

```bash
# Secrets / Unicode / config policy
gitleaks detect --config .gitleaks.toml --report-format sarif --report-path gitleaks.sarif
python scripts/unicode_scan.py
python scripts/validate_configs.py .
python scripts/ci_policy_check.py

# Dependency audit
pip-audit -r requirements.txt && pip-audit -r requirements-dev.txt

# Pre-commit formatting & lint (PEP8)
pre-commit install
pre-commit run --all-files

# Tests & coverage
python -m pytest -q
python -m pytest tests/ --cov=. --cov-report=term-missing

# Performance / stress check (optional)
python scripts/benchmark.py --stress-neurons 100000 --stress-steps 5 --stress-conn-prob 1e-4
```

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Usage Examples](docs/USAGE.md)
- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Testing](docs/TESTING.md)
- [CI/CD](.github/CI.md)
- [Retrieval ablation protocol](docs/NECESSITY_ORACLE.md)
- [Contributing](CONTRIBUTING.md)

## Scientific Foundation

Selected parameter sources:
- **13 DOI references** (see [Bibliography](docs/BIBLIOGRAPHY.md))
- **58,065 cells** (Pachicano Nature Comm 2025)
- **Ca²⁺ thresholds** θ_d=1.0μM, θ_p=2.0μM (Graupner PNAS 2012)

## Features

✅ **Public API scaffold** - Minimal CA1Network for quick-start usage  
✅ **Reproducible regression tests** - The golden suite uses seed 42.
✅ **Validated** - 6 deterministic golden tests  
✅ **Research package** - Type hints, tests, CI/CD, and documentation.

The public `CA1Network` scaffold emits synthetic activity. The circuit primitives and retrieval tests support implementation claims within their measured scope. Electrophysiological validation remains open.

## Citation

```bibtex
@software{hippocampal_ca1_lam_2025,
  title = {CA1 Hippocampus Framework v2.0},
  author = {neuron7x},
  year = {2025},
  url = {https://github.com/neuron7x/Hippocampal-CA1-LAM}
}
```

## License

MIT License - see [LICENSE](LICENSE)

## Contact

- Issues: [GitHub Issues](https://github.com/neuron7x/Hippocampal-CA1-LAM/issues)
