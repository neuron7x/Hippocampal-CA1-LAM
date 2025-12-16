#!/usr/bin/env python3
"""CI policy enforcement for GitHub Actions workflows."""

from __future__ import annotations

import glob
import os
import re
import sys
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    print("PyYAML is required for CI policy checks. Install with `pip install pyyaml`.")
    sys.exit(1)

WORKFLOW_DIR = os.path.join(".github", "workflows")


def load_workflow(path: str) -> Tuple[Dict[str, Any], List[str]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"{path}: cannot read workflow ({exc})")
        return {}, []
    try:
        parsed = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        print(f"{path}: YAML parse error: {exc}")
        return {}, text.splitlines()
    return parsed, text.splitlines()


def has_pull_request_target(trigger: Any) -> bool:
    if trigger is None:
        return False
    if isinstance(trigger, str):
        return trigger == "pull_request_target"
    if isinstance(trigger, list):
        return any(has_pull_request_target(item) for item in trigger)
    if isinstance(trigger, dict):
        return "pull_request_target" in trigger or any(
            isinstance(k, str) and k == "pull_request_target" for k in trigger.keys()
        )
    return False


def is_sha(ref: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-fA-F]{40}", ref))


def is_pinned(uses_value: str) -> bool:
    if uses_value.startswith("./") or uses_value.startswith("docker://"):
        return True
    if "@" not in uses_value:
        return False
    ref = uses_value.split("@", 1)[1]
    return is_sha(ref)


def find_line(lines: List[str], needle: str) -> int:
    for idx, line in enumerate(lines, start=1):
        if needle in line:
            return idx
    return 1


def record(violations: List[Tuple[str, int, str]], file: str, line: int, reason: str) -> None:
    violations.append((file, line, reason))


def check_workflow(path: str) -> List[Tuple[str, int, str]]:
    data, lines = load_workflow(path)
    rel_path = os.path.relpath(path)
    violations: List[Tuple[str, int, str]] = []

    if "permissions" not in data or data.get("permissions") is None:
        record(violations, rel_path, 1, "Missing explicit top-level permissions block")

    if has_pull_request_target(data.get("on")):
        record(violations, rel_path, find_line(lines, "pull_request_target"), "pull_request_target trigger is not allowed")

    jobs = data.get("jobs", {})
    if isinstance(jobs, dict):
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps", [])
            if not isinstance(steps, list):
                continue
            for step in steps:
                if not isinstance(step, dict):
                    continue
                uses_val = step.get("uses")
                if isinstance(uses_val, str) and not is_pinned(uses_val):
                    record(
                        violations,
                        rel_path,
                        find_line(lines, uses_val),
                        f"Action reference '{uses_val}' is not pinned to a commit SHA",
                    )
                run_val = step.get("run")
                if isinstance(run_val, str):
                    lower_run = run_val.lower()
                    temp_markers = ("/__w", "runner.temp", "runner_temp")
                    if ("chmod" in lower_run or "chown" in lower_run) and any(
                        marker in lower_run for marker in temp_markers
                    ):
                        snippet = run_val.splitlines()[0] if run_val.splitlines() else "chmod"
                        record(
                            violations,
                            rel_path,
                            find_line(lines, snippet.strip()),
                            "Detected chmod/chown on runner workdir or temp directories",
                        )
    return violations


def main() -> int:
    repo = os.getcwd()
    workflow_dir = os.path.join(repo, WORKFLOW_DIR)
    if not os.path.isdir(workflow_dir):
        print("No workflows directory found; nothing to validate.")
        return 0

    all_paths = sorted(
        glob.glob(os.path.join(workflow_dir, "*.yml"))
        + glob.glob(os.path.join(workflow_dir, "*.yaml"))
    )
    violations: List[Tuple[str, int, str]] = []
    for path in all_paths:
        violations.extend(check_workflow(path))

    if violations:
        for file, line, reason in violations:
            print(f"{file}:{line}: {reason}")
        print(f"\nFAIL: {len(violations)} CI policy violation(s) detected.")
        return 1

    print(f"PASS: {len(all_paths)} workflow(s) comply with CI policy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
