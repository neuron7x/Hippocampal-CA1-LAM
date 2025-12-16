#!/usr/bin/env python3
"""Validate JSON/YAML configs and GitHub Issue Forms.

Requires PyYAML for YAML parsing; exits with an error if it is missing so the
gate cannot silently skip YAML validation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Dict, List

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    print("PyYAML is required for config validation. Install via `pip install pyyaml`.", file=sys.stderr)
    sys.exit(1)


def list_tracked_files(repo_path: str) -> List[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        files = result.stdout.strip().splitlines()
    except subprocess.CalledProcessError:
        files = []
        for root, _, filenames in os.walk(repo_path):
            if ".git" in root:
                continue
            for name in filenames:
                files.append(os.path.relpath(os.path.join(root, name), repo_path))
    return files


def validate_json(path: str) -> List[str]:
    errors: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            json.load(handle)
    except json.JSONDecodeError as exc:
        errors.append(f"JSON parse error at line {exc.lineno} column {exc.colno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"Cannot read file: {exc}")
    return errors


def validate_issue_form(content: Dict[str, object]) -> List[str]:
    errors: List[str] = []
    if not isinstance(content, dict):
        return ["Issue form must be a mapping"]
    if not content.get("name") or not isinstance(content.get("name"), str):
        errors.append("Missing or invalid 'name' field")
    if not content.get("description") or not isinstance(content.get("description"), str):
        errors.append("Missing or invalid 'description' field")
    if "body" not in content:
        errors.append("Missing required 'body' list")
    elif not isinstance(content["body"], list) or not content["body"]:
        errors.append("'body' must be a non-empty list")
    return errors


def validate_yaml(path: str, repo_path: str) -> List[str]:
    errors: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            content = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        return [f"YAML parse error: {exc}"]
    except OSError as exc:
        return [f"Cannot read file: {exc}"]

    rel = os.path.relpath(path, repo_path)
    if rel.startswith(".github/ISSUE_TEMPLATE/") and rel.endswith(".yml") and os.path.basename(path) != "config.yml":
        errors.extend(validate_issue_form(content if isinstance(content, dict) else {}))
    return errors


def main() -> int:
    repo_path = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
    files = list_tracked_files(repo_path)

    json_files = [os.path.join(repo_path, f) for f in files if f.endswith(".json")]
    yaml_files = [os.path.join(repo_path, f) for f in files if f.endswith((".yml", ".yaml"))]

    total_errors = 0
    for path in sorted(json_files):
        for err in validate_json(path):
            total_errors += 1
            print(f"{os.path.relpath(path, repo_path)}: {err}")

    for path in sorted(yaml_files):
        for err in validate_yaml(path, repo_path):
            total_errors += 1
            print(f"{os.path.relpath(path, repo_path)}: {err}")

    if total_errors:
        print(f"\nFAIL: {total_errors} configuration validation error(s) found.")
        return 1

    print(f"PASS: Validated {len(json_files)} JSON and {len(yaml_files)} YAML file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
