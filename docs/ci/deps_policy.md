# Dependency Vulnerability Policy

The dependency gate runs `pip-audit` on every push and pull request to detect
known vulnerabilities in Python requirements files. The workflow is pinned to a
specific `actions/checkout` and `actions/setup-python` SHA, installs a pinned
version of `pip-audit`, and fails the build on any findings.

If vulnerabilities are detected, JSON and text reports are uploaded as an
artifact for review. Run locally with:

```bash
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt  # when present
```
