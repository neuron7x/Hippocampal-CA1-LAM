## Copilot PR Body Requirements

- Begin every PR body with either `Phase: N`/`Phase: N.N` (e.g., `Phase: 0.0`) or `Closes #<issue-number>`.
- Always include a `Verification:` section (or `## Verification`) with at least one command, such as:

  ```bash
  python -m pytest -q
  ```

- Keep the PR template structure intact—do not remove or rename the required sections.
