"""Command-line utilities for Hippocampal CA1-LAM."""

from __future__ import annotations

import argparse
import sys
from typing import Callable, List, Tuple

from .validation import golden_tests

TestCase = Tuple[str, Callable[[], object]]


def _collect_golden_tests() -> List[TestCase]:
    """Return the deterministic golden tests used for smoke validation."""
    return [
        ("Laminar inference", golden_tests.test_laminar_inference_golden),
        ("Network stability", golden_tests.test_network_stability_golden),
        ("Calcium plasticity", golden_tests.test_calcium_plasticity_golden),
        ("Input specificity", golden_tests.test_input_specific_plasticity_golden),
        ("Theta/SWR switching", golden_tests.test_theta_swr_switching_golden),
        ("Reproducibility", golden_tests.test_full_reproducibility),
    ]


def run_golden_suite(args: list[str] | None = None) -> int:
    """Execute the golden suite with optional listing mode (Python 3.10+ baseline)."""
    parser = argparse.ArgumentParser(description="Hippocampal CA1-LAM golden validation suite")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available golden tests without executing them",
    )
    parsed = parser.parse_args(args=args)

    tests = _collect_golden_tests()

    if parsed.list:
        for name, _ in tests:
            print(name)
        return 0

    print("=" * 70)
    print("Hippocampal CA1-LAM :: Golden Validation Suite")
    print("=" * 70)
    passed = 0
    failed = 0

    for name, func in tests:
        try:
            func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as exc:
            print(f"✗ {name}: {exc}")
            failed += 1
        except Exception as exc:  # pragma: no cover - defensive path
            print(f"✗ {name}: ERROR - {exc}")
            failed += 1

    print("-" * 70)
    print(f"RESULTS: {passed}/{len(tests)} passed")

    return 0 if failed == 0 else 1


def main() -> None:
    raise SystemExit(run_golden_suite())


if __name__ == "__main__":
    main()
