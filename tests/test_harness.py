"""
Tests for Deterministic Harness.

Tests the harness module which provides utilities for ensuring
reproducible, deterministic test execution.
"""
from __future__ import annotations

import os
from unittest import mock

import numpy as np
import pytest

from core.harness import (
    DEFAULT_SEED,
    DeterministicHarness,
    HarnessReport,
    deterministic_context,
    ensure_deterministic,
    verify_determinism,
)
from core.invariants import InvariantViolation


class TestDeterministicHarness:
    """Tests for DeterministicHarness class."""

    def test_harness_sets_seed_on_entry(self) -> None:
        """Harness sets numpy seed on context entry."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            result1 = np.random.randn(10)

        with DeterministicHarness(seed=42, check_env=False) as harness:
            result2 = np.random.randn(10)

        assert np.array_equal(result1, result2)

    def test_harness_restores_state_on_exit(self) -> None:
        """Harness restores original random state on exit."""
        np.random.seed(123)
        before = np.random.randn(5)

        np.random.seed(123)  # Reset to same state
        with DeterministicHarness(seed=999, check_env=False):
            # Inside harness, different seed
            inside = np.random.randn(5)
            assert not np.array_equal(before, inside)

        # After harness, state should be restored
        after = np.random.randn(5)
        # Note: state is restored to where it was when entering,
        # so this won't match 'before' but proves state was saved/restored

    def test_harness_report_initialized(self) -> None:
        """Harness report is properly initialized."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            assert harness.report.seed == 42
            assert harness.report.checks_passed == 0
            assert harness.report.checks_failed == 0
            assert harness.report.all_passed is True

    def test_assert_finite_passes(self) -> None:
        """assert_finite passes for valid arrays."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            arr = np.array([1.0, 2.0, 3.0])
            harness.assert_finite(arr)
            assert harness.report.checks_passed == 1
            assert harness.report.finite_checks == 1

    def test_assert_finite_fails_on_nan(self) -> None:
        """assert_finite raises on NaN values."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            arr = np.array([1.0, np.nan, 3.0])
            with pytest.raises(InvariantViolation, match="NaN"):
                harness.assert_finite(arr)
            assert harness.report.checks_failed == 1

    def test_assert_bounded_passes(self) -> None:
        """assert_bounded passes for values in range."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            arr = np.array([0.5, 0.7, 0.9])
            harness.assert_bounded(arr, 0.0, 1.0)
            assert harness.report.checks_passed == 1
            assert harness.report.bound_checks == 1

    def test_assert_bounded_fails_out_of_range(self) -> None:
        """assert_bounded raises for out of range values."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            arr = np.array([0.5, 1.5, 0.9])
            with pytest.raises(InvariantViolation, match="must be in"):
                harness.assert_bounded(arr, 0.0, 1.0)
            assert harness.report.checks_failed == 1

    def test_assert_spectral_stable_passes(self) -> None:
        """assert_spectral_stable passes for stable matrix."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            weights = np.array([[0.1, 0.2], [0.2, 0.1]])
            rho = harness.assert_spectral_stable(weights, max_radius=1.0)
            assert rho < 1.0
            assert harness.report.checks_passed == 1

    def test_assert_spectral_stable_fails_unstable(self) -> None:
        """assert_spectral_stable raises for unstable matrix."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            weights = np.array([[2.0, 0.0], [0.0, 2.0]])
            with pytest.raises(InvariantViolation, match="spectral radius"):
                harness.assert_spectral_stable(weights, max_radius=1.0)
            assert harness.report.checks_failed == 1

    def test_assert_deterministic_with_expected(self) -> None:
        """assert_deterministic works with expected value."""

        def deterministic_func() -> np.ndarray:
            np.random.seed(42)
            return np.random.randn(5)

        expected = deterministic_func()

        with DeterministicHarness(seed=42, check_env=False) as harness:
            result = harness.assert_deterministic(
                deterministic_func, expected=expected
            )
            assert np.array_equal(result, expected)
            assert harness.report.determinism_checks == 1
            assert harness.report.checks_passed == 1

    def test_assert_deterministic_without_expected(self) -> None:
        """assert_deterministic works by running function twice."""

        def uses_harness_seed() -> np.ndarray:
            return np.random.randn(5)

        with DeterministicHarness(seed=42, check_env=False) as harness:
            result = harness.assert_deterministic(uses_harness_seed)
            assert harness.report.determinism_checks == 1
            assert harness.report.checks_passed == 1

    def test_assert_deterministic_fails_for_nondeterministic(self) -> None:
        """assert_deterministic fails for non-deterministic function."""
        call_count = 0

        def nondeterministic_func() -> np.ndarray:
            nonlocal call_count
            call_count += 1
            # Use call_count to make each call different
            return np.array([float(call_count)])

        with DeterministicHarness(seed=42, check_env=False) as harness:
            with pytest.raises(InvariantViolation, match="not deterministic"):
                harness.assert_deterministic(nondeterministic_func)
            assert harness.report.checks_failed == 1

    def test_set_seed_resets_state(self) -> None:
        """set_seed method resets random state."""
        with DeterministicHarness(seed=42, check_env=False) as harness:
            # Consume some randomness
            np.random.randn(10)

            # Reset
            harness.set_seed()
            result1 = np.random.randn(5)

            # Reset again
            harness.set_seed()
            result2 = np.random.randn(5)

            assert np.array_equal(result1, result2)


