from __future__ import annotations

import importlib
import sys

_PKG = importlib.import_module("core")
sys.modules[__name__] = _PKG

for _mod in [
    "ca1_network",
    "config",
    "contracts",
    "hierarchical_laminar",
    "invariants",
    "laminar_structure",
    "metrics",
    "neuron_model",
    "theta_swr_switching",
]:
    sys.modules[f"{__name__}.{_mod}"] = importlib.import_module(f"core.{_mod}")

__all__ = getattr(_PKG, "__all__", [])
