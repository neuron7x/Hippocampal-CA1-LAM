# Secrets Policy

Secret scanning is enforced with gitleaks on every push and pull request. The
workflow is pinned to a specific action SHA and uses the minimal permissions
required (`contents: read`). If gitleaks detects a secret, the build fails and a
SARIF report is uploaded as an artifact for triage (14 day retention).

Configuration lives in `.gitleaks.toml` and only includes a small, targeted
allowlist for binary/lock files to avoid masking real leaks.

Run locally with:

```bash
gitleaks detect -c .gitleaks.toml --redact
```
