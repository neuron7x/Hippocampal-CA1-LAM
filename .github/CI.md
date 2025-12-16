# CI/CD Overview

This repository uses focused security workflows with consistent `security-*` naming.

## Workflows

| Workflow | Purpose |
|----------|---------|
| `python-tests.yml` | Python tests on 3.10, 3.11, 3.12 for every push to `main` and all PRs |
| `security-secrets.yml` | Secret scanning via Gitleaks |
| `security-unicode.yml` | Trojan Source prevention via `scripts/unicode_scan.py` |
| `security-validate-configs.yml` | YAML/JSON validation |
| `security-ci-policy.yml` | Enforces workflow pinning and policy checks |
| `security-actionlint.yml` | Validates GitHub Actions syntax |
| `security-deps.yml` | Dependency vulnerability audit via pip-audit |
| `docs-link-check.yml` | Validates documentation links |
| `phase-validation.yml` | Ensures PR metadata matches the evolution plan |

All workflows trigger on pull requests; security suites also run on pushes to `main`.

## Local Reproduction

```bash
pip install -r requirements-dev.txt

# Security gates
gitleaks detect --config .gitleaks.toml --report-format sarif --report-path gitleaks.sarif
python scripts/unicode_scan.py
python scripts/validate_configs.py .
python scripts/ci_policy_check.py
pip-audit -r requirements.txt && pip-audit -r requirements-dev.txt

# Lint/format (PEP8)
pre-commit install
pre-commit run --all-files

# Tests
python -m pytest -q
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## Deployment

- **Staging/preview:** run `bash deploy_to_github.sh` from a clean branch after all gates pass to publish artifacts to your fork for validation.
- **Production:** merge to `main` only after staging verification and passing CI. All workflow actions are pinned to SHAs for supply-chain safety.

## PR Checklist

- Link to the relevant roadmap issue (e.g., `Phase: X.Y` or `Closes #123`).
- Include `Verification:` with the exact commands executed (tests, audits, benchmarks).
- Attach CI run links or logs showing success for security gates, tests, and coverage.