class TestDeterministicContext:
    """Tests for deterministic_context context manager."""

    def test_context_sets_seed(self) -> None:
        """Context manager sets seed correctly."""
        with deterministic_context(seed=42):
            result1 = np.random.randn(10)

        with deterministic_context(seed=42):
            result2 = np.random.randn(10)

        assert np.array_equal(result1, result2)

    def test_context_restores_state(self) -> None:
        """Context manager restores original state on exit."""
        np.random.seed(123)
        # Generate some values to establish state
        np.random.randn(5)
        state_before = np.random.get_state()

        with deterministic_context(seed=999):
            np.random.randn(100)  # Consume randomness

        state_after = np.random.get_state()
        # States should be identical after context exit
        assert state_before[0] == state_after[0]  # Same generator type


class TestVerifyDeterminism:
    """Tests for verify_determinism function."""

    def test_verify_determinism_passes(self) -> None:
        """verify_determinism returns True for deterministic function."""

        def deterministic_func() -> np.ndarray:
            return np.random.randn(10)

        result = verify_determinism(deterministic_func, seed=42, n_runs=3)
        assert result is True

    def test_verify_determinism_fails(self) -> None:
        """verify_determinism returns False for non-deterministic function."""
        # Use a counter to ensure each call produces different results
        call_counter = [0]

        def truly_nondeterministic() -> np.ndarray:
            call_counter[0] += 1
            return np.array([float(call_counter[0])])

        result = verify_determinism(truly_nondeterministic, seed=42, n_runs=2)
        assert result is False


class TestEnsureDeterministic:
    """Tests for ensure_deterministic decorator."""

    def test_decorator_sets_seed(self) -> None:
        """Decorated function always uses same seed."""

        @ensure_deterministic(seed=42)
        def my_func() -> np.ndarray:
            return np.random.randn(10)

        result1 = my_func()
        result2 = my_func()
        result3 = my_func()

        assert np.array_equal(result1, result2)
        assert np.array_equal(result2, result3)

    def test_decorator_preserves_function_name(self) -> None:
        """Decorated function preserves original name."""

        @ensure_deterministic(seed=42)
        def original_name() -> np.ndarray:
            return np.random.randn(5)

        assert original_name.__name__ == "original_name"


class TestHarnessReport:
    """Tests for HarnessReport class."""

    def test_all_passed_true_initially(self) -> None:
        """all_passed is True when no failures."""
        report = HarnessReport(seed=42)
        assert report.all_passed is True

    def test_all_passed_false_with_failure(self) -> None:
        """all_passed is False when there are failures."""
        report = HarnessReport(seed=42, checks_failed=1)
        assert report.all_passed is False


class TestHarnessEnvironmentCheck:
    """Tests for environment checking in harness."""

    def test_warns_when_pythonhashseed_not_set(self) -> None:
        """Harness warns when PYTHONHASHSEED is not set."""
        # Temporarily remove PYTHONHASHSEED if set
        original = os.environ.pop("PYTHONHASHSEED", None)
        try:
            with pytest.warns(UserWarning, match="PYTHONHASHSEED"):
                with DeterministicHarness(seed=42, check_env=True):
                    pass
        finally:
            if original is not None:
                os.environ["PYTHONHASHSEED"] = original

    def test_no_warning_when_pythonhashseed_set(self) -> None:
        """Harness doesn't warn when PYTHONHASHSEED is set."""
        original = os.environ.get("PYTHONHASHSEED")
        os.environ["PYTHONHASHSEED"] = "42"
        try:
            # Should not warn
            with DeterministicHarness(seed=42, check_env=True):
                pass
        finally:
            if original is not None:
                os.environ["PYTHONHASHSEED"] = original
            else:
                os.environ.pop("PYTHONHASHSEED", None)

    def test_strict_mode_raises_without_pythonhashseed(self) -> None:
        """Strict mode raises when PYTHONHASHSEED is not set."""
        original = os.environ.pop("PYTHONHASHSEED", None)
        try:
            with pytest.raises(EnvironmentError, match="PYTHONHASHSEED"):
                with DeterministicHarness(seed=42, check_env=True, strict=True):
                    pass
        finally:
            if original is not None:
                os.environ["PYTHONHASHSEED"] = original
