"""
Deterministic Test Harness for Hippocampal CA1-LAM.

This module provides utilities to ensure reproducible, deterministic
test execution:

1. Seed management - consistent random state across numpy
2. Environment checks - verify PYTHONHASHSEED is set
3. Determinism verification - assert same inputs produce same outputs
4. Finite safety guards - detect NaN/Inf early

Usage:
    from core.harness import DeterministicHarness

    with DeterministicHarness(seed=42) as harness:
        result = my_function()
        harness.assert_finite(result)
        harness.assert_deterministic(my_function, expected=result)
"""
from __future__ import annotations

import os
import warnings
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

import numpy as np

from .invariants import (
    InvariantViolation,
    check_bounded,
    check_finite,
    check_spectral_radius,
)


# Default seed for all deterministic operations
DEFAULT_SEED = 42

# Tolerance for floating point comparisons
DEFAULT_RTOL = 1e-10
DEFAULT_ATOL = 1e-10


@dataclass
class HarnessReport:
    """Report from deterministic harness run."""

    seed: int
    checks_passed: int = 0
    checks_failed: int = 0
    finite_checks: int = 0
    determinism_checks: int = 0
    bound_checks: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Check if all checks passed."""
        return self.checks_failed == 0


class DeterministicHarness:
    """
    Context manager for deterministic test execution.

    Provides:
    - Automatic seed setting on entry
    - Seed restoration on exit
    - Helper methods for common invariant checks
    - Report generation

    Example:
        with DeterministicHarness(seed=42) as harness:
            net = CA1Network(N=10, seed=42)
            result = net.simulate(duration_ms=100)
            harness.assert_finite(result['weights'])
            harness.assert_bounded(result['weights'], 0, 100)
    """

    def __init__(
        self,
        seed: int = DEFAULT_SEED,
        check_env: bool = True,
        strict: bool = False,
    ):
        """
        Initialize harness.

        Args:
            seed: Random seed to use
            check_env: Whether to check PYTHONHASHSEED environment
            strict: Whether to raise on warnings
        """
        self.seed = seed
        self.check_env = check_env
        self.strict = strict
        self._original_state: Optional[Dict[str, Any]] = None
        self.report = HarnessReport(seed=seed)

    def __enter__(self) -> "DeterministicHarness":
        """Enter context: set seed and optionally check environment."""
        # Save original numpy random state
        self._original_state = {"numpy": np.random.get_state()}

        # Set deterministic seed
        np.random.seed(self.seed)

        # Check environment
        if self.check_env:
            hash_seed = os.environ.get("PYTHONHASHSEED")
            if hash_seed is None:
                msg = (
                    "PYTHONHASHSEED not set. For full determinism, "
                    "run with PYTHONHASHSEED=42"
                )
                self.report.warnings.append(msg)
                if self.strict:
                    raise EnvironmentError(msg)
                else:
                    warnings.warn(msg, stacklevel=2)

        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> bool:
        """Exit context: restore original random state."""
        if self._original_state is not None:
            np.random.set_state(self._original_state["numpy"])
        return False  # Don't suppress exceptions

    def set_seed(self, seed: Optional[int] = None) -> None:
        """
        Reset to deterministic state.

        Args:
            seed: Optional seed override (uses harness seed if not provided)
        """
        np.random.seed(seed if seed is not None else self.seed)

    def assert_finite(
        self,
        arr: np.ndarray,
        name: str = "array",
    ) -> None:
        """
        Assert array contains only finite values.

        Args:
            arr: Array to check
            name: Name for error messages
        """
        self.report.finite_checks += 1
        try:
            check_finite(arr, name)
            self.report.checks_passed += 1
        except InvariantViolation as e:
            self.report.checks_failed += 1
            self.report.errors.append(str(e))
            raise

    def assert_bounded(
        self,
        arr: np.ndarray,
        low: float,
        high: float,
        name: str = "array",
    ) -> None:
        """
        Assert array values are within bounds.

        Args:
            arr: Array to check
            low: Lower bound (inclusive)
            high: Upper bound (inclusive)
            name: Name for error messages
        """
        self.report.bound_checks += 1
        try:
            check_bounded(arr, low, high, name)
            self.report.checks_passed += 1
        except InvariantViolation as e:
            self.report.checks_failed += 1
            self.report.errors.append(str(e))
            raise

    def assert_spectral_stable(
        self,
        weights: np.ndarray,
        max_radius: float = 1.0,
        name: str = "weights",
    ) -> float:
        """
        Assert weight matrix has spectral radius <= max_radius.

        Args:
            weights: Square weight matrix
            max_radius: Maximum allowed spectral radius
            name: Name for error messages

        Returns:
            Computed spectral radius
        """
        try:
            rho = check_spectral_radius(weights, max_radius, name)
            self.report.checks_passed += 1
            return rho
        except InvariantViolation as e:
            self.report.checks_failed += 1
            self.report.errors.append(str(e))
            raise

    def assert_deterministic(
        self,
        func: Callable[..., np.ndarray],
        *args: Any,
        expected: Optional[np.ndarray] = None,
        rtol: float = DEFAULT_RTOL,
        atol: float = DEFAULT_ATOL,
        **kwargs: Any,
    ) -> np.ndarray:
        """
        Assert function produces deterministic output.

        If expected is provided, compares against it.
        Otherwise, runs function twice and compares results.

        Args:
            func: Function to test
            *args: Positional arguments to function
            expected: Optional expected output
            rtol: Relative tolerance
            atol: Absolute tolerance
            **kwargs: Keyword arguments to function

        Returns:
            Function result

        Raises:
            InvariantViolation: If function is not deterministic
        """
        self.report.determinism_checks += 1

        # First run
        self.set_seed()
        result1 = func(*args, **kwargs)

        if expected is not None:
            # Compare to expected
            if not np.allclose(result1, expected, rtol=rtol, atol=atol):
                max_diff = np.max(np.abs(result1 - expected))
                msg = (
                    f"Function {func.__name__} produced unexpected result: "
                    f"max difference = {max_diff}"
                )
                self.report.checks_failed += 1
                self.report.errors.append(msg)
                raise InvariantViolation(msg)
        else:
            # Run again and compare
            self.set_seed()
            result2 = func(*args, **kwargs)

            if not np.allclose(result1, result2, rtol=rtol, atol=atol):
                max_diff = np.max(np.abs(result1 - result2))
                msg = (
                    f"Function {func.__name__} is not deterministic: "
                    f"max difference = {max_diff}"
                )
                self.report.checks_failed += 1
                self.report.errors.append(msg)
                raise InvariantViolation(msg)

        self.report.checks_passed += 1
        return result1

    def assert_state_bounded_after_steps(
        self,
        simulate_func: Callable[[], Dict[str, np.ndarray]],
        n_steps: int = 1,
        max_state_size: int = 1000000,
    ) -> Dict[str, np.ndarray]:
        """
        Assert state doesn't grow unboundedly after simulation steps.

        Args:
            simulate_func: Function that runs simulation and returns state dict
            n_steps: Number of simulation steps
            max_state_size: Maximum allowed total state size in elements

        Returns:
            Final simulation result
        """
        result = None
        for _ in range(n_steps):
            result = simulate_func()

        if result is None:
            raise ValueError("simulate_func must return a result")

        # Check total state size
        total_elements = sum(
            arr.size for arr in result.values() if isinstance(arr, np.ndarray)
        )

        if total_elements > max_state_size:
            msg = f"State size {total_elements} exceeds maximum {max_state_size}"
            self.report.checks_failed += 1
            self.report.errors.append(msg)
            raise InvariantViolation(msg)

        self.report.checks_passed += 1
        return result


@contextmanager
def deterministic_context(seed: int = DEFAULT_SEED):
    """
    Simple context manager for deterministic execution.

    Usage:
        with deterministic_context(seed=42):
            result = np.random.randn(10)
            # Will always produce same result for seed=42

    Args:
        seed: Random seed
    """
    original_state = np.random.get_state()
    np.random.seed(seed)
    try:
        yield
    finally:
        np.random.set_state(original_state)


def verify_determinism(
    func: Callable[..., np.ndarray],
    *args: Any,
    seed: int = DEFAULT_SEED,
    n_runs: int = 2,
    rtol: float = DEFAULT_RTOL,
    atol: float = DEFAULT_ATOL,
    **kwargs: Any,
) -> bool:
    """
    Verify a function produces deterministic outputs.

    Args:
        func: Function to test
        *args: Positional arguments
        seed: Random seed to use
        n_runs: Number of runs to compare
        rtol: Relative tolerance
        atol: Absolute tolerance
        **kwargs: Keyword arguments

    Returns:
        True if all runs produce identical results
    """
    results = []

    for _ in range(n_runs):
        np.random.seed(seed)
        result = func(*args, **kwargs)
        results.append(result)

    # Compare all results to the first
    reference = results[0]
    for i, result in enumerate(results[1:], 1):
        if not np.allclose(reference, result, rtol=rtol, atol=atol):
            return False

    return True


F = TypeVar("F", bound=Callable[..., Any])


def ensure_deterministic(seed: int = DEFAULT_SEED) -> Callable[[F], F]:
    """
    Decorator to ensure function runs deterministically.

    Usage:
        @ensure_deterministic(seed=42)
        def my_simulation():
            return np.random.randn(10)

    Args:
        seed: Random seed to set before each call
    """
    import functools

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            np.random.seed(seed)
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
