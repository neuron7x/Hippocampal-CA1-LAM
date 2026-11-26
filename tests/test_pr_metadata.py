import pytest

from scripts.validate_pr_metadata import verification_error


@pytest.mark.parametrize("title", ["## Verification", "Verification:"])
def test_accepts_template_and_legacy_verification_headings(title):
    assert verification_error(f"Phase: 7.3\n{title}\n```bash\nmake check\n```") is None


@pytest.mark.parametrize(
    "body",
    [
        "",
        "<!-- Phase: 7.3 -->\n## Verification\n- make check",
        "Closes #1\n## Verification\n```bash\n# Commands run locally:\n```\n## Testing\nmake check",
    ],
)
def test_requires_phase_and_nonempty_evidence_in_its_own_section(body):
    assert verification_error(body)
