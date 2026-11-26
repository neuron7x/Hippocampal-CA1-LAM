"""Exercise CI guards through the same entry points used in Actions."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run_guard(cwd, script, *args, python_flags=()):
    return subprocess.run(
        [sys.executable, *python_flags, str(ROOT / script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def track(repo, *paths):
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "--", *paths], cwd=repo, check=True)


@pytest.mark.parametrize(
    ("trigger", "job", "diagnostic"),
    [
        (
            "pull_request_target",
            "uses: owner/repo/.github/workflows/check.yml@" + "a" * 40,
            "pull_request_target trigger is disallowed",
        ),
        (
            "[push, pull_request_target]",
            "uses: ./.github/workflows/check.yml",
            "pull_request_target trigger is disallowed",
        ),
        (
            "{pull_request_target: {}}",
            "uses: ./.github/workflows/check.yml",
            "pull_request_target trigger is disallowed",
        ),
        ("push", "uses: owner/repo/.github/workflows/check.yml@main", "not pinned"),
        ("push", "steps: [{uses: 'docker://alpine@sha256:1'}]", "not pinned"),
    ],
)
def test_policy_rejects_disallowed_workflow(tmp_path, trigger, job, diagnostic):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "check.yml").write_text(
        f"on: {trigger}\npermissions: {{}}\njobs:\n  example:\n    {job}\n",
        encoding="utf-8",
    )

    result = run_guard(tmp_path, "scripts/ci_policy_check.py")

    assert result.returncode == 1
    assert diagnostic in result.stdout


def test_policy_accepts_pinned_and_local_references(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "check.yml").write_text(
        f"""on: {{push: {{}}}}
permissions: {{}}
jobs:
  reusable:
    uses: owner/repo/.github/workflows/check.yml@{'a' * 40}
  local:
    runs-on: ubuntu-latest
    steps:
      - uses: ./.github/actions/example
      - uses: docker://alpine@sha256:{'0' * 64}
""",
        encoding="utf-8",
    )

    assert run_guard(tmp_path, "scripts/ci_policy_check.py").returncode == 0


def test_policy_rejects_empty_workflow_directory_and_file(tmp_path):
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    assert run_guard(tmp_path, "scripts/ci_policy_check.py").returncode == 1
    (workflows / "check.yml").write_text("", encoding="utf-8")
    assert run_guard(tmp_path, "scripts/ci_policy_check.py").returncode == 1


def test_unicode_fails_when_git_listing_is_unavailable_or_empty(tmp_path):
    result = run_guard(tmp_path, "scripts/unicode_scan.py")
    assert result.returncode == 1
    assert "git ls-files failed" in result.stderr

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    result = run_guard(tmp_path, "scripts/unicode_scan.py")
    assert result.returncode == 1
    assert "no tracked text files" in result.stderr


def test_unicode_reports_disallowed_controls_in_tracked_paths(tmp_path):
    name = " résumé\nspace.TXT"
    (tmp_path / name).write_text("plain text\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("ignored\n", encoding="utf-8")
    track(tmp_path, name, ".gitignore")
    assert run_guard(tmp_path, "scripts/unicode_scan.py").returncode == 0

    (tmp_path / name).write_text("prefix" + chr(1) + "\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(chr(0x2060) + "\n", encoding="utf-8")

    result = run_guard(tmp_path, "scripts/unicode_scan.py")
    assert result.returncode == 1
    assert ":1:7 U+0001" in result.stdout
    assert ".gitignore:1:1 U+2060" in result.stdout


def test_config_rejects_malformed_tracked_yaml_with_non_ascii_name(tmp_path):
    name = " résumé\nspace.YAML"
    (tmp_path / name).write_text("a: [\n", encoding="utf-8")
    track(tmp_path, name)

    result = run_guard(tmp_path, "scripts/validate_configs.py", ".")

    assert result.returncode == 1
    assert f"{name}: YAML parse error" in result.stdout


def test_config_fails_when_yaml_parser_is_missing(tmp_path):
    (tmp_path / "valid.yml").write_text("a: b\n", encoding="utf-8")
    result = run_guard(
        tmp_path, "scripts/validate_configs.py", ".", python_flags=("-I", "-B", "-S")
    )

    assert result.returncode == 1
    assert "PyYAML is required" in result.stderr


def test_config_checks_source_archive_without_git(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("job: value\n", encoding="utf-8")
    assert run_guard(tmp_path, "scripts/validate_configs.py", ".").returncode == 0

    config.write_bytes(b"invalid utf-8: \xff\n")
    result = run_guard(tmp_path, "scripts/validate_configs.py", ".")
    assert result.returncode == 1
    assert "Cannot read file" in result.stdout
