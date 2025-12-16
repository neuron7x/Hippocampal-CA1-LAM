# CI Policy

The CI policy gate enforces safe defaults for GitHub Actions:

- Every workflow must declare explicit top-level `permissions` (least privilege).
- All third-party actions must be pinned to a commit SHA (no floating tags).
- `pull_request_target` triggers are blocked unless justified.
- Steps may not run `chmod`/`chown` against the runner workdir or temp paths.

The policy is implemented in `scripts/ci_policy_check.py` and runs on every
push/PR via `.github/workflows/security-ci-policy.yml`. Violations print the
offending file and line number so they can be fixed quickly.
