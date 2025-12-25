from __future__ import annotations

import importlib
import sys

_PKG = importlib.import_module("plasticity")
sys.modules[__name__] = _PKG

for _mod in ["calcium_plasticity", "unified_weights"]:
    sys.modules[f"{__name__}.{_mod}"] = importlib.import_module(f"plasticity.{_mod}")

__all__ = getattr(_PKG, "__all__", [])
