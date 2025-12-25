# Project Status – Hippocampal-CA1-LAM (2025-12-25)

## Baseline Verification

| Check | Command | Status |
|-------|---------|--------|
| Editable install (dev) | `pip install -e ".[dev]"` | ✅ |
| Package import | `python -c "import hippocampal_ca1_lam; print(hippocampal_ca1_lam.__version__)"` | ✅ |
| Golden tests | `python -m hippocampal_ca1_lam.cli` | ✅ |
| Pytest suite | `python -m pytest -q` | ✅ |
| Build artifact | `python -m build` | ✅ |

## Claims vs Evidence

| Claim | Evidence | Status | Action |
|-------|----------|--------|--------|
| One-command quick start installs and runs golden tests | `quick_start.sh` provisions venv, installs `.[dev]` optionally, executes `python -m hippocampal_ca1_lam.cli` (6/6 golden) | OK | Keep script in sync with CLI |
| Public API is importable with version | `hippocampal_ca1_lam` package exports `CA1Network`, `UnifiedWeightMatrix`, `NetworkStateController`, `__version__` | OK | Surface new API additions through this module |
| Namespaced imports for legacy modules | Wrapper subpackages (`hippocampal_ca1_lam.core`, etc.) expose existing modules without touching PYTHONPATH | Partial | Gradually migrate callers away from top-level `core/` imports |
| CI validates supported Python versions | `.github/workflows/python-tests.yml` runs on 3.10–3.12 with editable install + build step | OK | Extend matrix if support broadens |
| Build artifacts reproducible | `pyproject.toml` + dev extra includes `build`; CI runs `python -m build` | OK | Publish wheels when ready |
| Legacy docs mention `pip install -r requirements.txt` | Archived manifests (e.g., FINAL_MANIFEST.md) still reference legacy command | PARTIAL | Update or annotate legacy docs in next doc refresh |

## Roadmap / Limitations

- PyPI publication is not yet automated; release remains manual.
- Legacy manifest-style docs may lag behind the pyproject-first workflow.
- GPU/JAX acceleration remains a roadmap item (see docs/EVOLUTION_PLAN.md).
