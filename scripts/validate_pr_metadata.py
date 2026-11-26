"""Validate the phase reference and verification evidence of a pull request."""

import os
import re
from pathlib import Path

PHASE = re.compile(r"^\s*(?:[-*]\s+)?(?:Phase:\s*\d{1,2}\.\d{1,2}\b|Closes\s+#\d+\b)", re.I | re.M)
VERIFICATION = re.compile(r"^(?:#{1,6}\s+Verification:?|Verification:)\s*$", re.I)
NEXT_HEADING = re.compile(r"^#{1,6}\s+")


def verification_error(body: str) -> str | None:
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    if not PHASE.search(body):
        return "Add a Phase reference or Closes #issue-number."

    in_verification = False
    in_fence = False
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if not in_verification:
            in_verification = not in_fence and bool(VERIFICATION.fullmatch(line))
            continue
        if not in_fence and NEXT_HEADING.match(line):
            break
        if line.strip("-* ").strip() and not line.startswith("#"):
            return None

    return "Add a command or CI run link under Verification."


def main() -> int:
    if not Path(".github/PULL_REQUEST_TEMPLATE.md").is_file():
        print("::error::Missing pull request template.")
        return 1
    error = verification_error(os.environ.get("PR_BODY", ""))
    if error:
        print(f"::error::{error}")
        return 1
    print("Pull request metadata satisfies phase policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
