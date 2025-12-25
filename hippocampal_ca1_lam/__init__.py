"""
Public API surface for the Hippocampal CA1-LAM package.

This module exposes a stable, minimal interface for downstream users and
provides a single source of truth for the package version.
"""

from __future__ import annotations

from .core.ca1_network import CA1Network, SimulationResult
from .core.theta_swr_switching import NetworkState, NetworkStateController, StateTransitionParams
from .data.biophysical_parameters import get_default_parameters
from .plasticity.unified_weights import UnifiedWeightMatrix

__all__ = [
    "__version__",
    "CA1Network",
    "SimulationResult",
    "UnifiedWeightMatrix",
    "NetworkState",
    "NetworkStateController",
    "StateTransitionParams",
    "get_default_parameters",
]

# Keep version in sync with pyproject.toml / setup.py
__version__ = "2.0.0"
