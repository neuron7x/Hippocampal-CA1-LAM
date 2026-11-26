#!/usr/bin/env python3
"""
CI policy checks for GitHub Actions workflows.

Enforces:
  - Top-level permissions must be explicitly set (principle of least privilege)
  - All actions must be pinned to immutable SHAs (no floating tags)
  - pull_request_target trigger is blocked by default
  - chmod/chown on runner work/temp directories is disallowed
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - surfaced in CI
    print(f"PyYAML is required: {exc}", file=sys.stderr)
    sys.exit(1)


WORKFLOW_DIR = Path(".github/workflows")
SHA_PATTERN = re.compile(r"[0-9a-fA-F]{40}")
DOCKER_DIGEST_PATTERN = re.compile(r"[^\s@]+@sha256:[0-9a-f]{64}")
BOOLEAN_TAG = "tag:yaml.org,2002:bool"
RUNNER_PATH_PATTERN = re.compile(
    r"(/__w/)|(\${{\s*runner\.temp\s*}})|(\$RUNNER_TEMP)|(\${RUNNER_TEMP})",
    re.IGNORECASE,
)
CHMOD_PATTERN = re.compile(r"\b(?:sudo\s+)?(?:chmod|chown)\b", re.IGNORECASE)


class WorkflowLoader(yaml.SafeLoader):
    """Resolve true/false as booleans while keeping bare workflow keys as strings."""


WorkflowLoader.yaml_implicit_resolvers = {
    first: [(tag, pattern) for tag, pattern in rules if tag != BOOLEAN_TAG]
    for first, rules in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
WorkflowLoader.add_implicit_resolver(
    BOOLEAN_TAG, re.compile(r"^(?:true|false)$", re.IGNORECASE), "tTfF"
)


def find_line_number(lines: list[str], needle: str) -> int:
    for idx, line in enumerate(lines, start=1):
        if needle in line:
            return idx
    return 1


def is_pinned(uses_value: str) -> bool:
    if uses_value.startswith("./"):
        return len(uses_value) > 2
    if uses_value.startswith("docker://"):
        return bool(DOCKER_DIGEST_PATTERN.fullmatch(uses_value.removeprefix("docker://")))
    action, _, ref = uses_value.partition("@")
    return bool(action and SHA_PATTERN.fullmatch(ref))


def extract_triggers(on_field: Any) -> set[str]:
    if isinstance(on_field, str):
        return {on_field}
    if isinstance(on_field, (list, dict)) and all(isinstance(item, str) for item in on_field):
        return set(on_field)
    return set()


def check_workflow(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
        data = yaml.load(content, Loader=WorkflowLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"{path}:1:1 Cannot read workflow: {exc}"]
    if not isinstance(data, dict):
        return [f"{path}:1:1 Workflow must be a mapping"]

    lines = content.splitlines()
    issues: list[str] = []
    if "permissions" not in data:
        issues.append(f"{path}:1:1 Missing top-level permissions block")

    triggers = extract_triggers(data.get("on"))
    if not triggers:
        issues.append(f"{path}:1:1 Missing or invalid workflow triggers")
    if "pull_request_target" in triggers:
        line_no = find_line_number(lines, "pull_request_target")
        issues.append(f"{path}:{line_no}: pull_request_target trigger is disallowed")

    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        return issues + [f"{path}:1:1 Workflow must declare at least one job"]

    def check_uses(entry: dict) -> None:
        if "uses" not in entry:
            return
        value = entry["uses"]
        if not isinstance(value, str) or not is_pinned(value):
            line_no = find_line_number(lines, str(value))
            issues.append(f"{path}:{line_no}: action or workflow {value!r} is not pinned to a SHA")

    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            issues.append(f"{path}:1:1 Job {job_id!r} must be a mapping")
            continue
        check_uses(job)
        steps = job.get("steps", [])
        if not isinstance(steps, list):
            issues.append(f"{path}:1:1 Job {job_id!r} steps must be a list")
            continue
        for step in steps:
            if not isinstance(step, dict):
                issues.append(f"{path}:1:1 Job {job_id!r} step must be a mapping")
                continue
            check_uses(step)
            run_value = step.get("run")
            if isinstance(run_value, str):
                for line in run_value.splitlines():
                    if CHMOD_PATTERN.search(line) and RUNNER_PATH_PATTERN.search(line):
                        line_no = find_line_number(lines, line.strip())
                        issues.append(
                            f"{path}:{line_no}: disallowed chmod/chown on runner workspace/temp"
                        )

    return issues


def main() -> int:
    if not WORKFLOW_DIR.is_dir():
        print("No .github/workflows directory found", file=sys.stderr)
        return 1

    workflow_files = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml"))

    if not workflow_files:
        print("No GitHub Actions workflow files found", file=sys.stderr)
        return 1

    violations: list[str] = []
    for wf in workflow_files:
        violations.extend(check_workflow(wf))

    if violations:
        print("CI policy violations detected:")
        for violation in violations:
            print(violation)
        return 1

    print("All workflows comply with CI policy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
