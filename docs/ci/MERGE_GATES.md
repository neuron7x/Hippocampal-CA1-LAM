# Canonical integration

On the canonical GitHub repository, verify the Actions budget allows runners to start and enable CodeQL code scanning in advanced setup. Keep default setup off when the committed workflow is responsible for SARIF upload. Verify Dependabot alerts, version updates, and secret scanning in the repository's security settings.

1. Open a PR into `main` and inspect the workflow run's event and SHA. Require `CI gate`, `Validate PR metadata`, and `Analyze Python` to pass, and resolve any CodeQL findings according to their disposition.
2. Confirm the three distribution artifacts, their checksums, and the three CycloneDX reports for that same run. Verify the GitHub Actions app emitted each expected check.
3. Enforce those checks in an active `main` ruleset bound to the GitHub Actions app. Require PRs and an up-to-date base, disallow branch deletion and force pushes, and leave bypass empty where supported. Enforce approval only with a second eligible reviewer. The metadata and CodeQL checks currently cover PRs, so configure corresponding merge-queue checks before turning on a merge queue.
4. On a disposable control PR, remove its verification evidence, then restore it. Confirm the metadata check fails and reruns after the edit. Review the local gate predicate against a missing result and a failed matrix result.
5. Merge only after observing the required statuses. Verify the new `main` SHA, the post-merge CI and CodeQL runs, and the external link run. Use a revert PR for rollback.

See [CI details](../../.github/CI.md) for local commands. Earlier logs in this directory are historical snapshots tied to their own runs.
