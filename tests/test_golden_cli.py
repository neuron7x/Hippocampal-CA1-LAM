import subprocess
import sys

import pytest

import test_golden_standalone
from validation import golden_tests


@pytest.mark.parametrize(
    ("module", "case"),
    [
        (test_golden_standalone, "test_laminar_inference"),
        (golden_tests, "test_laminar_inference_golden"),
    ],
)
def test_golden_command_fails_when_a_case_fails(module, case, monkeypatch, capsys):
    def failed_case():
        raise AssertionError("controlled regression")

    monkeypatch.setattr(module, case, failed_case)

    assert module.main() == 1
    assert "controlled regression" in capsys.readouterr().out


@pytest.mark.parametrize("module", ["test_golden_standalone", "validation.golden_tests"])
def test_golden_command_requires_assertions(module):
    result = subprocess.run(
        [sys.executable, "-O", "-m", module], capture_output=True, text=True, check=False
    )

    assert result.returncode == 1
    assert "assertions to be enabled" in result.stderr
