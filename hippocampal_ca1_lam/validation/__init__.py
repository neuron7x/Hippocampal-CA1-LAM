from __future__ import annotations

import importlib
import sys

_PKG = importlib.import_module("validation")
sys.modules[__name__] = _PKG

for _mod in ["golden_tests", "validators"]:
    sys.modules[f"{__name__}.{_mod}"] = importlib.import_module(f"validation.{_mod}")

__all__ = getattr(_PKG, "__all__", [])
